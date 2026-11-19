# MEMORY.md — Project Nexus
> **Agent auto-memory file.** Append new entries after each resolved blocker or completed session.
> Never overwrite existing entries. Read this file at session start (CLAUDE.md §BOOT step 2).
> Format: `[YYYY-MM-DD] [ID] Category | Issue | Fix`

---

## Failure Patterns — Pre-Populated

> These are known pitfalls pre-loaded from project inception. Add new entries below the last entry.

### Library Incompatibilities
| ID | Issue | Fix |
|---|---|---|
| L-001 | `prophet` requires `pystan >= 3.0` — conflicts with older Python environments | Pin: `prophet==1.1.5`, `pystan==3.9.0` |
| L-003 | `torch` GPU version mismatch on GPU hosts | Specify CUDA version in `requirements.txt`: `torch==2.1.0+cu118` |

### API & Connection Issues
| ID | Issue | Fix |
|---|---|---|
| A-003 | Perplexity API intermittent 429 (rate limit) | Exponential backoff: 2s → 4s → 8s → 16s; max 4 retries |

### Modeling & Data Pitfalls
| ID | Issue | Fix |
|---|---|---|
| M-001 | Time series train/test split ignoring time order → data leakage | Always use `TimeSeriesSplit`; never shuffle time series data |
| M-002 | FX rate applied to wrong date (T vs T+1 settlement) | Use T+2 settlement convention; document in data dictionary |
| M-003 | Outlier soybean oil prices (market spike days) distort ARIMA fit | IQR-based outlier capping before fitting; log-transform prices |
| M-004 | Seasonal decomposition on monthly data with < 24 months fails | Require minimum 24 months; fall back to ETS if insufficient |

### Architecture & Code Structure
| ID | Issue | Fix |
|---|---|---|
| C-001 | Circular imports when refactoring `src/` modules | Keep `utils.py` dependency-free; import direction: `utils → models → pipelines` |
| C-002 | Notebook outputs bloat GitHub repo (embedded images) | Use `nbstripout` as pre-commit hook; keep outputs out of the repo (local artifacts folder) |

### LLM-Specific Pitfalls
| ID | Issue | Fix |
|---|---|---|
| LLM-001 | Claude hallucinates column names not in schema | Always paste schema header (first 3 rows or `df.dtypes`) in prompt |
| LLM-002 | Long analysis prompts lose context mid-response | Break into sub-tasks; use README.md §QR as persistent anchor |
| LLM-003 | Different LLMs return inconsistent output formats | Specify exact format in prompt: "respond only with a markdown table with columns: X, Y, Z" |

---

## Session Learnings — Append New Entries Here

<!-- FORMAT: | [YYYY-MM-DD] | [ID] | Category | Issue encountered | Resolution | -->

> **월별 아카이브 운영(조정자 지시)**: 모든 월간 학습은 `docs/memory_archive/YYYY-MM.md`에 기록.
> 갱신 시 **당월 파일**에 추가한다. 과거 상세는 온디맨드 로드:
> @docs/memory_archive/2026-04.md · @docs/memory_archive/2026-05.md · @docs/memory_archive/2026-06.md · @docs/memory_archive/2026-07.md · 2026-08.md · **2026-09.md(당월)**

