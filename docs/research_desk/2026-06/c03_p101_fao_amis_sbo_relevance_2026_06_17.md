# FAO AMIS Market Monitor — SBO 관련성 분석 및 파이프라인 통합 계획
**작성일**: 2026-06-17  
**참여**: C-03 · P1-01 · P1-02 · P1-03 · P1-04  
**자료**: `data/raw/FAO/AMIS/` — 93개 PDF (17년 10월~26년 5월)  
**결정 ID**: D-016 (FAO AMIS 통합 우선순위), D-017 (파이프라인 통합 방식)

---

## 1. FAO AMIS Market Monitor 보고서 구조

**C-03 (데이터 소싱):**  
FAO AMIS Market Monitor는 국제연합 식량농업기구(FAO) 주관의 월간 농산물 시장 모니터링 보고서입니다. 매월 발간 (1월·8월 제외, 연 10회). 93개 파일 = 2017년 10월~2026년 5월.

### 1.1 보고서 페이지 구성

| 섹션 | 내용 | SBO 관련성 |
|---|---|---|
| Executive Summary | 핵심 시장 동향 요약 | 중 — 텍스트 기반 시그널 |
| Cereals S&D | 밀·옥수수·쌀 공급/수요 밸런스 | 낮음 |
| **Oilcrops S&D** | 대두 생산·소비·재고 | **높음 — 대두 압착량 = SBO 공급 선행** |
| **Vegetable Oils S&D** | 식물성유지 공급/수요/재고 (대두유 포함) | **최고** |
| **Price Monitor** | FAO Vegetable Oil Price Index | **최고 — 월별 가격 벤치마크** |
| Policy Notes | 주요국 수출입 정책 변경 | 높음 — 구조적 단절 트리거 |

### 1.2 연도별 파일 현황

| 연도 | 파일 수 | 비고 |
|---|---|---|
| 2017 | 9 | 10~12월 (가장 이른 3개월) |
| 2018~2025 | 각 10 | 2월~7월 + 9~12월 (1월·8월 제외) |
| 2026 | 4 | 2~5월 (최신 — 연간 발간 진행 중) |
| **합계** | **93** | |

---

## 2. SBO 관련 핵심 지표 식별

### 2.1 수량 지표 (Vegetable Oils S&D 섹션)

**P1-01 (대두유 시장 전문가):**  
Vegetable Oils 섹션은 팜유·대두유·유채유·해바라기유 집계 데이터를 제공합니다. SBO 단독 분리가 가능한 경우도 있고, 전체 식물성유지 합산만 제공하는 경우도 있습니다.

| 지표 | 코드 | 단위 | SBO 특정 가능 여부 |
|---|---|---|---|
| 전체 식물성유지 생산량 | `FAO_AMIS_VEGEOIL_PRODUCTION` | 100만 MT | 부분 — 품목별 분해 필요 |
| 전체 식물성유지 소비량 | `FAO_AMIS_VEGEOIL_CONSUMPTION` | 100만 MT | 부분 |
| 전체 식물성유지 기말재고 | `FAO_AMIS_VEGEOIL_STOCKS` | 100만 MT | 부분 |
| 재고사용비율 | `FAO_AMIS_VEGEOIL_STU` | % | 직접 제공 시 고우선 |
| 식물성유지 가격지수 | `FAO_VEGEOIL_PRICE_IDX` | 지수 (2014-16=100) | 복합 — SBO 비중 40%+ |

**P1-02 (거시경제):**  
FAO Food Price Index (FFPI)의 Vegetable Oils 하위 지수는 SBO·CPO·유채유·해바라기유의 국제 가격을 가중 집계합니다. SBO 비중이 가장 높아 (약 40%) 사실상 SBO 가격 프록시로 사용 가능합니다.

### 2.2 Oilcrops 섹션 (대두 원료)

| 지표 | 코드 | SBO 연결 |
|---|---|---|
| 전세계 대두 생산량 | `FAO_AMIS_SOY_PRODUCTION` | 압착 원료 공급 → SBO 공급 6~9개월 선행 |
| 전세계 대두 소비량 | `FAO_AMIS_SOY_CONSUMPTION` | 압착 수요 대리 지표 |
| 전세계 대두 기말재고 | `FAO_AMIS_SOY_STOCKS` | WASDE와 교차 검증용 |
| 대두 STU | `FAO_AMIS_SOY_STU` | 대두 시장 타이트니스 |

