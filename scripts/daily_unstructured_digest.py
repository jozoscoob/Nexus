#!/usr/bin/env python3
"""
일별 비정형 신호 다이제스트 — Perplexity 수집분 요약 (A-163 · 조정자 지시 8/14)

지시: "Perplexity로 수집하는 비정형 데이터는 일 단위 갱신이 가능하므로
      매일 확인·수집·요약할 것."

동작: 당일 수집된 실시간 프록시 지표(지정학·해협·정책뉴스·운임·기상특보)를
      data/raw parquet에서 모아 하나의 한국어 다이제스트로 렌더링한다.
      수치와 함께 note(Perplexity 근거 발췌)를 보존해 '요약'이 되게 한다.

출력: reports/market/daily_unstructured_digest_{YYYY-MM-DD}.md
      (+ stdout — 워크플로우가 GITHUB_STEP_SUMMARY로 노출)
"""
from __future__ import annotations

import glob
import os
import re
import time
from datetime import date
from pathlib import Path

import pandas as pd

RAW = os.environ.get("NEXUS_DATA_ROOT", "data/raw")
OUT = Path("reports/market")
# A-181: 일별 신호의 변수별 영구 아카이브 (조정자 지시 8/16 — 아티팩트 7~30일 한계 해소).
#   커밋 저장은 unstructured_analysis.yml 인덱스 CSV 선례(A-090)를 따른다.
ARCHIVE = Path("data/processed/unstructured_daily_signals.csv")

# 일 단위 갱신되는 비정형·프록시 지표 (커넥터별)
DAILY_UNSTRUCTURED = {
    "지정학 위험":   ["GPR_REALTIME", "GPR", "GPR_QUALITATIVE", "HORMUZ_THREAT_LEVEL", "HORMUZ_AWRP_MULTIPLIER"],
    "정책 뉴스":     ["ARG_EXPORT_TAX_NEWS", "INDIA_DUTY_NEWS", "BIODIESEL_MANDATE_NEWS",
                     "WASDE_CONSENSUS_SCORE", "US_BIOFUEL_POLICY_NEWS"],   # A-289: 미국 RFS·SRE·45Z·RIN·NOPA
    "지정학 이벤트": ["SUEZ_RED_SEA_RISK", "UKRAINE_GRAIN_CORRIDOR", "US_CHINA_TARIFF_STATUS",
                     "BRAZIL_HARVEST_PROGRESS"],
    # A-273(2026-09-25): 미국–이란·러시아–EU 분쟁 상태(검색 요약 2종) + 통신사 지정학 레인(농산물 맥락 불요)
    "지정학 동향":   ["US_IRAN_CONFLICT_STATUS", "RUSSIA_EU_RELATIONS_STATUS",
                     "RSS_REUTERS_GEO", "RSS_AP_GEO"],
    # A-274: 커넥터 발행 코드명과 정합(구 AIS_*_TANKERS는 발행된 적 없음 → 아카이브 0행)
    "해협 탱커":     ["AIS_HORMUZ_TANKER_COUNT", "AIS_MALACCA_TANKER_COUNT", "AIS_PANAMA_TANKER_COUNT",
                     "AIS_HORMUZ_RISK", "AIS_MALACCA_RISK", "AIS_PANAMA_RISK",
                     "SBO_STRAIT_RISK_COMPOSITE"],
    "GeoIntel 복합": ["GEOINTEL_RISK_COMPOSITE", "SEISMIC_RISK", "GDELT_EVENT_SCORE"],
    "운임(실시간)":  ["BCAA", "BCTI_PROXY"],
    "기상 특보":     ["WEATHER_ALERT_COUNT", "WEATHER_ANOMALY_SCORE"],
    # RSS_SOURCES 전 계열을 등재한다 — 레지스트리에 없으면 수집돼도 다이제스트에
    # 나타나지 않고 온톨로지 태그 배정 점검(C12)에서도 빠진다.
    "전문 매체":     ["RSS_FARMDOC_DAILY", "RSS_WORLD_GRAIN", "RSS_OFI_MAGAZINE",
                     "RSS_GRAIN_ORG", "RSS_SOYGROWERS", "RSS_CLIMATEPOL",
                     "RSS_AGMARKET", "RSS_GRAINCENTRAL", "RSS_TFM", "RSS_UKRAGRO",
                     # 2026-09-13 승인자 지시 — Reuters·AP (대두유 수급·가격 영향 기사 매일 점검)
                     "RSS_REUTERS_COMMODITIES", "RSS_REUTERS_CLIMATE_ENERGY",
                     "RSS_AP_COMMODITIES", "RSS_AP_WORLD"],
}

# ── 전문 매체 RSS (조정자 지시 8/25 · 확장 8/25 2차 — 일별·거시 시황 소스) ──────
# egress_allowlist 등재 호스트만. RSS 실패는 다이제스트를 죽이지 않는다(비치명).
# URL 후보는 폴백 순서 — 실제 피드 경로는 Actions 런 로그로 판정(샌드박스 열람 차단).
# ⚠️ IGC(igc.int)는 RSS 부재 추정 — 월별 Grain Market Report는 수동/추후 경로(미편입).
def _gnews(site: str, topic: str, when: str = "2d") -> str:
    """Google News RSS 검색 프록시 URL — 매체(site:)와 주제어를 질의에 넣어 서버측에서 좁힌다."""
    from urllib.parse import quote
    q = f"when:{when} site:{site} {topic}"
    return f"https://news.google.com/rss/search?q={quote(q)}&hl=en-US&gl=US&ceid=US:en"


