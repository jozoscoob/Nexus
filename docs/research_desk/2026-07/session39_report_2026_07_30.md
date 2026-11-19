# Session 39 — 종합 보고 (API 대안·17개 설계결정·문의 답변·기술 스택)

**작성일**: 2026-07-30 · **참여**: C-01(종합) · C-02~08 · P1-01~06

---

## 1. KOSIS 404 원인·조치 (완료)
- **원인**: `llm_health_check.yml`이 **중단된 구 엔드포인트**(`statisticsData.do`)를 여전히 호출
  (지난 세션에 커넥터만 갱신, 헬스체크 미갱신 — 제 누락).
- **조치**: 헬스체크를 신규 `statisticsParameterData.do` URL 방식(조정자 파라미터)으로 교체 완료.
  다음 헬스체크 실행에서 정상 여부 확인 가능.

## 2. 샌드박스 프록시 차단(data.go.kr·kosis.kr) — 수동 대응 대안 (Req)

| # | 대안 | 방법 | 수고 |
|---|---|---|---|
| A | **GitHub Actions 실행** (권장) | Actions 탭 → 해당 워크플로우 → Run workflow. 러너는 차단 없음 — 코드·키 이미 구성됨 | 클릭 2회 |
| B | **로컬 PC 1회 실행** | 사내/개인 PC에서 `python scripts/ingest_customs_gw_xlsx.py` (키는 임시 env로) → 산출 xlsx만 업로드 | 중 |
| C | **포털 수동 다운로드** | data.go.kr·KOSIS 웹 화면에서 CSV/xlsx 다운로드 → 기존 규칙대로 폴더 업로드 (기존에 하시던 방식) | 중 |
| D | 프록시 허용 요청 | 샌드박스 운영 측에 `apis.data.go.kr`·`kosis.kr` 허용 요청 | 불확실 |

→ **A가 기본 경로**입니다. 제가 코드·잡을 모두 준비해 두므로, 조정자는 실행 버튼과 결과 확인만
   담당하시면 됩니다(수동 부담 최소화).

## 3. 관세청 확장 수집 사전 준비 (완료 — 8/3 착수 가능)
- data.go.kr 점검(7/29 19:00~8/2 18:00) 대비, **9개 품목 폴더 × 10개국 템플릿 90개** 생성 완료.
- 형식: 기존 업로드본과 동일(시트 `2010년~2026년` × 행 `1~12월` × 5지표열).
- 8/3(월) 이후: Actions `Historical Analysis Pipeline` → `connector=customs-gw` 실행 시 템플릿과
  동일 구조로 실데이터 채움(또는 포털 수동 다운로드분을 템플릿에 덮어쓰기).

## 4. 신규 WBS (완료 — WBS_0730.xlsx, 템플릿 무관 신규 작성)
- **조건 반영**: ①G1 리포트 자동화 **8/31 완료** ②G2 Preview 모델+대시보드 **9/10(9월 초)**
  ③7개 업무 카테고리 구조 ④지연 대응 규칙 명기 ⑤파일명 일자 갱신 규칙.
- 구성: 4개 Phase × 18개 작업, 주 단위 컬러 Gantt(카테고리별 색), 매크로 없음(호환성↑).
- 구 xlgantt 템플릿(WBS_0727.xlsm) 제거.

## 5. 문의 답변

### 5.1 Historical Analysis Pipeline에서 8개 잡이 'Skipped'인 이유
**설계된 정상 동작**입니다. 조정자 결정(Req 1.2.1 — "Historical은 API 호출 제외")에 따라
`include_api` 입력(기본 **false**)으로 **API 커넥터 잡 7종**(economic·shipping·wasde·climate·
production·commodity·customs)+1을 게이트했습니다. 기본 실행은 **수동 업로드 히스토리 전용**이며,
API 포함이 필요할 때만 Run workflow에서 `include_api=true`를 지정하면 해당 잡들이 실행됩니다.

### 5.2 BO=F는 Databento 유료가 유일한가?
**아닙니다.** 우선순위별 대안:
| 순위 | 방법 | 비용 | 상태 |
|---|---|---|---|
| 1 | **yfinance + curl_cffi** (브라우저 임퍼소네이션) | 무료 | ✅ 적용 완료 — 다음 실행에서 검증 |
| 2 | **stooq.com CSV 직접 호출** (`zl.f` 심볼) | 무료 | 폴백 후보(shipping BDI에서 검증된 패턴) |
| 3 | **TE 수동 xlsx** — TE에 Soybean Oil 시세 존재 시 기존 14종과 동일 방식 업로드 | 무료(수동) | 조정자 확인 필요 |
| 4 | Databento / Barchart OnDemand | 유료($5~25/mo) | 1~3 실패 시 최후 수단 |
→ **1번을 먼저 검증**하고, 실패 시 2→3→4 순으로 이행 권장.

## 6. 기간 정합 — 2010.01 기준선 (Req 1)
- 워크플로우 기본값: `start_year=2010`·`end_year=2026` (반영 완료).
- 수동 업로드: TE·NASA·WASDE·ICE·FAO·관세청 모두 2010~ 정렬 완료(일부 소스 고유 한계:
  Sunflower 2012.05~·CFI 2013.09~·WCI 2025~·DAP/Urea 2019~ — 소스 자체 미제공 구간).
