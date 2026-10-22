"""A-292 — Scrapling 본문 크롤링: 도메인 정책·본문 추출·코퍼스 중복 제거(네트워크 없음)."""
from __future__ import annotations

import json

import pandas as pd
import pytest

pytest.importorskip("scrapling")
from scrapling.parser import Selector  # noqa: E402

from src.pipeline.connectors import scrapling_connector as sc  # noqa: E402

POLICY = {"allow": {"farmdocdaily.illinois.edu": {"selector": [".entry-content"]}},
          "block": {"reuters.com": "약관"}}


def test_policy_file_loads_and_blocks_tos_domains() -> None:
    pol = sc.load_policy()
    assert sc._domain_rule("www.reuters.com", pol)[0] == "block"
    assert sc._domain_rule("www.investing.com", pol)[0] == "block"
    assert sc._domain_rule("farmdocdaily.illinois.edu", pol)[0] == "allow"
    assert sc._domain_rule("example.com", pol)[0] == "unknown"


def test_blocked_and_unknown_domains_never_fetched(monkeypatch) -> None:
    monkeypatch.setattr(sc, "_robots_ok", lambda url: pytest.fail("robots 조회 불필요"))
    assert sc.fetch_article("https://www.reuters.com/markets/x", POLICY) == ""
    assert sc.fetch_article("https://example.com/a", POLICY) == ""


def test_extract_text_prefers_rule_selector_and_skips_short_blocks() -> None:
    body = "Soybean oil futures rose as biodiesel demand firmed. " * 10
    page = Selector(f"<html><body><nav>menu</nav><article>short</article>"
                    f"<div class='entry-content'><p>{body}</p><script>x()</script></div></body></html>")
    text = sc.extract_text(page, [".entry-content", "article"])
    assert text.startswith("Soybean oil futures rose") and "x()" not in text and "menu" not in text
    assert sc.extract_text(page, ["article"]) == ""          # 200자 미만 = 추출 실패


def test_enrich_and_append_dedupes_by_url(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sc, "fetch_article", lambda url, pol: "본문 " * 100)
    items = [{"title": "Crush margins", "link": "https://farmdocdaily.illinois.edu/a",
              "date": pd.Timestamp("2026-10-20"), "_kw": "crush"}]
    recs = sc.enrich_items(items, "RSS_FARMDOC_DAILY", POLICY)
    assert recs[0]["published"] == "2026-10-20" and recs[0]["available_at"]
    assert sc.append_corpus(recs, tmp_path) == 1
    assert sc.append_corpus(recs, tmp_path) == 0
    (f,) = tmp_path.glob("*.jsonl")
    assert json.loads(f.read_text(encoding="utf-8").splitlines()[0])["indicator"] == "RSS_FARMDOC_DAILY"
