"""시맨틱 레이어(YAML) → Obsidian 볼트 '보기' 내보내기.

정본은 저장소 YAML(`src/semantic/entities.yaml`·`ontology.yaml`)이며 볼트는 읽기용 사본이다.
볼트에서 고친 내용은 다음 내보내기에서 덮어쓰인다 — 수정은 YAML에서 하고 검증기를 통과시킨다.

산출(기본 `data/vault_view/Nexus`, gitignore):
  Nexus 홈.md            목차·건수·편집 규칙
  용어/{표준명}.md        entities.yaml 용어(별칭 = 국문명·약어·동의어·TERM-ID → [[TERM-041]]도 연결됨)
  인과/{CE-xxx}.md        ontology.yaml causal_edges(원인→경로→결과 노드·근거·지표)
  노드/{노드}.md          인과 DAG 노드(들어오고 나가는 사슬 — 그래프 보기용)
  분류/{분류}.md          용어 분류 허브
  문헌 요약/{파일}.md     references/summaries 요약(원문·전문 변환본은 내보내지 않음 — 저작권)

실행: docker exec -w /repo docker-runner-1 python scripts/export_obsidian_vault.py
볼트 반영: 호스트에서 scripts/sync_obsidian_vault.ps1 (도커는 Google Drive 가상 드라이브를 보지 못함)
"""
from __future__ import annotations

import os
import re
import shutil
from collections import defaultdict
from pathlib import Path

import yaml

ENTITIES = Path("src/semantic/entities.yaml")
ONTOLOGY = Path("src/semantic/ontology.yaml")
SUMMARIES = Path("docs/research_desk/references/summaries")
OUT = Path(os.environ.get("NEXUS_VAULT_EXPORT", "data/vault_view/Nexus"))
MARKER = ".nexus_managed"  # 이 표지가 있는 폴더만 비우고 다시 씀(사용자 노트 보호)
META_KEYS = {"version", "source", "erd_ref", "managed_by"}
BAD_CHARS = re.compile(r'[\\/:*?"<>|#^\[\]]')
BANNER = "> [!info] 저장소 YAML에서 생성된 보기임. 수정은 `{src}`에서 하고 검증기 통과 후 다시 내보낼 것."


def safe(name: str) -> str:
    return BAD_CHARS.sub("-", str(name)).strip(" .") or "unnamed"


def fm(d: dict) -> str:
    return "---\n" + yaml.safe_dump(d, allow_unicode=True, sort_keys=False).strip() + "\n---\n"


def load() -> tuple[dict, dict]:
    with ENTITIES.open(encoding="utf-8") as f:
        ent = yaml.safe_load(f)
    with ONTOLOGY.open(encoding="utf-8") as f:
        ont = yaml.safe_load(f)
    return ent, ont


def term_names(ent: dict) -> dict[str, str]:
    """TERM-ID → 노트 파일명(표준명, 중복 시 ID 덧붙임)."""
    names: dict[str, str] = {}
    seen: set[str] = set()
    for key, terms in ent.items():
        if key in META_KEYS or not isinstance(terms, list):
            continue
        for t in terms:
            n = safe(t.get("canonical") or t["term_id"])
            if n.lower() in seen:
                n = f"{n} ({t['term_id']})"
            seen.add(n.lower())
            names[t["term_id"]] = n
    return names


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def edge_nodes(e: dict) -> list[str]:
    return [e["cause"]["node"], *[m["node"] for m in e.get("mechanisms", [])], e["outcome"]["node"]]