- 커넥터 기본 시작연도도 2010으로 통일 예정(다음 백필 시 HISTORICAL_START_YEAR=2010 주입 확인).
- **말단 정합**: 수동본 최신월(2025.12~2026.07 상이) → 월별 갱신 시 당월−1월까지 통일 원칙.

## 7. '17개 설계 결정' 요약 (session38 §4 — 회신 대기 현황)

| # | 항목 | 권고 | 상태 |
|---|---|---|---|
| D1 | 원산지 확대 | 말聯·인니·파라과이·베트남·EU 추가 | ✅ **조정자 승인**(확장 수집 지시) |
| D2 | 유료 소스 | Phase 2 정밀도 확인 후 | 대기 |
| D3 | 수집 주기 | G1=월별, G2=일별 | ✅ 승인(Daily는 G2 유예) |
| D4 | 0 vs 결측 | 무거래 0 보존·대체 금지 | ✅ 승인(교차검증 룰) |
| D5 | 통합본 vs 국가합 | 총량=통합본/구성=국가 | ✅ 승인 |
| D6 | 이상치 | IQR 1.5 | 권고 적용 |
| D7 | 분석창 | 2010~2026 | ✅ **승인**(2010.01 기준선 지시) |
| D8 | 단위 표준 | USD/MT 통일 | 권고 적용 |
| D9 | 결측 보간 | 가격 ffill≤3일·수급 금지 | 권고 적용 |
| D10 | 공선성 | ElasticNet | 권고 적용 |
| D11 | 유의성 | Bonferroni | 권고 적용 |
| D12 | 임계 재보정 | 분포 기반(P90) | 권고 적용 |
| S1 | 인과엣지 승인 | 도메인(P1-01~04) 검증 필수 | 권고 적용(P1-06 스펙 반영) |
| S2 | 엔티티 등재 | 3회 이상 or 도메인 지정 | 권고 적용 |
| S3 | 그래프 저장소 | 엣지 200+ 시 Neo4j | 권고 적용(YAML 우선) |
| S4 | 다국어 | +포르투갈·스페인어 | 권고 적용 |
| S5 | 출처 보존 | 필수(미충족 반려) | 권고 적용(P1-05/06 스펙 반영) |

→ **명시 승인 4건(D1·D3·D4·D5·D7)** 외 나머지는 "무회신 시 권고안 적용" 원칙에 따라 적용 중.
   이의 있는 항목만 지정해 주시면 됩니다.

## 8. 역할 실행 필요 라이브러리·컴포넌트 (Req 3 — 현 시점 스택)

| 계층 | 컴포넌트 | 용도 | 상태 |
|---|---|---|---|
| 수집 | httpx·curl_cffi·yfinance·comtradeapicall | API 커넥터 | ✅ |
| 정형화 | pandas·openpyxl·pyarrow·pdfplumber·pypdf | xlsx/PDF → parquet | ✅ |
| 분석(G1) | statsmodels(Granger)·scikit-learn(LASSO/ElasticNet)·xgboost·shap | 변수 중요도 | ✅ 승인 목록 |
| NLP(P1-05) | transformers(`ProsusAI/finbert`)·sentence-transformers | ABSA·감성(Phase B) | 목록 등재, 도입 승인 대기 |
| 시맨틱(P1-06) | PyYAML(현행)·**neo4j 드라이버**(엣지 200+ 시) | 온톨로지·그래프 | YAML 운용 중 |
| 시각화(C-07) | plotly(HTML 대시보드)·weasyprint(PDF) | G1 리포트·G2 대시보드 | ✅ |
| 백엔드/DB | GitHub Actions(오케스트레이션)·parquet(스토리지)·DW(보류)·클라우드 학습 환경(Phase 4 설계) | 인프라 | ✅/예정 |
| 프런트 | plotly 정적 HTML(현행) → Phase 4에서 필요 시 경량 프레임워크 검토 | 대시보드 | 현행 충분 |

**신규 도입 필요(승인 요청)**: ①`transformers`+`torch` — G2 Preview 감성 레이어(FinBERT) 시점에
설치(Actions 러너, ~2GB) ②`neo4j` — S3 조건 도달 시.

## 9. P1-05·P1-06 재작성 (완료)
- **P1-05**: 조정자 상세 롤 + Dual-Agent Guide 전면 반영(ABSA 4단계, aspect 7종 — `LOGISTICS_
  DISRUPTION_FLAG` 신규, S·Confidence 이중 점수, evidence_snippet 의무, JSON 스키마, Phase A/B).
- **P1-06**: Enterprise Semantic Architecture 반영(온톨로지 vs 지식그래프, Minimum Viable Ontology,
  LLM-as-Oracle(KGFiller/HyWay)+결정론 사전 병행, QUDT 단위, DAG 강제).
- **모델 확정**: 가이드는 Gemini 3.1 Pro 권고였으나 **조정자 지시로 primary=Claude Sonnet 5**,
  secondary=gemini-3.1-pro(보조 검증용). 대안 검토: 가이드 벤치마크상 GPT-5.5 Thinking이
  JSON 스키마 통과율 최고(99.3%)이나, 프로젝트 도구체계(Claude Code·STRUCTURED_EXTRACT 라우트)
  정합성과 지시 준수 특성상 **Sonnet 5가 적정** — 현행 유지 권고.
