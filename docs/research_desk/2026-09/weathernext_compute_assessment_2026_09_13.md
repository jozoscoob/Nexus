# WeatherNext 컴퓨트 판정 — "GPU가 반드시 필요한가, VM으로 처리 가능한가" (DQ-25 보완) — 2026-09-13

> 승인자 질문(DQ-25 후속): *"GPU가 꼭 필요한가? VM으로 처리할 수 있는가?"*
> 선행 문서: `climate_regions_forecast_weathernext_2026_09_13.md`(산지 23지점·Open-Meteo 예보 층·WeatherNext 3 접근 조건)
> 라벨 규약: CONFIRMED(원문 확인) / INFERENCE(근사·추정) / DATA GAP(미확보). 모든 URL은 2026-09-13 조회.
> 관점 협의 방식: 별도 하위 에이전트 실행 도구가 이 세션에 없어, 데이터 과학 관점·MLOps 관점의 기준 문서
> (`.claude/agents/c03-data-scientist.md`·`c04-document-intelligence.md`·`.claude/rules/modeling.md`)를 읽고
> 각 관점의 논리를 **본 세션이 대신 전개**했음을 명시한다(§3 각 절에 표기).

---

## §1 결론 한 줄

**GPU는 필수가 아니다.** 필요한 것은 경로에 따라 ① 계정·쿼리 비용(WeatherNext 3 **데이터** 경로 — 모델을 실행하지
않으므로 컴퓨트 자체가 없음) 또는 ② CPU VM 시간(오픈 모델 GraphCast_small·GenCast 1.0°의 **자체 추론** — 느리지만
가능)이며, **산지 23지점·15일 예보 확보가 목적이라면 모델 자체 실행은 불필요**하다. GPU가 실제로 요구되는 것은
0.25° 고해상 GenCast·WeatherNext 2 추론(vRAM 60GB급·호스트 RAM 300GB급)과 파인튜닝뿐이며, 두 가지 모두
현 목적(가격 동인 보조 신호)에 비해 과잉이다.

---

## §2 경로별 비교표

