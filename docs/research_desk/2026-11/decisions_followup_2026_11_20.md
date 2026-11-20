# 결정 후속 — 옵션 내려받기 명세 · 유료 호가 대안 · 공개용 사본 계획 · 주간 진행 요약 (2026-11-20)

> 최종 결정자 회신(11-20 11:20 KST) 반영. 3번(히스토리 재작성)은 면접 이후 처리.

## 1. 대두유 옵션(OZL) 내려받기 명세 — 승인자가 직접 내려받음

| 항목 | 값 |
|---|---|
| 데이터셋 | `GLBX.MDP3`(CME Globex) |
| 심볼 | `OZL.OPT` (stype_in = **parent** — 대두유 옵션 전 계약·전 행사가) |
| 스키마 ① | **definition** — 행사가·만기·콜/풋·기초 선물(underlying_id)·승수. 내재변동성 계산의 필수 메타 |
| 스키마 ② | **statistics** — 일별 **정산가**(stat_type = settlement)·**미결제약정**(open interest)·거래량 |
| 스키마 ③(선택) | ohlcv-1d — 체결 기반 일봉(유동성 점검용). 내재변동성 계산에는 ①②로 충분 |
| 기간 | 2010-06-06 ~ 현재(보유 ZL 선물 통계와 같은 시작일) |
| 형식 | 기존 ZL과 같게 CSV + zstd 압축, 일자별 분할(split by day) |
| 비용·용량 | 옵션은 행사가 수가 많아 선물보다 행 수가 큼 — 포털의 비용 추정을 먼저 확인(statistics·definition은 통상 소액). 수백 MB~수 GB 예상 |
| 넣을 곳 | `data/raw/Databento/GLBX.MDP3/Options/OZL/definition/` · `.../statistics/` (저장소 미추적 — 라이선스 데이터) |

**내재변동성 산출 계획(파일 수령 후)**
1. 정의 파일로 옵션 → (만기, 행사가, 콜/풋, 기초 ZL 계약) 연결. 기초 가격은 보유한 ZL 계약별 통계의 **같은 날 정산가**(같은 계약 — 롤 혼입 없음).
2. Black-76 역산(유럽형 근사, 미국형 조기행사 프리미엄은 등가격 근처에서 작아 1차는 무시), 무위험금리 = FRED 3개월 국채(DGS3MO), 만기까지 연 단위 일수.
3. 만기별 **등가격 내재변동성**(행사가가 선물가에 가장 가까운 콜·풋 평균) → 30·60거래일 **고정 만기 보간** → 지평 1·5·20·60일에 맞춘 시장 기대 폭.
4. as-of: 정산가는 장 마감 후 공개 → available_at = 정산일 + 1영업일(장중 누수 방지 규약과 동일).
5. 쓰임: G2 화면에 '시장이 기대하는 폭'으로 B4a′ 폭과 나란히 표시 → 급등기 위쪽 이탈(최근 1년 60일 위 이탈 30%) 점검. 범위 산식 결합은 같은 walk-forward 조건에서 비교 후에만.

## 2. 유료 호가(한국 CFR basis·탱커 운임) 대안

| 목적 | 대안 | 비용 | 측정/대리 | 주기·지연 | 판단 |
|---|---|---|---|---|---|
| 한국 도착 basis | **관세청 CIF − CBOT 잔차**(이미 구축, `landed_cost.py`) | 무료 | 측정(실제 수입 신고가) — basis·운임·보험·품질이 섞인 잔차 | 월별·약 1개월 지연 | **유지 — 주 층** |
| 원산지 FOB basis | **아르헨티나 공식 FOB 가격**(농업부 MAGyP, 수출세 산정 기준가) · 로사리오 곡물거래소(BCR) 일일 FOB/FAS 표 | 무료 | 측정(항구 FOB) | 일별 | **채택 권고** — FOB − ZL = 원산지 basis |
| 운임+보험(아르헨티나 경로) | **관세청 아르헨티나산 CIF − 아르헨티나 FOB** | 무료 | 측정 차감으로 얻는 내재 운임·보험·마진 | 월별 | **채택 권고** — 유료 탱커 지수의 가장 직접적인 대체 |
| 아시아 CFR 시장가 | CME 7IF(CFR India) − ZL | 일봉 추정 USD 0 | 대리(인도 도착) | 일별 | 보조 감시만 — 한국 도착가와 다른 시장(이전 판단 유지) |
| 미국 현물 basis | USDA 공개 보고서 | 무료 | — | — | 조사 결과 **무료 일별 대두유 현물 가격 API 확인 안 됨**(NASS Fats & Oils는 물량만) — 보류 |
| 탱커 운임 지수 | LSEG·Argus·Fastmarkets 식물성유 운임 평가 | 유료 | — | 주간 | 무료 대안 없음 확인 — 위 '내재 운임'으로 대체 |
| 운임 압력 신호 | PortWatch 해협 통과량(보유)·브렌트(연료비 대리, 보유) | 무료 | 대리 | 일별 | 유지 — 운임 수준이 아니라 압력 방향 신호 |

