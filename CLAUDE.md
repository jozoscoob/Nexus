# CLAUDE.md — Project Nexus
> Persistent operating rules. Loaded every session by Claude Code. **Hard limit: ≤ 120 lines.**
> Project context (goals, data, glossary, scope): → `README.md §QR`
> Module-specific rules: → `.claude/rules/*.md` (load only the file relevant to your task — see §4)

---

## §BOOT — Session Start Protocol
1. Read `README.md §QR` — confirm commodity scope (soybean oil only), goal IDs (G1/G2/G3), human gate.
2. Scan `MEMORY.md` — check for known pitfalls before starting any modeling or pipeline task.
3. Load the path-scoped rule file from §4 **only if** your task falls within that module's directory.
4. State the active task and the rule sections you are applying before writing any code.
5. If the task instruction is ambiguous: ask one focused clarifying question before executing.

---

## §1 PROJECT IDENTITY

| Field | Value |
|---|---|
| **Commodity** | Soybean oil (대두유) — crude + refined. Scope is fixed; do not extend without explicit instruction. |
| **Decision output** | Daily Buy / Hold procurement signal. AI recommends; human approves. Never execute autonomously. |
| **Goals** | G1: 동인 순위+**과거 유사국면 실측 참조** — 차별점: **대두유 시장·유통 구조를 통합해 실무에서 놓치기 쉬운 요인까지 정량 지표로 제시**(README §QR, 상시 원칙) · G2: 확률 가격밴드(P10/P50/P90) · G3: 레짐 확률+**3-시뮬레이션**(per-MT regret) — 정본: README §QR (2026-08-28 재정립) |
| **Horizons** | 1 · 5 · 20 · 60 거래일 직접 예측 (≈1일·1주·1개월·3개월). 60일 = 약 3개월 조달 의사결정 지평 |
| **Model policy** | 단일 거대 모델 확정 금지 — **Champion–Challenger 포트폴리오**. 승격은 사전 등록된 규칙으로만 (→ `docs/research_desk/2026-08/model_strategy_2026_08_12/`) |
| **Data scope** | 외부 파이프라인 데이터 **전용**(MEMORY **D-021**이 D-006을 대체 — 내부 S&OP/ERP는 학습·검증·피처·proxy 어디에도 투입 금지). G2 학습은 개인 노트북 Docker(로컬) |
| **as-of rule** | 모델의 t일 입력 = `available_at ≤ t`인 최근값. `available_at` 없는 피처는 투입 금지 |
| **Environment** | 개인 노트북(퇴사 후 개인 프로젝트 — 2026-11-16 승인자). Docker + n8n 로컬 실행. 사내 방화벽·DRM·클라우드 이관(Azure/AWS/Snowflake) 제약 해제. 저장소 용량 초과 시 원본은 Google Drive 보관 |

---

## §2 HARD CONSTRAINTS — Never Override

| Constraint | Rule |
|---|---|
| **Runtime** | 의존성은 Docker 이미지 안에서 버전 고정 설치(호스트 전역 설치 지양). 실행·스케줄은 n8n → 컨테이너 |
| **Human gate** | All Buy/Hold outputs require human approval. Use **Plan Mode** for any procurement-affecting analysis. |
| **Secrets** | Never commit credentials. Use GitHub Secrets + Azure Key Vault. Always reference `os.environ['KEY']`. |
| **Scope lock** | Do not extend to commodities other than soybean oil without explicit written instruction. |
| **Serialization** | Never use `pickle`. Use `joblib` (sklearn) or `mlflow.log_model()`. |
| **Data I/O** | Never use `openpyxl` or Excel for pipelines. 정본은 저장소 parquet + DuckDB(Snowflake 폐기 2026-11-16). 수동 업로드 xlsx 판독은 허용 |
| **Shell access** | Never use `os.system()` or `subprocess` for data access. Use SDK connectors only. |

---

## §3 CODE RULES