# ── 2026-09-13 승인자 지시 후속 — Reuters·AP 3단 폴백 체인 (A-259) ────────────────
# 채널 순서: ① Google News RSS 프록시 → ② GDELT DOC 2.0(domain: 한정) → ③ Bing News RSS
#           → ④ 원문 섹션 URL(비브라우저 차단 예상 — 열람용). 승자 규칙 = **관련 기사 ≥1건을
#           낸 첫 채널**(구 규칙 '항목이 있는 첫 URL'은 무관 기사만 있는 채널이 승리해 뒤 채널을
#           가리는 결함이 있었음). 어느 채널이 이겼는지는 note 앞머리 "[채널: …]"로 남긴다.
# ⚠️ GDELT DOC 질의 주의(웹 조사 확인):
#   - `domain:` 는 부분 문자열 매칭(reuters.com → www.reuters.com·jp.reuters.com 모두 포함).
#   - `site:`·`when:` 연산자는 없음 — 기간은 timespan 파라미터로만 제어(2d = 48시간).
#   - OR 는 반드시 괄호 안에서만 허용, 다단어는 큰따옴표 필수(기존 _gnews 주제어와 동일 형식이라
#     그대로 재사용). 3자 미만 단어·특수문자는 거부될 수 있음(주제어에 없음).
#   - 무료 API 레이트리밋이 엄격 — 호출 간 6초 간격(geointel_connector A-142 동일), 일 최대 4회.
#   - seendate 는 `YYYYMMDDTHHMMSSZ`(UTC) — 기사 발행일이 아니라 GDELT 색인 시각이므로 하루
#     정도 늦게 잡힐 수 있음(2일 컷오프 안에서 흡수).
GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
_TOPIC_REUTERS_COMMODITIES = ("(soybean OR soyoil OR \"soybean oil\" OR \"vegetable oil\" OR "
                              "\"palm oil\" OR crush OR biodiesel OR tariff OR \"export tax\" "
                              "OR freight OR carbon)")
_TOPIC_REUTERS_CLIMATE_ENERGY = ("(biofuel OR biodiesel OR \"renewable diesel\" OR RVO OR EPA OR "
                                 "drought OR \"El Nino\" OR \"La Nina\" OR climate)")
_TOPIC_AP_COMMODITIES = ("(soybean OR \"soybean oil\" OR \"vegetable oil\" OR \"palm oil\" OR "
                         "commodities OR futures OR CFTC OR tariff OR freight)")
_TOPIC_AP_WORLD = ("(\"Red Sea\" OR Hormuz OR \"Black Sea\" OR \"Suez\" OR Argentina OR "
                   "Brazil OR drought OR tariff OR shipping)")
# A-273: 지정학 레인 — 분쟁·제재·해협 기사(농산물 맥락 없이도 통과, 채널당 3건 캡)
_TOPIC_GEO = ("(Iran OR Hormuz OR Houthi OR Russia OR Ukraine OR \"Black Sea\" OR sanctions OR "
              "CIA OR ceasefire)")
_CHANNEL_LABELS = {"gnews": "Google News", "gdelt": "GDELT", "bing": "Bing News",
                   "rss": "공식 RSS", "raw": "원문"}
_GDELT_CALLS = 0   # 프로세스 내 GDELT 호출 수 — 첫 호출 전에는 대기하지 않는다(테스트가 patch 가능)


def _gdelt(domain: str, topic: str, timespan: str = "2d") -> dict:
    """GDELT DOC 2.0 폴백 슬롯 — URL 대신 dict 스펙(질의는 호출 시점에 조립)."""
    return {"gdelt": {"domain": domain, "topic": topic, "timespan": timespan}}


def _bing(site: str, topic: str) -> str:
    """Bing News RSS 검색 URL(site: 한정 + 주제어, format=rss) — 표준 RSS 2.0(약 14건 상한)."""
    from urllib.parse import quote_plus
    return f"https://www.bing.com/news/search?q={quote_plus(f'site:{site} {topic}')}&format=rss"


def _channel_of(entry: str | dict) -> str:
    """슬롯 항목 → 채널명 {gnews, gdelt, bing, rss, raw}."""
    if isinstance(entry, dict):
        return "gdelt"
    if "news.google.com" in entry:
        return "gnews"
    if "bing.com" in entry:
        return "bing"
    if "reuters.com" in entry or "apnews.com" in entry:
        return "raw"
    return "rss"


