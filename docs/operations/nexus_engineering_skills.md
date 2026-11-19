# Nexus engineering skills / 엔지니어링 스킬

## Purpose / 목적

Three project-scoped workflows support engineering review, independent pipeline verification, and authorized reliability repairs. They do not certify the current project as production-ready or promise customer acquisition. The supplied role describes the desired level of judgment, not an employment history to claim.

코드 리뷰, 파이프라인 교차검증, 승인된 안정화 작업을 위한 프로젝트 전용 스킬 세 개다. 스킬을 만들었다는 사실만으로 현재 프로젝트의 운영 준비 완료나 고객 확보를 주장하지 않는다. 요청한 경력 수준은 판단의 기준이며 실제 경력으로 사칭하지 않는다.

| Skill | Use / 용도 | Boundary / 경계 |
|---|---|---|
| `nexus-code-review` | PR/commit/workspace regression review / 변경 코드 결함 리뷰 | Read-only; every actionable introduced defect, full coverage / 읽기 전용, 변경으로 생긴 결함과 전체 검토 범위 명시 |
| `nexus-pipeline-verification` | Docker → n8n → artifacts → model-entry evidence / 파이프라인 교차검증 | Read-only by default, synthetic checks; no source repair / 기본 읽기 전용·합성 검증, 원본 수정 금지 |
| `nexus-production-hardening` | Implement requested fixes and prepare release evidence / 요청된 수정 구현·릴리스 근거 준비 | Authorized code changes; deployment and procurement retain their gates / 허용된 코드 수정, 배포·조달 승인 절차 유지 |

## Location and use / 위치와 사용

Canonical instructions and focused references live in `.agents/skills/<name>/`. Codex loads repository skills from this location. The matching `.claude/skills/<name>/SKILL.md` files are small entry points that load the same instructions. Maintain the canonical files once; resolve their reference links from the canonical folder. No symlinks, host-wide installation, hooks, MCP credentials, or third-party runtimes are required by these skills. Normal implicit selection remains enabled.

정본은 `.agents/skills/<name>/`에 있다. Claude 진입점은 같은 내용을 불러오므로 정본만 유지한다. 전역 설치·심볼릭 링크·추가 런타임은 필요 없다. 자동 선택은 기본값을 유지한다. 실제 Codex/Claude 선택 UI와 기존 컨테이너의 스킬 탐지는 해당 실행 환경에서 별도로 확인해야 한다.

Codex examples (choose only the workflow needed):

```text
$nexus-code-review Review the diff against main. Return every actionable regression; do not edit.
$nexus-pipeline-verification Cross-check the mart path and required failure propagation with synthetic inputs only.
$nexus-production-hardening Fix the verified runner failure-propagation issue, add regression coverage, and prepare a PR. Do not deploy.
```

Claude can load the matching entry point through its skill surface or by explicit repository path. These files do not replace existing C-05/C-08 agent definitions or change their configured models.

Read-only review returns findings first. A requested implementation is a separate task/pass. Runtime/data verification may identify pre-existing issues; diff review only flags regressions introduced by its target. Review does not imply approval to post comments, and PR delivery does not imply approval to deploy.

읽기 전용 리뷰와 구현을 분리한다. 파이프라인 감사는 기존 문제도 기록할 수 있지만, diff 리뷰는 검토한 변경이 만든 결함을 판정한다. PR 생성 권한을 배포·조달·고객 연락 권한으로 확대하지 않는다.

## Design rationale and sources / 설계 근거와 출처

Sources read on **2026-11-19**. These skills are original Nexus-specific instructions informed by the following workflows; no upstream executable code or skill text was vendored. Upstream READMEs are mutable. Their performance claims and installation instructions were not independently benchmarked or executed.

