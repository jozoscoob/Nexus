# .claude/rules/data_pipeline.md
> Load this file when working in `src/pipeline/` or designing any data ingestion component.
> These rules govern all data access patterns for the Nexus project.
> 실행 환경: 개인 노트북 Docker(n8n → runner 컨테이너). 정본 저장소는 repo의 parquet, 질의는 DuckDB.

---

## DuckDB — SQL Conventions (parquet 직접 질의)

```sql
-- ✅ Correct: CTE-based, uppercase keywords, snake_case identifiers, LIMIT on exploratory
WITH monthly_prices AS (
    SELECT
        price_date,
        origin_country,
        cif_price_usd_per_mt,
        ROW_NUMBER() OVER (PARTITION BY origin_country ORDER BY price_date DESC) AS rn
    FROM read_parquet('data/raw/customs_*.parquet')
    WHERE price_date >= CURRENT_DATE - INTERVAL 10 YEAR
)
SELECT * FROM monthly_prices WHERE rn = 1 LIMIT 100;

-- ❌ Wrong: nested subqueries, no LIMIT, lowercase keywords
select * from (select * from read_parquet('data/raw/customs_*.parquet') order by price_date desc);
```

**Rules:**
- Always include `LIMIT` in exploratory queries
- CTEs over nested subqueries
- 시점 정합 조인은 `ASOF JOIN`(available_at ≤ t)을 쓴다 — 기간초 forward-fill 금지(D-023)
- 경로는 상수·환경변수(`NEXUS_DATA_ROOT`)로 둔다 — 절대경로 하드코딩 금지

## Python DuckDB Pattern

```python
from pathlib import Path

import duckdb
import pandas as pd

RAW_DIR = Path("data/raw")


def query_to_dataframe(sql: str) -> pd.DataFrame:
    """parquet 직접 질의 — 서버 불필요, 읽기 전용 연결."""
    try:
        with duckdb.connect(database=":memory:") as conn:
            return conn.execute(sql).df()
    except duckdb.Error as e:
        raise RuntimeError(f"[오류] DuckDB 질의 실패: {e}") from e
```

## External API — Retry Pattern

All external API calls (commodity price feeds, WASDE, BDI, ENSO, etc.) must implement exponential backoff.

```python
import time
import httpx
from typing import Any

def fetch_with_retry(url: str, max_retries: int = 4, **kwargs: Any) -> httpx.Response:
    """외부 API 호출 — 지수 백오프 재시도 포함."""
    delay = 2
    for attempt in range(max_retries):
        try:
            response = httpx.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"[오류] API 호출 실패 ({url}): {e}") from e
            time.sleep(delay)
            delay *= 2   # 2s → 4s → 8s → 16s
```

## Data Directory Rules

```
data/
├── raw/          # 수집 산출물. parquet·라이선스 데이터는 .gitignore로 커밋하지 않음
├── processed/    # Committed if schema-documented. Store as Parquet, not CSV.
├── gold/         # feature mart (재생성 산출물 — 계약 yaml·리포트만 추적)
├── snapshots/    # scripts/build_snapshot_manifest.py 가 쓰는 입력 스냅샷 매니페스트(SHA256)
└── schemas/      # YAML schema definitions for each processed dataset (column name, dtype, nullable, description)
```

- All `processed/` files must have a corresponding `schemas/` YAML entry before being committed
- Notebook outputs (charts, DataFrames) stay out of the repo — local artifacts folder only (see MEMORY C-002)

## Environment Variables — `.env.template`

키 이름은 저장소 루트 `.env.template`이 정본이다. 실제 값은 로컬 `.env`(gitignore)와 GitHub Secrets에만 둔다.
코드는 항상 `os.environ['KEY']`(또는 `.get`)로 읽는다 — 하드코딩 금지.