def export_terms(ent: dict, names: dict[str, str], edges_by_term: dict[str, list[str]]) -> dict[str, list[str]]:
    by_cat: dict[str, list[str]] = defaultdict(list)
    for key, terms in ent.items():
        if key in META_KEYS or not isinstance(terms, list):
            continue
        for t in terms:
            name = names[t["term_id"]]
            cat = t.get("category") or key
            by_cat[cat].append(name)
            aliases = [a for a in [t["term_id"], t.get("canonical_ko"), t.get("abbr"), *(t.get("synonyms") or [])] if a]
            meta = {"term_id": t["term_id"], "aliases": aliases, "class": t.get("class"), "status": t.get("status"),
                    "price_direction": t.get("price_direction"), "priority": t.get("priority"),
                    "tags": ["nexus/용어", f"nexus/{safe(t.get('class') or 'Unclassified')}"]}
            lines = [fm(meta), f"# {t.get('canonical')} ({t.get('canonical_ko') or ''})", "",
                     BANNER.format(src=ENTITIES), "",
                     f"- 분류: [[분류/{safe(cat)}|{cat}]] · {t.get('subcategory') or ''}",
                     f"- 정의: {t.get('definition') or '—'}",
                     f"- 해석 규칙: {t.get('interpretation_rules') or '—'}",
                     f"- 영향 대상: {t.get('impact_target') or '—'} · 단위: {t.get('unit_range') or '—'}",
                     f"- 경보 기준: {t.get('alert_criteria') or '—'}",
                     f"- 관계 유형: {t.get('relations') or '—'} · 관리 관점: {t.get('owner_agent') or '—'}"]
            if edges_by_term.get(t["term_id"]):
                lines += ["", "## 관련 인과 사슬", *[f"- [[인과/{eid}|{eid}]]" for eid in edges_by_term[t["term_id"]]]]
            write(OUT / "용어" / f"{name}.md", "\n".join(lines) + "\n")
    for cat, items in by_cat.items():
        body = [fm({"tags": ["nexus/분류"]}), f"# {cat}", "", f"용어 {len(items)}개", "",
                *[f"- [[용어/{n}|{n}]]" for n in sorted(items)]]
        write(OUT / "분류" / f"{safe(cat)}.md", "\n".join(body) + "\n")
    return by_cat


def export_edges(ont: dict, names: dict[str, str]) -> tuple[int, int]:
    node_in: dict[str, list[str]] = defaultdict(list)
    node_out: dict[str, list[str]] = defaultdict(list)
    for e in ont.get("causal_edges", []):
        eid, nodes = e["edge_id"], edge_nodes(e)
        for a, b in zip(nodes, nodes[1:]):
            node_out[a].append(eid)
            node_in[b].append(eid)
        chain = " → ".join(f"[[노드/{safe(n)}|{n}]]" for n in nodes)
        terms = [names[t] for t in e["cause"].get("entity_terms", []) if t in names]
        lag = e.get("lag_trading_days") or {}
        meta = {"edge_id": eid, "direction": e.get("direction"), "status": e.get("status"),
                "category": e.get("category"), "lag_min": lag.get("min"), "lag_max": lag.get("max"),
                "tags": ["nexus/인과", f"nexus/status/{e.get('status')}"]}
        lines = [fm(meta), f"# {eid} {e.get('label_ko', '')}", "", BANNER.format(src=ONTOLOGY), "",
                 f"**사슬**: {chain}", "", f"- 방향: {e.get('direction')} · 상태: {e.get('status')}",
                 f"- 시차: {lag.get('min')}~{lag.get('max')} 거래일 — {e.get('lag_basis') or ''}",
                 f"- 원인 용어: {', '.join(f'[[용어/{n}|{n}]]' for n in terms) or '—'}",
                 f"- 지표: {', '.join(f'`{i}`' for i in e.get('indicators', [])) or '—'}"]
        if e.get("interpretation_rules"):
            lines.append(f"- 해석 규칙: {e['interpretation_rules']}")
        ev = e.get("evidence") or []
        if ev:
            lines += ["", f"## 근거 ({len(ev)}건)"]
            lines += [f"- {x.get('source_type', '')}: `{x.get('ref', '')}` {x.get('locator', '')} — {x.get('note', '')}" for x in ev]
        write(OUT / "인과" / f"{safe(eid)}.md", "\n".join(lines) + "\n")
    for n in set(node_in) | set(node_out):
        body = [fm({"tags": ["nexus/노드"]}), f"# {n}", ""]
        if node_in.get(n):
            body += ["## 들어오는 사슬", *[f"- [[인과/{x}|{x}]]" for x in sorted(set(node_in[n]))], ""]
        if node_out.get(n):
            body += ["## 나가는 사슬", *[f"- [[인과/{x}|{x}]]" for x in sorted(set(node_out[n]))]]
        write(OUT / "노드" / f"{safe(n)}.md", "\n".join(body) + "\n")
    return len(ont.get("causal_edges", [])), len(set(node_in) | set(node_out))