RSS_SOURCES = {
    # farmdoc daily(일리노이대) — 작황·바이오연료·무역 실증 분석 (A-201 farmdoc 논문 계열)
    "RSS_FARMDOC_DAILY": ["https://farmdocdaily.illinois.edu/feed"],
    # World Grain — 곡물·유지 산업 전문지 (한국 압착·생산 기사 다수 — 부록 3차)
    "RSS_WORLD_GRAIN": ["https://www.world-grain.com/rss/articles",
                        "https://www.world-grain.com/rss"],
    # OFI(Oils & Fats International) — 유지 산업 전문지 (한국 압착·중국 순수출 기사)
    "RSS_OFI_MAGAZINE": ["https://www.ofimagazine.com/news/rss",
                         "https://www.ofimagazine.com/rss"],
    # GRAIN — 농업·식량 체계 NGO (토지·정책 신호)
    "RSS_GRAIN_ORG": ["https://grain.org/en/rss",
                      "https://grain.org/system/articles.rss"],
    # ASA(미 대두협회) — 미 대두 정책·업계 신호 (부록 2차 #6 Iowa Soy 계열)
    "RSS_SOYGROWERS": ["https://soygrowers.com/feed/",
                       "https://soygrowers.com/category/news-releases/feed/"],
    # 크라이미트폴 — 한국 기후·에너지 매체 (SAF·바이오연료 국문 — 부록 8차 원문 소스)
    # A-269: 전체 기사 피드가 1순위라 골프·관광 기사가 유입됐음 → 섹션 피드(S1N2)를 1순위, 전체는 폴백
    "RSS_CLIMATEPOL": ["https://www.climatepol.com/rss/S1N2.xml",
                       "https://www.climatepol.com/rss/allArticle.xml"],
    # ── 2026-08-28 조정자 추가 지시 4계열 (egress v2.5) — WordPress /feed 관행,
    #    실피드 URL은 샌드박스 차단으로 미검증: 첫 Actions 런 로그로 확정(비치명 설계) ──
    # AgMarket.Net — 조간·마감 시장 분석
    "RSS_AGMARKET": ["https://www.agmarket.net/feed/",
                     "https://www.agmarket.net/category/daily/pm-report/feed/"],
    # Grain Central(호주) — 무역·작황·기상
    "RSS_GRAINCENTRAL": ["https://www.graincentral.com/feed/",
                         "https://www.graincentral.com/trade/feed/"],
    # Total Farm Marketing — TFM 360° 곡물 리포트 (시세 페이지는 yfinance·TE로 기수집)
    "RSS_TFM": ["https://www.totalfarmmarketing.com/feed/",
                "https://www.totalfarmmarketing.com/tfm-reports/tfm-360-grain/feed/"],
    # UkrAgroConsult — 흑해 유지작물·곡물·물류 (해바라기유 축 — D-049 정합)
    "RSS_UKRAGRO": ["https://ukragroconsult.com/en/feed/",
                    "https://ukragroconsult.com/feed/"],
    # ── 2026-09-13 승인자 지시 — Reuters·AP 6개 섹션 (egress v2.6 → v2.7 폴백 확장) ────
    #   두 매체 모두 공개 RSS를 폐지(Reuters 2020·AP hub .rss 미유지 — 웹 조사 확인)했으므로
    #   ① Google News RSS 검색 프록시(site: 한정 + 대두유 수급·가격 키워드 서버측 삽입 —
    #   표준 RSS 2.0) → ② GDELT DOC 2.0 domain: 한정(egress 기등재) → ③ Bing News RSS
    #   (egress v2.7) → ④ 승인자 원문 섹션 URL(비브라우저 차단 예상·열람용). 전 채널 비치명 —
    #   실제 통과 채널은 첫 Actions 런 로그·아카이브 note "[채널: …]"로 실증한다.
    # A-273: 통신사 지정학 레인(미국–이란·러시아–EU·흑해·제재) — 같은 채널 체인, 전용 게이트(_GEO_SOURCES) · 통신사 농산물 레인보다 앞에 두어 해협 기사를 먼저 가져감(A-276)
    "RSS_REUTERS_GEO": [
        _gnews("reuters.com", _TOPIC_GEO),
        _gdelt("reuters.com", _TOPIC_GEO),
        _bing("reuters.com", _TOPIC_GEO),
        "https://www.reuters.com/world/middle-east/"],
    "RSS_AP_GEO": [
        _gnews("apnews.com", _TOPIC_GEO),
        _gdelt("apnews.com", _TOPIC_GEO),
        _bing("apnews.com", _TOPIC_GEO),
        "https://apnews.com/hub/iran"],
    "RSS_REUTERS_COMMODITIES": [
        _gnews("reuters.com", _TOPIC_REUTERS_COMMODITIES),
        _gdelt("reuters.com", _TOPIC_REUTERS_COMMODITIES),
        _bing("reuters.com", _TOPIC_REUTERS_COMMODITIES),
        "https://www.reuters.com/markets/commodities/",
        "https://www.reuters.com/markets/carbon/"],
    "RSS_REUTERS_CLIMATE_ENERGY": [
        _gnews("reuters.com", _TOPIC_REUTERS_CLIMATE_ENERGY),
        _gdelt("reuters.com", _TOPIC_REUTERS_CLIMATE_ENERGY),
        _bing("reuters.com", _TOPIC_REUTERS_CLIMATE_ENERGY),
        "https://www.reuters.com/sustainability/climate-energy/"],
    "RSS_AP_COMMODITIES": [
        _gnews("apnews.com", _TOPIC_AP_COMMODITIES),
        _gdelt("apnews.com", _TOPIC_AP_COMMODITIES),
        _bing("apnews.com", _TOPIC_AP_COMMODITIES),
        "https://apnews.com/hub/commodity-markets",
        "https://apnews.com/hub/commodity-futures-trading-commission"],
    "RSS_AP_WORLD": [
        _gnews("apnews.com", _TOPIC_AP_WORLD),
        _gdelt("apnews.com", _TOPIC_AP_WORLD),
        _bing("apnews.com", _TOPIC_AP_WORLD),
        "https://apnews.com/world-news"],
    # S&P Global Commodity Insights: 공개 RSS 부재 추정 — 자동 수집 미등재(실패 소음 방지).
    # 부록 인사이트는 Perplexity 프록시 경유 요약으로 커버 (egress에는 열람용 등재)
}
# SBO·유지 관련 기사만 통과 — A-269(2026-09-14) 재설계:
#   ① 영문은 제목+요약 소문자 부분 일치(종전과 동일), 단 'saf'는 safety에 걸리므로 단어 경계 정규식으로만.
#   ② 국문은 '유지'(인명·"유지하다"에 오탐 — 실측 '오호리 유지로') 대신 '유지류'로, SAF는 '지속가능항공유'.
#   ③ 국문 매체(RSS_CLIMATEPOL)는 **제목 매칭 필수** — 설명문 단독 매칭이 골프·관광 기사를 통과시켰다.
#   ④ 매칭 키워드를 항목에 기록(`_kw`) → note 접두 `[채널: X · kw:…]`로 감사 가능.
_RSS_KEYWORDS_EN = (
    "soybean", "soy oil", "soyoil", "soybean oil", "vegetable oil", "oilseed",
    "palm oil", "canola", "rapeseed", "sunflower", "crush", "biodiesel",
    "renewable diesel", "wasde", "export tax", "tariff", "south korea", "nopa", "small refinery", "45z",
    "biofuel", "freight", "drought", "el niño", "el nino", "la niña", "la nina",
    "red sea", "hormuz", "black sea",
)
_RSS_KEYWORDS_KO = (
    "대두", "대두유", "팜유", "식용유", "유지류", "바이오디젤", "바이오연료",
    "항공유", "지속가능항공유", "곡물", "수출세", "관세",
)
# 단어 경계 필수 — 'safety'·'nervous'(rvo) 오탐 차단(A-274). 그 자체로 특정적이라 맥락어 불요.
_RSS_KEYWORD_REGEX = (re.compile(r"\bsaf\b"), re.compile(r"\brvo\b"), re.compile(r"\bcftc\b"))
_TITLE_ONLY_SOURCES = {"RSS_CLIMATEPOL"}                  # 국문 종합 매체: 제목에 키워드가 있어야 통과
_RSS_KEYWORDS = _RSS_KEYWORDS_EN + _RSS_KEYWORDS_KO       # 하위 호환(테스트·외부 참조)
NOTE_BUDGET = 2400                                         # A-284: 한국어 헤드라인+원제+요약 400자×3건(구 900)
DESC_CHARS = 400                                           # A-284: 요약 저장 160→400자(승인자 지시 — 본문 근거 보존)
_TAG_RE = re.compile(r"<[^>]+>")

