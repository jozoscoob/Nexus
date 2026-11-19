# GitHub Actions 사용 범위 — 로컬 n8n + Docker로 못 하는 일만 남긴다 (2026-11-19)

> 승인자 지시(2026-11-19): n8n + Docker로 처리할 수 없는 작업 유형을 식별·문서화하고, GitHub Actions는
> 꼭 필요한 경우에만 쓴다.
> 배경: 저장소 Actions는 2026-09-29 이후 성공 실행이 없고 10-25부터 전 워크플로우가 `startup_failure` 상태다.
> 정기 수집은 이미 로컬 runner가 대신하고 있었다 — 이번 정리로 Actions 정의도 그 현실에 맞춘다.

## 1. 원칙

| 구분 | 실행 위치 | 판정 기준 |
|---|---|---|
| 정기 수집·마트·게이트·백테스트·다이제스트 | **로컬 n8n → runner 컨테이너**(`docker/jobs.py`) | PC가 켜져 있고 `.env` 키로 실행 가능하면 로컬 |
| GitHub 이벤트에 반응해야 하는 일 | **Actions** | PR·이슈 이벤트는 GitHub 밖에서 받을 방법이 없음 |
| PC가 꺼져 있어도 돌아야 하는 일 | **Oracle Cloud Free 서버**(같은 compose) → 차선책 Actions | 상시 실행이 필요할 때만 |

## 2. n8n + Docker로 못 하는 작업 유형 (Actions가 꼭 필요한 경우)

| 작업 유형 | 왜 로컬로 안 되나 | 해당 워크플로우 | 처리 |
|---|---|---|---|
| **PR 상태 검사**(merge 전 자동 차단) | PR 이벤트·체크 결과 표시는 GitHub 안에서만 동작 | `quality_gate.yml`(pull_request) | **유지** |
| **이슈 이벤트 반응**(이슈 생성·라벨 → Projects 보드 편입) | 이슈 웹훅을 받으려면 외부 공개 엔드포인트가 필요 — 로컬 n8n은 사설망 | `projects_sync.yml`(issues) | **유지** |
| **Wiki 미러 발행** | 저장소 GITHUB_TOKEN으로 wiki 저장소에 push(로컬도 PAT로 가능하나 토큰을 하나 더 관리해야 함) | `publish_wiki.yml`(docs/wiki 변경 push) | **유지**(변경 시에만 발화·스케줄 없음) |
| **GitHub Secrets에만 있는 키가 필요한 일** | 로컬 `.env`에 해당 키가 없음(현재 OpenAI 키) | `cross_verify.yml`(main push 시 GPT 교차검증) | **유지** — 로컬 `.env`에 `OPENAI_API_KEY`를 넣으면 로컬 job으로 옮길 수 있음 |
| **PC 전원이 꺼진 동안의 정기 실행** | 로컬 n8n은 노트북이 켜져 있어야 동작 | (없음 — 현재는 PC 가동 시간에 실행) | 필요해지면 **Oracle Free 서버에 같은 compose 배치**가 1순위, Actions schedule은 차선 |

> 이 다섯 가지 외에는 로컬에서 같은 일을 할 수 있다. 특히 사내망 시절의 우회용 트리거(push로 발화해 외부 API를
> 호출하던 워크플로우)는 사내 방화벽이 사라져 이유가 없어졌다.

## 3. 이번에 바꾼 것

**정기 실행(schedule) 해제 — 수동 실행(workflow_dispatch)만 유지**
`external_data_refresh` · `te_xlsx_update` · `llm_health_check` · `llm_model_monitor` · `weekly_wbs`

**push 자동 발화 해제 — 수동 실행만 유지**(사내망 우회용이었음)
`decode_incoming_b64` · `fetch_reference_docs` · `fx_volume_proxy` · `market_structure_verify` ·
`probe_customs_pairs` · `reference_pdf_to_md` · `run_data_integration_now` · `run_historical_now` · `te_xlsx_update`

**자동 발화가 남은 워크플로우(꼭 필요한 4종)**
`quality_gate`(PR) · `projects_sync`(이슈) · `publish_wiki`(docs/wiki 변경) · `cross_verify`(main push, OpenAI 키)

나머지(`historical_backfill`, `unstructured_analysis` 등)는 원래 수동 실행 전용이며 그대로 둔다.
워크플로우 파일은 삭제하지 않았다 — 로컬 장애 때 수동으로 돌릴 수 있는 예비 경로이기 때문이다.

