"""
기사 본문 크롤링 — Scrapling (A-292)

목적: RSS는 제목+요약(≤400자)만 준다. 키워드 게이트를 통과한 기사 링크에 한해 원문 본문을
      가져와 온톨로지 필터·시계열화가 읽을 수 있는 코퍼스(JSONL)로 남긴다.

범위: 링크 단건 GET만 한다(목록 순회·검색 페이지 크롤링 없음). 도메인 정책은
      config/crawl_sources.yaml(allow/block) + 실행 시 robots.txt 판정. 모든 실패는 비치명.

출력: data/processed/crawl_corpus/YYYY-MM.jsonl — 1행 1기사
      {url, domain, indicator, title, published, available_at, kw, text}
      available_at = 수집 시각(UTC) — as-of 규칙(모델 t일 입력은 available_at ≤ t).

의존성: scrapling[fetchers]==0.5 (Fetcher = curl_cffi 브라우저 TLS 지문), pyyaml
"""
from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

POLICY_PATH = Path("config/crawl_sources.yaml")
CORPUS_DIR = Path("data/processed/crawl_corpus")
DEFAULT_SELECTORS = ("article", "main", "[itemprop=articleBody]", "body")
MAX_TEXT_CHARS = 6000                     # 기사당 저장 상한 — 저장소 증가 통제(일 40건 × 6KB)
MIN_TEXT_CHARS = 200                      # 이보다 짧으면 본문 추출 실패로 본다(메뉴·쿠키 배너)
DAILY_CAP = int(os.environ.get("CRAWL_DAILY_CAP", "40"))
DOMAIN_DELAY_S = 2.0                      # 같은 도메인 연속 요청 간격
USER_AGENT = "Mozilla/5.0 (Nexus data pipeline; soybean-oil research)"
_WS_RE = re.compile(r"\s+")

_robots: dict[str, RobotFileParser | None] = {}
_last_hit: dict[str, float] = {}
_fetched = 0


def load_policy(path: Path = POLICY_PATH) -> dict:
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {"allow": data.get("allow") or {}, "block": data.get("block") or {}}


def _domain_rule(host: str, policy: dict) -> tuple[str, dict | str | None]:
    """('block', 사유) | ('allow', 규칙) | ('unknown', None). 하위 도메인은 상위 규칙을 따른다."""
    for key in ("block", "allow"):
        for dom, rule in policy[key].items():
            if host == dom or host.endswith("." + dom):
                return key, rule or {}
    return "unknown", None


def _robots_ok(url: str) -> bool:
    p = urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in _robots:
        rp = RobotFileParser(f"{base}/robots.txt")
        try:
            rp.read()
        except Exception:                 # noqa: BLE001 — robots 조회 실패 = 판정 불가 → 수집 안 함
            rp = None
        _robots[base] = rp
    rp = _robots[base]
    return bool(rp and rp.can_fetch(USER_AGENT, url))


def extract_text(page, selectors: tuple[str, ...] | list[str]) -> str:
    """Scrapling Selector/Response → 본문 텍스트(공백 축약·상한 절단). 후보 중 첫 충분한 길이."""
    for css in selectors:
        found = page.css(css)
        if not found:
            continue
        text = _WS_RE.sub(" ", str(found[0].get_all_text(separator=" ", strip=True))).strip()
        if len(text) >= MIN_TEXT_CHARS:
            return text[:MAX_TEXT_CHARS]
    return ""


def fetch_article(url: str, policy: dict) -> str:
    """정책·robots 통과 시 본문 텍스트, 아니면 ''(비치명)."""
    global _fetched
    host = urlparse(url).netloc.lower()
    kind, rule = _domain_rule(host, policy)
    if kind != "allow" or _fetched >= DAILY_CAP or not _robots_ok(url):
        return ""
    wait = DOMAIN_DELAY_S - (time.monotonic() - _last_hit.get(host, -DOMAIN_DELAY_S))
    if wait > 0:
        time.sleep(wait)
    try:
        from scrapling.fetchers import Fetcher

        page = Fetcher.get(url, impersonate="chrome", stealthy_headers=True, timeout=30,
                           follow_redirects=True, headers={"User-Agent": USER_AGENT})
    except Exception as e:                # noqa: BLE001 — 네트워크·의존성 어느 쪽이든 비치명
        print(f"[경고] 본문 크롤링 실패({host}): {type(e).__name__}")
        return ""
    finally:
        _last_hit[host] = time.monotonic()
        _fetched += 1
    if getattr(page, "status", 200) >= 400:
        print(f"[경고] 본문 크롤링 HTTP {page.status}({host})")
        return ""
    return extract_text(page, (rule or {}).get("selector") or DEFAULT_SELECTORS)


def enrich_items(items: list[dict], indicator: str, policy: dict | None = None) -> list[dict]:
    """게이트 통과 기사 → 코퍼스 레코드(본문 추출 성공분만). 정책 로드 실패 시 []."""
    try:
        policy = policy or load_policy()
    except Exception as e:                # noqa: BLE001
        print(f"[경고] 크롤링 정책 로드 실패 — 본문 수집 건너뜀: {type(e).__name__}")
        return []
    records = []
    for it in items:
        text = fetch_article(it.get("link", ""), policy) if it.get("link") else ""
        if not text:
            continue
        records.append({
            "url": it["link"], "domain": urlparse(it["link"]).netloc.lower(),
            "indicator": indicator, "title": it.get("title", ""),
            "published": str(it["date"].date()) if hasattr(it.get("date"), "date") else "",
            "available_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "kw": it.get("_kw", ""), "text": text,
        })
    return records


def append_corpus(records: list[dict], corpus_dir: Path = CORPUS_DIR) -> int:
    """월별 JSONL에 URL 기준 중복 없이 추가. 추가 건수 반환."""
    if not records:
        return 0
    corpus_dir.mkdir(parents=True, exist_ok=True)
    out = corpus_dir / f"{records[0]['available_at'][:7]}.jsonl"
    seen = set()
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            try:
                seen.add(json.loads(line)["url"])
            except (ValueError, KeyError):
                continue
    new = [r for r in records if r["url"] not in seen]
    with out.open("a", encoding="utf-8") as f:
        for r in new:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[본문 코퍼스] {len(new)}건 추가 → {out}")
    return len(new)