# ── A-284(검증 4): 기사별 한국어 헤드라인 — 다이제스트 단계에서 1회 생성·캐시·커밋 ──────────
# 모델: 승인자 지정 gpt-5.6-luna(추론 xhigh — 독해·번역 정확도 최우선). 실패·키 부재는 원제 폴백(비치명).
# 비용 통제: 기사당 1회(hashlib 캐시 커밋) · 일 상한 KO_HEADLINE_DAILY_CAP(기본 60) · 배치 호출(지표당 1회).
KO_SEP = " ‖ "                                             # note 규약: `ko ‖ 원제 — 요약 (url)` — 브리프 파서와 공유
KO_CACHE = Path("data/processed/ko_headline_cache.json")
KO_DAILY_CAP = int(os.environ.get("KO_HEADLINE_DAILY_CAP", "60"))
KO_MODEL = os.environ.get("BRIEF_LLM_MODEL", "gpt-5.6-luna")
KO_EFFORT = os.environ.get("BRIEF_LLM_EFFORT", "xhigh")
KO_MAX_CHARS = 40
_KO_SYSTEM = ("너는 대두유 조달 데스크의 편집자다. 영문(또는 국문) 기사 제목과 요약을 읽고 한국어 헤드라인 한 줄로 "
              f"바꿔라. 규칙: ①{KO_MAX_CHARS}자 이내 ②사실만(전망·확률·매수·매도 판단 표현 금지) ③고유명사·수치·단위 보존 "
              "④기관·매체 이름은 통용 한글 표기 ⑤JSON만 출력.")
_KV_KEY_RE = re.compile(r"(?:^|[\s|])([A-Z][A-Z_]{1,}):\s*")   # 브리프 _parse_kv와 같은 키 정의(2자+·공백 선택)


def _is_kv_note(text: str) -> bool:
    """`KEY: value | KEY: value` 구조화 응답인가(키 2개 이상) — 구조화 행은 브리프가 이미 한글로 렌더."""
    return len(_KV_KEY_RE.findall(str(text or "").replace("**", ""))) >= 2


def _ko_key(title: str, desc: str) -> str:
    import hashlib
    return hashlib.sha1(f"{title}|{str(desc)[:300]}".encode("utf-8")).hexdigest()[:20]


def _load_ko_cache() -> dict:
    try:
        import json
        return json.loads(KO_CACHE.read_text(encoding="utf-8")) if KO_CACHE.is_file() else {}
    except Exception:                                          # noqa: BLE001
        return {}


def _save_ko_cache(cache: dict) -> None:
    import json
    KO_CACHE.parent.mkdir(parents=True, exist_ok=True)
    KO_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")


def _llm_ko_batch(items: list[dict]) -> dict[str, str]:
    """[{key,title,desc}] → {key: ko}. OpenAI 직접 호출(reasoning_effort 미지원 시 자동 생략). 실패는 빈 사전."""
    import json
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key or not items:
        return {}
    try:
        from openai import OpenAI
    except ImportError:
        print("[정보] openai 패키지 미설치 — 한국어 헤드라인 생략(원제 유지)")
        return {}
    payload = [{"id": i, "title": it["title"][:200], "desc": str(it.get("desc", ""))[:400]}
               for i, it in enumerate(items)]
    req = {"model": KO_MODEL,
           "messages": [{"role": "system", "content": _KO_SYSTEM},
                        {"role": "user", "content": "다음 기사 각각의 한국어 헤드라인을 만들어라. "
                                                    'JSON {"headlines":[{"id":0,"ko":"..."}]} 형식만. 기사: '
                                                    + json.dumps(payload, ensure_ascii=False)}],
           "response_format": {"type": "json_object"}}
    try:
        client = OpenAI(api_key=key)
        try:
            resp = client.chat.completions.create(**req, reasoning_effort=KO_EFFORT)
        except TypeError:
            resp = client.chat.completions.create(**req)
        except Exception as e:                                 # noqa: BLE001 — 400(effort 미지원) 등
            if "reasoning" in str(e).lower() or "effort" in str(e).lower():
                resp = client.chat.completions.create(**req)
            else:
                raise
        data = json.loads(resp.choices[0].message.content or "{}")
    except Exception as e:                                     # noqa: BLE001 — 비치명(원제 폴백)
        print(f"[경고] 한국어 헤드라인 호출 실패(비치명 · 모델 {KO_MODEL}): {type(e).__name__}: {str(e)[:160]}")
        return {}
    out: dict[str, str] = {}
    for h in data.get("headlines", []) or []:
        try:
            i = int(h.get("id"))
            ko = re.sub(r"\s+", " ", str(h.get("ko", ""))).strip().replace(KO_SEP.strip(), "|")
            ko = ko.replace(" ⋅ ", " · ").replace(" — ", " - ")            # note 분할 규약(⋅·—) 보호
        except (TypeError, ValueError):
            continue
        if 0 <= i < len(items) and ko:
            out[items[i]["key"]] = ko[:KO_MAX_CHARS + 20]
    return out


def ko_headlines(items: list[dict]) -> dict[str, str]:
    """기사 목록 [{title, desc}] → {key: ko}. 캐시 우선·일 상한·배치 호출. 키 없거나 실패면 빈 값(원제 폴백)."""
    if not items:
        return {}
    cache = _load_ko_cache()
    today_k = f"_calls_{date.today().isoformat()}"
    used = int(cache.get(today_k, 0) or 0)
    result: dict[str, str] = {}
    todo: list[dict] = []
    for it in items:
        k = _ko_key(it.get("title", ""), it.get("desc", ""))
        it["key"] = k
        if k in cache and cache[k]:
            result[k] = cache[k]
        elif len(todo) + used < KO_DAILY_CAP:
            todo.append(it)
    if todo and os.environ.get("OPENAI_API_KEY", "").strip():
        got = _llm_ko_batch(todo)
        if got:
            cache.update(got)
            cache[today_k] = used + len(todo)
            _save_ko_cache(cache)
            result.update(got)
            print(f"[한국어 헤드라인] 신규 {len(got)}/{len(todo)}건 생성(캐시 적중 {len(result) - len(got)}) · "
                  f"모델 {KO_MODEL}/{KO_EFFORT} · 일 사용 {used + len(todo)}/{KO_DAILY_CAP}")
    elif todo:
        print(f"[정보] OPENAI_API_KEY 미설정 — 한국어 헤드라인 {len(todo)}건 생략(원제 유지)")
    return result


