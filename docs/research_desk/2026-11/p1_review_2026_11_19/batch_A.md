# P1 6관점 검토 — Batch A (doc10~doc17, 가격·수급 핵심 동인 논문 8편)

> 작성 2026-11-19 · 읽기 전용 검토(저장소 파일 수정 없음) · 입력: `_pdfparse_cache/corpus/out_mineru/doc10~17.md`(MinerU, `<!-- page N of M -->` = PDF 쪽).
> 관점: P1-01 상품 분석 · P1-02 지정학·무역 · P1-03 기후 · P1-04 공급망·물류 · P1-05 뉴스·감성 · P1-06 시맨틱·온톨로지.
> 중복 대조 대상: `docs/research_desk/2026-11/market_structure_pdf_review_2026_11_17.md`(이하 **11/17 검토** — 같은 8편 영문 검토, Part A), `src/semantic/ontology.yaml`(CE-001~024), `entities.yaml`(TERM 237), `methods.yaml`(MP-01~20), `docs/memory_archive/2026-08~11.md`, `.claude/rules/modeling.md`.
> **파싱 결함(DATA GAP)**: doc12의 MinerU 출력은 12쪽 중 **1쪽만** 담고 있다(`doc12.md` 3.3KB). 본 검토의 doc12 수치는 같은 PDF(`corpus/in/doc12.pdf`)를 pdftotext로 다시 추출한 결과에서 PDF 쪽 번호 기준으로 확인했다. 추출본은 scratchpad에만 두었다. MinerU 재파싱이 필요하다.
> **G2 타깃 전제**: 승인 대기 중인 결정은 "CME 공식 정산가(Databento statistics) · 전일 미결제약정(OI) 기준 근월 ZL · 롤 일자 플래그"다. 아래 A-01·A-02는 이 결정과 직접 맞물린다.
> 라벨: CONFIRMED(원문 확인) · INFERENCE(원문에서 도출한 추론) · DATA GAP · NOT COMPARABLE.

---

## 1. 문서별 3줄 요약

**doc10 · Barboza Martignone·Paparas·Behrendt 2023 (Agricultural Sciences 14) · SBO 관련성: 하**
- 대두(원곡) 7개 시장(CBOT·Rotterdam·Paranaguá·Rosario 현물/선물·중국 현물·Dalian)을 2009-09~2019-05 구간에서 TAR/MTAR로 분석했고, 비대칭 가격전이는 어느 시장에서도 기각되지 않았다(p.12~15).
- 정부 개입(아르헨 수출세·중국 지지가격)은 비대칭이 아니라 구조변화와 공적분 약화로 나타났다(p.10 "fading effect of the Cointegration vectors", p.15).
- Table 1 평균 가격 열 정렬이 MinerU 출력에서 명확하다. Paranaguá 438·Rotterdam 461·CBOT 415·중국 630·Rosario 282/288 USD/t(p.7). 대두유 수치는 없다.

**doc11 · Schaefer·Myers·Johnson·Helmar·Radich 2022 (AERE 51) · SBO 관련성: 상**
- 2000~2020 월별 자료로 미·EU 바이오디젤 원료유와 원유의 공적분을 추정했다. 정책 더미(급변)와 세계 원유 생산(완만한 이동) 두 경로를 분리했다(p.6~8).
- 미국 대두유의 원유 총탄력은 0.29(2000년대 초) → 0.96(EPAct 후) → 0.18(2015-01)로 움직였다(p.11). EU 대두유는 0.67 → 0.07(ILUC 후)로 떨어졌다(p.12).
- 탄력은 원유 가격 수준이 높을수록 커진다(p.5 도출식). 정책 시점을 ±6개월 무작위로 흔들어도 결과가 견고했다(p.13). 저자는 고변동기 효과를 미검증으로 남겼다(p.13).

