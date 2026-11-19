# 유료 뉴스·시장정보 소스 가격 조사 (2026-09-13) — DQ-24 배경 자료

**요청**: 승인자 — Reuters·AP 공개 RSS 폐지 이후 무료 3단 체인(Google News RSS 검색 → GDELT DOC 2.0 → Bing News RSS →
원문 섹션)으로 일별 수집을 구현한 상태에서, **유료 뉴스 소스의 목록과 가격**을 정리해 결정 대기(DQ-24)의 판단 근거로 제공.
**조회일**: 2026-09-13 (전 항목 공통). **통화**: 표기 그대로(USD/EUR).
**라벨**: CONFIRMED = 제공사 공식 페이지에 게시된 가격을 확인 · INFERENCE = 제3자(가격 비교·조달 벤치마크 사이트) 보고 ·
DATA GAP = 공개 가격 없음 → "견적 필요(공개 가격 없음)". 숫자는 어느 경우에도 추정·창작하지 않음.
**조회 제약(정직 표기)**: 세션 프록시가 제공사 가격 페이지 직접 열람을 차단(A-069 유형)해 검색 색인의 제공사 도메인 문구로
확인함. reuters.com·ap.org·dowjones.com은 검색 크롤러 자체를 차단해 공식 페이지 인용이 불가 → 해당 항목은 DATA GAP.
**관련 문서**: `media_source_fallback_design_2026_09_13.md`(무료 체인 설계·§7 DQ-24) · `decision_queue.md`(DQ-24) ·
`docs/infra/egress_allowlist.yaml` v2.7(신규 호스트는 등재 선행 — 미등재 시 수집 정지 전례 A-069).

## §1 소스별 가격·조건 표

열: 소스 | 제공사 | 커버리지(대두유·유지·상품 뉴스 적합성) | 접근 방식 | 공개 가격(금액·통화·단위·URL) | 라이선스·재배포/저장 |
Nexus 적합성(일별 기사 수·원문 링크·재현성·이관 용이) | 판정 | 라벨

### 1-A. 통신사·터미널 계열 (Reuters·AP·Bloomberg·Dow Jones)