def _clean_desc(raw: str, n: int = DESC_CHARS) -> str:
    """RSS description/summary → 태그·개행 제거 후 n자."""
    import html as _html
    txt = _html.unescape(_TAG_RE.sub(" ", str(raw or "")))
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt[:n].rstrip() + ("…" if len(txt) > n else "")


# 범용 키워드(관세·운임·가뭄·해협 등)는 농산물·유지 맥락어와 **동반될 때만** 통과 — 실측 오탐: AP 'Irish whiskey tariff'.
# A-274: 'crush'(크리켓 crush Sri Lanka)·'el niño'(보건 기사)도 범용어로 — 농산물 맥락 동반 필수.
_GENERIC_KEYWORDS = {"tariff", "export tax", "freight", "drought", "red sea", "hormuz", "black sea", "south korea",
                     "biofuel", "crush", "el niño", "el nino", "la niña", "la nina", "관세", "수출세", "곡물"}
# A-274: 맥락어 'oil'은 원유 기사(한국 원유 수입 정책 등)를 통과시켰다 → 식용유·유지 표현으로 한정.
_AGRI_CONTEXT = ("soy", "soyoil", "vegetable oil", "palm oil", "edible oil", "cooking oil", "oilseed",
                 "grain", "crop", "farm", "agri", "palm", "biodiesel", "canola", "rapeseed",
                 "sunflower", "wheat", "corn", "vessel", "tanker", "ship", "strait", "commodit", "harvest",
                 "대두", "유지류", "곡물", "농산", "농업", "팜", "선박", "해협", "운임", "바이오")
# A-273: 지정학 레인 전용 게이트 — 분쟁·제재·해협 어휘(단어 경계), 농산물 맥락 불요
_GEO_SOURCES = {"RSS_REUTERS_GEO", "RSS_AP_GEO"}
_GEO_KEYWORD_REGEX = re.compile(
    r"\b(iran|iranian|hormuz|houthi|red sea|russia|russian|ukraine|ukrainian|black sea|sanctions?|cia|"
    r"ceasefire|strait|tankers?|brent)\b|이란|호르무즈|러시아|우크라이나|흑해|제재", re.IGNORECASE)
_GEO_LANE_CAP = 3


def _match_keyword(title: str, desc: str, indicator: str = "") -> str | None:
    """통과 키워드 반환(없으면 None). 국문 매체는 제목 기준, 그 외는 제목+요약. 범용어는 맥락어 동반 필수.
    지정학 레인(_GEO_SOURCES)은 전용 어휘만 보고 농산물 맥락을 요구하지 않는다(A-273)."""
    t = str(title).lower(); d = str(desc).lower()
    blob = t if indicator in _TITLE_ONLY_SOURCES else f"{t} {d}"
    if indicator in _GEO_SOURCES:
        m = _GEO_KEYWORD_REGEX.search(blob)
        return m.group(0).lower() if m else None
    has_ctx = any(c in blob for c in _AGRI_CONTEXT)
    for k in _RSS_KEYWORDS_EN + _RSS_KEYWORDS_KO:
        if k in blob and (k not in _GENERIC_KEYWORDS or has_ctx):
            return k
    for rx in _RSS_KEYWORD_REGEX:                      # 단어 경계 SAF는 그 자체로 특정적 — 맥락어 불요
        if rx.search(blob):
            return rx.pattern.strip("\\b")
    return None


def _items_from_rss(content: bytes) -> list[dict]:
    """RSS 2.0 <item> 및 Atom <entry> → 항목 dict {title, link, desc, date}. pubDate 부재·파싱 실패는 당일.

    A-269: 요약문(description/summary/content:encoded)을 보존해 브리프가 '핵심 내용'을 쓸 수 있게 한다.
    """
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime

    root = ET.fromstring(content)
    items: list[dict] = []

    def _date(txt: str | None) -> pd.Timestamp:
        if not txt:
            return pd.Timestamp(date.today())
        try:
            return pd.Timestamp(parsedate_to_datetime(txt).date())
        except Exception:
            try:
                return pd.Timestamp(pd.Timestamp(txt).date())
            except Exception:
                return pd.Timestamp(date.today())

    for it in root.findall(".//item"):                       # RSS 2.0
        desc = (it.findtext("description") or it.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or "")
        items.append({"title": (it.findtext("title") or "").strip(),
                      "link": (it.findtext("link") or "").strip(),
                      "desc": _clean_desc(desc),
                      "date": _date(it.findtext("pubDate"))})
    ns = "{http://www.w3.org/2005/Atom}"
    for en in root.findall(f".//{ns}entry"):                # Atom
        link_el = en.find(f"{ns}link")
        link = (link_el.get("href") if link_el is not None else "") or ""
        desc = en.findtext(f"{ns}summary") or en.findtext(f"{ns}content") or ""
        items.append({"title": (en.findtext(f"{ns}title") or "").strip(),
                      "link": link.strip(), "desc": _clean_desc(desc),
                      "date": _date(en.findtext(f"{ns}updated") or en.findtext(f"{ns}published"))})
    return items