**doc12 · Baryshpolets·Devadoss·Sabala 2022 (JAAEA 1) · SBO 관련성: 상**
- 공간균형모형(대두·대두유·대두박) 시뮬레이션이다. 중국 25% 관세를 철폐하면 미국 압착이 −7.29%, 미국 대두유 가격이 +5.49% 움직이고, 대두박 가격은 −2.49%다(p.6~7).
- 대두유 가격은 미국·멕시코를 제외한 거의 모든 나라에서 하락한다(p.7). 한국은 모형 내 수입국이며 중국산 대두박 수입이 늘어난다(p.7).
- Phase One 합의에서 중국은 2017년 대비 추가 구매 125억 달러를 약속했으나 실제는 65억 달러였다(p.2). MFP 지급은 1.65(2018)·2.05(2019) $/bu였다(p.2).

**doc13 · Qanitha 외 2024 (IOP EES 1379, VEGOIL 학회) · SBO 관련성: 하**
- 2020~21년 수출액 기준 BCG 매트릭스 분석이다. 아르헨 36%·브라질 12%·미국 5.26% 점유이고(p.5), 아르헨은 "cash cow"로 분류됐다(p.8).
- 통계 검정과 시계열이 없다. 가격 급등기의 금액 기준 "성장"이라 물량 정보가 아니다(p.7 Table 1, 세계 +59.9%).
- 인도네시아 팜유기금(BPDPKS)의 협력·지원이 명시돼 있다(p.10). 이해상충 표기가 필요하다.

**doc14 · Kyriazis 2024 (Economies 12:57) · SBO 관련성: 중**
- IMF 월간 4개 유지(1990-01~2023-10)로 TVP-VAR 연결성을 분석했다. SBO가 팜유에서 받는 충격이 36.11이고 TCI는 33.34다(p.7 Table 2).
- SBO는 팬데믹·러우 전쟁기에 "non-negligible absorber"였다(p.9). 해바라기유의 대외 연결성은 전쟁기에 40% 직전까지 올랐다(p.9).
- 올리브유는 거의 고립돼 있어 프로젝트 범위 밖이다. 실익은 IMF 월간 장기 이력과 위기기 흡수자 해석이다.

**doc15 · Fousekis 2024 (J. Econ. Finance 48) · SBO 관련성: 상**
- 2015-01~2023-05 일별 선물(investing.com, p.5 각주3)로 SBO-팜유 분위수 coherency를 추정했다. bull-bull은 0.149~0.175(10% 수준만 유의)이고 bear-bear는 0.239~0.506이다(p.6 Table 1).
- 국면 비대칭(bear=bull 기각)은 1개월·1년 척도에서만 유의하다(p=0.015, p.8 Table 3). **1주 척도에서는 기각되지 않는다**(p=0.423, p.7 Table 2). 조정은 대략 1개월 안에 끝난다(p.7).
- 탈동조 구간은 2021-Q2(RD 수요)와 2022-Q2~Q3(인니 수출금지)이다(p.5 각주4). SBO 일별 수익률의 필터 모형은 ARMA(1,1)-GARCH(2,2)다(p.12 Table 8).

**doc16 · Fousekis·Grigoriadis 2025 (Modern Finance 3(3)) · SBO 관련성: 상**
- 2010~2025-05 Yahoo 근월 ZS·ZM·ZL(p.4)로 WLMC를 적용했다. oilshare는 2020년까지 25~35%였고 2021~22년 급등해 이후 약 40%다(p.5).
- 유박(oil–meal) 상관은 최근 −0.5까지 내려간다(p.9). 크러시 스프레드는 반지속성(평균회귀)을 보인다(p.9). 정보 흐름은 하류에서 원료로 간다(수요 주도, ZS 지배, p.10~11).
- 실현변동성에서는 ZS RV가 지배(=수신자)다(p.13~14). 후반기에는 대두박 RV가 대두유·대두 RV에 끌려간다(p.11). 지연 효과는 다루지 않았다(p.14).

**doc17 · Cortazar·Ortega·Pérez 2025 (Risks 13:9) · SBO 관련성: 중**
- 옥수수·대두·밀의 5요인(3잠재+작물연도 2) 칼만 모형이다. 대두 리스크 프리미엄은 만기 1년 미만에서 음(−), 장기에서는 약 2%로 수렴한다(p.15).
- 신·구곡 계약은 서로 다른 실물 공급에 묶여 따로 가격이 매겨진다(p.2~3). 전환월(대두 9월물)은 추정에서 제외했다(p.8).
- 애널리스트(Bloomberg) 기대가격의 MAPE는 표본 내 4.21·표본 외 14.48이고, 선물 적합은 0.21·0.40이다(p.12 Table 6). 대두 투기세력은 주로 순매수였다(p.15).