| 경로 | 무엇을 실행하나 | GPU 필요 | CPU VM 가능? | 예상 소요/비용 | 운영 부담 | 라벨 |
|---|---|---|---|---|---|---|
| ① Open-Meteo 예보(현행) | HTTP 호출만. 23지점×15일, `best_match`(ECMWF IFS/AIFS) | **불필요** | VM조차 불필요(Actions 러너·일별 런) | 무료 티어 10,000회/일·5,000회/시 한도 내(런당 23호출). **단, 무료 티어는 비상업 용도 한정** — 사내 조달 업무는 상업 이용으로 해석될 여지가 있어 Standard 플랜(월 $29·100만 호출) 검토 필요 | 최소(구현 완료·egress v2.7 등재) | CONFIRMED(한도·요금) · INFERENCE(상업성 판정) |
| ② WeatherNext 3 데이터 추출 | BigQuery/Earth Engine/GCS에 **이미 산출된** 예보에서 23지점 시계열을 쿼리 | **불필요**(모델은 Google이 실행) | VM 불필요 — 클라이언트 SDK 호출만(Actions 또는 소형 VM) | Google Cloud 계정 + 데이터 요청서(승인 5~7영업일, 유료 계약 불요). BigQuery 온디맨드 첫 1 TiB/월 무료·이후 $6.25/TiB(3자 집계). 전체 앙상블 GCS는 Requester Pays·글로벌 1회 수백 GB — **점 추출은 파티션(init_time) 필터 설계에 좌우**, 설계 없이 전량 스캔 시 월 무료분 소진 가능 | 중(계정·과금 상한·egress 4~5종 신규·이력=CC BY 4.0 vs 실시간=실험 약관 분리) | CONFIRMED(접근 구조·요금 체계) · INFERENCE(월 비용) · DATA GAP(Earth Engine 상업 플랜 금액) |
| ③ 오픈 모델 CPU VM 추론 | GraphCast_small(1°·13층) 또는 GenCast 1.0°/Mini를 ERA5 입력으로 자체 실행 | **불필요**(JAX CPU 백엔드) | **가능하나 느림** — "10일 예보가 CPU에서 수 시간 vs GPU 약 1분"(ECMWF ai-models). 0.25° 계열은 호스트 RAM 250~300GB가 필요해 일반 VM 범위 밖 | 1° 결정론 1런/일 기준 16 vCPU·64GB VM(n2-standard-16 $0.777/h·m6i.4xlarge $0.768/h) 수 시간 ≈ **일 $2~5** + ERA5 입력 확보. GenCast 앙상블(50멤버×30스텝)은 CPU에서 비현실적 | 높음(ERA5/HRES 입력 파이프라인·JAX 환경·메모리 누수 이슈 보고·1° 해상도라 23지점 국지 skill 불리) | CONFIRMED(CPU 가능·속도 격차) · INFERENCE(시간·비용) |
| ④ 동일 GPU VM 추론 | 위와 동일 모델을 GPU로 | **1° 계열: 16GB급**(T4·L4·A10G) / **0.25° GenCast: vRAM ~60GB + RAM ~300GB**(H100급) / WeatherNext 2 non-Mini: **H100 필수**(README) | 해당 없음 | 1°: T4 ≈ $0.35/h·L4 ≈ $0.70/h(GCP)·g5.xlarge A10G $1.006/h(클라우드) — 런당 분 단위. 0.25°: a3-highgpu-1g H100 $11.06/h(GCP); 30스텝 1멤버 ≈ 25분(H100·triblockdiag) → 50멤버 단일 GPU 직렬 ≈ 20시간 ≈ **$220+/일**(INFERENCE) | 높음(GPU 표면 부재 — 컴퓨트 중립 계약상 Challenger 동결 사유) | CONFIRMED(메모리·런타임) · INFERENCE(비용 환산) |
| ⑤ 파인튜닝/재학습 | 산지 특화 재학습 | **필수(다기 TPU/GPU)** — README "TPU에 최적화" | 불가 | 학습 규모 수치 미조회 — 산출 불가 | 매우 높음 | CONFIRMED(GPU/TPU 필수) · DATA GAP(규모) |

보조 사실: 오픈 모델 입력은 ERA5(재분석·약 5일 지연) 또는 HRES 초기장이며, 상시 운용은 ECMWF 오픈데이터/MARS
연결이 별도로 필요하다(ai-models 구조). WeatherBench2 ERA5 Zarr는 6시간·13층·0.25°만으로 47TB급(3자 인용)이라
**전체 다운로드는 논외**, 단일 초기화에 필요한 2시점 슬라이스만 원격 읽기하는 방식이 전제다(INFERENCE — 슬라이스 GB급).

---

## §3 관점 협의 요약

### 데이터 과학 관점 (본 세션이 기준 문서 §0·§5·§6에 근거해 전개)
1. 목적 함수는 "23지점 15일 예보값을 G1 보조 피처·브리프 전망 블록으로 쓰는 것"이지 전지구 예보 생산이 아니다 —
   **모델 실행은 목적 달성의 필요조건이 아니다**(데이터 계약이 모델 선택보다 먼저 — First Principles ①).
2. 오픈 모델 CPU 경로의 실효 해상도는 1°(약 100km)로, 산지 격자 대비 Open-Meteo `best_match` 0.25°보다 거칠다 —
   기술적으로 돌아가도 **skill 개선 근거가 없다**.
3. 어떤 경로든 **기준선(persistence·기후평년)을 이기는 리드일수별 skill 실측이 선행** — 검증 없는 예보 피처는
   5단계 게이트에 진입할 수 없다(D-014·기준선 독트린).
