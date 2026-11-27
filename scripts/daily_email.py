"""Morning email body (English) — approved structure 2026-11-27.

  1. Pipeline run: steps, timing, failures, and a fix or alternative for every failure or skipped source
  2. Codex review: what was checked, findings by severity, items waiting for approval
  3. G1 report: Drive link, soybean oil price, a short summary (the report file itself stays unchanged)
  3-1. Proposals: only items that clear the bar (critical/high Codex findings, or a rule backed by today's numbers),
       each with its evidence. If nothing clears the bar, the email says so.

Plain style (humanizer rules): short declarative sentences, no decorative bold or emoji headings, no filler.
"""
from __future__ import annotations

import glob
import json
import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "reports" / "ops"
PIPE = ROOT / "reports" / "pipeline"
QUEUE = ROOT / "codex_work" / "queue" / "pending.json"

JOB_NAME = {"collect_free": "Collect", "te_update": "TE prices", "digest": "News digest",
            "codex_verify_semantic": "Codex semantic review", "manual_parsers": "Manual uploads",
            "mart_build": "Mart build", "vault_export": "Vault view", "quality": "Quality check",
            "codex_verify_data": "Codex data check", "band_compare": "Range methods", "baseline": "Baseline",
            "g1_report": "G1 report", "g2_preview": "G2 preview", "run_report": "Run report",
            "drive_upload": "Drive upload"}
SEVERITY = {"치명": "critical", "높음": "high", "참고": "note"}
# 실패·건너뜀 → 해결책/대안(규칙표). 위에서부터 첫 일치 적용
REMEDIES = [
    (r"PERPLEXITY", None),   # 구독 해지 — 실패로 보고하지 않음
    (r"401|credentials|인증 실패", "The source rejected the API key. Check or renew the key; until then the last good data is used."),
    (r"429|rate.?limit|slow down|409", "Rate-limited by the source. It retries on the next run with wider spacing; last good data stays in use."),
    (r"timed out|timeout|Timeout", "The source did not answer in time. It retries on the next run; last good data stays in use. Three misses in a row get a longer timeout or a quieter time slot."),
    (r"\b5\d\d\b", "Server error on the source's side. It retries on the next run; last good data stays in use."),
    (r"미등록|not set|환경변수가 설정되지", "No API key is configured, so this source is skipped. Add the key to collect it."),
    (r"Token Required|비공개", "The source is no longer public. Existing data is kept; an alternative source is needed."),
    (r"패키지 미설치|No module named|ModuleNotFoundError", "A Python package is missing in the runner image. I add it to the image."),
]
CODE_ERROR = ("This is a code or data-contract error, not a source problem. Codex investigates it in the next review "
              "and I fix it.")
KEY_SERVICE = {"BOK_ECOS": "Bank of Korea ECOS", "KOSIS": "KOSIS", "OPENWEATHERMAP": "OpenWeatherMap",
               "NASA_FIRMS": "NASA FIRMS", "AISSTREAM": "AISstream", "TRADING_ECONOMICS": "Trading Economics"}
KNOWN = {"ENSO_ONI": "El Nino index (ENSO ONI)", "BDI_ZSCORE": "Baltic Dry Index z-score",
         "GPR_NORMALIZED": "geopolitical risk index (GPR, normalised)"}
CATEGORY_EN = {"지정학": "geopolitical index", "작황(WASDE 수동": "WASDE manual upload", "NASA POWER": "NASA POWER crop weather",
               "ICE 선물": "ICE futures volumes", "BRL/USD": "BRL/USD exchange rate", "ENSO ONI": "ENSO ONI upload",
               "GATS 미국 수출액": "GATS US export value", "PS&D": "PS&D upload", "FAO AMIS": "FAO AMIS",
               "GAIN": "USDA GAIN reports", "AIS": "strait tanker transits (AIS)", "비정형 신호 시계열": "unstructured signal series"}


def _remedy(text: str, failed_step: bool = False) -> str | None:
    for pat, fix in REMEDIES:
        if re.search(pat, text, re.I):
            return fix
    return CODE_ERROR if failed_step else "Cause not classified yet. I will look at the log and report back."


def _source_name(line: str) -> str:
    """'[경고] EIA Brent 수집 실패: ...' → 'EIA Brent' · 'KOSIS_API_KEY 미등록' → 'KOSIS' · GDELT 질의는 'GDELT'."""
    body = re.sub(r"^\[경고\]\s*", "", line)
    m = re.search(r"([A-Z][A-Z_]+?)_(?:MAP_)?(?:API_)?KEY", body)
    if m:
        return KEY_SERVICE.get(m.group(1), m.group(1).replace("_", " ").title())
    m = re.match(r"([A-Za-z][A-Za-z0-9 /&.\-]*?)(?=\s*['(:]|\s+[^\x00-\x7f]|$)", body)
    name = (m.group(1) if m else body[:40]).strip()
    return "GDELT" if name.startswith("GDELT") else name


