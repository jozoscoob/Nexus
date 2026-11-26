#!/usr/bin/env python3
"""
파이프라인 요약 PDF 보고서 생성기 — WBS 1.1.8
Korean + English 이중 언어 PDF 생성.
출력: reports/pipeline/pipeline_report_{YYYYMMDD_HHMM}_{ko|en}.{html|pdf}
"""
from __future__ import annotations

import glob
import os
from datetime import datetime
from pathlib import Path
from typing import Literal

import pandas as pd

OUTPUT_DIR = "data/raw"
REPORT_DIR = "reports/pipeline"  # WBS 1.6.1 경로 규약

# ── 번역 테이블 ─────────────────────────────────────────────────────────────
_T: dict[str, dict[str, str]] = {
    "title_main": {
        "ko": "Nexus 외부 데이터 파이프라인",
        "en": "Nexus External Data Pipeline",
    },
    "title_sub": {
        "ko": "요약 및 데이터 품질 보고서",
        "en": "Summary & Data Quality Report",
    },
    "run_id": {"ko": "실행 ID", "en": "Run ID"},
    "generated": {"ko": "생성 시각 (UTC)", "en": "Generated (UTC)"},
    "total_files": {"ko": "총 파일", "en": "Total Files"},
    "total_rows": {"ko": "총 행 수", "en": "Total Rows"},
    "success": {"ko": "판독 가능 파일", "en": "Readable files"},   # 파일을 읽었다는 뜻일 뿐 수집 성공이 아님
    "error": {"ko": "오류", "en": "Error"},
    "section_connector": {"ko": "커넥터별 수집 결과", "en": "Connector Collection Results"},
    "col_file": {"ko": "파일명", "en": "Filename"},
    "col_rows": {"ko": "행 수", "en": "Rows"},
    "col_size": {"ko": "크기", "en": "Size"},
    "col_null": {"ko": "결측치", "en": "Null %"},
    "col_time": {"ko": "수집 시각 (UTC)", "en": "Ingested At (UTC)"},
    "col_status": {"ko": "상태", "en": "Status"},
    "warn_title": {"ko": "⚠️ 데이터 품질 주의 파일", "en": "⚠️ Data Quality Warnings"},
    "warn_body": {
        "ko": "결측치 5% 초과 — API 키·소스 연결 상태 확인 필요.",
        "en": "Null rate exceeds 5% — verify API key and source connectivity.",
    },
    "quality_title": {"ko": "데이터 품질 기준 (WBS 1.1.8)", "en": "Data Quality Thresholds (WBS 1.1.8)"},
    "quality_ok": {"ko": "결측치 &lt;5%: 정상", "en": "Null &lt;5%: OK"},
    "quality_warn": {"ko": "결측치 5–15%: 주의 ⚠️", "en": "Null 5–15%: Warning ⚠️"},
    "quality_alert": {"ko": "결측치 &gt;15%: 경보 🚨", "en": "Null &gt;15%: Alert 🚨"},
    "quality_stale": {"ko": "미갱신 &gt;5영업일: STALE 판정", "en": "Not refreshed &gt;5 business days: STALE"},
    "lang_label": {"ko": "한국어 보고서", "en": "English Report"},
}


def _t(key: str, lang: str) -> str:
    return _T.get(key, {}).get(lang, key)


def _collect_stats() -> list[dict]:
    # 재귀 glob이 최상위 파일도 포함 — 최상위 glob을 더하면 같은 파일을 두 번 셌음(Codex 근본 원인 조사 H)
    files = sorted(glob.glob(f"{OUTPUT_DIR}/**/*.parquet", recursive=True))
    results = []
    for f in files:
        try:
            df = pd.read_parquet(f)
            size_kb   = os.path.getsize(f) / 1024
            ingested  = df["ingested_at"].max() if "ingested_at" in df.columns else "N/A"
            null_pct  = df.isnull().mean().mean() * 100
            results.append({
                "file":        Path(f).name,
                "rows":        len(df),
                "cols":        len(df.columns),
                "size_kb":     round(size_kb, 1),
                "ingested_at": str(ingested)[:19],
                "null_pct":    round(null_pct, 1),
                "status":      "OK",
            })
        except Exception as e:
            results.append({
                "file": Path(f).name, "rows": "–", "cols": "–",
                "size_kb": "–", "ingested_at": "–", "null_pct": "–",
                "status": f"ERROR: {e}",
            })
    return results


