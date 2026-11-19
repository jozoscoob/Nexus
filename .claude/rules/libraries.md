# .claude/rules/libraries.md
> Load this file when working in any `src/` module or `notebooks/`.
> These are the **only** approved libraries. Do not introduce new dependencies without updating this file.
> All version constraints are minimum versions unless a specific pin is noted.

---

## Python — Approved Libraries

```
# Data & Numerics
pandas >= 2.0           # tabular data
numpy >= 1.26           # numerical operations

# Machine Learning
scikit-learn >= 1.4     # classical ML, preprocessing, TimeSeriesSplit
xgboost >= 2.0          # G1: XGBoost variable importance
shap >= 0.44            # G1: SHAP explainability (required alongside xgboost)
lightgbm >= 4.0         # gradient boosting alternative

# Statistical / Econometric Time Series
statsmodels >= 0.14     # ARIMA, SARIMA, SARIMAX, VAR, Granger causality
arch >= 6.0             # G2: GARCH / EGARCH volatility modeling (Python-native)
prophet >= 1.1          # seasonal time series (⚠ pin pystan==3.9.0 — see MEMORY L-001)

# Deep Learning
torch >= 2.0            # LSTM, TFT (⚠ specify CUDA version — see MEMORY L-003)
pytorch-forecasting >= 1.0  # G2/G3: Temporal Fusion Transformer (TFT)

# NLP / Sentiment (G2 qualitative layer)
transformers >= 4.38    # G2: FinBERT sentiment scoring
sentence-transformers >= 2.5  # embedding-based document similarity

# Signal Processing
# ⚠️ vmdpy — 2026-08-12 기본 구성에서 제외. 전체 시계열 일괄 분해는 미래 정보 누수를 일으킴.
#    사용 시 각 fold 학습 창 내 one-sided/rolling 재적합 필수 (modeling.md G2 참조).
PyWavelets >= 1.5      # W0 Stage 2: Wavelet Coherence 유지류 동조화 보조 분석(DQ-13 승인 2026-08-29).
                       # 용도 한정 — 사후 기술 분석 전용(예측 피처 파생 금지: VMD와 동일한 전체 계열
                       # 분해 누수 경로 차단, M-010 정합). Surrogate 검정은 사전 등록 1회만.

# Uncertainty Quantification
mapie >= 0.8            # G2: EnCQR(Ensemble Conformalized QR) 구간 보정 — 2026-08-12 용도 갱신

# Feature Mart / as-of Join (2026-08-12 신규)
duckdb >= 1.0           # ASOF JOIN 기반 시점 정합 feature view — 서버 불필요, parquet 직접 질의

# Challenger 딥러닝 (해당 실험 단계에서만 설치)
darts >= 0.30           # N-BEATSx · N-HiTS · TFT 통합 인터페이스
neuralforecast >= 1.7   # Nixtla 계열 (PatchTST 포함)

# 외부 저장소 클라이언트 (조정자 계정 발급 후 사용)
supabase >= 2.0         # 사건·근거 관계형 적재 (SUPABASE_URL / SUPABASE_SERVICE_KEY)
neo4j >= 5.0            # 지식그래프 투영 — validated 엣지만 (도입 시점: 조사 §5 게이트 이후)

# Optimization (G3 procurement optimizer)
pulp >= 2.7             # linear/mixed-integer programming
scipy >= 1.12           # scipy.optimize as fallback

# Multi-LLM Integration (src/utils/)
openai >= 1.30              # OpenAI API + Perplexity (OpenAI-compatible endpoint)
google-genai >= 2.0         # Gemini API (⚠ google-generativeai 지원 종료 — MEMORY L-010 참조)

# Model Tracking (로컬)
mlflow >= 2.10                      # model tracking and registration (use over pickle) — 로컬 추적 저장소

# PDF 판독·변환 (2026-09-09 등재 — A-251 references 규칙)
pymupdf >= 1.24         # PDF → Markdown 변환(scripts/pdf_to_markdown.py) · 요약 PDF 판독(FAO/GAIN 요약기와 병행)
pdfplumber >= 0.11      # 표 추출 · GAIN/FAO 텍스트 판독(1차)
pypdf >= 4.0            # 판독 폴백

# Data Validation
great-expectations >= 0.18  # schema and quality checks on pipeline inputs

# Visualization
plotly >= 5.0           # interactive charts (export as HTML or PNG)
```

## R — Approved Libraries

```r
tidyverse            # data wrangling + ggplot2 visualization
forecast             # ARIMA, ETS, TBATS
tseries              # ADF/KPSS unit root tests, GARCH
vars                 # Vector Autoregression (VAR)
rugarch              # GARCH family models (primary for G2 volatility)
DBI + duckdb         # parquet 질의(DuckDB)
pointblank           # data quality checks (R equivalent of great_expectations)
```

## Hard Constraints — Forbidden Patterns

| Pattern | Reason | Use Instead |
|---|---|---|
| `pickle` | Insecure, version-fragile | `joblib.dump()` or `mlflow.log_model()` |
| `openpyxl` / Excel I/O | Bypasses parquet as source of truth | parquet 읽기·쓰기 + DuckDB 질의 |
| `os.system()` / `subprocess` for data | Security policy violation | SDK connectors only |
| `random_state` shuffle on time series | Causes data leakage (see MEMORY M-001) | `sklearn.model_selection.TimeSeriesSplit` |
