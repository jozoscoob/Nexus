# 데이터 갱신 주기 및 보존 기간 분류표

**작성일**: 2026-06-17  
**작성자**: C-01 Senior PM (C-04 Document Intelligence 검토)  
**근거**: CLAUDE.md §1 Correction 1 — C-02/C-04 데이터를 일별/비일별로 분류하고 보존 기간 설정

---

## 1. 일별(Daily) 갱신 데이터

> 거래일(월~금) 기준 매일 수집. GitHub Actions cron: `"30 20 * * 0-4"` (KST 05:30 평일)

| 커넥터 | 데이터 소스 | 지표 코드 | 갱신 주기 | 보존 기간 |
|---|---|---|---|---|
| `commodity_connector.py` | CBOT BO=F (yfinance) | `CBOT_SBO_FUTURES` | 일별 (10일 lookback) | 7일 (artifact) / 영구 (DW) |
| `commodity_connector.py` | FRED CPO 프록시 | `CPO_PRICE_USD` | 일별 | 7일 / 영구 |
| `commodity_connector.py` | BCRA ARS/USD | `FX_ARS_USD` | 일별 | 7일 / 영구 |
| `economic_connector.py` | FRED (Fed 금리, VIX) | `US_FEDFUNDS`, `VIX` | 일별 (영업일) | 7일 / 영구 |
| `economic_connector.py` | FRED (CPI, 환율) | `US_CPI`, `FX_BRL_USD`, `FX_CNY_USD` | 일별 | 7일 / 영구 |
| `economic_connector.py` | BOK ECOS (원/달러) | `FX_KRW_USD` | 일별 (영업일) | 7일 / 영구 |
| `shipping_connector.py` | BDI (Trading Economics/stooq) | `BDI` | 일별 (영업일) | 7일 / 영구 |
| `shipping_connector.py` | BCAA 탱커 운임 | `BCAA`, `BCTI` | 일별 (영업일) | 7일 / 영구 |
| `geointel_connector.py` | USGS 지진 (M≥2.5) | `GEOINTEL_RISK_COMPOSITE` | 일별 (실시간 전용) | 7일 / 영구 |
| `geointel_connector.py` | NOAA 기상 경보 | `GEOINTEL_RISK_COMPOSITE` | 일별 (실시간 전용) | 7일 / 영구 |
| `geointel_connector.py` | GDELT 이벤트 | `GEOINTEL_RISK_COMPOSITE` | 일별 (실시간 전용) | 7일 / 영구 |
| `geointel_connector.py` | NASA FIRMS 산불 | `GEOINTEL_RISK_COMPOSITE` | 일별 (실시간 전용) | 7일 / 영구 |
| `ais_connector.py` | AISstream.io (호르무즈/말라카/파나마) | `SBO_STRAIT_RISK_COMPOSITE` | 일별 (실시간 전용) | 7일 / 영구 |
| `production_connector.py` | NASA POWER (농업기상) | `AGROMET_*` | 일별 | 7일 / 영구 |
| `climate_connector.py` | Open-Meteo ERA5-Land (12개 지역) | `WEATHER_*` | 일별 | 7일 / 영구 |
| `climate_connector.py` | OpenWeatherMap | `OWM_*` | 일별 | 7일 / 영구 |

> **주의**: `geointel_connector.py`와 `ais_connector.py`는 `BACKFILL_MODE=true`일 때 완전히 건너뜀.  
> 과거 데이터 복원 불가 — 실시간 전용.

---

## 2. 주별(Weekly) 갱신 데이터

| 커넥터 | 데이터 소스 | 지표 코드 | 갱신 주기 | 보존 기간 |
|---|---|---|---|---|
| `commodity_connector.py` | USDM 가뭄 모니터 | `DROUGHT_INDEX` | 매주 목요일 발표 | 7일 / 영구 |

---

## 3. 월별(Monthly) 갱신 데이터

| 커넥터 / 출처 | 데이터 소스 | 지표 코드 | 발표 시점 | 보존 기간 |
|---|---|---|---|---|
| `wasde_connector.py` | USDA FAS PSD (마케팅연도 기준) | `WASDE_SBO_*`, `WASDE_SOY_*` | 매월 WASDE 발표일 | 7일 / 영구 |
| `gpr_connector.py` | Caldara & Iacoviello GPR 지수 | `GPR` | 매월 말 업데이트 | 7일 / 영구 |
| `gpr_connector.py` | Perplexity 정책 뉴스 프록시 | `ARG_EXPORT_TAX_NEWS`, `BIODIESEL_MANDATE_NEWS` 등 | 일별 (BACKFILL 시 건너뜀) | 7일 |
| `climate_connector.py` | NOAA CPC ONI (ENSO 지수) | `ENSO_ONI` | 매월 업데이트 | 7일 / 영구 |
| `economic_connector.py` | KOSIS (한국 CPI) | `KR_CPI` | 매월 | 7일 / 영구 |
| `scripts/ingest_wasde_xlsx.py` (신규) | USDA FAS WASDE Excel 업로드 | `WASDE_*` (월별 시트) | 수동 업로드 (월별 WASDE 이후) | 영구 (DW) |
| `scripts/ingest_psd_data.py` (신규) | USDA FAS PS&D Excel (`Oil, Soybean`) | `PSD_SBO_*` | 연 1회 + 분기 개정 | 영구 |
| `scripts/ingest_gats_data.py` (신규) | USDA GATS 수출 통계 (HS 1507) | `GATS_US_EXPORT_*` | 월별 (당해연도), 연별 (과거) | 영구 |
| C-04 → PDF 추출 | FAO AMIS Market Monitor (PDF) | `FAO_AMIS_*` | 매월 (Jan/Aug 제외) | 영구 |
| C-04 → PDF 추출 | USDA FAS GAIN 보고서 (PDF) | 텍스트 → FinBERT | 비정기 (사건 기반) | 영구 |

