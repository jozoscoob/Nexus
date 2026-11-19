"""한국향 대두유·대체유 해상 경로 시나리오 — 실시간 선박 위치 없이 '경로 조정 가능성'을 보여 준다.

입력: config/route_scenarios.yaml(경로·우회로·비상 상황 정의) + IMF PortWatch 해협 통과 척수 parquet.
산출: ①해협별 현재 상태(최근 28일 탱커 통과 vs 고정 기준기 2019~2022) ②비상 상황별 과거 선례(사건 구간 vs 기준 구간 변화율,
매번 원자료에서 재계산) ③경로별 평시·우회 항해일과 예상 지연(거리 차 ÷ 경제 속력 — 근사치).
해석 규율: 과거 실측 요약과 거리 산술까지만 제시한다 — 지연 '확률'·가격 영향 크기는 주장하지 않는다(A-191).
PortWatch는 주간 갱신·4~7일 지연이라 '현재 상태'는 데이터 기준일 시점이다.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "route_scenarios.yaml"
RAW_DIR = Path(os.environ.get("NEXUS_DATA_ROOT", ROOT / "data" / "raw"))
OUT_DIR = ROOT / "reports" / "market"
NM_PER_DAY_PER_KNOT = 24  # 1노트 = 1해리/시
TANKER = "TANKER"


@dataclass
class StraitStatus:
    code: str
    recent_mean: float | None
    baseline_median: float | None
    change_pct: float | None
    state: str  # normal | disrupted | elevated | unknown


@dataclass
class Precedent:
    name: str
    event: tuple[str, str]
    baseline: tuple[str, str]
    changes: dict[str, float | None] = field(default_factory=dict)


def load_config(path: Path = CONFIG) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_transits(raw_dir: Path = RAW_DIR, kind: str = TANKER) -> pd.DataFrame:
    """해협 코드(열) × 일자(행) 일별 통과 척수. 파일이 없으면 빈 프레임."""
    files = sorted(glob.glob(str(raw_dir / "portwatch_chokepoints_*.parquet")))
    if not files:
        return pd.DataFrame()
    d = pd.read_parquet(files[-1], columns=["price_date", "indicator_code", "value"])
    suffix = f"_{kind}_TRANSITS"
    d = d[d["indicator_code"].str.endswith(suffix)]
    d["code"] = d["indicator_code"].str[3:-len(suffix)]
    return d.pivot_table(index="price_date", columns="code", values="value").sort_index()


def _mean(s: pd.Series, a: str, b: str) -> float | None:
    v = s.loc[a:b].dropna()
    return float(v.mean()) if len(v) else None


def _pct(new: float | None, base: float | None) -> float | None:
    if new is None or base is None or base <= 0:
        return None
    return round((new / base - 1) * 100, 1)


def strait_status(tr: pd.DataFrame, rule: dict) -> tuple[dict[str, StraitStatus], str | None]:
    if tr.empty:
        return {}, None
    asof = tr.index.max()
    recent0 = asof - pd.Timedelta(days=rule["recent_days"] - 1)
    base0, base1 = (str(x) for x in rule["reference_period"])
    out = {}
    for code in tr.columns:
        s = tr[code]
        rec = s.loc[recent0:asof].dropna()
        base = s.loc[base0:base1].dropna()
        rm = float(rec.mean()) if len(rec) else None
        bm = float(base.median()) if len(base) else None
        ch = _pct(rm, bm)
        if ch is None:
            state = "unknown"
        elif ch <= rule["disrupted_drop_pct"]:
            state = "disrupted"
        elif ch >= rule["elevated_rise_pct"]:
            state = "elevated"
        else:
            state = "normal"
        out[code] = StraitStatus(code, rm and round(rm, 1), bm and round(bm, 1), ch, state)
    return out, asof.strftime("%Y-%m-%d")


def precedents(tr: pd.DataFrame, cont: dict) -> list[Precedent]:
    res = []
    for p in cont.get("precedents", []):
        ev, bl = [str(x) for x in p["event"]], [str(x) for x in p["baseline"]]
        pr = Precedent(p["name"], (ev[0], ev[1]), (bl[0], bl[1]))
        for code in p["series"]:
            if tr.empty or code not in tr.columns:
                pr.changes[code] = None
                continue
            pr.changes[code] = _pct(_mean(tr[code], *ev), _mean(tr[code], *bl))
        res.append(pr)
    return res


def extra_days(nm_alt: float, nm_base: float, speed: dict) -> tuple[float, float]:
    """거리 차를 경제 속력 범위로 나눈 추가 항해일(빠른 속력 → 하한)."""
    diff = nm_alt - nm_base
    lo = diff / (speed["high"] * NM_PER_DAY_PER_KNOT)
    hi = diff / (speed["low"] * NM_PER_DAY_PER_KNOT)
    return round(lo, 1), round(hi, 1)


def route_options(cfg: dict, status: dict[str, StraitStatus]) -> list[dict]:
    """경로별 평시 상태와 우회 대안 — 평시 경로 해협이 'disrupted'면 우회 권고 표시."""
    out = []
    for rid, r in cfg["routes"].items():
        blocked = [c for c in r.get("normal_path", []) if status.get(c) and status[c].state == "disrupted"]
        alts = []
        for a in r.get("alternatives", []):
            via_bad = [c for c in a.get("via", []) if status.get(c) and status[c].state == "disrupted"]
            lo, hi = extra_days(a["nm"], r["normal_nm"], cfg["speed_knots"])
            alts.append({"id": a["id"], "name": a["name"], "avoids": a.get("avoids", []),
                         "extra_days": [lo, hi], "via_disrupted": via_bad,
                         "usable": not via_bad})
        out.append({"id": rid, "name": r["name"], "commodity": r.get("commodity", ""),
                    "base_lead_days": r["base_lead_days"], "normal_path": r.get("normal_path", []),
                    "blocked_now": blocked, "alternatives": alts, "note": r.get("note", "")})
    return out


def contingency_view(cfg: dict, tr: pd.DataFrame, status: dict[str, StraitStatus]) -> list[dict]:
    """비상 상황별: 영향 경로·우회 지연 범위·과거 선례·현재 발동 여부."""
    routes = cfg["routes"]
    out = []
    for cid, c in cfg["contingencies"].items():
        if cid == "normal":
            continue
        aff = set(c.get("affected", []))
        impacts = []
        for rid, r in routes.items():
            if not aff & set(r.get("normal_path", [])):
                continue
            usable = [a for a in r.get("alternatives", [])
                      if aff & set(a.get("avoids", [])) and not aff & set(a.get("via", []))]
            detours = []
            for a in sorted(usable, key=lambda a: a["nm"]):
                lo, hi = extra_days(a["nm"], r["normal_nm"], cfg["speed_knots"])
                bad = [v for v in a.get("via", []) if status.get(v) and status[v].state == "disrupted"]
                detours.append({"name": a["name"], "extra_days": [lo, hi], "via_disrupted_now": bad})
            impacts.append({"route": rid, "name": r["name"], "detours": detours})
        active = [a for a in aff if status.get(a) and status[a].state == "disrupted"]
        out.append({"id": cid, "name": c["name"], "affected": sorted(aff), "active_now": active,
                    "lane_effect": c.get("lane_effect", "").strip(), "route_impacts": impacts,
                    "precedents": [p.__dict__ for p in precedents(tr, c)]})
    return out


ALERT_REGION_STRAITS = {"HORMUZ": ["HORMUZ"], "RED_SEA": ["BAB_EL_MANDEB", "SUEZ"], "BLACK_SEA": [],
                        "MALACCA": ["MALACCA"], "TAIWAN": ["TAIWAN_STRAIT"]}


def recent_alerts(raw_dir: Path = RAW_DIR, days: int = 14) -> dict:
    """해역별 최근 해사 경보 보도(건수·근거 3건) — maritime_alerts_connector 산출물. 없으면 빈 dict."""
    files = sorted(glob.glob(str(raw_dir / "maritime_alerts_*.parquet")))
    if not files:
        return {}
    d = pd.read_parquet(files[-1], columns=["price_date", "indicator_code", "value", "note"])
    d = d[d["indicator_code"].str.endswith("_COUNT")]
    d = d[d["price_date"] >= d["price_date"].max() - pd.Timedelta(days=days - 1)]
    out = {}
    for code, g in d.groupby("indicator_code"):
        reg = code[len("MARALERT_"):-len("_COUNT")]
        notes = [n for n in g.sort_values("price_date", ascending=False)["note"].dropna()]
        items = [x.strip() for n in notes for x in n.split(" | ")][:3]
        out[reg] = {"count": int(g["value"].sum()), "last": g["price_date"].max().strftime("%Y-%m-%d"),
                    "straits": ALERT_REGION_STRAITS.get(reg, []), "items": items}
    return out


def build(raw_dir: Path = RAW_DIR, config_path: Path = CONFIG) -> dict:
    cfg = load_config(config_path)
    tr = load_transits(raw_dir)
    status, asof = strait_status(tr, cfg["status_rule"])
    return {"as_of": asof, "source": "IMF PortWatch 일별 해협 통과(탱커) — 주간 갱신·4~7일 지연",
            "status": {k: v.__dict__ for k, v in status.items()},
            "routes": route_options(cfg, status),
            "contingencies": contingency_view(cfg, tr, status),
            "alerts": recent_alerts(raw_dir),
            "caveats": ["추가 항해일은 항로 거리 차 ÷ 탱커 경제 속력(12.5~14노트)의 근사치(INFERENCE)",
                        "운하 대기일·선복 확보 지연은 PortWatch로 측정되지 않음(미측정)",
                        "과거 선례는 통과 척수 변화의 실측 요약 — 향후 지연·가격의 확률 주장이 아님"]}


def _fmt(v: float | None, unit: str = "%") -> str:
    return "—" if v is None else f"{v:+.1f}{unit}" if unit == "%" else f"{v:.1f}"


def to_markdown(rep: dict) -> str:
    st_ko = {"normal": "평시", "disrupted": "🔴 차질", "elevated": "🟡 유입 증가", "unknown": "자료 없음"}
    L = [f"# 해상 경로 시나리오 — 데이터 기준일 {rep['as_of']}", "",
         f"> 원천: {rep['source']}. " + " · ".join(rep["caveats"]), "",
         "## 1. 해협 현재 상태 (최근 28일 평균 vs 기준기 2019~2022 중앙값, 탱커/일)", "",
         "| 해협 | 최근 | 기준선 | 변화 | 판정 |", "|---|---|---|---|---|"]
    for k, s in sorted(rep["status"].items()):
        L.append(f"| {k} | {_fmt(s['recent_mean'], '')} | {_fmt(s['baseline_median'], '')} | "
                 f"{_fmt(s['change_pct'])} | {st_ko[s['state']]} |")
    L += ["", "## 2. 경로별 평시·우회", ""]
    for r in rep["routes"]:
        lead = f"{r['base_lead_days'][0]}~{r['base_lead_days'][1]}일"
        flag = f" — ⚠️ 평시 경로 차질: {', '.join(r['blocked_now'])}" if r["blocked_now"] else ""
        L.append(f"- **{r['name']}** (평시 리드타임 {lead}, 경유 {', '.join(r['normal_path']) or '수집 해협 없음'}){flag}")
        for a in r["alternatives"]:
            mark = "" if a["usable"] else f" — 경유 해협 차질({', '.join(a['via_disrupted'])})"
            L.append(f"  - {a['name']}: +{a['extra_days'][0]}~{a['extra_days'][1]}일{mark}")
        if r["note"]:
            L.append(f"  - 참고: {r['note']}")
    L += ["", "## 3. 비상 상황별 영향과 과거 선례", ""]
    for c in rep["contingencies"]:
        now = f" — **현재 발동**({', '.join(c['active_now'])})" if c["active_now"] else ""
        L += [f"### {c['name']}{now}", "", c["lane_effect"], ""]
        for i in c["route_impacts"]:
            d = (" / ".join(f"{x['name']} +{x['extra_days'][0]}~{x['extra_days'][1]}일"
                            + (f"(현재 경유 해협 차질: {', '.join(x['via_disrupted_now'])})"
                               if x["via_disrupted_now"] else "") for x in i["detours"])
                 or "가용 우회로 없음(대기 또는 공급원 전환)")
            L.append(f"- {i['name']}: {d}")
        for p in c["precedents"]:
            ch = " · ".join(f"{k} {_fmt(v)}" for k, v in p["changes"].items())
            L.append(f"- 선례 '{p['name']}' ({p['event'][0]}~{p['event'][1]}, 기준 {p['baseline'][0]}~"
                     f"{p['baseline'][1]}): {ch}")
        L.append("")
    return "\n".join(L)


def run() -> dict:
    rep = build()
    if rep["as_of"] is None:
        raise SystemExit("[오류] PortWatch parquet 없음 — portwatch_connector.py를 먼저 실행하세요")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md = OUT_DIR / f"route_scenarios_{date.today():%Y-%m-%d}.md"
    md.write_text(to_markdown(rep), encoding="utf-8")
    js = ROOT / "data" / "processed" / "route_scenarios_latest.json"
    js.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    dis = [k for k, s in rep["status"].items() if s["state"] == "disrupted"]
    print(f"[완료] 경로 시나리오 → {md} · 기준일 {rep['as_of']} · 차질 해협 {dis or '없음'}")
    return rep


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
