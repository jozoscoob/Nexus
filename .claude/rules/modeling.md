# .claude/rules/modeling.md
> Load this file when working in `src/forecasting/`, `src/risk/`, or any modeling notebook.
> All method selections marked `[M]` are subject to change. Do not treat them as committed architecture.
> Always reference README.md §QR for goal IDs (G1/G2/G3) before reading this file.

---

## Data Constraint — External-Only (Applies to G1/G2/G3)
> **MEMORY D-021 (supersedes D-006)**: 내부 S&OP/ERP 데이터는 **가용량 부족 + 더미 비중 과다**로
> **분석에 사용하지 않는다**. 기존 "Phase A 외부전용 → Phase B 내부검증" 이원 설계에서 내부 데이터
> 축을 **전면 제거**함. 모든 G1/G2/G3 모델링은 **외부 파이프라인 데이터 전용**이며, 내부 데이터를
> 학습·검증·피처 어디에도 투입하지 않는다.
> (구 D-006: "Phase A 외부전용 / Phase B 내부검증" — 더 이상 유효하지 않음.)

---

## G1 — Variable Importance & Risk Alert System

**Objective**: Identify which macro/micro factors most drive soybean oil price movements.
**+ 유사국면 참조(D-051)**: 변수 상태가 현재와 유사했던 과거 연도들의 이후 실측 분포를
참조로 제공한다(`src/forecasting/analogue_g1.py` — 과거 관측 요약까지만, A-191).

### Method Stack (2026-08-12 조사 패키지 반영)
| Step | Method | Library | Output |
|---|---|---|---|
| Feature selection | **Elastic Net** (안정성 선택) | `scikit-learn` | 공선성 제어된 변수 집합 |
| Importance ranking | LightGBM/XGBoost + SHAP | `lightgbm`·`xgboost`·`shap` | 기여도 순위 |
| Importance (교차검증) | Permutation importance | `scikit-learn` | SHAP 삼각검증 |
| Lead-lag | Granger (Bonferroni α/m) | `statsmodels` | 시차·p값 |
| 충격 반응 | **국소투영(Local Projections)** | `statsmodels` | 시차별 반응 크기·지속기간 |
| Event signals | P1-05 ABSA (evidence 필수) | — | 게이트 통과 사건만 피처화 |

> LASSO 단독은 다중공선성 하에서 동행 변수 중 하나만 남겨 중요도를 불안정하게 만든다(M-005).
> **Elastic Net + 트리 모델 양쪽에서 반복 선택된 변수만 핵심 동인으로 승격**한다.

### 중요도 산출 단위
전체 기간 하나가 아니라 **horizon(1·5·20·60일) × 레짐(Bear/Neutral/Bull) × 원산지별**로 산출한다.

### Alert Trigger Logic
- Define threshold per variable (e.g., BDI > 2σ from 90-day rolling mean → alert)
- Alert output: Korean-language message + variable name + current vs. threshold value
- Alerts must be explainable: include top-3 SHAP contributors for each triggered alert

---

## G2 — Price Band Forecasting (Futures Price Volatility)

**Objective**: horizon별 **확률 가격밴드** 산출.
**Output contract**: P10/P25/P50/P75/P90 · 50/80/95% 구간 · 상승확률 · 임계가격 초과확률 ·
레짐별 empirical coverage. (구 "상단/점추정/하단/신뢰수준" 4종은 분위수 계약으로 대체)

> **데이터 제약**: 상단 §Data Constraint(**D-021**) 참조 — 내부 데이터는 사후 검증에도
> 사용하지 않는다. 구 D-006의 "Phase B 내부검증" 단서는 폐기됨.

> **Compute Environment**: **컴퓨트 중립 계약**. 학습 스크립트는 로컬 parquet 경로 입력의 순수 CLI이며
> 실행 표면을 가정하지 않는다. 산출은 모델 아티팩트 + `metrics.json` + 매니페스트(입력 스냅샷 SHA256·git SHA·
> lockfile 해시 — 3중 동결). 추적은 로컬 `mlflow`. 운영 학습 표면은 개인 노트북 Docker(n8n → runner 컨테이너),
> 상시 실행이 필요하면 Oracle Cloud Free Tier 서버를 보조로 쓴다. 재현 조건: "동일 스냅샷에서 다른 표면 재실행 시
> 지표 차 <0.5%". GPU가 필요한 Challenger는 GPU 표면을 확보할 때까지 **동결('미평가', 기각 아님)**.