4. WeatherNext 3의 정확도 주장(2m 기온 CRPS 최대 40% 개선 vs ENS·단기 리드)은 공개 벤치마크 수치이며,
   **산지·리드 8~15일·강수 변수에서 자체 검증 없이는 인용 불가**.
5. 정당화되는 유일한 시험은 §5의 동일 표본 skill 비교 — 그 결과 Open-Meteo가 리드 8~15일에서 기준선 대비
   우위를 잃을 때만 WeatherNext 3 데이터가 비용 대비 근거를 얻는다.

### MLOps 관점 (본 세션이 기준 문서 Mission B·컴퓨트 중립 계약에 근거해 전개)
1. 실행 표면: ①②는 Actions/ETL 배치에서 HTTP·SDK 호출로 끝나 **신규 표면이 필요 없다**. ③은 CPU VM 1대 +
   ERA5 입력 파이프라인, ④는 GPU 표면 신설 — 후자는 현재 '미평가(동결)' 사유와 정면 충돌한다.
2. 비용: ② 월 무료 1 TiB 안에서 점 추출은 설계 가능하나 **Requester Pays 상한·파티션 필터·쿼리 리뷰**를 운영 규율로
   두어야 한다. ③은 일 $2~5, ④는 1° 기준 시간당 $0.35~1.0, 0.25° 앙상블은 일 $200대 — 목적 대비 불균형.
3. egress: ②는 bigquery·storage·earthengine·oauth2 계열 4~5종 신규 등재(결정 후), ③④는 GCS(가중치·ERA5)와
   ECMWF 오픈데이터 호스트가 추가된다 — 11월 통합 시 미등재는 곧 정지(A-069 전례).
4. 운영 부담: ③④는 JAX 버전·어텐션 구현(GPU는 `triblockdiag_mha` 강제)·메모리 누수 이슈·입력 지연(ERA5 5일)을
   떠안는다. ②는 약관 이원화(이력 CC BY 4.0 / 실시간 실험 약관)와 계정 거버넌스가 부담의 전부다.
5. 라이선스 준수 점검 1건 표면화: Open-Meteo 무료 티어는 **비상업 한정** — 사내 조달 파이프라인 사용은 Standard
   플랜($29/월) 가입이 안전하다(승인 필요 사항 — 지원·승인 상시 발언 원칙).

### 합의
- "GPU 필수" 명제는 **거짓**(0.25° 자체 추론·파인튜닝에만 참). "VM으로 가능" 명제는 **참이나 불필요** — 목적상
  VM조차 필요 없는 ①②가 정답 영역이다.
- 순서: ① 30일 skill 검증 → 결과에 따라 ② 조건부 진행. ③④는 Challenger 동결 유지(GPU 표면 결정과 분리).
- 즉시 승인 요청 1건: Open-Meteo 상업 플랜 여부(무료 유지 vs $29/월).

---

## §4 권고와 DQ-25 선택지 갱신 문안

**권고: B(보류·조건부 A)** — 지금 GPU도 VM도 발주하지 않는다. Open-Meteo 예보 층의 30일 이력이 쌓이면 §5 절차로
skill을 재고, 리드 8~15일에서 기준선 우위를 잃는 변수가 있을 때 WeatherNext 3 **데이터 요청(A)** 을 진행한다.
계정 개설만 선행하는 것은 검토 5~7영업일을 감안한 허용 선택지다.

DQ-25 행 교체 문안(decision_queue 반영용):