---

## 2. 제안 목록

| ID | 문서 | 제안 내용(프로젝트 반영) | 반영 위치 | 주관 | 다른 관점 의견 | 우선 | 라벨 | 근거 locator(≤20단어) | 이미 반영 여부 |
|---|---|---|---|---|---|---|---|---|---|
| A-01 | doc17 | **G2 라벨은 같은 계약 안에서만 계산한다.** OI 근월 ZL은 7월물→8/9/10/12월물 롤에서 구곡·신곡 경계를 넘는다. h=20/60 수익률이 롤을 걸치면 계약 간 스프레드가 라벨에 섞이므로 같은 계약 수익률을 연결하거나 비율 조정한다. 롤 플래그 구간은 별도 coverage로 보고한다 | G2 타깃 명세 · modeling.md Validation Protocol · `src/evaluation/band_backtest.py` 설계 노트 | P1-01 | P1-04 동의(신곡 브라질 수확기와 겹침) · P1-06 주의: ZL 적용은 대두 논문에서 유추한 것 | Must | INFERENCE | doc17 p.2 "new and old crop derivatives are tied to different physical supplies and are priced consequently" · p.8 전환월 제외 | 신규(롤 플래그만 승인안에 있음) |
| A-02 | doc16 | **정정: 11/17 검토 순위 1의 "yfinance ZM=F/ZS=F 즉시 사용"을 G2 피처에서 뺀다.** 크러시·oilshare는 ZL 타깃과 같은 원천(Databento statistics 정산가)·같은 OI 근월 규칙·같은 롤 달력으로 만든다. yfinance는 탐색용으로만 쓴다 | G2 설계 · data connector(ZM/ZS 반입) · 11/17 검토 §(a) rank 1 정정 메모 | P1-01 | P1-06 동의(원천 혼합 시 as-of·롤 불일치) · P1-04 주의: ZM/ZS 반입 지연 시 G1 탐색만 허용 | Must | CONFIRMED(논문 자료=Yahoo 근월) / NOT COMPARABLE(정산가 타깃과) | doc16 p.4 "daily front-month futures prices ... obtained from Yahoo Finance" | 정정 대상(11/17 검토 rank 1) |
| A-03 | doc16 | CE-024(한국 압착 채산성 악화) evidence 추가: 2021년 이후 oilshare가 약 40%로 올랐고(대두박 가치 비중 하락) 유박 상관이 음(−)으로 전환했다. 압착 수익이 대두유에 쏠려 대두박가 압박이 구조화했다는 배경이다 | ontology CE-024 evidence(source_id·page·quote) | P1-04 | P1-01 주의: 미국 선물 지표이므로 한국 압착 마진과 직결 금지 · P1-06 동의(배경 note, candidate 유지) | Should | INFERENCE | doc16 p.5 "fluctuated between 25 and 35 per cent until 2020; it rose precipitously in 2021 and 2022" · p.9 "as low as -0.5" | 신규(CE-024 evidence는 FAS Seoul·기사뿐) |
| A-04 | doc16 | 용어 후보 3종: Oilshare(대두유 가치 비중 = 유가×11lb ÷ (유가×11lb + 대두박가×44lb)) · Board Crush Spread · BOPO(SBO−팜유 선물 스프레드). 정의·단위·출처를 표준화한다 | entities.yaml candidate TERM-238~240 · metrics.yaml | P1-06 | P1-01 동의 · P1-04 주의: 실제 수율(약 12lb)은 별도 변형으로 둔다(11/17 검토 Paper 7 (c)) | Should | CONFIRMED(정의) | doc16 p.4 oilshare 정의(11 lb oil, 44 lb meal) · doc15 p.3 "soybean-palm oil spread (BOPO)" | 신규(entities에 oilshare·BOPO·crush margin 없음, TERM-033은 물량) |
| A-05 | doc12 | **CE-011 evidence와 노드 분리.** 관세 철폐 시 미국 SBO는 +5.49%, 미국·멕시코 외 대두유 가격은 하락하고 한국도 모형 내 수입국이다. 현행 단일 `SBO_INTL_PRICE`·DOWN 표기는 미국 ZL과 수입국 CIF 방향이 반대인 점을 담지 못한다 | ontology CE-011 evidence + 결과노드 분리 후보(`US_SBO_PRICE` vs `IMPORTER_SBO_PRICE`) | P1-02 | P1-01 동의(한국 바이어 핵심) · P1-06 주의: SEM 비교정학이므로 크기 인용 금지, 분리는 candidate | Should | CONFIRMED(모형 결과) / INFERENCE(한국 적용) | doc12 p.7 "almost every country sees a decrease in domestic price ... except for the United States and Mexico" | 11/17 검토 rank 3 제안·**온톨로지 미반영**(CE-011 evidence에 doc12 없음) |
| A-06 | doc12 | **무역합의 구매약속의 이행률 할인 규칙.** Phase One의 추가 구매 약속 125억 달러 중 실제는 65억 달러(약 52%, 도출)였다. 2026 부산 합의의 SOE 구매(CE-011 기존 evidence)도 약속은 상한, 이행은 ESR 실측으로만 반영한다 | CE-011 interpretation_rules · P1-05 `US_CN_TARIFF_SENTIMENT` 채점 규칙(약속 발표 강도 감액) | P1-02 | P1-05 동의(발표≠선적) · P1-04 동의(ESR 801/5700 확인) | Should | CONFIRMED(p.2 수치) / INFERENCE(52%는 도출·규칙) | doc12 p.2 "China only purchased $6.50 billion more in 2020 than it did in 2017" | 신규 |
| A-07 | doc11 | CE-020 evidence 추가: 총탄력 0.29→0.96→0.18(미국)·0.67→0.07(EU). lag_basis에 "2015년까지 셰일 확대로 연계 약화, 2020년 이후 재강화(기존 note)"를 함께 적어 시기 의존을 명시한다 | ontology CE-020 evidence | P1-01 | P1-06 동의 · P1-02 주의: 표본이 2020에서 끝나 RD 시대에 외삽 금지 | Should | CONFIRMED | doc11 p.11 "increased to 0.96% for soy oil" · "fell to 0.18% for soy oil" | 11/17 검토 Paper 2 제안·**온톨로지 미반영** |
| A-08 | doc11 | **에너지 효과의 가격수준 의존성.** 원유 수준이 높을수록 탄력이 크다. G1 중요도와 G2 피처에 `Δ원유 × 원유수준(또는 분위)` 상호작용을 후보로 두고, horizon×레짐 분해에서 고유가 레짐을 따로 본다 | modeling.md G1 중요도 산출 단위 · G2 피처 후보 | P1-01 | P1-02 동의(지정학발 유가 급등기 해석) · C-03 영역: ablation 필수 | Could | INFERENCE | doc11 p.5 elasticity "is increasing as the crude oil price rises" | 신규(11/17 검토는 정책 레짐 상호작용만 제안) |
| A-09 | doc11 | **정책 시점 지터 검정.** 정책 더미·유사국면 창의 시작일을 공포일 기준 ±6개월(또는 ±k거래일) 범위에서 무작위로 100회 이동해 계수와 순위의 안정성을 확인한다. 저장은 published_at/effective_from 분리(D-023)를 따른다 | modeling.md Validation Protocol(정책 이벤트 견고성) · G1 analogue | P1-02 | P1-06 동의(D-023과 정합) · P1-01 주의: 일별 모형에서는 ±6개월이 과대하므로 창 폭을 horizon에 맞춘다 | Should | CONFIRMED(방법) / INFERENCE(적용) | doc11 p.13 "window of time beginning 6 months before the enactment ... ending 6 months after" | 신규 |
| A-10 | doc11 | 캐놀라-SBO 대체 경보(P1-04 표, CFR 20 USD/MT)는 구조적 프리미엄 추세를 제거한 뒤 판정해야 한다. 캐놀라 프리미엄은 20년간 SBO 대비 +28% 확대됐다(재인용) | p104 경보표 주석 · TERM-056 부호 조정 시 함께 | P1-04 | P1-01 동의 · P1-06 주의: 재인용(Schaefer 2021) 수치라 1차 출처 확인 전 note로만 둔다 | Could | INFERENCE | doc11 p.2 premiums "increased by 28% and 4%, respectively, relative to soy oil" | 신규 |
| A-11 | doc15 | **CE-015 해석 규칙 보강(정정 포함).** bull-bull coherency 0.149~0.175 대 bear-bear 최대 0.506이다. 다만 국면 비대칭은 1개월·1년 척도에서만 유의하고 1주에서는 유의하지 않다. 따라서 "랠리 시 팜유 비추종"은 h=20/60 해석에 적용하고, h=1/5에는 적용하지 않는다 | ontology CE-015 interpretation_rules + evidence | P1-01 | P1-06 동의(A-201 규칙의 독립 정량 근거) · P1-05 주의: investing.com 자료라 재현 불가 표기 | Should | CONFIRMED | doc15 p.7 Table 2 1주 bear=bull 검정 0.09 (p=0.423) · p.8 Table 3 1개월 (p=0.015) | 11/17 검토 rank 2(지평 ≤20일)·**CE-015 evidence에 doc15 없음**. 1주 무의미는 신규 정정 |
| A-12 | doc15 | G2 stress slice에 2021-Q2(RD 탈동조)와 2022-Q2~Q3(인니 수출금지)를 이름 붙여 추가한다. 현행 목록은 2022 러우만 포함한다 | modeling.md Validation 7항 | P1-01 | P1-02 동의(정책 충격) · P1-04 동의 | Should | CONFIRMED | doc15 p.5 "decoupled ... in the second quarter of 2021 and in the second and third quarter of 2022" | 11/17 검토 rank 6 제안·**modeling.md 미반영** |
| A-13 | doc15·16 | **G2 변동성 층 사전정보.** SBO 일별 수익률 필터는 GARCH(2,2)였다. ZS RV는 지배변수(=수신자)이므로 ZS/ZM RV가 ZL 분산을 선행한다고 기대하지 않는다. EGARCH-X 외생변수는 ZL 자체 변동성·에너지·정책을 우선한다 | G2 EGARCH-X 실험 카드(외생변수 후보 순위) | P1-01 | C-03 영역: 동일 fold 비교로만 결정 · P1-04 동의 | Could | INFERENCE | doc16 p.11 "the RV of meal price appears to be driven by the RVs of oil and soybean prices" · doc15 p.12 | 신규 |
| A-14 | doc16 | **크러시 마진 괴리를 평균회귀 상태변수로 쓰는 G3 시나리오 축.** 마진이 고점이면 압착 확대 → 후행 대두유 공급 증가(CE-022 기제)를 하방 시나리오 근거로 쓴다. 단 ZL이 공식에 포함되므로 지연 구성과 ablation을 전제로 한다 | G3 3-시나리오 설계 · CE-022 note | P1-04 | P1-01 동의 · P1-06 주의: Verleger 예측력은 ZS 대상(ZL 아님) | Could | INFERENCE | doc16 p.9 "the crush spread displays anti-persistence; that is, it tends to revert to its long-run equilibrium level" | 신규(11/17 검토는 피처·레짐 축만 제안) |
| A-15 | doc14 | CE-014(흑해 해바라기유) evidence: 러우 전쟁기 해바라기유 대외 연결성이 40% 직전까지 상승했고 SBO는 흡수자였다. 충격은 대체유 → SBO 방향으로 들어온다는 기제 근거다 | ontology CE-014 evidence | P1-02 | P1-01 동의 · P1-06 주의: 월간 전표본 평활 경로라 선후행 주장 금지 | Should | CONFIRMED | doc14 p.9 "a non-negligible absorber of spillover impacts during the pandemic and the Russia–Ukraine conflict" | 신규(CE-014 evidence 미대조 — 11/17 검토는 배경만 언급) |
| A-16 | doc17 | **COT 순포지션 부호를 리스크 프리미엄 부호로 읽지 않는다.** 대두는 단기 프리미엄이 음(−, 투기 순매도를 시사)인데 COT상 투기세력은 순매수였다. 논문 내부에서도 부호가 엇갈린다. COT는 z-score 피처로만 쓰고 해석 문구는 금지한다 | `cot_connector` 해석 규칙 · entities CFTC COT 항목 해석규칙 · P1-05 감성 연계 | P1-05 | P1-01 동의 · P1-06 동의(해석규칙 필드) | Should | INFERENCE | doc17 p.15 "soybean risk premiums are negative for shorter maturities" vs "soybean speculators predominantly took long positions" | 신규(11/17 검토 rank 9의 해석 보정) |
| A-17 | doc17 | ZL 기간구조 피처를 2버킷(당해 마케팅연도 vs 차기)으로 단순화한다. 차기 이후 연도 간 차이는 불필요하다는 결과를 근거로 원월 Databento 추가 조회 범위(비용)를 줄인다 | G2 기간구조 피처 설계 · Databento 원월 비용 추정 범위 | P1-01 | P1-04 동의(비용 절감) · P1-06 주의: 대두 결과의 ZL 유추 | Could | INFERENCE | doc17 p.15 "it is only necessary to differentiate the current marketing crop year from the future" | 신규(11/17 검토는 원월 전체 조회 가정) |
| A-18 | doc17 | 계절 정보 공개기(미국 7~8월 개화·남미 1~2월)에 G2 coverage를 계절 슬라이스로 분리 보고한다. 기존 P1-03 개화기 경보 창과 같은 달력을 쓴다 | modeling.md Validation(계절 슬라이스) · p103 경보 창 연계 | P1-03 | P1-01 동의 · P1-06 주의: SBO는 연중 압착이라 계절성은 원곡 경유 간접 효과 | Could | INFERENCE | doc17 p.4 "relevant information is revealed, especially during the growth and harvest periods" | 신규 |
| A-19 | 전편 | **evidence 메타 필드 추가: `funding`·`data_reproducibility`.** doc13은 팜유기금 지원(p.10), doc15는 investing.com·요청 시 제공(p.5·p.12), doc16은 Yahoo(p.4), doc17은 Bloomberg 유료(p.8~9)다 | ontology evidence 스키마 · `validate_semantic_layer.py` 선택 필드 | P1-06 | P1-05 동의(출처 신뢰도 C 산정에 사용) · P1-01 동의 | Should | CONFIRMED | doc13 p.10 "We acknowledge BPDPKS (Oil et al. Agency) for collaborating with IPB University" | 신규(일부 evidence note에 "USSEC 지원" 서술만 있음) |
| A-20 | doc10 | **정정: 11/17 검토 Paper 1의 "Table 1 열 정렬 불확실"을 해소한다.** Paranaguá 438·Rotterdam 461·CBOT 415 USD/t(대두)로 확정된다. 개입 시장의 수준 괴리(중국 +215, Rosario −133 대 CBOT, 도출)는 원곡 기준이며, G3 원산지 비교는 ZL이 아니라 원산지 FOB로 한다 | 11/17 검토 정정 메모 · G3 원산지 비교 설계 | P1-04 | P1-02 동의(수출세 할인) · P1-06 주의: 대두유에 수치 전용 금지 | Could | CONFIRMED(표) / INFERENCE(괴리 도출) | doc10 p.7 Table 1 "Mean \| 438 \| 461 \| 415 \| 630 \| 630 \| 282 \| 288" | 정정 대상 |
| A-21 | doc12 | doc12 MinerU 재파싱(1/12쪽만 출력). 재파싱 전까지 doc12 인용은 PDF 쪽 기준 pdftotext 확인본만 쓴다 | `_pdfparse_cache` 파이프라인 · 메모리 pdf-parser 설정 | P1-06 | P1-05 동의(C-04 추출 품질 게이트) | Must | DATA GAP | doc12.md "page 1 of 12"만 존재(3,361 bytes) | 신규 |
| A-22 | doc11·14 | IMF 월간 유지 장기 이력(1990~)과 Decatur·FOB Rotterdam 현물은 ZL 정산가와 **NOT COMPARABLE**이다. G1 유사국면 이력 보강에만 쓰고 G2 학습 표본에는 결합하지 않는다 | G1 analogue 데이터 규칙 · data connector 주석 | P1-06 | P1-01 동의 · P1-04 동의 | Should | NOT COMPARABLE | doc14 p.4 IMF "global prices ... monthly" · doc11 p.6 "Decatur (average wholesale tank price)" | 11/17 검토 rank 8(FRED IMF 백필) 제안. 결합 금지 규칙은 신규 |

