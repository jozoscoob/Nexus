"""시맨틱 레이어 → Obsidian 온톨로지 템플릿(보기). export_obsidian_vault.py가 호출한다.

산출(볼트 'Nexus/' 아래):
  방법/{AM-xx}.md · 선례/{MP-xx}.md   methods.yaml — 분석 방법·방법론 선례(속성 + 적용 관계 위키링크)
  템플릿/*.md                          새 용어·인과 사슬·분석 방법 노트용 Obsidian 템플릿(속성 틀)
  온톨로지 MOC.md                       엔티티 분류·관계 유형 62종·인과 사슬(분류별)·방법(목표별) 색인
  온톨로지 지도.canvas                  인과 사슬 24건을 원인→경로→결과 카드로 배치한 Obsidian 캔버스
  .obsidian-template/graph.json        그래프 보기 색 그룹(태그별) — 동기화 스크립트가 볼트에 설정이 없을 때만 복사
정본은 저장소 YAML이다 — 여기서 고친 내용은 다음 내보내기에서 사라진다.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
VAULT_PREFIX = "Nexus"     # 캔버스 파일 경로는 볼트 루트 기준
BAD = re.compile(r'[\\/:*?"<>|#^\[\]]')
CANVAS_COLOR = {"cause": "1", "mechanism": "3", "outcome": "5", "group": "6"}
GRAPH_GROUPS = [("tag:#nexus/인과", 0xE8A93C), ("tag:#nexus/노드", 0xFF5F5F), ("tag:#nexus/용어", 0x3FB950),
                ("tag:#nexus/방법", 0x39D0D8), ("tag:#nexus/선례", 0xA78BFA), ("tag:#nexus/문서", 0x4EA1FF),
                ("tag:#nexus/비정형요약", 0x8B949E), ("tag:#nexus/논문", 0xF778BA)]


def safe(s: str) -> str:
    return BAD.sub("-", str(s)).strip(" .")[:120] or "unnamed"


def fm(d: dict) -> str:
    return "---\n" + yaml.safe_dump(d, allow_unicode=True, sort_keys=False).strip() + "\n---\n"


def export(out: Path) -> dict[str, int]:
    ent = yaml.safe_load((ROOT / "src/semantic/entities.yaml").read_text(encoding="utf-8"))
    ont = yaml.safe_load((ROOT / "src/semantic/ontology.yaml").read_text(encoding="utf-8"))
    met = yaml.safe_load((ROOT / "src/semantic/methods.yaml").read_text(encoding="utf-8"))
    counts: dict[str, int] = {}

    def write(rel: str, text: str) -> None:
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    # 1) 분석 방법·선례 노트(관계: 선례 APPLIES_TO 방법)
    methods = {m["id"]: m for m in met.get("analysis_methods", [])}
    applied_by: dict[str, list[str]] = defaultdict(list)

    def mlink(a: str) -> str:
        return f"[[방법/{a}|{a} {methods[a].get('name_ko') or methods[a].get('name')}]]"

    for mp in met.get("method_precedents", []):
        for am in mp.get("applies_to", []) or []:
            applied_by[am].append(mp["id"])
        body = [fm({"id": mp["id"], "verdict": mp.get("verdict"), "goals": mp.get("target_goal"), "authors_year": mp.get("authors_year"),
                    "tags": ["nexus/선례", f"nexus/판정/{safe(mp.get('verdict') or '미정')}"]}),
                f"# {mp['id']} {mp.get('title', '')}", "", f"- 방법: {mp.get('method', '—')}",
                f"- 적용 대상: {', '.join(mlink(a) for a in mp.get('applies_to') or [] if a in methods) or '—'}",
                "", "## 제약", *[f"- {c}" for c in mp.get("constraints") or []]]
        write(f"선례/{safe(mp['id'])}.md", "\n".join(body) + "\n")
    for am, m in methods.items():
        body = [fm({"id": am, "family": m.get("family"), "goal": m.get("goal"), "role": m.get("role"), "status": m.get("status"),
                    "library": m.get("library"), "tags": ["nexus/방법", f"nexus/{m.get('goal')}", f"nexus/역할/{safe(m.get('role') or '')}"]}),
                f"# {am} {m.get('name_ko') or m.get('name')}", "", f"- 영문명: {m.get('name')}", f"- 산출 계약: {m.get('contract', '—')}",
                f"- 목표: [[온톨로지 MOC#목표별 분석 방법|{m.get('goal')}]] · 역할: {m.get('role')} · 상태: {m.get('status')}",
                "", "## 누수 방지 규칙", *[f"- {r}" for r in m.get("leakage_rules") or []],
                "", "## 근거 선례", *([f"- [[선례/{p}|{p}]]" for p in applied_by.get(am, [])] or ["- 없음"])]
        write(f"방법/{safe(am)}.md", "\n".join(body) + "\n")
    counts["방법"] = len(methods)
    counts["선례"] = len(met.get("method_precedents", []))

    # 2) Obsidian 템플릿(속성 틀) — 핵심 플러그인 '템플릿'의 폴더로 지정해 쓰면 됨
    templates = {
        "용어 템플릿": fm({"term_id": "TERM-", "aliases": [], "class": "", "status": "candidate", "price_direction": "CONTEXT",
                         "tags": ["nexus/용어"]}) + "# {{title}}\n\n- 분류: [[분류/]]\n- 정의:\n- 해석 규칙:\n- 관련 인과 사슬: [[인과/]]\n",
        "인과 사슬 템플릿": fm({"edge_id": "CE-", "direction": "UP|DOWN", "status": "candidate", "lag_min": None, "lag_max": None,
                           "tags": ["nexus/인과", "nexus/status/candidate"]}) +
                     "# {{title}}\n\n**사슬**: [[노드/원인]] → [[노드/경로]] → [[노드/결과]]\n\n- 원인 용어: [[용어/]]\n- 지표:\n\n## 근거\n- (문서 · 쪽 · 인용)\n",
        "분석 방법 템플릿": fm({"id": "AM-", "family": "", "goal": "G1|G2|G3", "role": "champion|challenger|baseline", "status": "",
                           "tags": ["nexus/방법"]}) + "# {{title}}\n\n- 산출 계약:\n\n## 누수 방지 규칙\n- \n\n## 근거 선례\n- [[선례/]]\n",
    }
    for name, text in templates.items():
        write(f"템플릿/{name}.md", text)
    counts["템플릿"] = len(templates)

    # 3) 온톨로지 MOC
    classes = Counter(t.get("class") or "미분류" for k, v in ent.items() if isinstance(v, list) for t in v if isinstance(t, dict))
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for e in ont.get("causal_edges", []):
        by_cat[e.get("category") or "기타"].append(e)
    rel = ont.get("relation_types", [])
    moc = [fm({"tags": ["nexus/MOC"]}), "# 온톨로지 MOC", "",
           "> [!info] 저장소 `src/semantic/*.yaml`에서 생성. 그래프 보기 색: 인과(호박)·노드(빨강)·용어(초록)·방법(청록)·선례(보라)·문서(파랑).", "",
           f"- 용어 {sum(classes.values())} · 인과 사슬 {len(ont.get('causal_edges', []))} · 관계 유형 {len(rel)} · 분석 방법 {len(methods)} · 선례 {counts['선례']}",
           "- 지도: [[온톨로지 지도.canvas|인과 사슬 캔버스]] · 홈: [[Nexus 홈]]", "", "## 엔티티 분류(class)",
           *[f"- {c}: {n}" for c, n in classes.most_common()], "", "## 인과 사슬(분류별)"]
    for cat, edges in sorted(by_cat.items()):
        moc += [f"### {cat}", *[f"- [[인과/{e['edge_id']}|{e['edge_id']}]] {e.get('label_ko', '')} `{e.get('status')}`" for e in edges]]
    moc += ["", "## 목표별 분석 방법"]
    for goal in sorted({m.get("goal") or "기타" for m in methods.values()}):
        moc += [f"### {goal}", *[f"- [[방법/{a}|{a} {m.get('name_ko') or m.get('name')}]] — {m.get('role')} · {m.get('status')}"
                                for a, m in methods.items() if (m.get("goal") or "기타") == goal]]
    moc += ["", "## 관계 유형", "| 코드 | 정의 | 정의역 → 치역 |", "|---|---|---|",
            *[f"| {r.get('code')} | {r.get('definition', '')} | {r.get('domain', '')} → {r.get('range', '')} |" for r in rel]]
    write("온톨로지 MOC.md", "\n".join(moc) + "\n")

    # 4) 캔버스 — 사슬마다 한 줄(원인 → 경로… → 결과), 줄마다 그룹 상자
    nodes, edges = [], []
    W, H, GX, GY = 260, 70, 320, 130
    for i, e in enumerate(ont.get("causal_edges", [])):
        chain = [("cause", e["cause"]["node"]), *[("mechanism", m["node"]) for m in e.get("mechanisms", [])], ("outcome", e["outcome"]["node"])]
        y = i * GY
        nodes.append({"id": f"g{i}", "type": "group", "x": -20, "y": y - 40, "width": GX * len(chain) + 20, "height": H + 60,
                      "label": f"{e['edge_id']} · {e.get('direction')} · {e.get('status')}", "color": CANVAS_COLOR["group"]})
        prev = None
        for j, (role, node) in enumerate(chain):
            nid = f"n{i}_{j}"
            nodes.append({"id": nid, "type": "file", "file": f"{VAULT_PREFIX}/노드/{safe(node)}.md", "x": j * GX, "y": y,
                          "width": W, "height": H, "color": CANVAS_COLOR[role]})
            if prev:
                edges.append({"id": f"e{i}_{j}", "fromNode": prev, "fromSide": "right", "toNode": nid, "toSide": "left"})
            prev = nid
        nodes.append({"id": f"l{i}", "type": "file", "file": f"{VAULT_PREFIX}/인과/{safe(e['edge_id'])}.md",
                      "x": GX * len(chain) + 20, "y": y, "width": 220, "height": H})
    write("온톨로지 지도.canvas", json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent=1))
    counts["캔버스 카드"] = len([n for n in nodes if n["type"] == "file"])

    # 5) 그래프 보기 색 그룹(볼트 설정 템플릿)
    graph = {"colorGroups": [{"query": q, "color": {"a": 1, "rgb": c}} for q, c in GRAPH_GROUPS],
             "showTags": False, "showAttachments": False, "hideUnresolved": True, "showOrphans": False,
             "showArrow": True, "centerStrength": 0.45, "repelStrength": 12, "linkDistance": 180, "lineSizeMultiplier": 1.2}
    write(".obsidian-template/graph.json", json.dumps(graph, ensure_ascii=False, indent=1))
    return counts
