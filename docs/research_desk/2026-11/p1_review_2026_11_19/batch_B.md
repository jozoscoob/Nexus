# P1 여섯 관점 검토 — Batch B (시장구조·중국/브라질 농기업·무역 네트워크·기후×무역)

- 검토일 2026-11-19 · 저장소 읽기 전용 · 입력: `_pdfparse_cache/corpus/out_mineru/doc{19,21,22,24,25,29,32,33}.md`
- 페이지 표기 `p.N`은 MinerU `<!-- page N of M -->` 기준 PDF 쪽 번호다. Fares(doc21)의 저널 인쇄 쪽은 PDF 쪽 번호에 476을 더한 값이다.
- 적용 관점: P1-01 상품(대두유) · P1-02 지정학·무역 · P1-03 기후 · P1-04 공급망·물류 · P1-05 뉴스·감성 · P1-06 시맨틱·온톨로지
- 중복 확인 범위: `docs/research_desk/2026-11/market_structure_pdf_review_2026_11_17.md`(이하 "11-17 리뷰"; 이 배치 8편 중 doc24를 뺀 7편과 Figueira를 이미 다룸), `src/semantic/ontology.yaml`(CE-001~024, supply_chain, concentration), `entities.yaml`, `methods.yaml`, `references/README.md`·`summaries/`, `memory_archive/2026-08~11`, `src/forecasting/analogue_g1.py`(사례 창 4건).
- 결론부터: 11-17 리뷰가 이미 넓게 훑었으므로 이번 배치의 가치는 **정정**에 있다. 특히 11-17 리뷰의 Must 1순위였던 "한국 원산지 HHI·의존지수(수집분에서 파생만 하면 됨)"는 그대로 구현하면 틀린다(B-01·B-02).

---

## 1. 문서별 3줄 요약

**doc19** · Cordeiro Junior·dos Santos·Silva·Cordeiro, RGSA 19(8), 2025 · SBO 관련성 **상**
- Balassa RCA를 원곡·대두박·대두유별로 브라질과 미국에 대해 계산했다. 데이터는 실제로 1980–2023년이다(p.9). 표 1의 기간 평균 대두유 RCA는 브라질 18.65→10.51, 미국 1.93→0.93이다(p.14).
- 미국 대두유는 2021년부터 RCA<1로 하락하며, 저자들은 바이오연료 내수를 원인으로 든다(p.13). 브라질은 2008년 혼합 의무화 이후 하락했다가, 2020년 의무 완화와 2022/23 압착 확대로 반등했다(p.13).
- 대두유를 직접 분석한 유일한 문헌이다. 다만 연간·금액 기준 지표라 1~60거래일 예측 피처가 되지 못한다. 인과 귀속은 2차 인용(BiodieselBR·USDA)이다.

**doc21** · Fares, J. Agrarian Change 23(3), 2023 · SBO 관련성 **하**(원곡·기업 재무. 대두유는 중국 압착 경로에서 추론)
- 2012–18년 중국 압착 투입 비중이 75%→64%로 떨어져 과잉설비가 드러난다(p.5). 2016년 부채비율은 Beidahuang 81.27%, COFCO 81.01%였다(p.5).
- COFCO 압착능력의 1/3(30/90 Mt)이 해외에 있다(p.12). 2018년 COFCO 브라질·아르헨 대두 수출의 41%가 비중국 행선지로 갔다(p.13).
- 저장소에 이미 같은 판본이 있다(README 58행). 요약 파일은 아직 골격이다. 이번 검토에서 새로 쓸 만한 것은 중국 압착 주체 구분(Sinograin·Jiusan·Hopefull, p.8)뿐이다.

**doc22** · Tixiliski, Brazilian J. Political Economy 44(2), 2024 · SBO 관련성 **하**
- 중국 농업 해외직접투자는 전체 해외직접투자의 1.3%이고, 2016년 279억 달러였다(p.7). 브라질 대두 사슬에 대한 중국 투자는 표 1에 정리돼 있다(COFCO 2.7, ChemChina 1.1, CMPorts 0.92, 단위 십억 달러. p.11).
- CMPorts의 Paranaguá 인수(9.25억)와 CCCC의 São Luís·Babitonga 투자가 나온다(p.13). 저자 스스로 원천 자료끼리 상충한다고 인정한다(p.11).
- 정성 연구다. 항만 서술은 컨테이너 터미널과 벌크 터미널을 구분하지 않는다(B-03).