> | DQ-25 | **WeatherNext 3 예보 데이터 요청 — GPU 불요 확인(9/13 보완)** | 승인자 질문 "GPU 필수? VM 가능?"에 대한 판정: 데이터 경로(BigQuery/Earth Engine 점 추출)는 **컴퓨트 자체가 없음**(계정·쿼리 비용만), 오픈 모델(GraphCast_small·GenCast 1°)은 **CPU VM으로 실행 가능하나 수 시간/런·1° 해상도라 23지점 목적에 불필요**, GPU는 0.25° 추론·파인튜닝에만 필수(`weathernext_compute_assessment_2026_09_13.md`). Open-Meteo 예보(구현 완료) 30일 skill 검증이 선행 | **A** 데이터 요청 진행(Google Cloud 계정·BigQuery 온디맨드·Requester Pays 상한·egress 4~5종 — GPU/VM 불요) / **B** 보류(권고): 30일 skill 검증 후 재상정, 계정 개설만 선행 허용 / **C** 오픈 모델 자체 추론 — CPU VM(일 $2~5·1°) 또는 GPU VM(1° $0.35~1.0/h·0.25° H100 $11/h) — 비권고·Challenger 동결 유지 | A: 계정+쿼리(월 1 TiB 무료·초과 $6.25/TiB) / B: 무료 / C: VM 시간 | B 즉시 → A는 10월 중순 skill 판정 후 |

병행 승인 요청(신규 등재 권고): **Open-Meteo 상업 플랜 가입 여부**(무료 티어 비상업 조항 — $29/월 Standard).

---

## §5 검증 절차 — 예보 skill 비교(사전 등록)

1. **표본**: Open-Meteo `FCST_{var}_{region}` 일별 발행분 30일 이상(2026-09-14~10-13) × 23지점 × 리드 1~15일.
   유효일별 관측 대조는 같은 커넥터의 아카이브 계열(ERA5-Land, 약 6일 지연)로 하며, 관측 결손일은 제외한다.
2. **변수**: 최고·최저기온(MAE·bias), 강수 합계(hit rate·MAE, 임계 1mm/10mm), ET₀(MAE). 토양수분은 예보 미제공.
3. **기준선**: persistence(발행일 관측 이월)·기후평년(2010~2025 동일 달력일 평균). 리드일수별로 skill score =
   1 − MAE_model/MAE_baseline.
4. **판정 규칙(결과 열람 전 고정)**: 리드 1~7일에서 두 기준선 모두 이기면 피처 후보 진입(5단계 게이트); 리드 8~15일에서
   하나라도 못 이기는 변수가 있으면 그 변수만 WeatherNext 3 데이터 비교 대상으로 지정한다.
5. **WeatherNext 3 비교(A 승인 시)**: 같은 발행일·유효일·23지점에 대해 64멤버 분위(P10/P50/P90)를 추출해 CRPS·MAE를
   Open-Meteo와 동일 표본에서 비교. 개선 폭이 리드 8~15일에서 CRPS 기준 통계적으로 유의(bootstrap CI)할 때만
   병행 수집을 상시화한다. 쿼리는 init_time 파티션 필터·23지점 좌표 조인으로 제한하고 월 스캔량을 로그로 남긴다.
6. **as-of**: 두 원천 모두 available_at = 발행 시각, vintage = 발행 회차(FCST_ 규칙 재사용). 미래 유효일 행은
   전망 행 분기로 available_at이 수집 시각에 캡되는지 합성 검증 1회.
7. **보고**: `reports/market/forecast_skill_{date}.md` — 변수×리드×지점 표·기준선 대비표·판정. 브리프 문구는
   판정 전까지 "참고" 유지(A-191).

---

## §6 출처 (전부 2026-09-13 조회)