def _gdelt_get_json(params: dict) -> dict:
    """GDELT DOC 2.0 GET → JSON dict. 실패 시 {}(비치명) — 테스트가 이 지점을 대체한다.

    geointel_connector(A-142·A-220)와 동일 규약: 매 시도 새 클라이언트(SSL 핸드셰이크
    타임아웃 시 커넥션 재사용 방지)·timeout 60/connect 20·429는 30초 대기·3회(10→20s 백오프).
    """
    import httpx

    for attempt in range(3):
        try:
            with httpx.Client(timeout=httpx.Timeout(60, connect=20)) as c:
                r = c.get(GDELT_DOC_URL, params=params)
            if r.status_code == 429:
                if attempt < 2:
                    print("[정보] GDELT 429 — 30초 대기 후 재시도")
                    time.sleep(30)
                    continue
                print("[경고] GDELT 재시도 후에도 429 — 건너뜀")
                return {}
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, dict) else {}
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            if attempt < 2:
                wait = 10 * (attempt + 1)
                print(f"[정보] GDELT 오류({type(e).__name__}) — {wait}s 후 재시도")
                time.sleep(wait)
                continue
            print(f"[경고] GDELT 3회 실패: {type(e).__name__}")
    return {}


def _items_from_gdelt(spec: dict) -> list[dict]:
    """GDELT DOC 2.0 artlist → 항목 dict 목록. 호출 간 6초 페이싱(첫 호출은 즉시)."""
    global _GDELT_CALLS
    if _GDELT_CALLS > 0:
        time.sleep(6)   # 무료 API 레이트리밋 — 프로세스 내 두 번째 호출부터 간격 유지
    _GDELT_CALLS += 1
    params = {
        "query": f"domain:{spec['domain']} {spec['topic']}",
        "mode": "artlist", "format": "json",
        "timespan": spec.get("timespan", "2d"),
        "maxrecords": "25", "sort": "DateDesc",
    }
    items: list[dict] = []
    for a in _gdelt_get_json(params).get("articles", []) or []:
        seen = str(a.get("seendate", "") or "")
        try:
            d = pd.Timestamp(pd.to_datetime(seen, format="%Y%m%dT%H%M%SZ").date()) if seen \
                else pd.Timestamp(date.today())
        except (ValueError, TypeError):
            d = pd.Timestamp(date.today())
        items.append({"title": str(a.get("title", "") or "").strip(),
                      "link": str(a.get("url", "") or "").strip(),
                      "desc": "", "date": d})
    return items


_TITLE_SUFFIX_RE = re.compile(r"\s*[-–|]\s*(ap news|reuters|apnews\.com|reuters\.com)\s*$", re.IGNORECASE)


def _norm_title(title: str) -> str:
    """채널 간 중복 판정용 제목 정규화 — 매체 접미('- AP News') 제거·소문자·공백 축약(A-274)."""
    t = _TITLE_SUFFIX_RE.sub("", str(title or "")).lower()
    return re.sub(r"\s+", " ", t).strip()


def _filter_items(items: list[dict], cutoff: pd.Timestamp, indicator: str = "",
                  seen_titles: set[str] | None = None, stats: dict | None = None) -> list[dict]:
    """2일 컷오프 + 키워드 게이트(매칭어 기록) + 링크·제목 중복 제거(첫 항목 유지).

    `seen_titles`를 넘기면 채널 간(AP 국제↔상품 등) 동일 기사를 뒤 채널에서 제거한다(A-274).
    """
    kept: list[dict] = []
    seen_links: set[str] = set()
    for it in items:
        if it["date"] < cutoff:
            continue
        kw = _match_keyword(it.get("title", ""), it.get("desc", ""), indicator)
        if kw is None:
            continue
        it["_kw"] = kw
        link = it["link"]
        if link and link in seen_links:
            continue
        nt = _norm_title(it.get("title", ""))
        if seen_titles is not None and nt and nt in seen_titles:
            if stats is not None:
                stats["dupes"] = stats.get("dupes", 0) + 1
            continue
        if indicator in _GEO_SOURCES and len(kept) >= _GEO_LANE_CAP:   # A-276: 캡을 기록 전에 적용
            break
        seen_links.add(link)
        if seen_titles is not None and nt:
            seen_titles.add(nt)
        kept.append(it)
    return kept


def _fetch_specialist_media() -> list[dict]:
    """전문 매체 채널 체인 → 일자·소스별 1행(값=관련 기사 수, note=[채널] 제목+링크 — S-5).

    채널: 공식 RSS / Google News 프록시 / GDELT DOC 2.0 / Bing News RSS / 원문. 승자 규칙은
    **관련 기사 ≥1건을 낸 첫 채널**(무관 기사만 있는 채널은 뒤 채널을 가리지 않는다).
    파싱은 stdlib XML만 사용(신규 의존성 없음 — httpx는 커넥터 공통 의존). 항목이 임계
    대상이 아니므로 온톨로지 후보 큐에는 넣지 않는다 — 태그 매칭·시계열화는
    build_unstructured_timeseries 편입 시(30일+ 축적 후) 판단.
    """
    try:
        import httpx
    except ImportError:
        print("[경고] httpx 미설치 — 전문 매체 RSS 수집 건너뜀")
        return []

    cutoff = pd.Timestamp(date.today()) - pd.Timedelta(days=2)
    rows: list[dict] = []
    winners: dict[str, str] = {}
    seen_titles: set[str] = set()                            # A-274: 채널 간 동일 기사 1회만
    for indicator, entries in RSS_SOURCES.items():
        kept: list[dict] = []
        channel = ""
        for entry in entries:
            ch = _channel_of(entry)
            try:
                if ch == "gdelt":
                    items = _items_from_gdelt(entry["gdelt"])
                else:
                    r = httpx.get(entry, timeout=30, follow_redirects=True,
                                  headers={"User-Agent": "Mozilla/5.0 (Nexus data pipeline)"})
                    r.raise_for_status()
                    items = _items_from_rss(r.content)
            except Exception as e:   # 네트워크·파싱 어느 쪽이든 비치명
                print(f"[경고] 매체 수집 실패({indicator}·{ch}): {type(e).__name__} — 다음 채널로")
                continue
            _st: dict = {}
            kept = _filter_items(items, cutoff, indicator, seen_titles, _st)
            if kept:
                channel = ch
                break
            if _st.get("dupes"):                              # A-276: 전부 중복이면 다음 채널로 넘기지 않음(재유입·호출 낭비 방지)
                break
        if not kept:
            continue
        winners[indicator] = channel
        if os.environ.get("CRAWL_FULLTEXT") == "1":          # A-292: 게이트 통과 기사 본문 → 코퍼스(비치명)
            try:
                import sys
                sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
                from src.pipeline.connectors import scrapling_connector as sc
                sc.append_corpus(sc.enrich_items(kept, indicator))
            except Exception as e:                            # noqa: BLE001
                print(f"[경고] 본문 크롤링 단계 실패(비치명): {type(e).__name__}")
        label = _CHANNEL_LABELS.get(channel, channel)
        by_date: dict[str, list[str]] = {}
        kws_by_date: dict[str, set[str]] = {}
        try:                                                  # A-284: 기사별 한국어 헤드라인(비치명)
            kos = ko_headlines([{"title": it["title"], "desc": it.get("desc", "")} for it in kept])
        except Exception as e:                                # noqa: BLE001
            print(f"[경고] 한국어 헤드라인 단계 실패(비치명): {type(e).__name__}")
            kos = {}
        for it in kept:
            d_key = str(it["date"].date())
            desc = it.get("desc", "")
            body = f"{it['title']} — {desc}" if desc else it["title"]
            ko = kos.get(_ko_key(it["title"], desc), "")
            if ko:
                body = f"{ko}{KO_SEP}{body}"
            by_date.setdefault(d_key, []).append(f"{body} ({it['link']})")
            kws_by_date.setdefault(d_key, set()).add(str(it.get("_kw", "")))
        for d, notes in sorted(by_date.items()):
            kw_txt = ",".join(sorted(k for k in kws_by_date.get(d, set()) if k))[:60]
            # A-269: 접두를 절단 범위 **안에** 두고(구 코드는 접두 밖에서 잘라 아카이브 [:500]이 재절단) 예산 900자
            note = (f"[채널: {label}" + (f" · kw:{kw_txt}" if kw_txt else "") + "] " + " ⋅ ".join(notes))[:NOTE_BUDGET]
            rows.append({"indicator": indicator, "date": d, "value": len(notes),
                         "note": note, "source": indicator.lower()})
    if rows:
        chan = ", ".join(f"{k}={v}" for k, v in sorted(winners.items()))
        print(f"[전문 매체] RSS 신호 {len(rows)}행 수집 "
              f"({', '.join(sorted({r['indicator'] for r in rows}))}) (채널: {chan})")
    return rows