**doc24** · Gouveris, Open J. Business & Management 12, 2024 · SBO 관련성 **하**
- ABCD 4사의 수직계열화·다각화를 개관한 글이다. 저자 소속이 고등학교(Gymnasium)다(p.1). 매출은 2015년 수치다(p.2).
- "ABCD 70% 지배"를 2차 인용으로 반복한다(p.2·p.5). Noble을 "인도 농기업"으로 잘못 적었다(p.10). 대두 용도 수치도 자기모순이다(p.5 vs p.6).
- 저장소의 `review_ABCD_competitiveness_oilseed_trading.pdf`와 같은 파일이다(11-17 리뷰 확인). 반면교사로만 쓴다.

**doc25** · Ribeiro & da Silva Filho, Contaduría y Administración 69(3), 2024 · SBO 관련성 **중**(1507을 포함하나 CMS 결과가 퇴화)
- UN Comtrade 연간 **금액**(USD) 자료(2000–2019)를 4개 구간으로 나눠 원곡·대두유·대두박을 CMS로 분해했다(p.7). 대두유의 세계성장 효과는 구간마다 100.03~101.82%다. 분포 효과와 경쟁력 효과는 −701,546 대 +701,546처럼 서로 상쇄하는 값으로 퇴화했다(p.16 표 6).
- 대두유 행선지 성장률 표(p.13 표 3)에는 중국 +2219%(2000/04)·−84.96%(2012/15), 이란 −100%(2016/19)가 나온다. 표에서 이란은 "Will"로 오역돼 있다. 혼합의무 2%→10%(2008–2018, p.13)와 EU 대두유 관세(p.19)도 서술된다.
- 대두유 경쟁력에 대한 결론이 서로 모순된다(p.16 "경쟁력 상실" vs p.22 "훨씬 경쟁적"). 표 10·13은 경쟁 수출국을 시장처럼 다뤄 개념부터 틀렸다(p.19·p.21). 11-17 리뷰 §5의 "인용 금지·반면교사" 판정을 유지하고, 정성 결론까지 금지 범위를 넓힌다(B-16).

**doc29** · Wang·Liu·Wang·Li, Foods 12(7), 2023 · SBO 관련성 **하**
- FAOSTAT HS1201 원곡 네트워크 5개 연도(2000–2020)를 분석했다. 교역량은 48.1→165.0 Mt(p.5), 노드 123→161, 엣지 660→1,010이다(p.5 표 2).
- 중국 수입 중 미국 비중은 52.0%(2000)→35.1%(2013)→18.9%(2018)로 내려갔다(p.12). 미국 제거 시 네트워크 효율은 0.302→0.290이다(p.12 표 3).
- 경로 길이 해석이 반대로 적혀 있다(p.3). 효율 변화는 4%에 불과하다. 서술 지표로만 쓴다.

**doc32** · Liu·Zhang·Failler·Wang, Systems 13(4), 2025 · SBO 관련성 **하**
- BACI HS120100 원곡 데이터(2000–2022)에 의존지수(식 1, p.7)와 TERGM을 적용했다. 안정성 계수는 1.527(p<0.001)로 경로의존을 보인다(p.22).
- 2018년 미국 대두 총수출은 −16.2%, 대중 수출은 −72.7%였다(p.16). 2020년 아르헨은 가뭄으로 생산 −7%, 원곡 수출 −33%였다(p.17). 한국은 반주변부(0.097~0.134, p.15)이고, 2018년 이후 지위가 강화됐다고 서술된다(p.16).
- 의존지수 식을 쓰려면 수출국 측 집중도가 필요하다(B-02). 본문에 i/j 오기가 있다(p.7).

**doc33** · Ali·Zhou·Cleary·Xie, Land 11(12), 2022 · SBO 관련성 **하**
- ISI-MIP(CMIP5, RCP2.6/8.5)와 GTAP v9(2011 DB)로 분석했다(p.7). 브라질 단수 극단 충격은 −17.66%, 그때 생산 −13.06%, 수출 −15.25%다(p.6·p.8).
- 중국 국내 생산, 타국 생산, 타국발 수입을 **모두 고정**했다(p.8). 그래서 가격 반응은 모형이 만든 결과다. GTAP 식물성유 부문이 있으나 결과는 보고되지 않았다(p.14).
- 브라질이 대두박·대두유 2위 수출국이라는 언급이 있다(p.2). 2차 서술이므로 인용하지 않는다.