### Data Sources (External Only — Phase A)
| Category | Source | Connector | Indicator |
|---|---|---|---|
| CBOT Futures | CME session/official settlement canonical series | canonical target pipeline | `CBOT_BO_CLOSE` |
| Geopolitical | Caldara GPR + Perplexity | `gpr_connector.py` | `GPR`, `HORMUZ_THREAT_LEVEL` |
| AIS Strait Risk | AISstream.io | `ais_connector.py` | `SBO_STRAIT_RISK_COMPOSITE` |
| GeoIntel | USGS/NOAA/GDELT/FIRMS | `geointel_connector.py` | `GEOINTEL_RISK_COMPOSITE` |
| Shipping | TE BDI REST / stooq | `shipping_connector.py` | `BDI` |
| FX | FRED DEXBZUS/DEXCHUS | `economic_connector.py` | `FX_BRL_USD`, `FX_CNY_USD` |
| ENSO/Climate | NOAA CPC ONI | `climate_connector.py` | `ENSO_ONI` |
| Crop Supply | USDA FAS PSD | `wasde_connector.py` | `WASDE_SBO_PRODUCTION` |

### Method Stack — Champion (2026-08-12 조사 패키지 반영)
| Step | Method | Library | Notes |
|---|---|---|---|
| 평균 경로 | SARIMAX / Dynamic Regression | `statsmodels` | 외생변수 효과, 소표본에 강함 |
| 비선형 분위수 | Quantile LightGBM | `lightgbm` | P10/P25/P50/P75/P90 직접 예측 |
| 변동성 | EGARCH-X | `arch` (Python), `rugarch` (R) | 변동성 군집·비대칭·꼬리 |
| 구간 보정 | **EnCQR** (Ensemble Conformalized QR) | `mapie` | 분포 무가정, 레짐별 coverage 보고 |
| 사건 신호 | P1-05 ABSA + evidence 게이트 | — | 게이트 통과분만 외생 입력 |

### Challenger (동일 fold에서 비교 후 승격)
GRU/LSTM (`torch`) · N-BEATSx/N-HiTS · TFT (`pytorch-forecasting`) · PatchTST · Chronos.
승격 조건은 `.claude/agents/c03-data-scientist.md` §4를 따른다.
**검토 대기(사전 평가 필요 — 2026-08-29 등재, A-213·A-224 이행)**:
MTGPR(Bayesian Multi-Task GPR — posterior 구간 내장이 G2 분위 계약과 정합하나
O(n³)·중국 도매지수 검증 한계, IEEE 2025 `references/`) ·
GAS-t(관측 구동 변동성 — Python 구현 부재로 구현 비용 유의, Mathematics 2025).
둘 다 §4 게이트 통과 전 후보 지위조차 아님 — 사전 평가 카드 작성이 선행 조건.

> ⚠️ **VMD/EMD 분해는 기본 구성에서 제외**(2026-08-12 결정). 전체 시계열을 한 번에 분해하면
> 미래 정보가 과거 fold로 유입된다. 사용 시 각 fold 학습 창 안에서 one-sided/rolling로만
> 재적합해야 한다. 구 `vmdpy` 전처리 단계는 이 근거로 폐기.

### 예측 지평 (직접 예측)
**1 · 5 · 20 · 60 거래일**. 60일을 약 3개월 조달 의사결정 지평으로 사용한다.
재귀 예측은 보조 실험으로만 둔다.

### 타깃 라벨·연속 계열 규칙 (2026-11-19 승인 — R-046)
- **라벨은 같은 계약 안에서만 계산한다.** h=20/60 수익률이 롤을 걸치면 계약 간 스프레드(구곡·신곡 등)가
  라벨에 섞인다. 같은 계약 수익률을 연결하거나 비율 조정하고, 롤을 걸친 구간은 coverage를 별도 보고한다
  (구·신곡 계약은 서로 다른 실물 공급에 묶여 따로 가격이 매겨짐 — Cortazar 외 2025 p.2·p.8).
- **크러시·oilshare 피처는 타깃과 같은 원천·같은 근월 규칙·같은 롤 달력으로 만든다**(Databento 정산가).
  Yahoo 근월(ZM=F·ZS=F)은 탐색용으로만 쓴다 — 원천을 섞으면 as-of·롤 불일치가 생긴다.
