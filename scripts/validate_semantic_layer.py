#!/usr/bin/env python3
"""시맨틱 레이어 v3 정합성 게이트 — src/semantic/* 교차 검증.

검사 항목:
  C1  파일 파싱      : YAML 5종 + JSON Schema 1종 로드 가능 여부
  C2  관계 코드      : entities.yaml relations ⊆ ontology.yaml relation_types
  C3  엔티티 클래스  : entities.yaml class ⊆ ontology.yaml entity_types.families
  C4  지표 바인딩    : indicator_bindings의 entity(term_id)·indicator 실존 여부
  C5  용어 사전 참조 : metrics.yaml dictionary_terms ⊆ entities.yaml term_id
  C6  쿼리 템플릿    : query_templates 지표 ↔ metrics 지표 상호 커버리지(경고)
  C7  인과엣지 계약  : 필수 필드·방향 어휘·관계 코드·evidence(S-5)·validated 서명(S-1)
  C8  DAG 무결성     : 전역 순환 검사 + 메커니즘 최소 1개 + 노드 역할 일관성
  C9  provenance 계약: SourceDocument 6필드·EvidenceSpan 4필드 선언 확인
  C10 이벤트 인스턴스: data/semantic/events/*.json — event_schema 필수 키·evidence 검증
  C11 신호 태그 매핑 : signal_tag_mapping ↔ UNSTR 레지스트리 ↔ metrics 정합
  C12 일별 신호 브리지: signal_tag_mapping.daily_codes ↔ DAILY_UNSTRUCTURED 레지스트리 정합
  C13 기법·선례 원장 : methods.yaml — 어휘·중복·원문 파일 실존·기법 참조(applies_to) 정합

종료 코드: warn 모드(기본)=항상 0(리포트만) · --strict=위반 존재 시 1.
관리: P1-06 · 실행 지점: unstructured_analysis.yml (비정형 파이프라인 게이트)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_DIR = ROOT / "src" / "semantic"
EVENTS_DIR = ROOT / "data" / "semantic" / "events"
REFERENCES_DIR = ROOT / "docs" / "research_desk" / "references"

EDGE_DIRECTIONS = {"UP", "DOWN", "CONTEXT"}
EDGE_STATUSES = {"candidate", "validated", "rejected"}
DOMAIN_VALIDATORS = {"P1-01", "P1-02", "P1-03", "P1-04"}
PROV_SOURCE_DOC_REQUIRED = {
    "document_id", "source_name", "file_path", "file_sha256", "publish_date", "ingested_at",
}
PROV_EVIDENCE_SPAN_REQUIRED = {"document_id", "page", "exact_quote", "extractor_version"}
EDGE_EVIDENCE_REQUIRED = {"source_type", "ref", "locator"}
PDF_SPAN_REQUIRED = PROV_EVIDENCE_SPAN_REQUIRED
EVENT_REQUIRED_KEYS = {"event_id", "event_type", "event_date", "region", "evidence", "confidence"}
EVENT_EVIDENCE_REQUIRED = {"document_id", "page", "exact_quote"}

# C13 — methods.yaml(v3.2 예측 로직 선례 층) 통제 어휘
METHOD_VERDICTS = {"채용", "Challenger 검토 대기", "배경", "인용 주의", "반면교사"}
METHOD_GOALS = {"G1", "G2", "G3", "W0", "공통"}
PRECEDENT_GOALS = {"G1", "G2", "G3", "W0", "배경"}
METHOD_ROLES = {"champion", "challenger", "baseline", "diagnostic", "frozen"}
METHOD_FAMILIES = {"statistical", "ml", "econometric", "simulation", "nonparametric"}
PRECEDENT_STATUSES = {"등재", "반영 완료", "대기"}
METHOD_REQUIRED = {"name", "name_ko", "family", "goal", "role", "contract", "status"}
PRECEDENT_REQUIRED = {"title", "authors_year", "ref", "method", "target_goal", "verdict",
                      "applies_to", "constraints", "evidence", "linked_contract", "status"}
PRECEDENT_EVIDENCE_REQUIRED = {"locator", "quote_ko"}


class Report:
    """위반(violation)·경고(warning) 수집기."""

    def __init__(self) -> None:
        self.violations: list[str] = []
        self.warnings: list[str] = []
        self.infos: list[str] = []

    def violation(self, check: str, msg: str) -> None:
        self.violations.append(f"[{check}] {msg}")

    def warning(self, check: str, msg: str) -> None:
        self.warnings.append(f"[{check}] {msg}")

    def info(self, check: str, msg: str) -> None:
        self.infos.append(f"[{check}] {msg}")


def _load_yaml(path: Path, report: Report) -> dict[str, Any] | None:
    try:
        with path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if not isinstance(data, dict):
            report.violation("C1", f"{path.name} — 최상위 구조가 매핑이 아님")
            return None
        return data
    except FileNotFoundError:
        report.violation("C1", f"{path.name} — 파일 없음 (경로: {path})")
        return None
    except yaml.YAMLError as exc:
        report.violation("C1", f"{path.name} — YAML 파싱 실패: {exc}")
        return None


def _load_json(path: Path, report: Report) -> dict[str, Any] | None:
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        report.violation("C1", f"{path.name} — 파일 없음 (경로: {path})")
        return None
    except json.JSONDecodeError as exc:
        report.violation("C1", f"{path.name} — JSON 파싱 실패: {exc}")
        return None


def _collect_terms(entities: dict[str, Any]) -> list[dict[str, Any]]:
    """entities.yaml의 그룹별 용어 리스트를 평탄화한다."""
    terms: list[dict[str, Any]] = []
    for value in entities.values():
        if isinstance(value, list):
            terms.extend(t for t in value if isinstance(t, dict))
    return terms


def check_relations(terms: list[dict[str, Any]], ontology: dict[str, Any], report: Report) -> None:
    """C2 — entities.yaml relations 코드가 ontology relation_types에 정의됐는지 검사."""
    defined = {r.get("code") for r in ontology.get("relation_types", [])}
    for term in terms:
        raw = str(term.get("relations", "") or "")
        for code in (c.strip() for c in raw.split(",") if c.strip()):
            if code not in defined:
                report.violation(
                    "C2", f"{term.get('term_id')} — 미정의 관계 코드 '{code}' (ontology 미등록)"
                )


def check_entity_classes(
    terms: list[dict[str, Any]], ontology: dict[str, Any], report: Report
) -> None:
    """C3 — entities.yaml class 값이 ontology entity_types.families에 등재됐는지 검사."""
    registered: set[str] = set()
    for family in ontology.get("entity_types", {}).get("families", []):
        registered.update(family.get("classes", []))
    for term in terms:
        cls = term.get("class")
        if cls and cls not in registered:
            report.violation("C3", f"{term.get('term_id')} — 미등재 엔티티 클래스 '{cls}'")


def _known_indicators(ontology: dict[str, Any], metrics: dict[str, Any]) -> set[str]:
    known = {m.get("code") for m in metrics.get("metrics", [])}
    bindings = ontology.get("indicator_bindings", {})
    for group in ("unstructured", "structured"):
        known.update(b.get("indicator") for b in bindings.get(group, []))
    known.update(bindings.get("unstructured_derived", {}).get("codes", []))
    known.discard(None)
    return known


def check_indicator_bindings(
    ontology: dict[str, Any],
    metrics: dict[str, Any],
    term_ids: set[str],
    report: Report,
) -> None:
    """C4 — 바인딩의 term_id 실존 + unstructured 바인딩 지표의 metrics.yaml 정의 여부."""
    bindings = ontology.get("indicator_bindings", {})
    metric_codes = {m.get("code") for m in metrics.get("metrics", [])}
    for group in ("unstructured", "structured"):
        for binding in bindings.get(group, []):
            indicator = binding.get("indicator", "?")
            for term in binding.get("entities", []):
                if term not in term_ids:
                    report.violation("C4", f"{indicator} — 존재하지 않는 term_id '{term}' 바인딩")
            if group == "unstructured" and indicator not in metric_codes:
                report.violation(
                    "C4", f"{indicator} — metrics.yaml INDICATOR_DEFINITION 미정의(비정형 지표)"
                )
    if not bindings.get("unstructured_derived", {}).get("codes"):
        report.warning("C4", "UNSTR_* 파생 지표 레지스트리가 비어 있음 — 존재 계약 부재")
    _check_structured_patterns(bindings, term_ids, report)


def _check_structured_patterns(
    bindings: dict[str, Any], term_ids: set[str], report: Report
) -> None:
    """C4 확장 — indicator_bindings.structured_patterns(선택 키) 계약 검사.

    정형 지표를 개별 코드가 아니라 이름 규칙(regex)으로 엔티티에 잇는 바인딩이다.
    키가 없으면 조용히 건너뛴다(도입 전 저장소와의 호환 — 부재는 결함이 아님).
    """
    patterns = bindings.get("structured_patterns")
    if not patterns:
        return
    if not isinstance(patterns, list):
        report.violation("C4", "structured_patterns — 리스트가 아님(항목 목록이어야 함)")
        return
    for idx, item in enumerate(patterns):
        if not isinstance(item, dict):
            report.violation("C4", f"structured_patterns[{idx}] — 매핑이 아님")
            continue
        label = item.get("pattern") or f"index {idx}"
        for field in ("pattern", "regex", "entities"):
            if not item.get(field):
                report.violation("C4", f"structured_patterns '{label}' — 필수 필드 '{field}' 누락")
        regex = item.get("regex")
        if isinstance(regex, str):
            try:
                re.compile(regex)
            except re.error as exc:
                report.violation("C4", f"structured_patterns '{label}' — regex 컴파일 실패: {exc}")
        elif regex is not None:
            report.violation("C4", f"structured_patterns '{label}' — regex가 문자열이 아님")
        entities = item.get("entities") or []
        if not isinstance(entities, list):
            report.violation("C4", f"structured_patterns '{label}' — entities가 리스트가 아님")
            continue
        for term in entities:
            if term not in term_ids:
                report.violation(
                    "C4", f"structured_patterns '{label}' — 존재하지 않는 term_id '{term}'"
                )


def check_dictionary_terms(
    metrics: dict[str, Any], term_ids: set[str], report: Report
) -> None:
    """C5 — metrics.yaml dictionary_terms가 entities.yaml에 실존하는지 검사."""
    for metric in metrics.get("metrics", []):
        code = metric.get("code", "?")
        terms = metric.get("dictionary_terms")
        if not terms:
            report.warning("C5", f"{code} — dictionary_terms 누락(용어 사전 미연결)")
            continue
        for term in terms:
            if term not in term_ids:
                report.violation("C5", f"{code} — 존재하지 않는 term_id '{term}' 참조")


def check_query_templates(
    templates: dict[str, Any], metrics: dict[str, Any], report: Report
) -> None:
    """C6 — 템플릿 지표 ↔ metrics 지표 상호 커버리지(불일치는 경고 — 감사 갭 7)."""
    metric_codes = {m.get("code") for m in metrics.get("metrics", [])}
    template_codes = {t.get("indicator") for t in templates.get("templates", [])}
    for code in sorted(template_codes - metric_codes):
        report.warning("C6", f"템플릿 지표 {code} — metrics.yaml INDICATOR_DEFINITION 없음")
    for code in sorted(metric_codes - template_codes):
        report.warning("C6", f"지표 {code} — query_templates.yaml 템플릿 없음")
    defaults = templates.get("defaults", {})
    if not defaults.get("evidence_return", {}).get("require_evidence_snippet"):
        report.violation("C6", "defaults.evidence_return.require_evidence_snippet 미선언(S-5)")


def check_causal_edges(
    ontology: dict[str, Any],
    metrics: dict[str, Any],
    term_ids: set[str],
    report: Report,
) -> None:
    """C7 — 인과엣지 필수 필드·어휘·관계 코드·evidence(S-5)·validated 서명(S-1) 검사."""
    edges = ontology.get("causal_edges", [])
    if not edges:
        report.violation("C7", "causal_edges 원장이 비어 있음")
        return
    defined_relations = {r.get("code") for r in ontology.get("relation_types", [])}
    known_indicators = _known_indicators(ontology, metrics)
    seen_ids: set[str] = set()
    for edge in edges:
        eid = edge.get("edge_id", "?")
        if eid in seen_ids:
            report.violation("C7", f"{eid} — edge_id 중복")
        seen_ids.add(eid)
        for field in ("label_ko", "category", "cause", "mechanisms", "outcome",
                      "direction", "status", "evidence"):
            if not edge.get(field):
                report.violation("C7", f"{eid} — 필수 필드 '{field}' 누락")
        if edge.get("direction") not in EDGE_DIRECTIONS:
            report.violation("C7", f"{eid} — direction '{edge.get('direction')}' 어휘 위반")
        if edge.get("status") not in EDGE_STATUSES:
            report.violation("C7", f"{eid} — status '{edge.get('status')}' 어휘 위반")
        for term in edge.get("cause", {}).get("entity_terms", []):
            if term not in term_ids:
                report.violation("C7", f"{eid} — cause에 존재하지 않는 term_id '{term}'")
        for indicator in edge.get("indicators", []):
            if indicator not in known_indicators:
                report.violation("C7", f"{eid} — 미등록 지표 '{indicator}' 참조")
        for step in edge.get("mechanisms", []):
            relation = step.get("relation")
            if relation == "DIRECT_CAUSE_TO_PRICE":
                report.violation("C7", f"{eid} — 금지 관계 DIRECT_CAUSE_TO_PRICE 사용")
            elif relation not in defined_relations:
                report.violation("C7", f"{eid} — 미정의 관계 코드 '{relation}'")
        if edge.get("outcome", {}).get("relation") != "MECHANISM_AFFECTS_OUTCOME":
            report.violation("C7", f"{eid} — outcome.relation은 MECHANISM_AFFECTS_OUTCOME 고정")
        for evidence in edge.get("evidence", []) or []:
            missing = EDGE_EVIDENCE_REQUIRED - set(evidence)
            if missing:
                report.violation("C7", f"{eid} — evidence 필수 필드 누락: {sorted(missing)}")
            if evidence.get("source_type") == "pdf_span":
                span_missing = PDF_SPAN_REQUIRED - set(evidence)
                if span_missing:
                    report.violation(
                        "C7",
                        f"{eid} — pdf_span EvidenceSpan 계약 위반(누락: {sorted(span_missing)})",
                    )
        if edge.get("status") == "validated":
            validators = set(edge.get("validated_by", []))
            if not validators:
                report.violation("C7", f"{eid} — validated인데 validated_by 서명 없음(S-1)")
            elif not validators & DOMAIN_VALIDATORS:
                report.warning("C7", f"{eid} — 도메인 검증자(P1-01~04) 서명 없음: {validators}")
            if not edge.get("evidence"):
                report.violation("C7", f"{eid} — validated인데 evidence 없음(S-5)")


def check_dag(ontology: dict[str, Any], report: Report) -> None:
    """C8 — 전역 순환 검사 + 메커니즘 최소 개수 + 노드 역할 일관성."""
    edges = ontology.get("causal_edges", [])
    min_mechanisms = int(ontology.get("dag_constraints", {}).get("min_mechanism_nodes", 1))
    adjacency: dict[str, set[str]] = {}
    causes: set[str] = set()
    mechanisms: set[str] = set()
    outcomes: set[str] = set()
    for edge in edges:
        eid = edge.get("edge_id", "?")
        cause_node = edge.get("cause", {}).get("node")
        outcome_node = edge.get("outcome", {}).get("node")
        mech_nodes = [m.get("node") for m in edge.get("mechanisms", [])]
        if len(mech_nodes) < min_mechanisms:
            report.violation(
                "C8", f"{eid} — 메커니즘 노드 {len(mech_nodes)}개(<{min_mechanisms}) — "
                "Cause→Price 직접 연결 금지 위반"
            )
        path = [cause_node, *mech_nodes, outcome_node]
        if None in path:
            report.violation("C8", f"{eid} — 노드 누락으로 경로 구성 불가")
            continue
        causes.add(cause_node)
        mechanisms.update(mech_nodes)
        outcomes.add(outcome_node)
        for src, dst in zip(path, path[1:]):
            adjacency.setdefault(src, set()).add(dst)
    overlap_out = (causes | mechanisms) & outcomes
    if overlap_out:
        report.violation("C8", f"결과 노드가 원인·메커니즘으로 재사용됨(순환 위험): {sorted(overlap_out)}")
    overlap_cm = causes & mechanisms
    if overlap_cm:
        report.warning("C8", f"원인·메커니즘 역할 중복 노드: {sorted(overlap_cm)}")
    # 반복 DFS 순환 검사 (white=0, gray=1, black=2)
    color: dict[str, int] = {node: 0 for node in adjacency}
    for start in adjacency:
        if color.get(start, 0) != 0:
            continue
        stack: list[tuple[str, list[str]]] = [(start, [start])]
        while stack:
            node, path_so_far = stack.pop()
            if color.get(node, 0) == 2:
                continue
            if color.get(node, 0) == 1:
                color[node] = 2
                continue
            color[node] = 1
            stack.append((node, path_so_far))  # 후처리(black 전환)용 재삽입
            for nxt in adjacency.get(node, ()):
                if color.get(nxt, 0) == 1 and nxt in path_so_far:
                    cycle = " → ".join(path_so_far[path_so_far.index(nxt):] + [nxt])
                    report.violation("C8", f"DAG 순환 발견: {cycle}")
                elif color.get(nxt, 0) == 0:
                    stack.append((nxt, path_so_far + [nxt]))
    report.info("C8", f"DAG 노드 {len(color)}개 · 원인 {len(causes)} · "
                      f"메커니즘 {len(mechanisms)} · 결과 {len(outcomes)}")


def check_provenance_contract(provenance: dict[str, Any], report: Report) -> None:
    """C9 — provenance.yaml 필수 필드 선언이 계약 기준을 충족하는지 검사."""
    declared_doc = set(provenance.get("source_document", {}).get("required", []))
    missing_doc = PROV_SOURCE_DOC_REQUIRED - declared_doc
    if missing_doc:
        report.violation("C9", f"SourceDocument 필수 필드 선언 누락: {sorted(missing_doc)}")
    declared_span = set(provenance.get("evidence_span", {}).get("required", []))
    missing_span = PROV_EVIDENCE_SPAN_REQUIRED - declared_span
    if missing_span:
        report.violation("C9", f"EvidenceSpan 필수 필드 선언 누락: {sorted(missing_span)}")
    if not provenance.get("extractor_registry"):
        report.warning("C9", "extractor_registry가 비어 있음 — 추출 버전 이력 추적 불가")


def check_event_instances(report: Report) -> None:
    """C10 — data/semantic/events/*.json 인스턴스의 event_schema 필수 계약 검사."""
    if not EVENTS_DIR.exists():
        report.info("C10", "data/semantic/events/ 없음 — 이벤트 인스턴스 검사 건너뜀(P1-05 Phase B)")
        return
    files = sorted(EVENTS_DIR.glob("*.json"))
    if not files:
        report.info("C10", "이벤트 인스턴스 0건 — 검사 건너뜀")
        return
    for path in files:
        payload = _load_json(path, report)
        if payload is None:
            continue
        events = payload if isinstance(payload, list) else [payload]
        for event in events:
            eid = event.get("event_id", path.name)
            missing = EVENT_REQUIRED_KEYS - set(event)
            if missing:
                report.violation("C10", f"{eid} — 필수 키 누락: {sorted(missing)}")
            evidence = event.get("evidence") or []
            if not evidence:
                report.violation("C10", f"{eid} — evidence 최소 1건 필요(근거 없는 이벤트 저장 금지)")
            for span in evidence:
                span_missing = EVENT_EVIDENCE_REQUIRED - set(span)
                if span_missing:
                    report.violation("C10", f"{eid} — evidence 필수 필드 누락: {sorted(span_missing)}")
            status = event.get("review_status", "extracted")
            if status not in {"extracted", "validated", "rejected"}:
                report.violation("C10", f"{eid} — review_status '{status}' 어휘 위반")


def check_daily_codes(ont: dict, rep: "Report") -> None:
    """C12(A-198): signal_tag_mapping.daily_codes ↔ 일별 아카이브 지표 정합.

    daily_codes는 일별 비정형 신호(DAILY_UNSTRUCTURED)를 온톨로지 태그에 잇는
    브리지다 — 코드 중복·미배정 일별 지표를 점검한다(승격은 여전히 수동 — S-1).
    """
    tags = (ont.get("signal_tag_mapping") or {}).get("tags") or []
    assigned: list[str] = []
    for t in tags:   # 태그는 일반 순회 — 신규 태그가 늘어도 코드 변경 없이 반영된다
        if not isinstance(t, dict):
            continue
        assigned.extend(t.get("daily_codes") or [])
    dups = {c for c in assigned if assigned.count(c) > 1}
    if dups:
        rep.violation("C12", f"daily_codes 중복 배정: {sorted(dups)}")
    try:
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
        from daily_unstructured_digest import DAILY_UNSTRUCTURED  # type: ignore
        all_daily: set[str] = set()
        for codes in DAILY_UNSTRUCTURED.values():
            all_daily.update(codes or [])
        unmapped = sorted(all_daily - set(assigned))
        if unmapped:
            rep.warning("C12", f"온톨로지 태그 미배정 일별 지표 {len(unmapped)}종: {unmapped[:8]}…"
                               if len(unmapped) > 8 else
                               f"온톨로지 태그 미배정 일별 지표 {len(unmapped)}종: {unmapped}")
        unknown = sorted(set(assigned) - all_daily)
        if unknown:
            rep.violation("C12", f"daily_codes에 실존하지 않는 지표: {unknown}")
    except Exception as exc:   # 의존성 부재·모듈 오류 어느 쪽이든 교차 검사만 생략(비치명)
        rep.warning("C12", f"daily_unstructured_digest 임포트 불가({type(exc).__name__}) — 교차 검사 생략")


def check_signal_tag_mapping(
    ontology: dict[str, Any],
    metrics: dict[str, Any],
    term_ids: set[str],
    report: Report,
) -> None:
    """C11 — 신호 태그 매핑 ↔ UNSTR 레지스트리 ↔ metrics 정합 검사."""
    mapping = ontology.get("signal_tag_mapping", {})
    tags = mapping.get("tags", [])
    if not tags:
        report.violation("C11", "signal_tag_mapping.tags가 비어 있음 — 태그 3원화 미해소")
        return
    registry = set(
        ontology.get("indicator_bindings", {}).get("unstructured_derived", {}).get("codes", [])
    )
    metric_codes = {m.get("code") for m in metrics.get("metrics", [])}
    mapped_unstr: set[str] = set()
    for tag in tags:
        tag_ko = tag.get("tag_ko", "?")
        for code in tag.get("unstr_codes", []):
            mapped_unstr.add(code)
            if code not in registry:
                report.violation("C11", f"태그 '{tag_ko}' — UNSTR 레지스트리 미등록 코드 '{code}'")
        absa = tag.get("absa_indicator")
        if absa is not None and absa not in metric_codes:
            report.violation("C11", f"태그 '{tag_ko}' — metrics.yaml 미정의 aspect 지표 '{absa}'")
        for term in tag.get("entities", []):
            if term not in term_ids:
                report.violation("C11", f"태그 '{tag_ko}' — 존재하지 않는 term_id '{term}'")
    unmapped = registry - mapped_unstr
    if unmapped:
        report.violation("C11", f"태그 매핑 없는 UNSTR 코드: {sorted(unmapped)}")


def _load_methods(report: Report) -> dict[str, Any] | None:
    """methods.yaml 로드 — 부재·파싱 실패는 C13 위반으로 기록(다른 검사는 계속 진행)."""
    path = SEMANTIC_DIR / "methods.yaml"
    try:
        with path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except FileNotFoundError:
        report.violation("C13", f"methods.yaml — 파일 없음 (경로: {path})")
        return None
    except yaml.YAMLError as exc:
        report.violation("C13", f"methods.yaml — YAML 파싱 실패: {exc}")
        return None
    if not isinstance(data, dict):
        report.violation("C13", "methods.yaml — 최상위 구조가 매핑이 아님")
        return None
    return data


def check_methods_layer(methods: dict[str, Any] | None, report: Report) -> None:
    """C13 — methods.yaml(예측 로직 선례 층 v3.2) 무결성 검사.

    문헌은 기법을 정당화할 뿐 대체하지 않는다. 따라서 검사는 세 가지에 집중한다.
      ① 판정·목표·역할이 통제 어휘 안인가(자유 서술 판정 금지)
      ② 인용한 원문이 references/ 에 실재하는가(근거 없는 등재 차단 — S-5)
      ③ 선례가 가리키는 기법(applies_to)이 실존하는가(끊어진 참조 차단)
    """
    if methods is None:
        return   # 파일 부재·파싱 실패는 로더가 C13 위반으로 이미 기록
    if not methods.get("schema_version"):
        report.violation("C13", "methods.yaml — schema_version 선언 없음")
    declared = set(methods.get("verdict_vocab") or [])
    if not declared:
        report.violation("C13", "methods.yaml — verdict_vocab 선언 없음(판정 어휘 미고정)")
    elif declared != METHOD_VERDICTS:
        report.warning(
            "C13",
            f"verdict_vocab 선언이 검증기 기준과 다름 — 파일 {sorted(declared)} / "
            f"기준 {sorted(METHOD_VERDICTS)}",
        )

    seen_ids: set[str] = set()

    def _dup(item_id: str) -> None:
        if item_id in seen_ids:
            report.violation("C13", f"{item_id} — id 중복")
        seen_ids.add(item_id)

    am_ids: set[str] = set()
    for method in methods.get("analysis_methods") or []:
        mid = method.get("id", "?")
        _dup(mid)
        am_ids.add(mid)
        for field in sorted(METHOD_REQUIRED - set(method)):
            report.violation("C13", f"{mid} — 필수 필드 '{field}' 누락")
        if method.get("goal") not in METHOD_GOALS:
            report.violation("C13", f"{mid} — goal '{method.get('goal')}' 어휘 위반")
        if method.get("role") not in METHOD_ROLES:
            report.violation("C13", f"{mid} — role '{method.get('role')}' 어휘 위반")
        if method.get("family") not in METHOD_FAMILIES:
            report.violation("C13", f"{mid} — family '{method.get('family')}' 어휘 위반")
        if not method.get("leakage_rules"):
            report.warning("C13", f"{mid} — leakage_rules 없음(누수 규율 미명시)")

    precedents = methods.get("method_precedents") or []
    for precedent in precedents:
        pid = precedent.get("id", "?")
        _dup(pid)
        for field in sorted(PRECEDENT_REQUIRED - set(precedent)):
            if field in {"applies_to", "constraints"}:
                continue   # 빈 리스트가 정당한 판정(배경 등재)이라 존재 여부만 아래에서 확인
            report.violation("C13", f"{pid} — 필수 필드 '{field}' 누락")
        if "applies_to" not in precedent:
            report.violation("C13", f"{pid} — applies_to 키 없음(빈 목록이라도 명시)")
        verdict = precedent.get("verdict")
        if verdict not in METHOD_VERDICTS:
            report.violation("C13", f"{pid} — verdict '{verdict}' 어휘 위반")
        goals = precedent.get("target_goal") or []
        if isinstance(goals, str):
            goals = [goals]
        if not goals:
            report.violation("C13", f"{pid} — target_goal 비어 있음")
        for goal in goals:
            if goal not in PRECEDENT_GOALS:
                report.violation("C13", f"{pid} — target_goal '{goal}' 어휘 위반")
        if precedent.get("status") not in PRECEDENT_STATUSES:
            report.violation("C13", f"{pid} — status '{precedent.get('status')}' 어휘 위반")
        for am in precedent.get("applies_to") or []:
            if am not in am_ids:
                report.violation("C13", f"{pid} — 존재하지 않는 기법 id '{am}' 참조")
        ref = precedent.get("ref")
        if not ref:
            report.violation("C13", f"{pid} — ref(원문 파일명) 없음")
        elif not ((REFERENCES_DIR / str(ref)).is_file()
                  or (REFERENCES_DIR / "summaries" / f"{Path(str(ref)).stem}.md").is_file()):
            # 원문 PDF는 저작권상 저장소 밖(로컬) 보관 — 요약이 작업 입력이므로 둘 중 하나면 출처 추적 가능(2026-11-24)
            report.violation("C13", f"{pid} — 원문·요약 모두 없음: references/{ref}")
        evidence = precedent.get("evidence") or {}
        if not isinstance(evidence, dict):
            report.violation("C13", f"{pid} — evidence가 매핑이 아님")
        else:
            for field in sorted(PRECEDENT_EVIDENCE_REQUIRED - set(evidence)):
                report.violation("C13", f"{pid} — evidence 필수 필드 '{field}' 누락(S-5)")
    report.info(
        "C13",
        f"기법 {len(am_ids)}종 · 선례 {len(precedents)}건 로드 — "
        f"채용 {sum(1 for p in precedents if p.get('verdict') == '채용')} · "
        f"검토 대기 {sum(1 for p in precedents if p.get('verdict') == 'Challenger 검토 대기')}",
    )


def run_checks() -> Report:
    report = Report()
    entities = _load_yaml(SEMANTIC_DIR / "entities.yaml", report)
    metrics = _load_yaml(SEMANTIC_DIR / "metrics.yaml", report)
    ontology = _load_yaml(SEMANTIC_DIR / "ontology.yaml", report)
    templates = _load_yaml(SEMANTIC_DIR / "query_templates.yaml", report)
    provenance = _load_yaml(SEMANTIC_DIR / "provenance.yaml", report)
    event_schema = _load_json(SEMANTIC_DIR / "event_schema.json", report)
    if event_schema is not None and "evidence" not in event_schema.get("required", []):
        report.violation("C1", "event_schema.json — evidence가 required에 없음(S-5 위반)")
    methods = _load_methods(report)
    check_methods_layer(methods, report)
    if not all(x is not None for x in (entities, metrics, ontology, templates, provenance)):
        return report  # 파싱 실패 시 후속 교차 검사는 무의미
    assert entities and metrics and ontology and templates and provenance
    terms = _collect_terms(entities)
    term_ids = {t.get("term_id") for t in terms}
    term_ids.discard(None)
    report.info("C1", f"용어 {len(terms)}건 · 관계 {len(ontology.get('relation_types', []))}종 · "
                      f"인과엣지 {len(ontology.get('causal_edges', []))}건 로드")
    check_relations(terms, ontology, report)
    check_entity_classes(terms, ontology, report)
    check_indicator_bindings(ontology, metrics, term_ids, report)
    check_dictionary_terms(metrics, term_ids, report)
    check_query_templates(templates, metrics, report)
    check_causal_edges(ontology, metrics, term_ids, report)
    check_dag(ontology, report)
    check_provenance_contract(provenance, report)
    check_event_instances(report)
    check_signal_tag_mapping(ontology, metrics, term_ids, report)
    check_daily_codes(ontology, report)
    return report


def render(report: Report, mode: str) -> str:
    lines = [
        "# 시맨틱 레이어 정합성 검증 리포트 (v3)",
        f"- 모드: {mode} · 위반 {len(report.violations)}건 · 경고 {len(report.warnings)}건",
    ]
    if report.violations:
        lines.append("\n## 위반 (게이트 차단 대상)")
        lines.extend(f"- 🔴 {v}" for v in report.violations)
    else:
        lines.append("- ✅ 위반 없음")
    if report.warnings:
        lines.append("\n## 경고 (잔여 갭 — 차단하지 않음)")
        lines.extend(f"- 🟡 {w}" for w in report.warnings)
    if report.infos:
        lines.append("\n## 정보")
        lines.extend(f"- ℹ️ {i}" for i in report.infos)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="시맨틱 레이어 v3 정합성 게이트")
    parser.add_argument("--strict", action="store_true",
                        help="위반 존재 시 exit 1 (기본은 warn 모드 — 리포트만 출력)")
    args = parser.parse_args()
    mode = "strict" if args.strict else "warn"
    report = run_checks()
    print(render(report, mode))
    if args.strict and report.violations:
        print(f"\n[오류] 시맨틱 레이어 검증 실패: 위반 {len(report.violations)}건. 위 목록을 확인하세요.")
        return 1
    if report.violations:
        print(f"\n[경고] 위반 {len(report.violations)}건 존재 — warn 모드이므로 게이트는 통과 처리함.")
    else:
        print("\n[완료] 시맨틱 레이어 정합성 검증 통과.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
