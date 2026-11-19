"""비정형·반정형 자료 → Obsidian 볼트 보기(문서 카드·요지·분류). export_obsidian_vault.py가 호출한다.

대상(2026-11-19 승인자 지시 — 비정형·반정형 전체 + 문서):
  연구 문서(docs/research_desk, references 제외) · 운영 문서 · 의사결정 원장(memory_archive)
  GAIN·FAO 문서 요약(data/raw/**/Summary/*.md) · 일별 비정형 다이제스트 · 일별 비정형 신호 CSV
  G2·G3 참고 논문(data/raw/References — 첫 쪽 초록 발췌) · 시장 구조 등 docx
  첨부 원본: 참고문헌 PDF·논문 PDF·docx(볼트 '첨부/'). GAIN·FAO 원본 PDF(약 1.6 GB)는 요약으로 대체해 복사하지 않음.

요지 추출은 규칙 기반(결론·요약·판정·권고 절 우선 → 없으면 첫 문단). LLM 요약이 아니므로 카드에 '추출 요지'로 표기.
"""
from __future__ import annotations

import csv
import re
import shutil
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES: list[tuple[str, list[str]]] = [
    ("G1 변인·유사국면", ["G1", "변인", "유사 시기", "유사국면", "경보", "variable importance", "analog"]),
    ("G2 가격 범위·방법론", ["G2", "참고 범위", "밴드", "분위", "band", "quantile", "conformal", "EWMA", "coverage"]),
    ("G3 조달·시뮬레이션", ["G3", "조달", "regret", "시뮬레이션", "구매 시점", "procurement", "분할 구매"]),
    ("시장 구조·가격 동인", ["시장 구조", "ABCD", "트레이딩", "Cargill", "Bunge", "COFCO", "팜유", "유채", "market structure"]),
    ("공급망·해상 물류", ["해상", "항로", "호르무즈", "운임", "BDI", "PortWatch", "물류", "chokepoint", "해협"]),
    ("정책·바이오연료", ["RFS", "RVO", "바이오", "45Z", "관세", "정책", "biofuel", "biodiesel"]),
    ("데이터·파이프라인", ["커넥터", "파이프라인", "as-of", "마트", "parquet", "수집", "DuckDB", "스키마", "파서"]),
    ("인프라·운영", ["Docker", "n8n", "Actions", "egress", "runner", "워크플로우", "Codex", "컨테이너"]),
    ("의사결정·보고", ["결정", "보고", "WBS", "decision", "승인", "브리핑"]),
]
# 요지 절 우선순위: 결론·요약류 → 판정·권고 → 결정 필요(마지막)
KEY_HEADINGS = [re.compile(r"^#{1,4}\s*.*(결론|한 줄|요약|핵심|TL;DR|Summary|Conclusion)", re.I),
                re.compile(r"^#{1,4}\s*.*(판정|권고|권장|제안)"),
                re.compile(r"^#{1,4}\s*.*(결정 필요|결정 요청)")]
INLINE_KEY = re.compile(r"^>?\s*\**(결론|한 줄 결론|요지)\**\s*[:：]")
HEADING = re.compile(r"^(#{1,4})\s+(.*)")
BAD = re.compile(r'[\\/:*?"<>|#^\[\]]')


def safe(name: str) -> str:
    return BAD.sub("-", name).strip(" .")[:120] or "unnamed"


def fm(d: dict) -> str:
    return "---\n" + yaml.safe_dump(d, allow_unicode=True, sort_keys=False).strip() + "\n---\n"


def categorize(text: str) -> list[str]:
    low = text.lower()
    scores = [(sum(low.count(k.lower()) for k in kws), cat) for cat, kws in CATEGORIES]
    ranked = [c for s, c in sorted(scores, key=lambda x: -x[0]) if s > 0]
    return ranked[:3] or ["기타"]


def key_points(text: str, limit: int = 8) -> list[str]:
    lines = [l.rstrip() for l in text.splitlines()]
    if lines and lines[0].strip() == "---":                      # 앞머리 frontmatter 제거
        end = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == "---"), 0)
        lines = lines[end + 1:]
    inline = [l.strip()[:300] for l in lines[:40] if INLINE_KEY.match(l.strip())]
    for pat in KEY_HEADINGS:
        for i, l in enumerate(lines):
            if not pat.match(l):
                continue
            out = list(inline)
            for m in lines[i + 1:]:
                if HEADING.match(m) and len(out) > len(inline):
                    break
                if m.strip() and not m.strip().startswith("|---"):
                    out.append(m.strip()[:300])
                if len(out) >= limit:
                    break
            if len(out) > len(inline):
                return out[:limit]
    if inline:
        return inline
    body = [l.strip()[:300] for l in lines if l.strip() and not HEADING.match(l) and not l.startswith("|---")]
    return body[:min(limit, 6)]