- WeatherNext 저장소 README — 모델 계보·가중치 GCS(dm_graphcast)·"TPU에 최적화, non-Mini는 H100 필요, Mini는 P100 가능"·라이선스: https://github.com/google-deepmind/weathernext
- GenCast 클라우드 VM 설정 문서 — 0.25° RAM ~250~300GB/vRAM 32~60GB · 1.0° RAM ~21~24GB/vRAM 8~16GB · 30스텝 8분(TPU splash)/15분(TPU triblockdiag)/25분(H100): https://raw.githubusercontent.com/google-deepmind/weathernext/main/docs/weathernext1_gen/cloud_vm_setup.md
- GenCast README — 변형 4종(0p25deg·Operational·1p0deg·Mini 8멤버 데모)·ERA5/HRES 입력: https://raw.githubusercontent.com/google-deepmind/weathernext/main/docs/weathernext1_gen/README.md
- GraphCast README — GraphCast(0.25°·37층)·GraphCast_small(1°·13층 "lower memory and compute")·operational: https://raw.githubusercontent.com/google-deepmind/weathernext/main/docs/weathernext1_graph/README.md
- ECMWF ai-models — "10일 예보가 CPU에서 수 시간, 최신 GPU에서 약 1분"·입력 MARS/CDS: https://github.com/ecmwf-lab/ai-models · GenCast 플러그인(GPU 권장·CPU 느림): https://github.com/ecmwf-lab/ai-models-gencast · CPU 256GB 12시간 무진행 이슈: https://github.com/ecmwf-lab/ai-models-graphcast/issues/20
- WeatherNext 3 모델·접근 안내(프록시 차단으로 검색 요약 경유 확인 — 데이터 요청서·5~7영업일·유료 계약 불요·전체 앙상블 Requester Pays 수백 GB·이력 CC BY 4.0/실시간 실험 약관): https://developers.google.com/weathernext/guides/models · https://developers.google.com/weathernext/guides/access-forecast · https://developers.google.com/weathernext/guides/bigquery · https://developers.google.com/weathernext/guides/gcs · Earth Engine 카탈로그 0.05°/0.1°: https://developers.google.com/earth-engine/datasets/catalog/projects_gcp-public-data-weathernext_assets_weathernext_3_0_0_0p05deg
- WeatherNext 3 정확도 주장(2m 기온 CRPS 최대 40% 개선 vs ENS, 단기 리드): https://developers.google.com/weathernext/guides/research
- Requester Pays 정의(요청자 프로젝트 과금·저장 비용은 소유자): https://docs.cloud.google.com/storage/docs/requester-pays
- BigQuery 온디맨드 $6.25/TiB·월 1 TiB 무료(공식 페이지가 프록시에서 절단되어 3자 집계 인용): https://cloud.google.com/bigquery/pricing · https://www.stackscored.com/pricing/data-warehouse/bigquery/
- Earth Engine 비상업 자격(비영리·학술·언론·정부 한정)·상업 이용은 유료 플랜: https://earthengine.google.com/noncommercial/ · https://developers.google.com/earth-engine/guides/access · https://cloud.google.com/earth-engine/pricing (플랜 금액 미조회)
- Open-Meteo 약관·요금(무료 10,000/일·5,000/시·600/분·비상업 한정 · Standard $29/월 100만 호출): https://open-meteo.com/en/terms · https://open-meteo.com/en/pricing
- GCP GPU 요금(3자 집계): T4 ≈ $0.35/h·L4 ≈ $0.70/h: https://gridstackhub.ai/providers/gcp-l4 · https://www.qovery.com/blog/google-cloud-gpu-instances-by-workload · H100 a3-highgpu-1g $11.06/h·A100 40GB $3.67/h: https://www.spheron.network/blog/google-cloud-a3-h100-pricing/ · https://www.cloudzero.com/blog/cloud-gpu-pricing-comparison/
- 클라우드 요금(3자 집계): g5.xlarge A10G $1.006/h: https://instances.vantage.sh/aws/ec2/g5.xlarge · p4d.24xlarge(8×A100 40GB) $21.96/h: https://instances.vantage.sh/aws/ec2/p4d.24xlarge · m6i.4xlarge $0.768/h: https://instances.vantage.sh/aws/ec2/m6i.4xlarge · GCP n2-standard-16 $0.777/h: https://instances.vantage.sh/gcp/n2-standard-16
- WeatherBench2 ERA5(6h·13층·0.25° 47TB 인용·전체 37층 시간별은 그 이상): https://weatherbench2.readthedocs.io/en/latest/data-guide.html · https://github.com/google-research/weatherbench2/issues/149