def main() -> int:
    today = pd.Timestamp(date.today())
    rows: list[dict] = []
    for f in sorted(glob.glob(os.path.join(RAW, "**", "*.parquet"), recursive=True)):
        try:
            df = pd.read_parquet(f)
        except Exception:
            continue
        if "indicator_code" not in df.columns or "price_date" not in df.columns:
            continue
        d = pd.to_datetime(df["price_date"], errors="coerce")
        recent = df[(d >= today - pd.Timedelta(days=2))]      # 주말·시차 여유 2일
        if recent.empty:
            continue
        for _, r in recent.iterrows():
            rows.append({
                "indicator": str(r["indicator_code"]),
                "date": str(pd.Timestamp(r["price_date"]).date()),
                "value": r.get("value"),
                "note": str(r.get("note", "") or "")[:900],   # A-284: 산문 근거 보존(구 400)
                "source": str(r.get("source_name", "") or ""),
            })

    # A-284: 산문형 프록시(브라질 수확·호르무즈 서사·정성 GPR 등)도 한국어 헤드라인 — 구조화(KEY: value) 행은 제외
    try:
        _attach_proxy_ko(rows)
    except Exception as e:                                    # noqa: BLE001 — 비치명
        print(f"[경고] 프록시 한국어 헤드라인 단계 실패(비치명): {type(e).__name__}: {e}")

    # 전문 매체 RSS (조정자 지시 8/25) — 실패해도 다이제스트는 계속
    try:
        rows += _fetch_specialist_media()
    except Exception as e:
        print(f"[경고] 전문 매체 RSS 단계 실패(비치명): {e}")

    got = {r["indicator"] for r in rows}
    lines = [f"# 일별 비정형 신호 다이제스트 — {date.today()}", "",
             "> Perplexity·실시간 프록시 수집분의 당일 요약 (조정자 지시 8/14 · A-163).",
             "> 수치와 함께 근거 발췌(note)를 보존한다 — S-5 출처보존.", ""]
    missing_all: list[str] = []
    for cat, inds in DAILY_UNSTRUCTURED.items():
        hit = [r for r in rows if r["indicator"] in inds]
        lines.append(f"## {cat}")
        lines.append("")
        if not hit:
            missing = [i for i in inds if i not in got]
            lines.append(f"_당일 수집 없음_ (대상: {', '.join(inds[:4])}"
                         f"{' …' if len(inds) > 4 else ''})")
            missing_all += missing
            lines.append("")
            continue
        lines.append("| 지표 | 일자 | 값 | 근거 발췌 |")
        lines.append("|---|---|---|---|")
        seen = set()
        for r in sorted(hit, key=lambda x: (x["indicator"], x["date"]), reverse=True):
            key = (r["indicator"], r["date"])
            if key in seen:
                continue
            seen.add(key)
            note = r["note"].replace("|", "／").replace("\n", " ")[:220]
            lines.append(f"| `{r['indicator']}` | {r['date']} | {r['value']} | {note} |")
        lines.append("")

    lines += ["## 수집 상태 요약", "",
              f"- 당일(±2일) 비정형 지표 확보: **{len(got & set(sum(DAILY_UNSTRUCTURED.values(), [])))}종** / "
              f"대상 {len(set(sum(DAILY_UNSTRUCTURED.values(), [])))}종",
              f"- 미확보: {', '.join(sorted(set(missing_all))[:12]) or '없음'}", ""]

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"daily_unstructured_digest_{date.today()}.md"
    text = "\n".join(lines) + "\n"
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"[완료] → {out}")

    _append_archive(rows)
    _emit_ontology_candidates(rows)
    return 0


_PROXY_TAG_RE = re.compile(r"^(\s*\[[^\]]*\]\s*)(.*)$", re.S)