- 크러시 마진은 인도월을 맞춘 조합(예: ZSX·ZMZ·ZLZ)으로 계산하고 가공비는 **대두 톤당**으로 차감한다
  (기름 톤당 환산 금지 — 헥산 공정 약 EUR 30/t 대두, Cravotto 외 2023 p.30 시뮬레이션 인용).

### Training Workflow (로컬 Docker)
```
1. strict gates → `data/gold/feature_mart.parquet` + contract   (n8n '마트·게이트' 노드)
2. 입력 스냅샷 매니페스트(SHA256·git SHA) → data/snapshots/{snapshot_id}/manifest.json
   (scripts/build_snapshot_manifest.py · 덮어쓰기 금지)
3. 배치 잡(runner 컨테이너) → src/forecasting/price_band_g2.py (순수 CLI)
4. 로컬 mlflow 추적 — autolog 우선
5. mlflow.log_model() → 로컬 모델 레지스트리 (never pickle)
6. 등록 모델 → 일별 추론 배치 → P10~P90 산출(parquet·브리프)
```

### Validation Protocol
1. Walk-forward(expanding 또는 sliding) 전용 — random split 금지(M-001)
2. 지표: 점(MAE·RMSE·sMAPE·MASE) · 방향(accuracy·MCC·Brier) ·
   확률구간(pinball·CRPS·empirical coverage·interval width·calibration error)
3. **Baseline 필수**: last value · seasonal naive · ETS. 이를 못 이기면 승격 없음
4. `model × metric × horizon × 레짐 × stress slice` 표로 보고 — 평균 단일 점수 금지
5. **표본 요건**: 고정 "24개월"은 통계 모델 fallback 기준일 뿐 딥러닝의 충분조건이 아니다
   (2026-08-12 개정). 복잡 모델은 유효 시계열 길이·독립 충격 수·피처 대비 표본 수·
   레짐별 사례 수로 판단한다(구 M-004 단독 기준 폐기)
6. G2 gate: 8개 외부 소스 C-08 DQSOps PASS + `available_at` 100% 존재
6-1. **정책 시점 지터 검정**(R-046): 정책 더미·유사국면 창의 시작일을 공포일 기준 ±창(일별 모형은 horizon에
   맞춘 ±k거래일, 월별은 ±6개월)에서 무작위 100회 이동해 계수·순위 안정성을 확인한다(Schaefer 외 2022 p.13).
   저장은 published_at/effective_from 분리(D-023)를 따른다.
7. **Stress slice 별도 보고**: 2012 가뭄 · 2018 미중 · 2020 팬데믹 · 2021-Q2(재생디젤 수요로 팜유와 탈동조) ·
   2022 러우 · 2022-Q2~Q3(인니 팜유 수출금지) · 2025 · 2026(미완결 → shadow slice)(R-046, Fousekis 2024 p.5). 사건 구간을 이상치로 제거하지 않는다.
   레짐별 coverage 분리 보고의 학술 근거: Heliyon 2024 Quantile VAR — 유지류 가격
   전이가 극단 분위수(0.1/0.9)에서 91%/87%로 동조화(꼬리 ≠ 중위, `references/`)
8. 최신 완전 기간은 **lockbox test**로 보존한다
9. **비교 불가 이력 결합 금지**(R-046): IMF 월간 유지 가격·Decatur/FOB 현물 등 장기 이력은 ZL 정산가와
   NOT COMPARABLE이다 — G1 유사국면 보강에만 쓰고 G2 학습 표본에는 결합하지 않는다.

---

## G3 — Bear/Bull/Hold Regime Signal

**Objective**: Classify current market regime and translate into Buy / Hold procurement recommendation.
**+ 3-시뮬레이션(D-051)**: ①현시점 구매 ②사전 그리드 대안 시점 ③분할 구매의 근사 손익
(per-MT regret — D-021). G2 분위수 모델 전에는 과거 실측 백테스트 서술까지만(A-191).
설계 정본은 **Annals of OR 2026 VoI**(Merzifonluoglu — 선도+옵션+현물 3채널 위험회피
포트폴리오·정보 가치, `references/` · A-230): CVaR를 P&L simulation 보고 지표 후보로
병기하고, 옵션형 계약은 §3c contract_type 확장 후보로 둔다(현행 spot|term — W2 P1).
**Output contract**: Regime label (Bear/Bull/Neutral) · Confidence · P&L impact estimate · Recommended action