def _first_error(d: dict) -> str:
    for step in d.get("steps", []):
        if step.get("returncode"):
            lines = [l for l in step.get("tail", "").splitlines() if "[오류]" in l or "Error" in l or "FAILED" in l]
            return (lines[-1] if lines else (step.get("tail", "").strip().splitlines() or [""])[-1])[:180]
    return ""


def _skipped(res: dict[str, dict]) -> list[tuple[str, str]]:
    """성공 단계 안의 [경고] — (원문, 해결책). 퍼플렉시티는 제외, 같은 해결책끼리 묶음."""
    seen: dict[str, list[str]] = {}
    for d in res.values():
        for step in d.get("steps", []):
            for ln in step.get("tail", "").splitlines():
                if not ln.startswith("[경고]"):
                    continue
                fix = _remedy(ln)
                if fix is None:
                    continue
                src = _source_name(ln)
                seen.setdefault(fix, [])
                if src not in seen[fix]:
                    seen[fix].append(src)
    return [(", ".join(v[:6]) + (f" and {len(v) - 6} more" if len(v) > 6 else ""), k) for k, v in seen.items()]


def _price() -> str | None:
    p = ROOT / "data" / "raw" / "cbot_session_close.parquet"
    if not p.is_file():
        return None
    d = pd.read_parquet(p, columns=["price_date", "value", "unit"]).dropna().sort_values("price_date")
    if len(d) < 2:
        return None
    last, prev = d.iloc[-1], d.iloc[-2]
    wk = d[d["price_date"] <= last["price_date"] - pd.Timedelta(days=7)]
    chg = last["value"] - prev["value"]
    out = (f"CBOT soybean oil (front month, settlement): {last['value']:.2f} {last['unit']} on "
           f"{pd.Timestamp(last['price_date']):%d %b}, {chg:+.2f} ({chg / prev['value']:+.2%}) vs {pd.Timestamp(prev['price_date']):%d %b}")
    if len(wk):
        w = wk.iloc[-1]["value"]
        out += f", {(last['value'] - w) / w:+.2%} over a week"
    return out + "."


def _g1() -> dict:
    files = sorted(PIPE.glob("g1_variable_importance_*_ko.md"), key=lambda p: p.stat().st_mtime)
    if not files:
        return {}
    t = files[-1].read_text(encoding="utf-8")
    alerts = re.findall(r"🚨 \*\*(\w+)\*\*: ([-\d.]+) \(임계값 ([^)]+)\)", t)
    ok = re.findall(r"✅ \*\*(\w+)\*\*", t)
    top = re.findall(r"^\| ([A-Za-z0-9_]+) \| (-?\d\.\d+) \| ([\d.]+) \|", t, re.M)
    stale = re.findall(r"^\| ([^|]+) \|[^\n]*?(🚨 기한 초과|📥 업로드 갱신 필요) \((\d+)영업일 · 허용 (\d+)\)", t, re.M)
    return {"file": files[-1].name, "alerts": alerts, "ok": ok, "top": top[:6],
            "all_zero": bool(top) and all(float(w) == 0 for _, _, w in top), "stale": stale}


def _cat_en(k: str) -> str:
    for key, en in CATEGORY_EN.items():
        if key in k:
            return en
    return k.strip()


