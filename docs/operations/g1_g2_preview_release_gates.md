# G1 / G2 Preview Release Gates

이 문서는 외부 데이터 전용 파이프라인의 재현 가능한 릴리스 기준을 정의한다. 계정명, 구독명,
네트워크 토폴로지, 개인 일정, 비밀정보는 기록하지 않는다.

## 현재 판정

- **G1**: canonical CBOT 세션 타깃과 핵심 피처가 준비도 게이트를 통과한 뒤에만 실행한다.
- **G2 Preview**: G1의 동일 snapshot을 사용하는 오프라인 배치 잡으로 한정한다. 실행 표면은 로컬 Docker runner(n8n 'G2 Preview' 워크플로우 — 마트·게이트 → 기준선 백테스트)다.
- **운영 G2/G3, 실시간 endpoint**: Preview의 선행조건이 아니다.

현재 Databento `ohlcv-1d` 산출물은 UTC 날짜 버킷이다. CME 거래 세션 종가나 공식 정산가가
아니므로 `CBOT_BO_UTC_*` 진단 계열로만 사용한다. `CBOT_BO_CLOSE`는 다음 중 하나를 만족한
별도 원천만 발행할 수 있다.

1. intraday trades/OHLCV를 CME 세션 경계와 휴일 캘린더로 재집계한 계열
2. 거래소 공식 settlement와 표본 교차검증을 통과한 계열

Sunday 값을 Monday로 단순 이동하는 방식은 한 UTC 버킷이 거래 세션을 나누는 문제를 해결하지
못하므로 허용하지 않는다.

## 구현 우선순위와 현재 장애물

| 우선순위 | 항목 | 이번 변경 | 완료 판정 |
|---|---|---|---|
| P0 | canonical target 의미 오류 | UTC 계열을 `CBOT_BO_UTC_*`로 격리하고 fallback 차단 | 세션/settlement 표본 교차검증 통과 |
| P0 | fail-open workflow | as-of·비정형·DQ·artifact 경로를 fail-closed로 연결 | 실패 주입 시 G1 job 미실행 |
| P0 | 시점 누수 | `available_at` ASOF mart와 fold 내부 전처리 강제 | 독립 pandas 재계산 및 시간분할 테스트 통과 |
| P1 | G1 재현성 | 단일 feature mart/contract만 입력으로 허용 | 동일 snapshot에서 보고서 재생성 |
| P1 | 입력 스냅샷 동결 | SHA256 매니페스트(`scripts/build_snapshot_manifest.py`) | `data/snapshots/{id}/manifest.json` 존재·덮어쓰기 금지 |
| P1 | G2 Preview | 현재 실행 코드가 없으므로 최소 champion/baseline 구현 필요 | 아래 Preview 완료 정의 전 항목 충족 |
| P2 | 운영 확장 | 실시간 endpoint·고급 challenger | Preview 이후 별도 승인 |

현재 저장소에 추가된 것은 P0/P1 릴리스 기반이다. canonical 정산 원천(Databento statistics)과 G2 학습
스크립트는 실행 검증이 필요한 항목이므로 문서만으로 완료 처리하지 않는다.

## 필수 게이트

| 순서 | 게이트 | 통과 기준 | 실패 동작 |
|---:|---|---|---|
| 1 | 수집 | 키·의존성·전체 구간 수집 성공, 필수 파일 생성 | 비정상 종료 |
| 2 | C-08 DQ | 빈 파일 없음, 필수 산출물 존재, 타깃 계약 통과 | 후속 job 중단 |
| 3 | as-of | `event_time`/`available_at` 결측·역전 0건 | 모델 진입 중단 |
| 4 | readiness | 타깃 세션 커버리지 ≥98%, 핵심 피처 월 커버리지 ≥85% | G1/G2 중단 |
| 5 | feature mart | DuckDB ASOF와 pandas 표본 재계산 일치 | 산출물 미발행 |
| 6 | G1 | `target_ret{1,5,20,60}` 명시, TimeSeriesSplit, fold 내부 전처리 | 보고서 미발행 |
| 7 | 입력 스냅샷 | 파일별 SHA256·행수·스키마를 매니페스트에 기록 | 매니페스트 없는 스냅샷 소비 금지 |

타깃 계약은 다음 값을 모두 요구한다.

- `indicator_code`: `CBOT_BO_CLOSE` 또는 승인된 canonical alias
- `target_eligible`: `true`
- `time_basis`: `CME_SESSION` 또는 `EXCHANGE_SETTLEMENT`
- `unit`: `USc/lb`
- 주말 날짜 0건, 세션당 1건, 양수 가격, as-of 역전 0건

## 실행 순서

1. Pull Request에서 `Pull Request Quality Gate`를 통과시킨다.
2. Historical/Data Integration workflow로 외부 데이터 아티팩트를 생성한다.
3. workflow 내부의 Model Readiness job이 feature mart와 contract를 생성한다.
4. G1 job은 raw 파일을 직접 피벗하지 않고 `data/gold/feature_mart.parquet`만 모델 입력으로 쓴다.
5. `scripts/build_snapshot_manifest.py`로 입력 스냅샷 매니페스트를 만든다(원천 run ID·git SHA 기록).
6. 학습 잡은 매니페스트가 존재하고 해시가 일치하는 snapshot만 입력으로 쓴다.

## 실행 표면·비밀정보 계약

실행 표면은 개인 노트북 Docker(n8n → runner 컨테이너)이며, 상시 실행이 필요하면 Oracle Cloud Free Tier
서버를 보조로 쓴다. 키는 로컬 `.env`(gitignore)와 GitHub Secrets에만 두고 코드는 `os.environ` 규약으로 읽는다.
저장소에는 값이 아닌 변수명만 둔다(`.env.template`). 라이선스 원천 데이터(Databento 등)는 저장소에 올리지 않는다.

## G2 Preview 완료 정의

G2 Preview는 다음 최소 범위만 완료로 인정한다.

- 오프라인 배치 잡(로컬 Docker runner)
- last-value·seasonal-naive baseline
- 단일 quantile/conformal champion
- 1·5·20일 P10/P50/P90; 60일은 데이터 게이트 통과 시 추가
- expanding walk-forward 평가
- MAE, pinball loss, empirical coverage, interval width
- MLflow run 및 입력 snapshot ID 기록
- 정적 HTML/JSON 평가 산출물

실시간 endpoint, 자동 Buy/Hold, deep-learning challenger는 Preview 완료 조건이 아니다.

## Merge 금지 조건

- 필수 단계에 `--warn`, `|| true`, `continue-on-error` 사용
- C-08 실패 후 `if: always()`로 G1 실행
- CBOT 부재 시 Brent/CPO/첫 컬럼을 타깃으로 대체
- raw parquet를 `price_date`로 직접 pivot하여 모델 입력으로 사용
- UTC 일봉을 CME 세션/settlement로 표기
- 생성 데이터·보고서를 workflow에서 main에 직접 push
- 매니페스트 없는 스냅샷을 학습 잡이 소비