def outline(text: str) -> list[str]:
    return [("  " * (len(m.group(1)) - 1)) + "- " + m.group(2).strip()[:100]
            for m in (HEADING.match(l) for l in text.splitlines()) if m and len(m.group(1)) <= 3][:25]


def doc_card(src: Path, text: str, group: str) -> tuple[str, str, list[str]]:
    cats = categorize(src.name + "\n" + text[:6000])
    date = re.search(r"(20\d{2})[-_.]?(\d{2})[-_.]?(\d{2})", src.name)
    meta = {"source": str(src.relative_to(ROOT)).replace("\\", "/"), "group": group, "category": cats[0],
            "categories": cats, "date": "-".join(date.groups()) if date else None,
            "tags": ["nexus/문서", f"nexus/분류/{safe(cats[0]).replace(' ', '_')}"]}
    pts = key_points(text)
    body = [fm(meta), f"# {src.stem}", "",
            "> [!summary] 추출 요지(규칙 기반 — 결론·요약 절 우선)", *[f"> {p}" for p in pts], "",
            f"분류: {' · '.join(f'[[문서 분류/{safe(c)}|{c}]]' for c in cats)}", "",
            "## 목차", *outline(text), "", "## 원문", "", text]
    return safe(src.stem), "\n".join(body) + "\n", cats


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    paras = []
    for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        t = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p, flags=re.S))
        if t.strip():
            heading = re.search(r'<w:pStyle w:val="(Heading|제목)\s?(\d)"', p)
            paras.append(("#" * int(heading.group(2)) + " " if heading else "") + t.strip())
    return "\n\n".join(paras)


def pdf_abstract(path: Path) -> tuple[str, str]:
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            t = (pdf.pages[0].extract_text() or "") if pdf.pages else ""
    except Exception as e:  # 손상·암호 PDF가 전체를 막지 않게
        return path.stem, f"(첫 쪽 판독 실패: {type(e).__name__})"
    t = re.sub(r"[ \t]+", " ", t)
    m = re.search(r"(?is)abstract[:.\s]*(.{200,1400}?)(?:\n\s*\n|keywords|1\.?\s+introduction)", t)
    first = next((l.strip() for l in t.splitlines() if len(l.strip()) > 15), path.stem)
    return first[:160], (m.group(1) if m else t[:900]).strip().replace("\n", " ")


def summary_meta(text: str) -> tuple[list[str], str]:
    tags = re.search(r"aspect 신호 태그\s*\|\s*([^|\n]+)", text)
    direc = re.search(r"방향성\(SBO 가격 기준\)\s*\|\s*([^|\n(]+)", text)
    return ([t.strip() for t in tags.group(1).split(",") if t.strip() and t.strip() != "—"] if tags else [],
            direc.group(1).strip() if direc else "미확인")