def _attach_proxy_ko(rows: list[dict]) -> None:
    """산문형 프록시 note에 `ko ‖ ` 삽입(접두 태그 뒤). 구조화 행·빈 본문·이미 삽입된 행은 건너뜀."""
    targets = set(sum(DAILY_UNSTRUCTURED.values(), []))
    cand: list[tuple[dict, str, str]] = []
    for r in rows:
        if r["indicator"] not in targets or str(r["indicator"]).startswith("RSS_"):
            continue
        m = _PROXY_TAG_RE.match(str(r.get("note", "")))
        tag, body = (m.group(1), m.group(2)) if m else ("", str(r.get("note", "")))
        body = body.strip()
        if not body or KO_SEP in body or _is_kv_note(body) or len(body) < 40:
            continue
        hangul = sum(1 for ch in body if "가" <= ch <= "힣")
        if hangul / max(1, len(body)) > 0.3:                  # 이미 한글 서술(GDELT 집계 등)은 요약 불요(런 #115 실측)
            continue
        cand.append((r, tag, body))
    if not cand:
        return
    kos = ko_headlines([{"title": body[:200], "desc": body[200:600]} for _, _, body in cand])
    n = 0
    for r, tag, body in cand:
        ko = kos.get(_ko_key(body[:200], body[200:600]), "")
        if ko:
            r["note"] = f"{tag}{ko}{KO_SEP}{body}"[:NOTE_BUDGET]
            n += 1
    if n:
        print(f"[한국어 헤드라인] 프록시 산문 {n}/{len(cand)}건 삽입")


def _append_archive(rows: list[dict]) -> None:
    """당일 수집 행을 변수별 일별 아카이브 CSV에 append (중복 제거·S-5 발췌 보존)."""
    targets = set(sum(DAILY_UNSTRUCTURED.values(), []))
    cat_of = {ind: cat for cat, inds in DAILY_UNSTRUCTURED.items() for ind in inds}
    new = pd.DataFrame([{
        "date": r["date"],
        "indicator": r["indicator"],
        "category": cat_of.get(r["indicator"], ""),
        "value": r["value"],
        "note": r["note"][:NOTE_BUDGET].replace("\n", " "),
        "source_name": r["source"],
        "appended_at": pd.Timestamp.now("UTC").isoformat(timespec="seconds"),
    } for r in rows if r["indicator"] in targets])
    if new.empty:
        print("[아카이브] 신규 비정형 신호 없음 — append 생략")
        return
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    if ARCHIVE.exists():
        old = pd.read_csv(ARCHIVE, dtype=str)
        merged = pd.concat([old, new.astype(str)], ignore_index=True)
    else:
        merged = new.astype(str)
    before = len(merged)
    merged = merged.drop_duplicates(subset=["date", "indicator"], keep="first")
    merged = merged.sort_values(["date", "indicator"]).reset_index(drop=True)
    n_new = len(merged) - (before - len(new))
    if ARCHIVE.exists() and n_new <= 0:
        print("[아카이브] 전량 기존재(중복) — 파일 무변경")
        return
    merged.to_csv(ARCHIVE, index=False, encoding="utf-8")
    print(f"[아카이브] 신규 {max(n_new, 0)}건 append → {ARCHIVE} (누적 {len(merged)}행)")


# ── 온톨로지 후보 큐 (A-198 · 조정자 재확인 후속) ────────────────────────────
# 일별 신호가 임계를 넘으면 event_schema.json의 MarketEvent 후보(review_status=
# extracted)로 대기열에 적재한다 — **자동화는 후보 발견·적재까지만**이며, causal_edges
# 승격은 P1-06 검증 계약(S-1: 도메인 검증 서명+evidence 필수)을 그대로 따른다.
# 기존 C10 게이트(validate_semantic_layer.py)가 이 파일을 무료로 검증한다.
CANDIDATE_DIR = Path("data/semantic/events")
# 임계: (지표, 판정 함수) — 값 파싱 실패는 후보 미적재(추측 금지)
_CANDIDATE_RULES = {
    "HORMUZ_THREAT_LEVEL":   lambda v: v >= 2,
    "SUEZ_RED_SEA_RISK":     lambda v: v >= 2,
    "US_CHINA_TARIFF_STATUS": lambda v: v >= 2,
    "GEOINTEL_RISK_COMPOSITE": lambda v: v >= 60,
    "GPR_REALTIME":          lambda v: v >= 200,   # 소통용 직관 기준(스킬 정합)
    "US_IRAN_CONFLICT_STATUS":    lambda v: v >= 2,   # A-273
    "RUSSIA_EU_RELATIONS_STATUS": lambda v: v >= 2,   # A-273
}


def _emit_ontology_candidates(rows: list[dict]) -> None:
    """임계 초과 일별 신호 → MarketEvent 후보 JSON (P1-06 검증 입구)."""
    import json
    cands = []
    for r in rows:
        rule = _CANDIDATE_RULES.get(r["indicator"])
        if rule is None:
            continue
        try:
            val = float(str(r["value"]).replace(",", ""))
        except (TypeError, ValueError):
            continue
        if not rule(val):
            continue
        cands.append({
            "event_id": f"EVT-{r['date']}-{r['indicator']}",
            "event_type": "MarketEvent",
            "event_date": r["date"],
            "region": "GLOBAL",
            "confidence": "LOW",                     # 프록시 단일 출처 — 검증 전
            "review_status": "extracted",            # S-1: 자동 승격 금지 — P1-06 검증 대기
            "indicator": r["indicator"],
            "value": val,
            "evidence": [{
                "document_id": f"daily_digest_{r['date']}",
                "page": 1,                            # 다이제스트 단일 페이지 산출물
                "exact_quote": (r.get("note") or "")[:300],
            }],
            "source_name": r.get("source", "perplexity_proxy"),
        })
    if not cands:
        print("[후보 큐] 임계 초과 신호 없음 — 온톨로지 후보 미생성")
        return
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    out = CANDIDATE_DIR / f"candidates_{cands[0]['event_date']}.json"
    out.write_text(json.dumps(cands, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[후보 큐] MarketEvent 후보 {len(cands)}건 → {out} (P1-06 검증 대기 — 자동 승격 없음)")


if __name__ == "__main__":
    raise SystemExit(main())