---

## 3. 관점 간 이견과 결론

1. **A-01 롤 처리(P1-01 vs P1-06).** P1-06은 대두 논문의 구·신곡 근거를 ZL로 옮기는 것이 추론이라고 지적했다. P1-01은 ZL 7월→신곡 계약 롤에서 스프레드가 실제로 존재한다고 반박했다. **결론**: 롤 플래그만으로는 부족하므로 같은 계약 라벨을 Must로 둔다. 근거 라벨은 INFERENCE로 유지하고, 첫 백테스트에서 롤 구간 오차를 별도로 보고해 실증한다.
2. **A-03 CE-024 evidence(P1-04 vs P1-01).** P1-01은 미국 oilshare를 한국 압착 마진의 대리로 쓰는 것을 경계했다. **결론**: 배경 note로만 넣고 candidate를 유지한다. 한국 실측(관세청 대두·대두유 수입, FAS Seoul)과 병기한다.
3. **A-05 CE-011 분리(P1-02 vs P1-06).** P1-06은 SEM 수치로 엣지 구조를 바꾸는 것에 신중하다. **결론**: 결과노드 분리는 candidate로 등재하고 크기(%)는 인용하지 않는다. AR/BR FOB 시계열을 확보한 뒤 국소투영으로 검증해 승격한다(11/17 검토 결론 유지).
4. **A-11 지평 적용(P1-01 vs 11/17 검토).** 11/17 검토는 "≤20일 정보"만 말했다. 원문은 1주에서 국면 비대칭이 유의하지 않다(p=0.423). **결론**: 팜유 비추종 해석은 h=20/60에 한정한다. h=1/5에서는 175 임계를 맥락 정보로도 약하게 취급한다.
5. **A-16 COT(P1-05 vs C-03 영역).** P1-05는 감성·포지셔닝 해석 문구를 원하지만 부호 불일치 근거가 있다. **결론**: 피처는 허용하고 사용자 대상 해석 문구는 금지한다.