def export(out: Path) -> dict[str, int]:
    counts: dict[str, int] = Counter()
    by_cat: dict[str, list[str]] = defaultdict(list)

    def write(rel: str, text: str) -> None:
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    # 1) 연구·운영 문서·의사결정 원장 → 문서 카드
    groups = [("연구", [p for p in (ROOT / "docs/research_desk").rglob("*.md") if "references" not in p.parts]),
              ("운영", list((ROOT / "docs/operations").glob("*.md")) + list((ROOT / "docs/architecture").glob("*.md"))),
              ("의사결정 원장", list((ROOT / "docs/memory_archive").glob("*.md")))]
    for group, files in groups:
        for src in sorted(files):
            name, card, cats = doc_card(src, src.read_text(encoding="utf-8", errors="replace"), group)
            write(f"문서/{group}/{name}.md", card)
            by_cat[cats[0]].append(f"문서/{group}/{name}")
            counts[f"문서 · {group}"] += 1

    # 2) docx → 카드 + 첨부 원본
    for src in sorted(list((ROOT / "data/raw").rglob("*.docx")) + list((ROOT / "docs").rglob("*.docx"))):
        name, card, cats = doc_card(src, docx_text(src), "docx")
        write(f"문서/docx/{name}.md", card + f"\n원본: ![[첨부/문서/{src.name}]]\n")
        (out / "첨부/문서").mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out / "첨부/문서" / src.name)
        by_cat[cats[0]].append(f"문서/docx/{name}")
        counts["문서 · docx"] += 1

    # 3) GAIN·FAO 문서 요약 → 신호 태그·방향 frontmatter
    sig = Counter()
    for src in sorted((ROOT / "data/raw").rglob("Summary/*.md")):
        rel = src.relative_to(ROOT / "data/raw")
        source = "GAIN" if "GAIN" in rel.parts else rel.parts[0]
        year = next((p for p in rel.parts if re.fullmatch(r"20\d{2}", p)), "연도미상")
        text = src.read_text(encoding="utf-8", errors="replace")
        tags, direc = summary_meta(text)
        sig.update(tags)
        meta = {"source": str(src.relative_to(ROOT)).replace("\\", "/"), "group": f"{source} 요약", "year": year,
                "signals": tags, "direction": direc,
                "tags": ["nexus/비정형요약", f"nexus/{source}", *[f"nexus/신호/{safe(t)}" for t in tags]]}
        write(f"비정형 요약/{source}/{year}/{safe(src.stem)}.md", fm(meta) + text)
        counts[f"비정형 요약 · {source}"] += 1
    write("비정형 요약/신호 색인.md", fm({"tags": ["nexus/색인"]}) + "# GAIN·FAO 요약 신호 색인\n\n| 신호 | 문서 수 |\n|---|---|\n"
          + "\n".join(f"| #nexus/신호/{safe(t)} | {n} |" for t, n in sig.most_common()) + "\n")

    # 4) G2·G3 참고 논문 → 첫 쪽 초록 발췌 카드 + 첨부 원본
    for src in sorted((ROOT / "data/raw/References").rglob("*")):
        if not src.is_file() or src.suffix.lower() not in ("", ".pdf"):
            continue
        group = "G2 금융공학 방법" if "G2" in src.parts else "G3 관점(고전파·케인스)"
        title, abstract = pdf_abstract(src)
        att = safe(src.stem) + ".pdf"
        (out / "첨부/논문").mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out / "첨부/논문" / att)
        frame = ("[[문서/연구/g2_methods_framework_2026_11_19|G2 방법론 프레임워크]]" if group.startswith("G2")
                 else "[[문서/연구/g3_perspectives_insights_2026_11_19|G3 관점 통찰]]")
        card = [fm({"group": group, "category": group.split()[0] + (" 가격 범위·방법론" if group.startswith("G2") else " 조달·시뮬레이션"),
                    "tags": ["nexus/논문", f"nexus/{group.split()[0]}"]}),
                f"# {src.stem}", "", f"- 첫 줄: {title}", f"- 적용 판정·근거: {frame}", f"- 원문: ![[첨부/논문/{att}]]", "",
                "> [!quote] 초록 발췌(첫 쪽)", f"> {abstract[:1200]}"]
        write(f"문헌/{group}/{safe(src.stem)}.md", "\n".join(card) + "\n")
        counts[f"문헌 · {group}"] += 1

    # 5) 참고문헌 PDF 원본 첨부(요약 카드는 '문헌 요약/')
    for src in sorted((ROOT / "docs/research_desk/references").glob("*.pdf")):
        (out / "첨부/참고문헌").mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out / "첨부/참고문헌" / src.name)
        counts["첨부 · 참고문헌 PDF"] += 1

    # 6) 일별 비정형 다이제스트·신호(반정형 CSV → 월별 표)
    for src in sorted((ROOT / "reports/market").glob("daily_unstructured_digest_*.md")):
        write(f"일별/다이제스트/{src.name}", fm({"tags": ["nexus/다이제스트"]}) + src.read_text(encoding="utf-8"))
        counts["일별 · 다이제스트"] += 1
    sig_csv = ROOT / "data/processed/unstructured_daily_signals.csv"
    if sig_csv.exists():
        months: dict[str, list[dict]] = defaultdict(list)
        with sig_csv.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                months[(row.get("date") or "")[:7]].append(row)
        for ym, rows in sorted(months.items()):
            lines = [fm({"tags": ["nexus/일별신호"]}), f"# 일별 비정형 신호 — {ym}", "",
                     "| 날짜 | 분류 | 지표 | 값 | 근거 발췌 |", "|---|---|---|---|---|"]
            for r in sorted(rows, key=lambda r: (r.get("date", ""), r.get("indicator", ""))):
                note = (r.get("note") or "").replace("|", "/").replace("\n", " ")[:160]
                lines.append(f"| {r.get('date')} | {r.get('category', '')} | {r.get('indicator')} | {r.get('value')} | {note} |")
            write(f"일별/신호/{ym or '날짜미상'}.md", "\n".join(lines) + "\n")
            counts["일별 · 신호(월)"] += 1

    # 7) 문서 분류 허브
    for cat, notes in by_cat.items():
        write(f"문서 분류/{safe(cat)}.md", fm({"tags": ["nexus/분류허브"]}) + f"# {cat}\n\n문서 {len(notes)}건\n\n"
              + "\n".join(f"- [[{n}|{Path(n).name}]]" for n in sorted(notes)) + "\n")
    return dict(counts)