| 소스 | 제공사 | 커버리지 | 접근 | 공개 가격 | 라이선스·저장 | Nexus 적합성 | 판정 | 라벨 |
|---|---|---|---|---|---|---|---|---|
| Reuters News(Workspace 내) | LSEG | 상품·농산물·바이오연료 데스크 보유 — 대두유 적합 상 | 터미널(Workspace) + Refinitiv Data API(계약 범위) | 공식 가격 미게시. 제3자: Workspace **$10,000~25,000/user/yr**(Vendr https://www.vendr.com/buyer-guides/refinitiv) · ~$22,000/user/yr, 축소판 ~$3,600/user/yr(Hudson Labs https://www.hudson-labs.com/blog/free-and-low-cost-alternatives-to-bloomberg) | named-user 라이선스·데이터 entitlement별 계약. 기사 저장·재배포는 계약 조항 | 단말 열람 중심 — 파이프라인 자동 수집엔 별도 피드 계약 필요. 일별 기사 수 충분·원문 보존 완전. 이관 시 계약 이전 절차 | 보류 | INFERENCE |
| Real-Time News / Machine Readable News(MRN) | LSEG | 동상(구조화·저지연 텍스트 피드, 감성 분석 포함) | Real-Time Platform(EMA/WebSocket) 또는 SFTP | 견적 필요(공개 가격 없음) — "Talk to us" 안내만(https://www.lseg.com/en/data-analytics/financial-data/financial-news-coverage/political-news-feeds-analysis/real-time-news) | 기업 계약(연 단위) | 원문·메타 완전 보존·재현성 최상. 신규 호스트 egress 등재 필요. 수집 규모(일 수천 건) 대비 대두유 관련분은 소수 | 보류(트리거 충족 시 견적) | DATA GAP |
| Reuters Connect | Reuters | 콘텐츠 라이선싱(퍼블리셔 재사용 목적) | 웹 포털·다운로드 | 견적 필요(공개 가격 없음) — 사이트가 검색 크롤러 차단, 공식 문구 인용 불가 | 재게시·재배포 용도 라이선스 — 분석용 파이프라인과 용도 불일치 가능 | 재게시 목적 상품이라 일별 자동 수집·저장 용도로는 부적합 추정 | 부적합(용도 불일치) | DATA GAP |
| AP Media API | Associated Press | 상품·국제·기후 일반 뉴스 — 대두유 전문성 중 | REST API(developer.ap.org) | 공식 가격 미게시(developer.ap.org 접근 불가). 제3자: **무료 평가 티어(프로토타입·저용량) + 운영 티어(견적) + 맞춤 티어**(APIs.io https://apis.io/plans/associated-press/associated-press-plans-pricing/) | 약관·재배포 제한 — 평가 티어는 상업 운영 불가 추정 | 원문·메타 보존. 평가 티어로 실험 가능(비용 0). 운영 전환 시 견적 | **후보(B안 — 평가 티어 실험)** | INFERENCE |
| Bloomberg Terminal | Bloomberg | 상품·농산물 뉴스 상 | 단말(per-seat) + Desktop API(단말 종속) | 공식 가격 미게시. 제3자: **$2,665/user/mo = $31,980/yr(단일)** · **$2,360/user/mo = $28,320/yr(2석+)**, 15건 계약 중앙값(CostBench https://costbench.com/software/financial-data-terminals/bloomberg-terminal/) | 2년 약정 관행. Desktop API는 단말 사용자 본인 용도 한정(서버 자동 수집 금지) | 자동 파이프라인 불가(단말 종속). 비용 대비 대두유 관련 기사 수 소수 | 부적합(비용·자동화 제약) | INFERENCE |
| B-PIPE / Enterprise News Feed | Bloomberg | 동상(기업 피드) | 서버 API(관리형 피드) | 견적 필요(공개 가격 없음). 제3자 참고: B-PIPE $2,000~3,000/mo · 엔터프라이즈 피드 통상 $100,000+/yr(GodelDiscount https://godeldiscount.com/blog/bloomberg-terminal-cost-2026) | 기업 계약 | 원문 보존·재현성 상. 규모 대비 과잉 | 부적합 | INFERENCE |
| Factiva | Dow Jones | 글로벌 언론 집계(Reuters·AP 포함 여부는 계약 소스 범위에 따름) | 웹 + Factiva Analytics/Snapshots API | 공식 미게시(dowjones.com 크롤러 차단). 제3자: **개인 $79/mo 시작**, 10석 $700~900/mo(ITQlick https://www.itqlick.com/factiva/pricing) · 대형 계약 $150,000~1,000,000+/yr(Vendr https://www.vendr.com/marketplace/dow-jones) | 기사 저장·텍스트마이닝은 별도 라이선스(Analytics 계약) | API 경로는 견적. 개인 요금제는 열람용(자동 수집 불가) | 보류 | INFERENCE |
| Dow Jones Newswires / Factiva Analytics API | Dow Jones | 동상 | API(Developer Platform) | 견적 필요(공개 가격 없음) — "전달 방식·범위에 따라 상이"(Datarade https://datarade.ai/data-providers/dow-jones-factiva/profile) | 기업 계약 | 원문·메타 보존·재현성 상 | 보류 | DATA GAP |

### 1-B. 상품 전문 PRA·분석기관 (유지·바이오연료)

| 소스 | 제공사 | 커버리지 | 접근 | 공개 가격 | 라이선스·저장 | Nexus 적합성 | 판정 | 라벨 |
|---|---|---|---|---|---|---|---|---|
| Platts Agriculture Alert / Biofuels Alert | S&P Global Commodity Insights | 식물성유지 일별 가격 평가·속보 — 대두유 적합 최상(약 40개 일별 현물·선물 가격) | 웹 플랫폼·알림·데이터 피드 | 견적 필요(공개 가격 없음) — "contact our team"(https://www.spglobal.com/energy/en/products-solutions/agriculture-food/platts-agriculture-alert) | 구독자 한정·재배포 금지. 가격 데이터는 별도 라이선스 | 뉴스+가격 동시 — DQ-1(basis 호가) 견적과 묶으면 중복 지출 방지 | 보류(DQ-1과 통합 견적) | DATA GAP |
| Fastmarkets Agriculture(Vegoils) | Fastmarkets | 팜·해바라기·유채·대두유 현물·선도 가격 + 뉴스 — 적합 최상 | 웹·데이터 피드·API | 견적 필요(공개 가격 없음)(https://www.fastmarkets.com/agriculture/veg-oils-and-meals/) | 구독 계약·재배포 금지 | 동상 | 보류(DQ-1과 통합 견적) | DATA GAP |
| AgriCensus(Fastmarkets 산하) | Fastmarkets | 곡물·유지 뉴스+가격 — 적합 상 | 웹·이메일 | 견적 필요(공개 가격 없음). **14일 무료 체험** 게시(https://www.agricensus.com/subscribe/) | 약관: 단일 사용자 요금, 재배포 금지 | 체험으로 기사 밀도 실측 가능 | 보류(체험 실측 후) | DATA GAP(체험 CONFIRMED) |
| Argus Biofuels | Argus Media | 바이오디젤·재생디젤·원료(SBO 포함) 가격·뉴스 — 적합 상(수요 축) | 웹·데이터 피드 | 견적 필요(공개 가격 없음). 무료 체험 가능 문구(https://www.argusmedia.com/en/solutions/products/argus-biofuels) | 구독 계약 | RVO·RIN 수요 축 보강용. 뉴스 자동 수집은 피드 계약 필요 | 보류 | DATA GAP |
| Mintec / Expana | Expana | 식품 원재료 17,000종 가격·예측 — 적합 중(가격 중심, 뉴스 약함) | SaaS 플랫폼(per-user 연간) | 견적 필요(공개 가격 없음)(https://www.mintecglobal.com/) | per-user 연간 구독 | 뉴스 목적엔 약함 | 부적합(목적 불일치) | DATA GAP |
| OIL WORLD Weekly/Monthly/Annual | ISTA Mielke GmbH | 유지·유지작물 수급·가격 전망 — 대두유 적합 최상(1958~) | PDF/웹 구독(반기·연) | 공개 가격 페이지 존재 안내(https://www.oilworld.biz/p/weekly → oilworld.biz/t/publications/subscription)하나 **프록시 차단으로 미열람** — 금액 미확인 | 구독자 한정·재배포 금지 | 뉴스가 아닌 주간 분석지 — P1-05/06 요약 파이프라인(FAO·GAIN 동형)에 적합, 일별 기사 수집 대체는 아님 | 후보(요약 코퍼스 — 별도 결정) | DATA GAP |
| UkrAgroConsult Daily Market Report | UkrAgroConsult | 흑해 곡물·유지 일별 가격·뉴스(대두유·해바라기유 포함) — 적합 상(흑해 축) | 이메일·웹 | **EUR 299 / 3개월**(https://ukragroconsult.com/en/publication/daily-market-report/) | 구독자 한정 | 일별 발간 — 흑해 계열(CE-013·014) 보강. 자동 수집은 이메일 파싱 필요 | 후보(저비용·흑해 축 한정) | CONFIRMED |
| UkrAgroConsult Black Sea & Danube Oilseed Report(주간) | UkrAgroConsult | 동상(주간) | 이메일·웹(3/6/12개월) | 견적 필요(공개 가격 없음 — 기간 옵션만 게시)(https://ukragroconsult.com/en/publication/black-sea-danube_vegoil-report/) | 동상 | 요약 코퍼스용 | 보류 | DATA GAP |
| APK-Inform Oilseeds & Oils Monthly / Agrimarket Weekly | APK-Inform | 우크라·러·터키·인도 유지 시장 — 적합 상(흑해 축) | PDF 구독 | 견적 필요(공개 가격 없음 — 구독 페이지 금액 미표시)(https://www.apk-inform.com/en/subscription/OO) | 구독자 한정 | 월간 — 요약 코퍼스용 | 보류 | DATA GAP |

### 1-C. 뉴스 집계 API (제3자 애그리게이터)

| 소스 | 제공사 | 커버리지 | 접근 | 공개 가격 | 라이선스·저장 | Nexus 적합성 | 판정 | 라벨 |
|---|---|---|---|---|---|---|---|---|
| NewsAPI.org | NewsAPI | 15만+ 매체 헤드라인·요약(본문 없음) — Reuters·AP 원문 포함 안 됨(링크만) | REST | 제공사 가격 페이지(https://newsapi.org/pricing) 금액은 검색 색인에 미노출. 제3자: **Developer 무료(비상업·24h 지연·100 req/day) · Business $449/mo(250k req, 상업 허용, 연납 −20%) · Advanced $1,749/mo**(APITube https://apitube.io/en-at/blog/post/news-api-pricing-breakdown-2026) | 본문 저장·재배포 금지, 무료 티어 상업 사용 금지 | 무료 3단 체인과 동일 정보(제목·링크·요약)를 유료로 사는 구조 — 추가 가치 없음 | 부적합 | INFERENCE |
| NewsAPI.ai(Event Registry) | Event Registry | 15만+ 매체·이벤트 클러스터링·15년 아카이브 | REST/SDK(토큰제) | **무료 2,000토큰(30일 아카이브) · 유료 $90~3,000/mo(5K~500K 검색) · 초과 토큰 $0.015**(https://newsapi.ai/plans) | 상업 이용 허용(플랜별), 재배포 제한 | 아카이브 검색(연도별 5토큰)이 유사국면(W1) 사후 검증에 유용. 일별 수집은 무료 체인과 중복 | 보류(아카이브 필요 시 재검토) | CONFIRMED |
| NewsCatcher | NewsCatcher | 뉴스·웹 검색(AI 에이전트 지향) | REST(크레딧제) | **무료 2,000크레딧 · Starter $50/mo(6,000크레딧) · Scale $500/mo(60,000크레딧)**; Base 모드 유효 레코드 1건=10크레딧(https://www.newscatcherapi.com/pricing) | 플랜별 상업 조건 | Starter 수준이면 일 20건 규모 가능 — 비용 낮음. 원문 링크 보존 | 보류(저비용 후보) | CONFIRMED |
| Perigon | Perigon | 실시간 뉴스+엔티티·감성(AI 인텔리전스) | REST | **스타트업 $550/mo(50k req, 제한적 상업 라이선스) · 맞춤 플랜 $24,000/yr~**(https://perigon.io/products/pricing/apis). 제3자: Free $0 · Basic $250/mo · Plus $550/mo(TrustRadius https://www.trustradius.com/products/perigon-news-api/pricing) | 상업 라이선스는 Business 이상 | 감성·엔티티가 P1-05 ABSA와 중복 | 보류 | CONFIRMED(공식 2건)·INFERENCE(하위 티어) |
| Quantexa News API(구 Aylien) | Quantexa | 9만+ 소스·NLP 강화·8년 아카이브 | REST(용도별 라이선스) | 견적 필요(공개 가격 없음 — "use case 기반 라이선스"). **14일 무료 체험** 게시(https://aylien.com/product/plans) | 용도 기반 계약 | 신규 가입이 Quantexa 고객 안내로 전환 중 — 제품 재편 리스크 | 보류 | DATA GAP(체험 CONFIRMED) |
| GNews API | GNews | 6만+ 매체 헤드라인(본문 없음) | REST | **$49.99/mo 시작(최대 30,000 req)**(https://gnews.io/pricing); 제3자: Essential €49.99 · Business €99.99 · Enterprise €249.99/mo(APITube — 통화 표기가 $/€로 엇갈려 페이지 확인 필요) | 무료 티어 비상업, 재배포 금지 | 무료 체인과 중복 | 부적합 | CONFIRMED(시작가)·INFERENCE(티어) |
| Bing News Search API(클라우드) | Microsoft | — | REST | **2025-08-11 서비스 종료(HTTP 410)**(Microsoft Learn https://learn.microsoft.com/en-us/lifecycle/announcements/bing-search-api-retirement). 후속 "Grounding with Bing Search"(ML 플랫폼 Agent 전용) **$35 / 1,000 transactions**(https://www.microsoft.com/en-us/bing/apis/grounding-pricing); 제3자 보고 $14/1K도 존재(SKU 상이 가능) | 에이전트 그라운딩 용도 — 구조화 검색 결과 반환 아님 | **Nexus 3단 체인의 Bing News RSS(무료·API 아님)와 무관** — 영향 없음 | 부적합(종료) | CONFIRMED |

### 1-D. 현행 지출 비교 기준 (프로젝트 기구독 — 참고)

| 항목 | 공개 가격 | URL | 라벨 |
|---|---|---|---|
| Perplexity Sonar Pro(온디맨드 프록시) | **$3 / 1M 입력 · $15 / 1M 출력** + 검색 컨텍스트(Low/Medium/High)별 요청당 수수료(제3자: $6~14 / 1,000 req) | https://docs.perplexity.ai/docs/getting-started/pricing · https://developer.puter.com/tutorials/perplexity-api-pricing/ | CONFIRMED(토큰)·INFERENCE(요청 수수료) |
| OpenAI(교차검증 gpt-5.6-sol) | **Sol $5 / $30 per 1M**(프로모션 $4/$20, 2026-11-21까지) · Terra $2/$12 · Luna $0.20/$1.20 | https://developers.openai.com/api/docs/pricing | CONFIRMED |
| Anthropic(에이전트 계층) | **Haiku 4.5 $1/$5 · Opus 5 $5/$25 per 1M**; Sonnet은 공식 문구 $3/$15(4.6)와 제3자 $2/$10(5) 상충 — 페이지 재확인 필요 | https://platform.claude.com/docs/en/about-claude/pricing | CONFIRMED(Haiku·Opus)·INFERENCE(Sonnet) |
| Trading Economics · Databento | 뉴스 아님(데이터) — 본 조사 범위 외 | — | — |

## §2 무료 체인 대비 비용 효과

| 축 | 무료 3단 체인이 주는 것 | 유료가 더하는 것 | Nexus 요구와의 관계 |
|---|---|---|---|
| 정보 단위 | 제목·원문 링크·일자·한 줄 요약(제목+링크 note 500자 보존 — S-5) | **본문 전문**·구조화 메타(태그·엔티티·감성) | 현행 산출 계약은 "관련 기사 수 + 제목·링크 발췌" — 본문은 요구 사항 아님. 본문 필요 시점 = P1-05 ABSA Phase B(비용 게이트) |
| 권리(entitlement) | 공개 RSS·공개 API의 메타데이터 사용 — 본문 비수집이라 저장 리스크 낮음 | 저장·텍스트마이닝·재배포 권리를 계약으로 확보 | 본문 저장을 시작하는 순간에만 유료 계약이 필수가 됨(현행 무관) |
| 지연·완전성 | Google News 준실시간 · GDELT 색인 시각(최대 하루 지연) · Bing 약 14건 상한 | 저지연·누락 없는 전수 피드 | 일별 KST 05:30 1회 수집이라 지연 민감도 낮음. 누락은 3단 중복으로 완화 — 첫 실행 로그로 0건 일수 실측 예정 |
| 아카이브 | 2일 컷오프(과거 검색 불가) | 다년 아카이브 검색(NewsAPI.ai 연도별 5토큰 등) | 과거 유사국면(W1) 사후 서술 검증엔 유용 — 그러나 FAO·GAIN 2,175건 요약 코퍼스가 이미 2010~ 커버 |
| 비용 | 0(egress 등재만) | 애그리게이터 $600~5,400/yr · 통신사 피드 견적(제3자 $10k~/user/yr) · 터미널 $28k~32k/석/yr | 대두유 관련 기사는 일 수 건 규모 — 전수 피드는 규모 대비 과잉 |
| 이관(D-026) | 무료 호스트 3종 egress 등재 완료(v2.7) | 신규 호스트·키·계약 이전 절차 추가 | 11월 CT 통합 전 신규 계약은 이관 표면 미확정 리스크 |

요지: 무료 체인의 결손은 **본문·아카이브·전수성** 세 가지이며, 현행 산출 계약(관련 기사 수·제목·링크)에는 셋 다 필요하지 않음.
유료가 가치를 갖는 지점은 (a) 본문 기반 ABSA 착수, (b) 아카이브 검색으로 W1 서술 검증, (c) 3단 전부의 반복 0건 — 세 조건 중
하나가 실측으로 확인될 때임.

## §3 권고

1. **보류(A안)** — 무료 3단 체인의 첫 실행 로그(다음 KST 05:30 런 · `media_source_fallback_design` §6 판정 항목 5종) 판정 전까지
   유료 도입은 착수하지 않음. 판정 근거: 4계열 승리 채널 분포 · 0건 일수 · GDELT 429 빈도.
2. **트리거(유료 검토 착수 조건)**: (a) 3단 전부 **7일 연속 0건**인 계열이 1개 이상, 또는 (b) 본문·전문 인용을 요구하는 분석
   요구(ABSA Phase B) 승인, 또는 (c) W1 사후 검증에 과거 기사 아카이브가 필요하다고 판정될 때.
3. 트리거 충족 시 **후보 순서와 예상 연 비용**(전부 공개 가격 기준 — 견적 항목은 범위 미기재):
   - 1순위 **AP Media API 평가 티어**(비용 0, INFERENCE) — 무료로 기사 밀도 실측 후 운영 티어 견적 여부 판단. 평가 티어의
     상업 운영 제한 조항을 계약서에서 먼저 확인.
   - 2순위 **NewsCatcher Starter**($50/mo ≈ **$600/yr**, CONFIRMED) 또는 **NewsAPI.ai 5K**($90/mo ≈ **$1,080/yr**, CONFIRMED) —
     (c) 아카이브 요구에는 NewsAPI.ai, (a) 결손 보강에는 NewsCatcher. 둘 다 본문 저장은 약관 확인 전 금지.
   - 3순위 **UkrAgroConsult Daily**(EUR 299/3개월 ≈ **EUR 1,196/yr**, CONFIRMED) — 흑해 축(CE-013·014) 전용 보강. 이메일
     파싱 구현 비용 병기 필요.
   - LSEG MRN·Platts·Fastmarkets·Argus는 **DQ-1(basis 호가) 견적과 묶어 1회 견적**만 요청 — 뉴스 단독 계약은 규모 대비 과잉.
   - Bloomberg 터미널·B-PIPE·Factiva 개인 요금제·NewsAPI.org·GNews·Bing Search API는 **부적합**(자동화 제약·중복·종료).
4. 공통 전제: 어떤 유료 호스트든 **egress allowlist 선등재 → 키는 GitHub Secrets → 저장은 제목·링크만**(본문 저장은 계약 확인 후)
   순서를 지킴. 11월 이관 전 신규 계약은 이관 표면(ETL 서버/오브젝트 스토리지) 확정 후로 미루는 것이 안전.

## §4 DQ-24 갱신 문안 (한 줄)

> DQ-24 | 유료 뉴스 소스 가격 조사 완료(`paid_news_sources_pricing_2026_09_13.md`) — 공개 가격 확인 6종(NewsAPI.ai $90/mo~ ·
> NewsCatcher $50/mo~ · Perigon $550/mo~ · GNews $49.99/mo~ · UkrAgroConsult EUR 299/3개월 · Grounding with Bing $35/1K), 통신사·PRA
> 피드는 전부 견적 필요(LSEG MRN·Reuters Connect·AP 운영·Dow Jones·Platts·Fastmarkets·Argus·Oil World) | **A 보류 유지** — 무료 3단
> 첫 실행 로그 판정 후, 트리거(7일 연속 0건 / 본문 요구 / 아카이브 요구) 충족 시 AP 평가 티어(무료) → NewsCatcher·NewsAPI.ai
> (연 $600~1,080) 순으로 재상정 | 9월 하순 첫 실행 로그 판정 후