## 4. 반영하지 말아야 할 것과 이유

- **doc12의 수치 크기(+5.49%, 복지 20.8억 달러 등)를 예측값이나 G3 시나리오 폭으로 쓰지 않는다.** 단일 보정연도 비교정학이고 시간 경로가 없다(p.6~10). 방향 사전정보로만 쓴다.
- **doc13의 BCG 분류와 금액 점유율을 사용자 대상 수치로 쓰지 않는다.** 금액 기준이고 팜유기금 지원이며(p.10), cash cow 정의(저성장)와 아르헨 +51% 성장이 서로 모순된다(p.4·p.7). 네덜란드 재수출·네팔 성장(p.5·p.9)도 한국 조달과 무관하다.
- **doc10의 TAR/MTAR·비대칭 ECM을 도입하지 않는다.** 전 시장에서 비대칭이 기각되지 않았다(p.12~15). Bai-Perron 사후 탐지 구조변화일을 피처로 쓰면 미래정보가 유입된다(p.4).
- **doc16 WLMC·doc15 quantile coherency·doc14 TVP-VAR 값을 피처로 쓰지 않는다.** 양측 가우시안 창(260일, doc16 p.8)과 전표본 추정은 비인과적이다. R 패키지(VisualDom·quantspec)도 승인 목록 밖이다(11/17 검토 §(c)와 동일).
- **doc11의 "셰일이 정책 효과를 상쇄"(0.18, 2015)를 현재 상태로 인용하지 않는다.** 표본이 2020에서 끝나 RD 붐 이전이다(p.6). 연간 원유 생산 이동항은 같은 연도 값을 매칭하므로 미래정보다(p.8).
- **doc17의 Bloomberg 애널리스트 기대가격을 구매하지 않는다.** 표본 외 MAPE가 14.48로 선물(0.40)보다 훨씬 나쁘다(p.12 Table 6). WASDE 대체안은 11/17 검토 rank 10에 이미 있다.
- **doc15·doc16 원자료(investing.com, Yahoo)를 재현 목적으로 수집하지 않는다.** 약관 위험이 있고(A-012) G2 타깃과 비교할 수 없다(A-02).