---

## 4. 연별(Annual) 갱신 데이터

| 커넥터 | 데이터 소스 | 지표 코드 | 갱신 주기 | 보존 기간 |
|---|---|---|---|---|
| `production_connector.py` | USDA NASS (미국 주별 대두 생산) | `NASS_US_SOY_*` | 연 1회 (마케팅연도 10월 기준) | 영구 |
| `production_connector.py` | FAOSTAT (국가별 대두유 생산) | `FAOSTAT_SBO_*` | 연 1회 | 영구 |
| `production_connector.py` | 아르헨티나 INDEC | `ARG_SOY_PRODUCTION` | 연 1회 | 영구 |
| `customs_connector.py` | 한국 관세청 (HS 1507, data.go.kr) | `KR_CUSTOMS_SBO_*` | 월별 누적 → 확정치 연별 | 영구 |
| `scripts/ingest_psd_data.py` | USDA FAS PS&D `Oilseed, Soybean.xlsx` | `PSD_SOY_*` | 연 1회 + 분기 개정 | 영구 |

---

## 5. BACKFILL_MODE 동작 요약

| 커넥터 | BACKFILL_MODE=true 동작 |
|---|---|
| `geointel_connector.py` | **완전 건너뜀** — 실시간 전용 |
| `ais_connector.py` | **완전 건너뜀** — 실시간 전용 |
| `gpr_connector.py` | GPR 역사 데이터 수집 (XLSX), Perplexity 프록시 건너뜀 |
| `shipping_connector.py` | BDI/BCAA 과거 데이터 수집 |
| `wasde_connector.py` | 2020~현재 PSD 마케팅연도 전체 수집 |
| `climate_connector.py` | ERA5 과거 재분석 데이터 수집 (2020-01-01~) |
| `commodity_connector.py` | CBOT 10일 lookback (backfill 미지원, 단기만) |

---

## 6. GitHub Actions 수집 스케줄

```yaml
# .github/workflows/external_data_refresh.yml
cron: "30 20 * * 0-4"   # UTC 20:30 = KST 05:30 (평일)
```

| 잡(Job) | 커넥터 | 수집 조건 |
|---|---|---|
| `economic` | economic_connector.py | 항상 실행 |
| `shipping` | shipping_connector.py | 항상 실행 |
| `commodity` | commodity_connector.py | 항상 실행 |
| `climate` | climate_connector.py | 항상 실행 |
| `wasde` | wasde_connector.py | 항상 실행 |
| `production` | production_connector.py | 항상 실행 |
| `customs` | customs_connector.py | 항상 실행 |
| `gpr` | gpr_connector.py | 항상 실행 |
| `ais` | ais_connector.py | `BACKFILL_MODE != true` 시 실행 |
| `geointel` | geointel_connector.py | `BACKFILL_MODE != true` 시 실행 |
| `gpr-sbo-correlation` | gpr_sbo_correlation.py | economic, gpr 완료 후 |

---

## 7. 수동 수집 데이터 (GitHub Actions 미포함)

아래 데이터는 파일 업로드 또는 스크립트 수동 실행 방식으로 수집:

| 데이터 | 수집 방식 | 담당 에이전트 | WBS |
|---|---|---|---|
| USDA FAS WASDE Excel (`17년~26년`) | 수동 파일 업로드 → `scripts/ingest_wasde_xlsx.py` | C-04 | 1.1.41 |
| USDA FAS PS&D Excel (Oil/Oilseed) | 수동 파일 업로드 → `scripts/ingest_psd_data.py` | C-04 | 1.1.41 |
| USDA GATS 수출 통계 Excel | 수동 파일 업로드 → `scripts/ingest_gats_data.py` | C-04 | 1.1.42 |
| FAO AMIS Market Monitor PDF (~94개) | LLM 기반 추출 → `scripts/ingest_fao_amis_pdf.py` | C-04 | 1.1.41 |
| USDA FAS GAIN 보고서 PDF | C-04 pdfplumber 추출 → FinBERT (P1-05) | C-04 + P1-05 | 1.1.40 |

---

*Project Nexus · 데이터 갱신 주기 분류 · C-01 PM · 2026-06-17*
