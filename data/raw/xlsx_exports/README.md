# xlsx_exports — 수집 데이터 열람 사본 (자동 생성)

> `scripts/export_parquet_to_xlsx.py`가 `data/raw/**/*.parquet`를 .xlsx로 변환·보관하는 폴더.
> 등록 API 데이터 + Perplexity 수집 데이터 + 수동 히스토리를 비개발 이해관계자가 열람 가능하게 함.

## 구조
```
xlsx_exports/
├── historical/   # 백필·수동 히스토리 (te_commodities·ice_monthly·gain·fao_amis·*_historical)
└── realtime/     # 일별 실시간 커넥터 산출물 (economic·shipping·climate·gpr·commodity 등)
```

## 규칙
- **자동 생성물**: 파이프라인(Historical Backfill / Daily Refresh)에서 갱신. 수동 편집 금지.
- **분석 소스 아님**: 분석 파이프라인의 단일 소스는 parquet (CLAUDE.md §2).
  이 xlsx는 감사·열람용 사본일 뿐임.
- indicator_code ≤10종이면 지표별 시트 분리, 그 외 단일 `data` 시트.
- tz-aware `ingested_at`은 엑셀 호환 위해 tz 제거 후 기록.

## 생성 방법
```bash
python scripts/export_parquet_to_xlsx.py   # data/raw/**/*.parquet → xlsx_exports/{historical,realtime}/
```