def export_summaries() -> int:
    if not SUMMARIES.is_dir():
        return 0
    n = 0
    for p in sorted(SUMMARIES.glob("*.md")):
        text = p.read_text(encoding="utf-8")
        head = "" if text.startswith("---") else fm({"source": str(p), "tags": ["nexus/문헌요약"]})
        write(OUT / "문헌 요약" / p.name, head + text)
        n += 1
    return n


def main() -> None:
    ent, ont = load()
    names = term_names(ent)
    edges_by_term: dict[str, list[str]] = defaultdict(list)
    for e in ont.get("causal_edges", []):
        for t in e["cause"].get("entity_terms", []):
            edges_by_term[t].append(e["edge_id"])
    if OUT.exists():
        if not (OUT / MARKER).exists() and any(OUT.iterdir()):
            raise SystemExit(f"[오류] {OUT}에 관리 표지({MARKER})가 없음 — 사용자 폴더일 수 있어 덮어쓰지 않음")
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / MARKER).write_text("export_obsidian_vault.py가 관리하는 폴더 — 이 안의 수정은 다음 내보내기에서 사라짐\n",
                              encoding="utf-8")
    cats = export_terms(ent, names, edges_by_term)
    n_edges, n_nodes = export_edges(ont, names)
    n_sum = export_summaries()
    from scripts.export_vault_documents import export as export_documents   # 비정형·반정형 문서 카드
    docs = export_documents(OUT)
    from scripts.export_vault_ontology import export as export_ontology    # 온톨로지 템플릿·MOC·캔버스·그래프 색
    docs.update({f"온톨로지 · {k}": v for k, v in export_ontology(OUT).items()})
    term = Path("reports/terminal/nexus_terminal.html")       # 대화형 터미널 사본(볼트에서 바로 열기)
    if term.exists():
        (OUT / "대시보드").mkdir(parents=True, exist_ok=True)
        shutil.copy2(term, OUT / "대시보드" / term.name)
        docs["대시보드 · Nexus Terminal"] = 1
    home = [fm({"tags": ["nexus/홈"]}), "# Nexus 시맨틱 레이어", "",
            BANNER.format(src="src/semantic/*.yaml"), "",
            f"- 용어 {len(names)}개 · 분류 {len(cats)}개 · 인과 사슬 {n_edges}건 · 노드 {n_nodes}개 · 문헌 요약 {n_sum}건",
            f"- 온톨로지 버전 {ont.get('version')} · 갱신 {ont.get('updated')}", "",
            "## 비정형·반정형 문서", *[f"- {k}: {v}건" for k, v in sorted(docs.items())],
            "- 문서 분류 허브: `문서 분류/` · GAIN·FAO 신호 색인: [[비정형 요약/신호 색인]]",
            "- 온톨로지: [[온톨로지 MOC]] · [[온톨로지 지도.canvas|인과 사슬 캔버스]] · 템플릿 폴더 `템플릿/`",
            "- 대시보드: [Nexus Terminal 열기](대시보드/nexus_terminal.html) — 브라우저에서 열림(차트·3D 표면·온톨로지 3D)", "", "## 용어 분류",
            *[f"- [[분류/{safe(c)}|{c}]] ({len(v)})" for c, v in sorted(cats.items())], "", "## 인과 사슬",
            *[f"- [[인과/{e['edge_id']}|{e['edge_id']}]] {e.get('label_ko', '')}" for e in ont.get("causal_edges", [])]]
    write(OUT / "Nexus 홈.md", "\n".join(home) + "\n")
    print(f"[완료] 볼트 보기 → {OUT}: 용어 {len(names)} · 인과 {n_edges} · 노드 {n_nodes} · 문헌 요약 {n_sum} · "
          + " · ".join(f"{k} {v}" for k, v in sorted(docs.items())))


if __name__ == "__main__":
    main()