## 4. 로컬 runner로 옮긴 작업 (`docker/jobs.py`)

| job | 내용 | 대체한 Actions |
|---|---|---|
| `collect_free` | 무료·키 기반 커넥터 11종: economic·climate·gpr·wasde·production·commodity·customs·cot + **geointel·shipping·portwatch(신규)** | `external_data_refresh` 수집 잡 |
| `te_update` | TE 시세 xlsx 증분 갱신(`TRADING_ECONOMICS_API_KEY`) → `ingest_te_xlsx.py` 정형화 | `te_xlsx_update` |
| `digest` | 일별 비정형 다이제스트(RSS·GDELT·신호 아카이브) | `external_data_refresh` 다이제스트 잡 |
| `manual_parsers` · `mart` · `baseline` · `tests` | 수동 업로드 파서 · 마트+게이트 · 밴드 백테스트 · pytest | `historical_backfill` · `quality_gate`(로컬 사전 검사) |

n8n 워크플로우(`docker/n8n/g2_preview.json`)에서 `POST http://runner:8000/run/<job>`으로 호출한다.
Perplexity 키가 없으면 gpr·shipping 커넥터의 Perplexity 프록시 부분은 경고 후 건너뛴다(비치명).

## 5. IMF PortWatch 전환 판정 (승인자 지시 2)

**결론: AISstream의 해협 통과 집계는 PortWatch로 대체한다. Perplexity의 뉴스·위험 등급은 대체할 수 없다.**

| 항목 | PortWatch | 판정 |
|---|---|---|
| 내용 | 해협 28곳 일별 통과 척수(탱커·건화물·컨테이너·전체), 위성 AIS 기반 | 대두유 경로 7곳 수집(수에즈·파나마·바브엘만데브·말라카·호르무즈·희망봉·대한해협) |
| 비용·키 | 무료·키 불필요(ArcGIS 공개 API) | 운영 부담 없음 |
| 기간 | 2019-01-01~ (실측 2,876일 × 21지표) | 유사 국면 분석에 충분 |
| **적시성** | **주 1회 갱신·약 4~7일 지연**(2026-11-19 기준 최신 11-15) | **실시간 아님** — 해협 봉쇄 같은 급변은 며칠 늦게 잡힘 |
| as-of | 규칙 `PW_` lag 9일(주간 배치의 최악 지연 보수 적용) | 모델 누수 없음 |
| Perplexity 대체 | 숫자(통과 척수)만 제공 — 사건 서술·위험 등급·정책 뉴스 없음 | **대체 불가** |

### 실시간 공백을 메우는 대안 (OSINT, 전부 무료)

| 대안 | 무엇을 주나 | 현재 상태 |
|---|---|---|
| GDELT 이벤트(해협·분쟁 키워드) | 15분 단위 뉴스 이벤트 건수 | geointel 커넥터에 구현됨 — 이번에 로컬 수집 편입 |
| UKMTO / JMIC 해사 경보 | 홍해·호르무즈 선박 공격·위협 경보 | 미구현 — 웹 공지 형식이라 RSS·HTML 판독 필요(후속 후보) |
| 미국 MARAD 해사 경보(MSCI Advisories) | 해역별 위협 등급·권고 | 미구현 — 후속 후보 |
| NGA 항행 경보(NAVAREA) | 항행 위험·군사 훈련 구역 | 미구현 — 후속 후보 |
| 전문 매체 RSS(farmdoc·World-Grain·OFI 등) | 시장·정책 뉴스 헤드라인 | 일별 다이제스트에 구현됨 |
| AISstream(선택) | 실시간 선박 위치(WebSocket) | 키 있으면 재사용 가능 — 실시간이 꼭 필요할 때만 |

권고: PortWatch(정량, 주간 지연) + GDELT·해사 경보(정성, 실시간)로 역할을 나눈다. 해사 경보 3종 수집기는
별도 승인 후 추가한다.

## 6. 남은 확인 사항

- Actions `startup_failure`의 원인(계정 결제·한도 등)은 저장소 코드로 판별할 수 없다. 위 4종이 다시 돌려면
  GitHub 설정 쪽 확인이 필요하다.
- `cross_verify`를 로컬로 옮기려면 로컬 `.env`에 `OPENAI_API_KEY`가 있어야 한다.