**P1-04 (물류):**  
대두 생산량 → 압착 일정 → SBO 공급 순서로 이어지는 인과 경로가 FAO AMIS에서 완전히 추적 가능합니다. PSD 연간 데이터와 달리 FAO AMIS는 월별로 갱신되므로 중요 선행 신호입니다.

### 2.3 정책 노트 (Policy Notes)

**P1-03 (지정학):**  
FAO AMIS는 매월 주요국 무역 정책 변경을 요약합니다. 인도 수입 관세, 인도네시아 수출 금지, EU 바이오디젤 정책 등 SBO 가격에 직접 영향을 주는 이벤트가 명시됩니다.  
→ NLP 키워드 감지 + 이벤트 dummy 변수 생성으로 활용 가능

---

## 3. 시계열 구성 방법

### 3.1 날짜 매핑 규칙

```
"17년 10월_Market Monitor Issue.pdf"
→ price_date = 2017-10-01 (발간 월 첫 날)
→ 실제 데이터 기준 마케팅연도는 보고서 내부에서 확인
```

누락 월 처리:
- 1월 (연간 데이터 미발간): 전월(12월) 데이터 forward fill
- 8월 (하계 휴간): 전월(7월) 데이터 forward fill
- 2017년 1월~9월: 데이터 없음 → 시계열 시작 = 2017-10-01

### 3.2 추출 가능 시계열 요약

| 기간 | 월수 | 가용 데이터 |
|---|---|---|
| 2017-10 ~ 2026-05 | 93개 | FAO AMIS 지표 전체 |
| 보간 후 (1월·8월) | 103개 | ffill limit=1 적용 |
| WASDE 교차 검증 | 2017~2026 | 중복 기간 |

---

## 4. C-03 결론 — 파이프라인 통합 계획 (D-016, D-017)

### D-016: FAO AMIS 통합 우선순위

**핵심 (즉시 추출 대상):**
1. `FAO_VEGEOIL_PRICE_IDX` — SBO 가격 월별 벤치마크. G2 캘리브레이션 기준점.
2. `FAO_AMIS_VEGEOIL_STU` — WASDE STU와 교차 검증용 독립 소스.
3. `FAO_AMIS_SOY_PRODUCTION` — 대두 생산량 월별 업데이트 (PSD 연간 보완).

**보조 (Phase B):**
4. `FAO_AMIS_VEGEOIL_PRODUCTION`, `_CONSUMPTION`, `_STOCKS`
5. Policy Notes → NLP 이벤트 dummy

### D-017: 파이프라인 통합 방식

**Historical Backfill 통합:**
- `scripts/ingest_fao_amis_pdf.py` 수동 실행 → `data/raw/fao_amis_historical.parquet`
- Parquet → DW 업로드 (클라우드 학습 환경 환경에서)
- `.github/workflows/historical_backfill.yml`: FAO AMIS 수집 단계 추가

**External Data Pipeline 통합 (Phase B):**
- 매월 FAO AMIS 신규 발간 → 자동 다운로드 → 추출 → DW 업데이트
- `.github/workflows/external_data_refresh.yml`: FAO AMIS 수집 단계 추가
- 다운로드 URL: `https://www.amis-outlook.org/market-monitor`

---

## 5. 데이터 활용 예시

### G1 (변수 중요도)
- `FAO_VEGEOIL_PRICE_IDX`를 CBOT SBO 가격의 독립 교차 검증 변수로 활용
- Granger 인과 검정: FAO 가격지수 → CBOT SBO 가격 (또는 역방향)

### G2 (가격밴드 예측)
- 월별 `FAO_VEGEOIL_PRICE_IDX` 수준을 SARIMAX 공변량으로 추가
- `FAO_AMIS_VEGEOIL_STU` 급변 시 G2 불확실성 확대 (예측 구간 확장)

### G3 (레짐 감지)
- `FAO_AMIS_SOY_PRODUCTION`의 분기 변화율 → Bear/Bull 레짐 전환 시그널
- Policy Notes 이벤트 dummy → 레짐 전환 외생 충격 변수

---

*→ `scripts/ingest_fao_amis_pdf.py` 생성 후 MEMORY.md D-016, D-017 추가 예정*