### Method Stack `[M]`
| Step | Method | Library | Notes |
|---|---|---|---|
| Regime detection | Markov Regime Switching | `statsmodels` | 2–3 state hidden Markov model |
| Seasonal exogenous | SARIMAX | `statsmodels` | Integrates macro covariates (FX, BDI, ENSO) |
| Multi-horizon regime | TFT | `pytorch-forecasting` | 3-month forward regime probability |
| P&L simulation | Monte Carlo (10,000 runs) | `numpy`, `scipy` | Distribution of outcomes per Buy/Hold |
| Scenario encoding | ENSO phase dummy + geopolitical index | Manual + `transformers` | Encodes climate + geopolitical shock inputs |

### 원산지·품질 시나리오 prior (2026-11-19 승인 — R-046)
- 브라질산 대비 미국산 조유 품질 격차는 **시간 불변 원산지 할인**(시나리오 상수)으로 둔다 — 원산지 더미만으로
  FFA 조정 R² 0.888, 성분·상호작용 포함 0.900(Flores 외 2026 표4·표7). 기상→품질 동적 경로는 보조 가설.
- 품질조정 CFR 스프레드는 점추정 대신 **범위**로 쓴다(브라질 NOL 0.71–2.43%, 표3) — 관세청 원산지별 CIF 잔차로
  먼저 검증한 뒤 경보 보정에 반영한다.

### Human-in-the-Loop Gate (Mandatory)
- G3 output always passes through CLAUDE.md §6 HITL protocol before being surfaced as a recommendation
- Never output a Buy/Hold signal without the P&L impact estimate and confidence range
- If Monte Carlo variance > 20%, flag output as HIGH UNCERTAINTY and escalate to human review

---

## Cross-Goal Rules

### as-of 시점 정합성 (2026-08-12 신설 — 최우선 제약)
```text
모델의 t일 입력값 = available_at ≤ t 를 만족하는 가장 최근 값
```
- 모든 피처에 `event_time` · `period_end` · `release_time` · `available_at` ·
  `source_vintage` · `ingested_at`을 분리 저장한다. 하나라도 없으면 **모델 투입 금지**.
- WASDE는 대상월이 아니라 **실제 발표일 이후**에만 사용한다. PSD 연간값도 공개·개정일 기준.
- 정책은 **발표일과 시행일을 분리**한다.
- 월·연간 자료의 일별 변환은 기간초 forward-fill이 아니라 **발표일 이후 as-of fill**.
- 개정값은 덮어쓰지 않고 **vintage별로 적재**한다(관세청·USDA 공통).
- G1/G2 목표가격은 `target_eligible=true`와
  `time_basis ∈ {CME_SESSION, EXCHANGE_SETTLEMENT}`를 모두 요구한다.
- UTC 날짜 기준 OHLCV(`CBOT_BO_UTC_*`)는 진단 피처이며 목표가격으로 사용할 수 없다.

### Time Series Non-Negotiables
- **Never** shuffle or randomly split time series data. Use `TimeSeriesSplit` (sklearn).
- 모든 전처리(scaling·imputation·변수선택·분해·calibration)는 **fold 내부에서 재적합**한다.
- **IQR 캡핑은 데이터 오류와 정상 노이즈에만** 적용한다(2026-08-12 개정).
  2020·2022 같은 검증된 시장 충격을 일괄 캡핑하면 G2/G3가 가장 중요한 꼬리위험을 학습하지
  못한다. 원본·robust 변환·캡핑 버전을 모두 실험하고 **사건 검증 결과로 선택**한다.
  (구 규칙 "ARIMA/GARCH 적합 전 항상 IQR 캡핑"은 이 근거로 폐기 — M-003, D6와 정합)
- FX rate: use T+2 settlement convention. Document date offset in all pipeline schemas (see MEMORY M-002).
- Log-transform soybean oil prices before fitting unless the model explicitly handles non-stationarity.

### Model Serialization
- Save all trained models with `mlflow.log_model()` or `joblib.dump()`. Never use `pickle`.
- Register model version in the local mlflow model registry after each production-quality fit.

### Interpretability Requirement
- All G1/G2/G3 outputs must include a human-readable explanation alongside the numerical result.
- G1: SHAP plot + top-5 variable narrative.
- G2: "Price expected between X–Y because of [top 2 drivers]" in Korean.
- G3: Regime label + one-sentence Korean rationale + P&L range.