def _render_html(
    stats: list[dict],
    run_id: str,
    run_ts: str,
    lang: Literal["ko", "en"] = "ko",
) -> str:
    rows_html = ""
    for s in stats:
        bg       = "#d4edda" if s["status"] == "OK" else "#f8d7da"
        null_val = s["null_pct"]
        null_warn = (
            " 🚨" if isinstance(null_val, float) and null_val > 15 else
            " ⚠️" if isinstance(null_val, float) and null_val > 5 else ""
        )
        rows_html += (
            f"<tr style='background:{bg}'>"
            f"<td>{s['file']}</td>"
            f"<td style='text-align:right'>{s['rows']}</td>"
            f"<td style='text-align:right'>{s['size_kb']} KB</td>"
            f"<td style='text-align:right'>{null_val}%{null_warn}</td>"
            f"<td>{s['ingested_at']}</td>"
            f"<td><b>{s['status']}</b></td>"
            f"</tr>\n"
        )

    total_rows = sum(s["rows"] for s in stats if isinstance(s["rows"], int))
    ok_count   = sum(1 for s in stats if s["status"] == "OK")
    err_count  = len(stats) - ok_count
    warn_files = [s["file"] for s in stats
                  if isinstance(s.get("null_pct"), float) and s["null_pct"] > 5]

    warn_section = ""
    if warn_files:
        warn_items = "".join(f"<li>{f}</li>" for f in warn_files)
        warn_section = (
            f"<h2>{_t('warn_title', lang)}</h2>"
            f"<ul style='color:#856404'>{warn_items}</ul>"
            f"<p>{_t('warn_body', lang)}</p>"
        )

    font_import = (
        "@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');"
        if lang == "ko" else ""
    )
    font_family = (
        "'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif"
        if lang == "ko" else
        "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
    )
    html_lang = "ko" if lang == "ko" else "en"

    return f"""<!DOCTYPE html>
<html lang="{html_lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nexus Pipeline Report {run_ts[:10]} ({lang.upper()})</title>
<style>
  {font_import}
  body  {{ font-family: {font_family};
           margin: 40px 60px; color: #333; font-size: 13px; line-height: 1.6; }}
  h1   {{ color: #1a237e; border-bottom: 3px solid #1a237e; padding-bottom: 10px; font-size: 20px; }}
  h2   {{ color: #283593; margin-top: 28px; font-size: 15px; }}
  .lang-badge {{ float: right; background: #1a237e; color: #fff; padding: 3px 10px;
                 border-radius: 12px; font-size: 11px; margin-top: 4px; }}
  .meta {{ background: #e8eaf6; padding: 14px 18px; border-radius: 8px; margin: 18px 0; }}
  .badge {{ display: inline-block; padding: 4px 12px; border-radius: 14px;
            font-size: 11px; font-weight: bold; margin: 2px; }}
  .ok   {{ background: #c8e6c9; color: #1b5e20; }}
  .err  {{ background: #ffcdd2; color: #b71c1c; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 12px; }}
  th    {{ background: #1a237e; color: #fff; padding: 9px 14px; text-align: left; }}
  td    {{ padding: 7px 14px; border-bottom: 1px solid #e0e0e0; }}
  tr:hover {{ opacity: 0.9; }}
  .quality-box {{ background: #fff8e1; border-left: 4px solid #ffc107; padding: 12px 16px;
                  border-radius: 4px; margin-top: 20px; font-size: 12px; }}
  .footer {{ margin-top: 48px; font-size: 11px; color: #9e9e9e;
             border-top: 1px solid #e0e0e0; padding-top: 14px; }}
</style>
</head>
<body>

<span class="lang-badge">{_t("lang_label", lang)}</span>
<h1>{_t("title_main", lang)}<br>{_t("title_sub", lang)}</h1>

<div class="meta">
  <strong>{_t("run_id", lang)}:</strong> {run_id}　│
  <strong>{_t("generated", lang)}:</strong> {run_ts}　│
  <strong>{_t("total_files", lang)}:</strong> {len(stats)}　│
  <strong>{_t("total_rows", lang)}:</strong> {total_rows:,}　│
  <span class="badge ok">{_t("success", lang)} {ok_count}</span>
  <span class="badge err">{_t("error", lang)} {err_count}</span>
</div>

<h2>{_t("section_connector", lang)}</h2>
<table>
  <tr>
    <th>{_t("col_file", lang)}</th>
    <th style="text-align:right">{_t("col_rows", lang)}</th>
    <th style="text-align:right">{_t("col_size", lang)}</th>
    <th style="text-align:right">{_t("col_null", lang)}</th>
    <th>{_t("col_time", lang)}</th>
    <th>{_t("col_status", lang)}</th>
  </tr>
  {rows_html}
</table>

{warn_section}

<div class="quality-box">
  <strong>{_t("quality_title", lang)}</strong><br>
  {_t("quality_ok", lang)} &nbsp;|&nbsp;
  {_t("quality_warn", lang)} &nbsp;|&nbsp;
  {_t("quality_alert", lang)} &nbsp;|&nbsp;
  {_t("quality_stale", lang)}
</div>

<div class="footer">
  Project Nexus · WBS 1.1.8 Data Quality Report · {_t("lang_label", lang)} ·
  Branch: claude/setup-nexus-llm-tools-RX4aS ·
  Generated: {run_ts} UTC
</div>

</body>
</html>"""


def _write_pdf(html_path: str, pdf_path: str) -> bool:
    try:
        from weasyprint import HTML as WeasyprintHTML  # type: ignore
        WeasyprintHTML(filename=html_path).write_pdf(pdf_path)
        return True
    except ImportError:
        print("[경고] weasyprint 미설치 — HTML만 저장됨.")
        return False
    except Exception as e:
        print(f"[경고] PDF 변환 실패: {e}")
        return False


def run() -> None:
    os.makedirs(REPORT_DIR, exist_ok=True)
    now    = datetime.utcnow()
    tag    = now.strftime("%Y%m%d_%H%M")
    run_ts = now.strftime("%Y-%m-%d %H:%M:%S")
    run_id = os.environ.get("GITHUB_RUN_ID", "local")

    stats = _collect_stats()
    if not stats:
        print(f"[경고] {OUTPUT_DIR} 에서 parquet 파일을 찾을 수 없음 — 보고서 건너뜀.")
        return

    for lang in ("ko", "en"):
        html_path = f"{REPORT_DIR}/pipeline_report_{tag}_{lang}.html"
        pdf_path  = f"{REPORT_DIR}/pipeline_report_{tag}_{lang}.pdf"
        with open(html_path, "w", encoding="utf-8") as fh:
            fh.write(_render_html(stats, run_id, run_ts, lang=lang))  # type: ignore[arg-type]
        print(f"[완료] HTML ({lang.upper()}) → {html_path}")
        ok = _write_pdf(html_path, pdf_path)
        if ok:
            print(f"[완료] PDF  ({lang.upper()}) → {pdf_path}")


if __name__ == "__main__":
    run()