def build(res: dict[str, dict], today: date) -> dict:
    failed = {j: d for j, d in res.items() if d.get("failed")}
    total = len(res)
    secs = sum(s.get("seconds", 0) for d in res.values() for s in d.get("steps", []))
    times = [datetime.fromisoformat(d["finished_at"]) for d in res.values() if d.get("finished_at")]
    subject = (f"[Nexus] Daily report, {today:%a %d %b %Y}: "
               + (f"{total - len(failed)} of {total} steps finished" if failed else f"all {total} steps finished"))
    L: list[str] = []

    # 1. Pipeline run
    L.append("1. Pipeline run")
    span = f" ({min(times):%H:%M} to {max(times):%H:%M})" if times else ""
    L.append(f"The run took {secs / 60:.0f} minutes{span}. {total - len(failed)} of {total} steps finished"
             + (f" and {len(failed)} failed." if failed else "."))
    for j, d in failed.items():
        err = _first_error(d)
        L.append(f"- {JOB_NAME.get(j, j)} failed: {err or 'no error line in the log'}")
        L.append(f"  Fix or alternative: {_remedy(err, failed_step=True)} Earlier good outputs stay in place.")
    skipped = _skipped(res)
    if skipped:
        L.append("Skipped sources (the run continued without them):")
        for src, fix in skipped:
            L.append(f"- {src}. {fix}")
    L.append("")

    # 2. Codex review
    L.append("2. Codex review")
    props_p = OPS / f"codex_proposals_{today:%Y-%m-%d}.json"
    props = json.loads(props_p.read_text(encoding="utf-8")) if props_p.is_file() else []
    data_items = [p for p in props if p.get("kind") == "data"]
    if not props_p.is_file():
        L.append("Codex did not run today.")
    else:
        counts = {}
        for p in data_items:
            counts[SEVERITY.get(p.get("severity", ""), "note")] = counts.get(SEVERITY.get(p.get("severity", ""), "note"), 0) + 1
        sev = ", ".join(f"{n} {k}" for k, n in sorted(counts.items(), key=lambda x: ["critical", "high", "note"].index(x[0])))
        man = OPS.parent.parent / "codex_work" / "inputs" / "manifest_data.json"
        scope = ""
        if man.is_file():
            m = json.loads(man.read_text(encoding="utf-8"))
            scope = (f"Codex read {len(m.get('public_files', []))} public data files in full and saw "
                     f"{len(m.get('restricted_families_stats_only', []))} licensed sources only as summary statistics. ")
        L.append(f"{scope}It reported {len(data_items)} data findings ({sev or 'none'}).")
        sem = sum(p.get("count", 0) for p in props if p.get("kind") == "semantic")
        if sem:
            L.append(f"The semantic review made {sem} proposals for the dictionary and causal chains.")
    pending = [x for x in json.loads(QUEUE.read_text(encoding="utf-8"))] if QUEUE.is_file() else []
    waiting = [x for x in pending if x.get("status") == "승인 대기"]
    if waiting:
        L.append("Waiting for your approval (reply with the ID, e.g. \"approve 2026-11-27-D2\" or \"reject ...\"):")
        for x in waiting[-6:]:
            if x.get("kind") == "semantic":
                L.append(f"- {x['id']}: {x.get('count', '')} dictionary and causal-chain proposals "
                         f"(list in codex_proposals_{x['id'][:10]}.md on Drive).")
            else:
                L.append(f"- {x['id']}: {x.get('file', '')}. {str(x.get('problem', ''))[:140]}")
    L.append("")

    # 3. G1 report
    L.append("3. G1 report")
    link_p = OPS / f"drive_links_{today:%Y-%m-%d}.json"
    link = json.loads(link_p.read_text(encoding="utf-8")).get("folder_url") if link_p.is_file() else None
    L.append(f"Today's folder: {link}" if link else "Today's folder: not uploaded (see Drive upload above).")
    price = _price()
    if price:
        L.append(price)
    g = _g1()
    if g:
        for code, val, thr in g["alerts"]:
            L.append(f"Alert: {KNOWN.get(code, code)} is {val}, beyond its threshold ({thr}).")
        if g["ok"]:
            L.append("Inside normal ranges: " + ", ".join(KNOWN.get(c, c) for c in g["ok"]) + ".")
        if g["top"]:
            L.append("Moved most closely with soybean oil over 20 days: "
                     + ", ".join(f"{n} {float(r):+.2f}" for n, r, _ in g["top"]) + ".")
            if g["all_zero"]:
                L.append("None of them predicted 20-day returns out of sample, so treat this as correlation only.")
        if g["stale"]:
            L.append("Data past its freshness limit: "
                     + "; ".join(f"{_cat_en(k)} ({a} business days, limit {b})" for k, _, a, b in g["stale"][:6]) + ".")
    L.append("")

    # 3-1. Proposals (gated)
    L.append("3-1. Proposals")
    bar: list[str] = []
    for p in [p for p in data_items if p.get("severity") in ("치명", "높음")][:3]:
        bar.append(f"- Codex ({SEVERITY[p['severity']]}, {p['id']}): {p.get('file', '')}. {str(p.get('problem', ''))[:200]}"
                   f" Suggested fix: {str(p.get('fix', ''))[:160]}")
    if g and g.get("all_zero"):
        bar.append("- Data science: at the 20-day horizon no variable keeps a weight in the Elastic Net "
                   f"(all top weights are 0 in {g['file']}). Test 1- and 5-day horizons before adding variables.")
    overdue = [s for s in (g.get("stale", []) if g else []) if s[1].startswith("🚨") and int(s[2]) > 3 * int(s[3])]
    for k, _, a, b in overdue[:2]:
        bar.append(f"- Data: {_cat_en(k)} is {a} business days old against a limit of {b}. Refresh the source or replace it.")
    L += bar or ["Nothing today met the bar for a proposal."]

    return {"subject": subject, "body": "\n".join(L), "failed": bool(failed), "steps": total}