결론: 유료 호가 없이도 **아르헨티나 공식 FOB**를 더하면 한국 도착가를 '원산지 FOB basis + 내재 운임·보험(측정) + 관세 + 환율'로 나눠 볼 수 있다(아르헨티나 경로). 미국 경로는 CIF − CBOT 잔차를 계속 쓴다. 수집은 공식 공개 자료만(웹 차단 우회 금지). 출처: [MAGyP 공식 FOB 미러(Alphacast)](https://www.alphacast.io/datasets/agricultural-official-fob-prices-44615) · [BCR 일일 FOB 표 예시](https://www.bcr.com.ar/es/print/pdf/node/112288) · [LSEG 팜유 탱커 운임 평가(유료)](https://www.lseg.com/en/data-analytics/products/workspace/updates/palm-oil-tanker-freight-assessment) · [Argus 바이오연료·원료 운임 평가(유료)](https://www.argusmedia.com/en/about-argus/media-centre/press-releases/argus-launches-global-biofuels-and-feedstocks-freight-assessments) · [USDA AMS 가공업체 보고서(사료 위주)](https://mymarketnews.ams.usda.gov/viewReport/3668). MAGyP 원 데이터셋의 최신 갱신일은 수집 전 확인 필요(미러에 중단 표기 계열이 섞여 있음).

## 4. 공개용 포트폴리오 사본 — 구성 계획(아직 만들지 않음)

| 쟁점 | 결정안 | 이유 |
|---|---|---|
| 형태 | **별도 공개 저장소**(예: `nexus-portfolio`) | 같은 저장소의 고아 브랜치는 저장소를 공개하는 순간 비공개 히스토리까지 노출됨 |
| 히스토리 | 공개본은 **릴리스마다 단일 커밋**(작성자 jozoscoob) | 내부 이력·민감 파일이 따라가지 않음 |
| 포함(허용 목록) | `src/`·`scripts/`(공개 가능분)·`docker/`(비밀 제외)·`config/`·`tests/`·`docs/architecture/`·선별 연구 문서·n8n 워크플로우 JSON·새로 쓴 README | 파이프라인 구조·방법·검증을 보여 주는 핵심 |
| 제외(거부 목록) | `.claude/`·`CLAUDE.md`·`.mcp.json`·`docs/memory_archive/`·`docs/_private/`·`reports/`(수치)·`data/raw`·참고문헌 원문·`MEMORY` 계열 | 도구 흔적·내부 원장·라이선스 데이터·저작권 |
| 데이터 | **합성 표본**(형식만 같은 가짜 시계열) + 공개 무료 소스 스크립트 | Databento·TE 등은 재배포 불가 |
| 화면 | 터미널·G2 화면은 합성 데이터로 생성한 정적 캡처/GIF | 실제 시세 재배포 방지 |
| 자동화 | `scripts/export_public.py`(허용 목록 복사 → 금지어·비밀 검사 → 커밋) + 공개 저장소 CI에 비밀 탐지·금지어 검사 | 사람이 빠뜨리는 위험 차단 |
| 금지어 검사 | 'Claude'·사내/팀장/이전 직장명·내부 코드(C-03 등)·호스트명·키 패턴 | 포트폴리오 규칙 |
| 위험 | 제외한 파일을 import하는 코드 깨짐 → 공개본에서 테스트 전체 통과를 게이트로 · 문서 속 내부 맥락 잔존 → 문서는 새로 요약해 싣기 | — |

## 5. 진행 상황 공유 — 주간 요약을 n8n으로

- 제안: n8n '주간 진행 요약'(월 09:00 KST) → runner 작업 `weekly_summary` → 지난 7일의 커밋·의사결정 원장·실행 보고 성패를 **10줄 이내**로 요약 → `reports/ops/weekly_progress_YYYY-MM-DD.md` + Obsidian 볼트 '진행' 폴더.
- `weekly_wbs.yml`(Actions, 9/29 이후 미사용)은 n8n 판이 한 번 정상 동작한 뒤 삭제.
- 평소 진행 보고는 지금처럼 단계 체크리스트 + 끝날 때 짧은 결과 보고로 유지.