---

## 2. 제안 목록

라벨: CONFIRMED(원문·1차 확인) · INFERENCE(해석·외부지식, 검증 필요) · DATA GAP · NOT COMPARABLE(원곡↔대두유 등 기준 상이)

| ID | 문서 | 제안 내용 | 반영 위치 | 주관 | 다른 관점 의견 | 우선 | 라벨 | 근거 locator(인용 ≤20단어) | 이미 반영 여부 |
|---|---|---|---|---|---|---|---|---|---|
| B-01 | doc29·doc32 (+저장소 실측) | **정정.** 11-17 리뷰 Must #1(한국 대두유 원산지 HHI·상위 2개국 비중)을 산출할 때 분모는 **전 세계 수입 합계**로 하고, `coverage_pct`를 필수 필드로 둔다. 수집국 합계만으로 계산하면 조유는 커버리지 25.2%에 불과해 HHI가 왜곡된다. 조유(1507.10)와 정제유(1507.90)는 따로 계산한다. 정제유는 99.9%가 중국발이라 HHI가 사실상 1이고, 이는 정보가 아니라 구조다. | `metrics.yaml` 신규 지표 후보(KR_SBO_ORIGIN_HHI) · `ontology.yaml supply_chain.customs_coverage_note` 규칙 인용 | P1-04 | P1-01 동의(G3 원산지 손익 전제) · P1-06 동의(합성지수 발행 금지 규칙과 정합) · P1-02 주의(월별 HHI 급변은 화물 1~2건 효과일 수 있음, 월 합계≠화물 규율) | Must | CONFIRMED(커버리지) / INFERENCE(지표 설계) | doc29 p.13 "share of China's soybean imports from the US and Brazil accounted for over 85%"(방법 전이) · ontology.yaml `crude_1507_10_1000 coverage_pct: 25.2` | 11-17 리뷰 (a)#1에서 제안됨 · **미반영**. 커버리지 규칙은 ontology.yaml에 이미 있음 |
| B-02 | doc32 | **정정.** 의존지수 Bimtd=R²·(C_ri/C_pj)에서 C_pj는 **수출국의 행선지 집중도**다. 관세청 자료로는 R_ij와 C_ri만 나오고 C_pj는 나오지 않는다. 따라서 11-17 리뷰의 "수집분에서 파생만"은 틀렸다. ① 1단계는 한국 측 항(R²·C_ri)만 산출하고 ② C_pj는 BACI HS150710/150790 연간치로 보완한다(연 단위 시차, 신규 egress 필요). 그전까지 C_pj는 DATA GAP으로 표기한다. 원문의 "export concentration of country i"는 j의 오기로 주석 처리한다. | 같은 지표 후보 spec · 11-17 리뷰 (c) 승인 목록(BACI) | P1-04 | P1-06 동의(식 정의를 provenance로 보존) · P1-01 주의(연간 C_pj를 월별 피처에 붙이면 as-of 누수 → `available_at` 고정) · P1-02 동의 | Must | CONFIRMED(식) / DATA GAP(C_pj) | doc32 p.7 "C_pj is the soybean export concentration of country i" · 같은 쪽 "standardised Herfindahl–Hirschman Index (HHI) method" | 11-17 리뷰 §7·(a)#1이 "collected, derive only"로 기술 → **정정 필요** |
| B-03 | doc22 | **정정.** "CMPorts가 브라질 최대 항만 Paranaguá를 인수"(p.13)는 과장으로 보인다. 인수 대상은 TCP **컨테이너 터미널**로 판단된다. 11-17 리뷰 (a)#10의 `PORT-PARANAGUA-TCP`를 대두·대두유 수출 노드나 RT-SANTOS-KR에 연결하지 않는다. 등재하더라도 class를 ContainerTerminal로 구분하고 SBO 경로와는 끊는다. 대두유는 액체 벌크 터미널로 선적된다(A-013과 같은 논리). | `ontology.yaml supply_chain.ports` 등재 보류 · `entities.yaml` 후보 메모 | P1-04 | P1-02 주의(중국 자본의 항만 레버리지 논점 자체는 유효하나 대두유 경로와 무관) · P1-06 동의(class 오분류 방지) | Should | INFERENCE(CMPorts 공시로 검증 필요) | doc22 p.13 "acquisition of Brazil's largest port, Paranaguá Port/Paraná State, by China Merchants Ports Holding (CMPorts) for 925 million" | 미등재(TCP·CMPorts 0건). 11-17 리뷰가 노드 등재를 제안했음 → 수정 권고 |
| B-04 | doc19 | CE-023에 **양방향 증거** 1건을 추가한다. 2008년 의무화 이후 BR 대두유 RCA가 하락했고, 2020년 의무 완화 후 수출로 재배치됐다. 2022/23 압착능력 확대도 함께 적는다. 기존 Argus·Alves note(조건부: 압착 증가가 의무 흡수를 넘을 수 있음)를 장기 시계열로 뒷받침한다. CE-022에는 "US 대두유 RCA<1(2021~)"을 추가한다. 인과는 저자 측정이 아니라 2차 인용이므로 candidate를 유지한다. | `ontology.yaml` CE-023·CE-022 `evidence` · `references/README.md` 신규 행 · summaries 신설 | P1-06 | P1-01 동의(US 대두유 수출 점유율=GATS÷PSD 파생은 11-17 리뷰 #4 유지) · P1-03 무관 · P1-04 주의(RCA는 금액 기준이라 물량 해석 금지) | Should | CONFIRMED(서술) / INFERENCE(인과) | doc19 p.13 "with the reduction in the biodiesel mandate, the national crushing industry relocated this product to the international market" · p.13 "from 2021 it was observed the absence of revealed comparative advantages" | 11-17 리뷰 §1 제안 · **미반영**(README·ontology에 doc19 없음) |
| B-05 | doc19 | Kandir법(1996, 1차·반가공 수출품 ICMS 면제)을 원곡 수출 우대의 **정책 레짐 엔티티**로 등재한다(PolicyInstrument, BR). 관련 감시 항목도 둔다. 브라질 조세개혁으로 ICMS가 IBS/CBS로 전환되면(외부지식, 단계 일정 미검증) 원곡 대비 대두유 수출 유인이 달라질 수 있다. | `entities.yaml` 후보 TERM · P1-05 aspect 키워드 후보 | P1-02 | P1-05 동의(저빈도 정책 이벤트로 키워드화) · P1-01 주의(분기~연 단위 효과, G2 피처 아님) · P1-06 주의(엣지 없이 엔티티만 등재) | Could | CONFIRMED(Kandir) / INFERENCE(조세개혁 영향) | doc19 p.10 "exempting primary and semi-elaborate products from the Tax on Circulation of Goods and Services (ICMS)" | 미등재(Kandir·ICMS 0건) |
| B-06 | doc29·doc32·doc19 | G1 analogue **사례 창 후보 2건**. ① 2018 미·중 관세(중국 수입 중 미국 비중 18.9%, 미국 대두 총수출 −16.2%) ② 2018 브라질 트럭 파업(수출 지연, 수입국 신뢰 저하). 현행 `analogue_g1.py`의 창은 2010-11·2012·2020-22·2022-23 네 개뿐이고 2018은 없다. 창 날짜는 `available_at` 기준으로 원문 대조 후 정한다. 중국 보복관세 목록에 HS1507이 포함됐는지는 DATA GAP이다. | `src/forecasting/analogue_g1.py` CASE 후보(승인 후) · `config/market_event_calendar.yaml` | P1-01 | P1-02 동의(2018은 CE-011 실측 창) · P1-04 동의(파업은 비기상 브라질 공급 충격) · P1-06 주의(원곡 수치를 대두유 반응으로 서술 금지) | Should | CONFIRMED(원곡 수치) / NOT COMPARABLE(대두유 반응) / DATA GAP(HS1507 관세) | doc29 p.12 "the share of the US was at an all-time low in 2018 of only 18.9%" · doc32 p.16 "US soybean exports to the world in 2018 decreased by 16.2%" · doc19 p.11 "trucker strike of 2018, which generated great delays in the flow of soybeans" | 11-17 리뷰 (a)#7·#8 제안 · **코드·캘린더 미반영** |
| B-07 | doc32 | **정정.** 2020년 아르헨 원곡 수출 −33%를 대두유 공급 감소로 옮기지 않는다. 아르헨은 압착 수출국이라 원곡 수출이 줄면 압착이 늘 수도 있다. 11-17 리뷰의 신규 후보 엣지 "AR 가뭄 → AR 대두유 수출여력↓"는 PSD AR 대두유 MY2019/20 대 2020/21을 대조하기 전까지 보류한다. 단일 원산지 가뭄 analogue는 이미 사례 ④(2022-23, 로사리오 가동률 45%)가 맡고 있다. | `ontology.yaml` 후보 엣지 등재 보류 메모 | P1-04 | P1-03 주의(ERA5 Córdoba 임계 보정 근거로는 유효) · P1-01 동의 · P1-06 동의(S-1) | Should | NOT COMPARABLE | doc32 p.17 "a 7% reduction in soybean production and a 33% decrease in soybean exports compared with 2019" | 11-17 리뷰 §7이 후보 엣지 제안 → **보류 권고** |
| B-08 | doc33 | **정정.** 11-17 리뷰의 캐비엇("타국발 수입 고정")에 빠진 부분이 있다. GTAP 실험은 **중국 국내 생산과 타국 생산까지 고정**했다. 따라서 세계 공급 반응이 없고 가격 효과는 모형 산물이다. 이 논문에서 가격 탄력이나 가격 크기를 가져오지 않는다. G3 "브라질 공급 충격" 시나리오의 상한 점검용(단수 최소 −17.66%, 생산 전이 약 0.74)으로만 쓴다. G2 밴드에는 넣지 않는다. | 11-17 리뷰 §8 캐비엇 보완 · G3 시나리오 메모 | P1-03 | P1-02 주의(복합위험 서사는 유지) · P1-01 동의 · P1-04 무관 | Should | CONFIRMED(가정) / INFERENCE(전이율 계산) | doc33 p.8 "we fixed China's domestic production, other countries' production, and imports of soybean from other countries" · p.8 "drop by 13.06% and 11.78%, respectively" | 11-17 리뷰 (a)#9가 Background로 등재 · 캐비엇 **보완 필요** |
| B-09 | doc21 | 중국 채널 분리 규율(국가 수요 vs 상업 채널)을 엔티티로 받친다. 압착 주체 **Sinograin(중앙 국유·비축)·Jiusan(Beidahuang 계열)·Hopefull(민영)·Chinatex**를 entities 후보로 등재한다. P1-05는 이 이름들을 SOE/commercial 태그로 매핑한다. COFCO 구매를 국가 비축으로 읽지 않는다는 A-219 규율을 실제로 집행하려면 이 사전이 필요하다. | `entities.yaml` 후보 TERM(owner P1-05) · P1-05 aspect 사전 | P1-05 | P1-02 동의(2025-26 SOE/상업 분리 실측과 정합) · P1-06 동의(source_id·page 보존) · P1-01 주의(중국은 대두유 순수출 국면일 수 있음 → CE-012 선행 점검 유지) | Should | CONFIRMED | doc21 p.8 "central state-owned Sinograin, the local Jiusan (Beidahuang's subsidiary) and the private-owned Hopefull" · p.13 "41% of COFCO's soybean exports from Brazil and Argentina went to the EU, ASEAN" | 규율은 이미 있음(A-219, README 58행, CE-012 note) · 엔티티 **미등재**(Sinograin 등 0건) |
| B-10 | doc19 | P1-05 `LOGISTICS_DISRUPTION_FLAG` 키워드에 **브라질 내륙 물류**를 추가한다(greve dos caminhoneiros, tabela do frete, BR-163 bloqueio). 현행 키워드는 해협·운하(Hormuz·Black Sea·Panama)뿐이다. | `.claude/agents/p105-news-sentiment.md` §2 Stage 2 표(승인 후) | P1-05 | P1-04 동의(브라질 물류는 수출 경쟁력의 유일한 마이너스 동인으로 이미 등재) · P1-06 주의(엣지 신설 없이 플래그만 둠) | Should | INFERENCE | doc19 p.11 "trucker strike of 2018, which generated great delays in the flow of soybeans" · p.12 "shook Brazil's image as a reliable supplier" | 미반영(p105에 strike/truck은 아르헨 항목만) |
| B-11 | doc32 | CE-011의 한국 측 뉘앙스를 evidence note로 단다. 2018 무역전쟁 때 미국이 재배치하면서 한국 등 미국 거래국의 지위가 강화됐다. CE-011 DOWN(미국 수출 여력 과잉)이 한국에 닿는 경로를 서술한다. 원곡 근거이므로 대두유 전이는 표기만 한다. | `ontology.yaml` CE-011 `evidence` | P1-02 | P1-01 주의(한국은 원곡도 압착해 조유를 생산하므로 경로가 간접적) · P1-06 동의(NOT COMPARABLE 표기 필수) | Could | NOT COMPARABLE | doc32 p.16 "the positions of South Korea, India, Canada, and other soybean trading partners of the United States were strengthened" | CE-011에 farmdoc 2018 실측은 있음 · 한국 관점 note **없음** |
| B-12 | doc24·doc21 | 골격 요약 2건을 채운다. ① `review_ABCD_…md`: 분류는 **반면교사**. 70% 주장은 NOT COMPARABLE(이미 ontology에 있음), Noble 국적 오기, 대두 용도 85% 자기모순, 2015년 매출을 적는다. ② `China_2023_financialized…md`: 11-17 리뷰 §2와 B-09 내용으로 채운다. | `references/summaries/` 두 파일 | P1-06 | P1-05 동의(오류 수치가 감성 사전·엔티티로 새지 않게 차단) · 나머지 이견 없음 | Should | CONFIRMED | doc24 p.10 "Noble's agricultural division (an Indian agribusiness company)" · p.5 "85% … processed into soybean meal and oil" vs p.6 "85% was used for feed" | 두 요약 모두 "(미작성)" 골격 상태 |
| B-13 | doc25·doc29·doc32 | **판독 품질 메모.** ① doc25는 처음 변환에서 p.1만 나왔으나 27/27쪽으로 재변환을 마쳤다(해소). ② doc29 MinerU p.10~13은 텍스트가 이중 중첩돼 있어 11-17 리뷰 locator(p.10)와 MinerU(p.11)가 어긋난다(closeness 16→71위). ③ doc32 표 4는 MinerU에서 행이 밀렸다. 안정성 1.52725는 본문 p.22를 정본으로 한다. | `_pdfparse_cache` 재변환 큐 · provenance 주석 | P1-06 | P1-05 동의(추출 품질 게이트) | Could | DATA GAP | doc25 재변환으로 해소 · doc32 p.22 "the estimated coefficient of stability is 1.52725" | 미기록 |
| B-14 | doc29 | 대두유 네트워크를 직접 분석한 원천 후보를 기록한다. Lu 외(2019)는 원곡·대두유·대두박 네트워크를 따로 분석했다. 원곡 네트워크 논문 대신 이 문헌을 확보할지 검토한다(중문, 접근 가능 여부 미확인). | `references/README.md` 확보 후보 메모 | P1-06 | P1-04 동의(대두유 기준 집중도가 필요) · P1-01 주의(네트워크 지표는 피처 금지 원칙 유지) | Could | DATA GAP | doc29 p.2 "analyzed the trade networks of soybean, soybean oil, and soybean meal using complex network analysis" | 미기록 |
| B-15 | doc25 | **정정.** 11-17 리뷰 §5·§7은 doc25 p.6을 "대두유 수출은 원곡보다 환율에 더 민감"(CE-021 뉘앙스)으로 요약했다. 원문은 크기가 아니라 **부호**를 말한다. 헤알 절하가 원곡·대두박에는 유리하지만 대두유 수출량은 초기 이후 줄인다는 것이다(Sonaglio 외 2011 재인용, 저자가 추정한 결과 아님). CE-021 evidence로 넣지 않는다. 대신 "BR 대두유 수출량의 환율 반응 부호는 원곡과 다를 수 있음 — 미검증" note 후보로만 둔다. | `ontology.yaml` CE-021 note 후보(검증 전 등재 보류) | P1-01 | P1-04 동의(한국향 BR 채널은 소형이라 영향 제한) · P1-06 주의(2차 인용이므로 exact_quote와 원출처를 같이 보존해야 함) · P1-02 무관 | Should | INFERENCE | doc25 p.6 "In the case of soy oil, such an effect would bring bad results, reducing its volume exported" | 11-17 리뷰가 "weak" 등급으로 CE-021 후보 제시 · **요약 정정 필요** · ontology 미반영 |
| B-16 | doc25 | **정정·확대.** 11-17 리뷰는 "CMS 수치 인용 금지, 행선지·정책 사실만 사용"으로 판정했다. 재변환본을 보면 **정성 결론도 쓸 수 없다**. ① 대두유 경쟁력 결론이 p.16(상실)과 p.22(우위)에서 정반대다. ② 표 10·13은 경쟁 수출국(AR·US)을 시장 분포 대상으로 넣어 값이 0과 100뿐이다. ③ 분포 효과와 경쟁력 효과가 같은 크기로 상쇄돼 있다. 이는 총변화가 0에 가까운 구간에서 잔차를 백분율로 나눈 결과다. methods.yaml MP-20(CMS 배경, 대기)에 **실패 사례**로 붙이고, 판정 규칙(구간 총변화가 기준치보다 작거나 \|효과\|>1000%면 퇴화로 판정)을 같이 적는다. | `src/semantic/methods.yaml` MP-20 note · `references/summaries/` 신설 시 "반면교사" 분류 | P1-06 | P1-01 동의(G1 기여 해석 대상 아님) · P1-04 동의(행선지 표 3만 서술로 사용) · 나머지 이견 없음 | Should | CONFIRMED(표·본문 모순) | doc25 p.16 표 6 분포 효과 "-701546", 경쟁력 효과 "701546" · p.22 "national soybean oil exports are much more competitive than other countries" | 11-17 리뷰 §5 "Counter-example (method)" 판정 · MP-20 연결 **미반영** |
| B-17 | doc25 | 브라질 대두유 **경쟁 수요처 메모**(P1-04·P1-02). 2000–2019년 주요 행선지는 인도·이란·중국·방글라데시·페루였다. 이란의 2016/19 −100%는 2018년 미국 제재 재개와 시기가 겹친다(외부지식, 인과 미검증). 행선지가 제재 때문에 끊길 수 있는 사례이므로 P1-02 정책 이벤트로 태그한다. 한국은 표에 없다. 수치는 금액 기준이고 2019년에 끝나므로 서술에만 쓴다. 월별 실측은 11-17 리뷰 Must #2(ComexStat NCM 1507)가 대체한다. | P1-04 시장구조 서술 메모 · P1-02 이벤트 태그 후보 | P1-04 | P1-02 동의(제재가 행선지를 바꾸는 사례) · P1-05 주의(표의 "Will" 오역이 엔티티로 새지 않도록 Iran으로 정규화) · P1-06 주의(인과 엣지 금지) | Could | CONFIRMED(표) / INFERENCE(제재 귀속) | doc25 p.13 "Iran registered the most excellent retraction of 100%" · p.13 표 3 "Will … -100.00" | 11-17 리뷰 §5가 행선지 사실을 기록함 · 제재 해석과 Iran 정규화는 **신규** |
| B-18 | doc25 | **정정.** p.19의 EU 대두유 관세(조유 3.8/7.6%, 정제유 6.1/11.4%)는 2008년 문헌의 재인용이다. 게다가 조유는 '공업용 저율', 정제유는 '공업용 고율'로 용도 순서가 뒤바뀌어 있다. "2019 EU–Mercosur 협정으로 관세가 면제돼 교역이 활발해졌다"는 서술도 근거가 없다. 협정 발효 여부와 시점은 별도 확인이 필요하다(DATA GAP). 관세율을 인용하지 않고, 협정 발효는 P1-02 감시 항목으로만 둔다. | P1-02 감시 목록 메모(엔티티·엣지 없음) | P1-02 | P1-01 주의(EU로 물량이 재배치되면 아시아 공급이 빠듯해질 수 있으나 한국 영향은 간접적) · P1-06 동의 | Could | DATA GAP(협정 상태) / CONFIRMED(원문 서술 불일치) | doc25 p.19 "tariffs are around 6.1% if destined for commercial use and 11.4% if imported for industrial use" | 11-17 리뷰 §5가 관세율을 사실로 기재 → **인용 보류 권고** |

---

## 3. 관점 간 이견과 결론

1. **원산지 집중도 지표(B-01·B-02).** P1-04와 P1-01은 Must로 본다. P1-02는 월별 변동이 화물 단위 잡음일 수 있다고 주의를 준다. **결론**: 분기 이동합계를 기본 단위로 하고, coverage_pct와 C_pj DATA GAP 표기를 필수로 둔다. 11-17 리뷰의 "파생만 하면 됨"은 철회한다.
2. **중국 자본의 브라질 항만(B-03).** P1-02는 레버리지 노드로서의 가치를 인정하자는 쪽이고, P1-04는 대두유 경로와 무관하다고 본다. **결론**: 레버리지 논점은 P1-02 서술 메모로만 남긴다. 온톨로지 port 노드와 SBO route는 연결하지 않는다.
3. **2018 analogue(B-06).** P1-02와 P1-04는 창 추가에 찬성한다. P1-01은 창 배지 규칙(창 안 에피소드 3건 이상)에 걸려 2018 창이 배지를 받지 못할 수 있다고 본다. **결론**: 창 등재와 배지 판정을 분리한다. 창은 사건 서술용으로 등재하고, 배지는 기존 규칙을 그대로 적용한다.
4. **기후×무역 논문(B-08).** P1-03은 입력에서 거부하고, P1-02는 복합위험 서사를 살리자는 입장이다. **결론**: 11-17 리뷰의 결론(Background)을 유지하되 캐비엇을 보완한다. G3 상한 점검에만 쓴다.
5. **아르헨 가뭄의 대두유 전이(B-07).** P1-03은 임계 보정 근거로 쓰고 싶어 하고, P1-04는 원곡→대두유 전이를 금지하자는 쪽이다. **결론**: 기후 임계 보정에는 쓰되 SBO 엣지는 보류한다.

---

## 4. 반영하지 말아야 할 것과 이유

- **doc25 CMS 효과값 전부와 대두유 경쟁력 결론**: 분포 효과와 경쟁력 효과가 ±701,546처럼 상쇄되는 퇴화 값이다(p.16). 경쟁력 결론은 p.16과 p.22에서 정반대다. 재변환본(27/27쪽)으로 11-17 리뷰의 "Do not use" 판정을 재확인했고, 정성 결론까지 금지 범위를 넓힌다(B-16). EU 관세율(p.19)과 환율 반응 서술(p.6)도 2차 인용이므로 수치·부호 모두 인용하지 않는다(B-15·B-18).
- **네트워크 중심성·핵심계수·TERGM 계수를 G2 피처로 쓰는 것**: 연간·원곡 기준이라 쓸 수 없다. TGL 2023 전례(지속성 기준선 우위)와 ontology `palm_origin_concentration.note`의 금지 원칙도 같은 결론이다. doc32 안정성 1.527은 지속성 기준선을 지지하는 서술 근거로만 쓴다.
- **doc29의 "closeness = 교란 저항력" 해석과 경로 길이 서술**: 저자 해석일 뿐이고, p.3의 "higher average path length means higher transmissivity efficiency"는 정의와 반대다.
- **doc33의 가격·후생 크기**(중국 가격 +0.24%, 후생 −45.3억 달러): 생산과 타국 수입을 고정한 데서 나온 산물이다(p.8). CMIP5·2030 지평이라 1~60거래일 예측과 무관하다.
- **doc24의 모든 수치**(ABCD 70%, 2015년 매출, Noble 국적, 대두 용도 85%): 2차 인용, 오기, 자기모순이 섞여 있다. 70%는 ontology에서 이미 NOT COMPARABLE이다.
- **doc22의 투자 총액과 COFCO "브라질 처리 1.4 Mt/년"**(p.12): 저자도 원천 상충을 인정했다(p.11). 단일 출처이고 회사 공시와 대조되지 않았다.
- **doc32 "Big Four의 중국 대두 공매도(2003)" 사건**(p.15): 논쟁적 서사다. analogue 창이나 이벤트 캘린더에 넣지 않는다.
- **RCA 수준값을 모형 입력으로 쓰는 것**(doc19): 연간·금액 지표다. 저자도 관세·보조금·환율 왜곡을 반영하지 못한다고 인정했다(p.8). 증거 서술로만 쓴다.
- **원곡 수치를 대두유 수치처럼 인용하는 것**(doc29·doc32·doc33 전반): 이 배치의 대두유 1차 수치는 doc19뿐이다. R-045의 "원곡·복합체 수치를 대두유로 인용 금지" 규율을 그대로 따른다.
- **이번 배치로 새 인과엣지를 등재하는 것**: 모든 제안은 evidence, 엔티티, 지표 spec 수준이다. 엣지 승격은 P1-06 검증과 S-1(Cause→Mechanism→Price)을 거쳐야 한다.