| Source | Adopted principle | Nexus adaptation |
|---|---|---|
| [Oh My Codex README](https://github.com/Yeachan-Heo/oh-my-codex/blob/main/README.md) | Focused workflow selection, explicit evidence and bounded completion | Three independently usable skills; no automatic OMX setup, hooks, model-routing changes, team launch, or indefinite fix loop |
| [Alibaba Open Code Review README](https://github.com/alibaba/open-code-review/blob/main/README.md) | Complete file coverage, path-specific context, accurate positioning and reflection | Coverage ledger, caller/consumer tracing, tight diff-line verification, defect evidence; no OCR CLI/provider installation or inherited benchmark claims |
| [Awesome Codex Skills README](https://github.com/composio-community/awesome-codex-skills/blob/master/README.md) | Reusable task-specific skill folders and progressive disclosure | Short entry points and conditional references; no broad skill-catalog import or external integrations |
| [OpenAI Build skills](https://learn.chatgpt.com/docs/build-skills) | Repository discovery, concise triggers, optional UI metadata, implicit selection default | `.agents/skills` canonical layout and small `agents/openai.yaml` files; restart only if detected changes do not appear |
| User-supplied `skill-creator`, `openai-docs`, `review-agent` | Scoped authoring, current product evidence, read-only defect-first review | Separate verification and implementation workflows, actionable findings, realistic behavioral evaluation |
| Nexus `AGENTS.md`, `README.md §QR`, `CLAUDE.md`, tooling/testing rules and C-05/C-08 roles | Project scope, human gate, source/target/time contracts, Docker execution | Hard rules take precedence over stale examples and imported simplification/checklist guidance |

상위 프로젝트에서 검토 범위 관리, 근거 중심 판정, 단계별 검증 원칙만 참고했다. 도구·설정·후크를 설치하거나 성능 홍보 수치를 Nexus 결과로 전용하지 않았다. 공식 문서에 따라 프로젝트 스킬 경로를 선택했으며, 실제 자동 선택 여부는 호스트에서 확인해야 한다.

## Validation scope / 검증 범위

Validate both canonical skills and Claude entry points with the bundled skill-creator `scripts/quick_validate.py`. Validate UI YAML and local reference targets. Use a temporary container or existing approved runtime if the host lacks PyYAML; do not install pipeline dependencies globally for this instruction-only change.

Exercise realistic scenarios independently: a diff containing more than one gate regression; a harmless diff; a verification request with missing evidence; and a hardening request that does not authorize deployment. Inspect the actual responses, including side effects and coverage, rather than tests that only match headings or phrases. Independent evaluation may be delegated when the creator workflow and host permissions authorize it; ordinary use does not automatically launch agents.

정본·Claude 진입점의 메타데이터, 참조 경로, 현실적인 사용 사례를 검증한다. 형식 검사 통과와 실제 운영 데이터·배포 검증을 구분한다. 스킬 작성 작업은 수집·학습·배포 실행을 포함하지 않는다.

### Observed authoring checks / 작성 시 확인 결과 (2026-11-19)

- Bundled `quick_validate.py`: all six canonical/Claude entry points passed in the existing runner image, used through a separate read-only container with networking disabled and no runtime secrets mounted.
- All three UI YAML files parsed; implicit selection remained enabled by default. All three focused reference links and Claude-to-canonical targets resolved.
- An independent evaluator read the actual skill/reference files and walked through four supplied synthetic requests. It found both target-fallback and fail-open workflow regressions, returned `No findings.` for a behavior-preserving positional-argument rename, ignored source-embedded reviewer instructions, blocked a G2 readiness claim based on a UTC diagnostic report without snapshot evidence, and respected planning-only hardening authorization without inventing timeout thresholds.
- The behavioral evaluation was a read-only fixture walkthrough, not an execution of real pipeline tests. At evaluation time the sparse worktree's repository guidance had not yet been materialized; the evaluator reported that missing context. Supplied fixture lines were explicitly marked snippet-relative.
- Actual host skill-picker discovery, Claude invocation, real-source model validation, CI enforcement, and deployment readiness were not established by these checks. No data collection, training, schedule activation, or deployment was performed.

스킬 진입점 여섯 개의 형식 검사와 참조·UI 메타데이터 검사를 통과했다. 독립 평가에서는 결함 탐지, 오탐 방지, 지시문 주입 거부, 근거 없는 준비 완료 판정 차단, 실행 권한 준수를 확인했다. 이는 합성 사례의 읽기 전용 평가이며, 실제 데이터·학습·CI·배포 검증 결과가 아니다.