### 3.1 Language
| Language | When to Use |
|---|---|
| **Python** | Default: ML models, pipelines, API integration, automation |
| **R** | Only when Python lacks equivalent: VAR (`vars`), GARCH (`rugarch`), unit root tests (`tseries`) |
| **SQL** | All Snowflake queries. CTEs over nested subqueries. Always include `LIMIT` in exploratory queries. |
| **C++ / Java** | Only after Python profiling confirms bottleneck (C++) or UDF deployment requires it (Java). Add a one-line comment justifying the switch. |

### 3.2 Style
- **Python**: PEP 8 · 100-char line limit · f-strings · type hints on all function signatures.
- **R**: tidyverse style · `<-` assignment · pipe (`|>`) for chains > 2 steps.
- No magic numbers — use named constants. Self-documenting variable names.

### 3.3 Error Messages
- **All** errors, warnings, log output → **Korean (한국어)**. External library stack traces stay in English.
```python
except ValueError as e:
    raise ValueError(f"[오류] 원자재 가격 데이터 로드 실패: {e}. 데이터 형식을 확인하세요.") from e
```

### 3.4 Commits
```
feat:     add LSTM price band module (G2)
fix:      correct T+2 FX settlement offset in pipeline
refactor: extract regime detector into src/risk/
data:     update soybean oil prices to Q1-2026
```

---

## §4 PATH-SCOPED RULES INDEX
> Load **only** the file matching your current working directory. Never load all files at once.

| Working In | Load | Contains |
|---|---|---|
| `src/forecasting/` or `notebooks/` | `.claude/rules/modeling.md` | G1/G2/G3 method specs, validation protocol, baseline requirements |
| `src/pipeline/` | `.claude/rules/data_pipeline.md` | Snowflake patterns, API retry logic, schema conventions |
| Any `src/` module | `.claude/rules/libraries.md` | Approved libraries with version pins (Python + R) |
| Any test file | `.claude/rules/testing.md` | pytest, great_expectations, time-aware split protocol |
| `docs/research_desk/references/` (공유 PDF) | `.claude/rules/references.md` | PDF→Markdown 변환·요약 절차 (PDF 직접 판독 금지) |
| **모든 작업** (도구 선택) | `.claude/rules/tooling.md` | 코딩=Ponytail · 아키텍처·워크플로우 도식=drawio-skill · 비정형 자료=Graft (승인자 지시 2026-09-28) |

---

## §5 WISC — Context Management

| Principle | Rule |
|---|---|
| **W**rite | Append new learnings to `MEMORY.md` after each resolved blocker. Git log = long-term memory. |
| **I**solate | Spawn a subagent for data-heavy research (e.g., 10-year historical audit). Return only findings to main session. |
| **S**elect | Load only the path-scoped rule file relevant to today's task (§4). Never load all rules simultaneously. |
| **C**ompress | Run `/compact` when context exceeds ~60% capacity. Preserve active task state and last key decision. |

---

## §6 HITL — Procurement Decision Gate
> Required for any output that influences a Buy / Hold decision or touches production data.

1. **Explore** — Read current market signals + internal inventory. Read-only. No writes.
2. **Plan** — Draft execution plan in Plan Mode. Explicitly state assumptions and data sources.
3. **Validate** — Human reviewer (or invoke `/co-validate` skill) checks plan for hallucinations and risk.
4. **Execute** — Implement only after explicit approval. Open a PR with a descriptive commit message.

---

## §7 MEMORY

| File | Rule |
|---|---|
| `MEMORY.md` | 인덱스·실패패턴만 유지. **월간 학습은 당월 아카이브 파일에 기록**(조정자 지시). |
| `docs/memory_archive/YYYY-MM.md` | 월별 아카이브(내용 무변경). 필요 시 온디맨드 로드 — 아래 @import 참조. |
| `git log --oneline -20` | Run to reconstruct prior decisions before starting a task with no recent MEMORY.md entry. |

> **컨텍스트 최적화(JIT · pointer-not-copy)**: 오래된 학습은 아카이브로 이관하고 포인터만 유지.
> 과거 세부가 필요할 때만 로드: @docs/memory_archive/2026-04.md · @docs/memory_archive/2026-05.md · @docs/memory_archive/2026-06.md · @docs/memory_archive/2026-07.md · @docs/memory_archive/2026-08.md
