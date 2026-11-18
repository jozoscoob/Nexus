> 원문 PDF는 저작권상 로컬 보관(`data/raw/Market Structure (Production & Distribution)/PDF/Market Structure/` — git 제외). 본 요약은 쪽 locator가 붙은 사실과 25단어 이하 원문 인용만 담는다. 포르투갈어 본문 · 전문가 관점 5종(P1-04·P1-06·P1-02·C-04·C-03) 검토 · 2026-11-18 반영(R-045).

# Alves et al. (2022) 대두 생산사슬 구조와 생산자→소매 가격전이 — 정밀 검토

검토일 2026-11-17 · 읽기 전용 검토(저장소 무수정) · locator `p.N` = 추출 텍스트 `--- page N ---`(PDF 쪽) · 포르투갈어 인용은 줄바꿈 하이픈만 복원(예: positiva-mente → positivamente)했고, 그 외에는 원문 그대로다.
선행 검토: `docs/research_desk/2026-11/market_structure_pdf_review_2026_11_17.md` "Paper 6 — Alves et al."(l.1288~1327). 그 검토의 정정 사항은 §3 끝의 "선행 검토 정정"에 모았다.

## 1. 서지

| 항목 | 내용 | locator |
|---|---|---|
| 저자 | Lucilio R. A. Alves(교신), André L. R. Sanches, Andréia C. de O. Adami, Geraldo S. de C. Barros, Mauro Osaki. 전원 ESALQ/USP 소속이며 교신저자는 CEPEA 소속 | p.1 |
| 학술지 | *Desenvolvimento em Questão* (Editora Unijuí, ISSN 2237-6453), Ano 20, n. 58, 2022, e12723, 1–24쪽 | p.1 |
| DOI | 10.21527/2237-6453.2022.58.12723 · 접수 2021-09-09 · 게재 승인 2022-03-03 · CC-BY 4.0 | p.1, p.24 |
| 메타 충돌 | p.1 하단에 "Ano 16 • n. 45 • out./dez. • 2018"이라는 템플릿 잔존 문구가 있다. 이는 DOI(2022.58)와 모순되므로 2022·n.58을 정본으로 본다(C-04) | p.1 |
| 자료 기간 | 2000-01~2018-12(월평균). 예외: 가공 수산물·IPCA 수산물은 2008-01부터, 바이오디젤·도매 경유·IPCA 경유는 2011-01부터. 식 1·2·3·4·6·7은 2000~2018, 식 5는 2008~2018, 식 8은 2011~2018 | p.7, p.10 |
| 출처 | FGV-Ibre(접근 2019-12-15), CEPEA-ESALQ(접근 2019-02-26), IBGE IPCA(접근 2020-04-13). 구조 통계: Conab(2020-04-22), USDA PSD(2020-04-07) | p.7, p.23 |
| 방법 | DF-GLS 단위근 검정 → Johansen 공적분 검정(λmax·trace) → 구조 VEC(1시차, 동시점 관계 행렬은 시장구조에 근거해 제약) → 누적 충격반응 탄성치(12개월)와 예측오차 분산분해(FEVD). 소프트웨어 WinRats. 모든 계열은 기준월=100으로 지수화한 뒤 자연로그를 취했고, **명목값이며 디플레이트하지 않았다** | p.6–7, p.10–11 |

## 2. 핵심 주장

- 브라질 대두 생산은 2000/01~2019/20 동안 연 6.25% 성장했다. 면적 +4.53%/년이 주도했고 단수는 +1.64%/년에 그쳤다(Conab) — p.2
- **압착(가공)은 2000~2019년 연 3.47%로 생산 증가 속도에 크게 못 미쳤다. 잉여는 주로 원두로 수출되어 수출 물량은 연 9.62% 늘었다** — p.2
  > "Entre os anos 2000 e 2019 o processamento de soja no Brasil cresceu a uma taxa de 3,47% a.a., bem abaixo do ritmo de produção." (p.2)
- 2010/11~2019/20 원두 수출은 국내 생산의 약 60%이며, 여기에 farelo·óleo 형태의 수출이 추가된다. 저자는 대외 거래 구조를 Lei Kandir(1996)와 연결한다 — p.2–3
- 세계 대두의 약 2/3가 grão·farelo·óleo 형태로 국가 간에 거래되고, 브라질도 같은 비율이다. 따라서 브라질은 최대 생산국이면서도 **가격수용자**이며, 국내가는 CBOT를 반영한다 — p.4
- 국내 원두 소비가 생산에서 차지하는 비중은 60%(2001–05)에서 41.5%(2014–18)로 낮아졌다. 반면 대두박 국내 흡수는 약 38%에서 52% 초과로 올랐다(USDA) — p.8
- **조유(óleo bruto)의 국내 소비 비중은 약 58%(2001–05)에서 82%(2014–18)로 올랐다** — p.8
  > "para o óleo bruto, o consumo interno passou a representar 82% da produção nacional de 2014 a 2018, enquanto absorvia cerca de 58%" (p.8)
- 압착 수율은 톤당 대두박 약 78%, 조유 19.2%다(Alves et al. 2018; USDA). 국내 소비 중 약 2.5%는 종자다 — p.8
- 조유의 용도는 식용(정제 → 레시틴 부산물)과 바이오디젤(글리세린 부산물) 두 갈래다 — p.8, p.21
- 혼합의무 경로: 2005년 B2 허용 → 2008년 의무화 → 2010년부터 5% → 2014년 6%, 이어 7% → **2017년 3월 8% → 2018년 3월 10%** → 2019년 11% → 2020년 12% — p.17
  > "em março de 2018, passou a vigorar a mistura de 10%. Mistura de 11% foi registrada em 2019 e, em 2020, de 12%." (p.17)
- **브라질 바이오디젤의 약 70%가 대두유 기반이다.** 초기 구매는 ANP가 맡으며, 저자는 이를 "정부 개입 시장"으로 규정한다 — p.17
  > "Do total de biodiesel produzido no Brasil, cerca de 70% têm como base o óleo de soja." (p.17)
- 대두 가격 충격은 8개 소매 품목 모두에 같은 방향(+)으로 전이된다. 강도 순서는 대두유 > 돼지고기 > 닭고기 > 쇠고기 > 경유 > 수산물 > 계란 > 마가린이다 — p.1, p.21–22
  > "o óleo de soja no mercado varejista é o que mais absorve impactos de preços da soja em grão" (p.17)
- 육류 소매가는 대두가 아니라 자체 가격·도매 육가·생축가에 주로 의존한다(FEVD). 생축가 FEVD의 85~90%는 자체 변수에서 나오지만, 이 수치는 논문에 제시되지 않았다 — p.16
- 계열은 명목값이다: "Todas as séries foram consideradas em valores nominais e, portanto, não foram deflacionadas" — p.7

## 3. 수치 원장

| 항목 | 값 | 단위 | 기간 | locator | 라벨 |
|---|---|---|---|---|---|
| 대두 생산 증가율 | 6.25 | %/년 | 2000/01–2019/20 | p.2 | CONFIRMED (1.0453×1.0164=1.0624로 면적·단수와 정합) |
| 면적 증가율 | 4.53 | %/년 | 2000/01–2019/20 | p.2 | CONFIRMED |
| 단수 증가율 | 1.64 | %/년 | 2000/01–2019/20 | p.2 | CONFIRMED |
| 압착 증가율 | 3.47 | %/년 | **역년** 2000–2019 | p.2 | CONFIRMED · 생산(작물연도)과 기간 기준이 달라 엄밀 비교는 NOT COMPARABLE |
| 원두 수출 물량 증가율 | 9.62 | %/년 | 2000–2019 | p.2 | CONFIRMED |
| 원두 수출/생산 | ≈60 | % | 2010/11–2019/20 | p.2 | CONFIRMED |
| 세계·브라질 교역 비율(grão+farelo+óleo) | ≈2/3 | % 생산 | 미상 | p.4 | CONFIRMED · 기간 DATA GAP |
| 원두 국내 소비/생산 | 60 → 41.5 | % | 2001–05 → 2014–18 | p.8 | CONFIRMED (USDA) |
| 대두박 국내 흡수/생산 | ≈38 → >52 | % | 2001–05 → 2014–18 | p.8 | CONFIRMED |
| **조유 국내 흡수/생산** | **≈58 → 82** | % | 2001–05 → 2014–18 | p.8 | CONFIRMED · USDA PSD는 대두유를 조유·정제유로 나누지 않으므로 "óleo bruto"는 저자의 표기다 |
| 조유 수출 여력 비중(1−흡수) | ≈42 → ≈18 | % | 同 | p.8에서 계산 | INFERENCE (재고 변동·수입을 무시한 계산) |
| 종자용 비중 | ≈2.5 | % 국내 소비 | 미상 | p.8 | CONFIRMED |
| 압착 수율 대두박 / 조유 | 78 / 19.2 | % 톤당 | 평균 | p.8 | CONFIRMED (출처 평균) · 합 97.2%(나머지는 손실·껍질 — INFERENCE) |
| 혼합률 B2 허용 | 2 | % | 2005 | p.17 | CONFIRMED |
| B2 의무화 | 2 | % | 2008(월 미기재) | p.17 | CONFIRMED · 월 DATA GAP |
| B3·B4 단계 | — | — | 2008–09 | 논문 누락 | DATA GAP (실제로 있었던 단계로 알려져 있으나 ANP 원문 대조 필요) |
| B5 | 5 | % | "desde 2010" | p.17 | CONFIRMED · 월 DATA GAP |
| B6 → B7 | 6 → 7 | % | 2014(월 미기재) | p.17 | CONFIRMED · 월 DATA GAP |
| B8 | 8 | % | **2017-03** | p.17 | CONFIRMED |
| B10 | 10 | % | **2018-03** (B9 언급 없음) | p.17 | CONFIRMED |
| B11 / B12 | 11 / 12 | % | 2019 / 2020(월 미기재) | p.17 | CONFIRMED · 자료 기간(~2018) 밖 |
| 바이오디젤 원료 중 대두유 | ≈70 | % | **기간 미기재** | p.17 | CONFIRMED · 기간 DATA GAP |
| 바이오디젤 물량·SBO 투입 톤수 | — | — | — | — | DATA GAP (논문에 없음) |
| 탄성: 대두 10% → IPCA 대두유 | +2.0 (탄성 0.20) | %, 12개월 누적 | 2000–2018 | p.17; Fig.7 | CONFIRMED (명목·브라질 소매) |
| → IPCA 돼지고기 | +1.7 (0.17) | 同 | 2000–2018 | p.13; Fig.3 | CONFIRMED |
| → IPCA 닭고기 | +1.2 (0.12) | 同 | 2000–2018 | p.11; Fig.2 | CONFIRMED |
| → IPCA 쇠고기 | +0.8 (**0.08**) | 同 | 2000–2018 | p.13; Fig.4 | CONFIRMED · 원문이 "0,08%"(1% 충격 기준)와 "0,8%"(10% 기준)를 한 문장에 섞어 씀 → 단위 혼동 주의 |
| → IPCA 경유 | +0.5 (0.05) | 同 | **2011–2018** | p.20; Fig.9 | CONFIRMED · 표본 짧음 |
| → IPCA 수산물 / 계란 / 마가린 | +0.28 / +0.25 / +0.16 | 同 | 2008–18 / 2000–18 / 2000–18 | p.16, p.17 | CONFIRMED |
| FEVD IPCA 대두유(3기) 대두/조유/정제유/자체 | 8.87 / 24.08 / 21.34 / 45.71 | % | 2000–2018 | p.19 표 8 | CONFIRMED (12기 8.87/24.10/21.33/45.70; 1기 2.58/5.70/5.77/85.95) |
| FEVD IPCA 마가린(3기) 대두/조유/정제유/도매/자체 | 0.30 / 0.91 / 2.36 / 16.84 / 79.60 | % | 2000–2018 | p.19 표 9 | CONFIRMED |
| FEVD IPCA 경유(3기) 대두/조유/바이오디젤/경유/자체 | 0.02 / 0.90 / 3.96 / 49.51 / 45.61 | % | 2011–2018 | p.20 표 10 | CONFIRMED · 12기 대두+조유+바이오디젤 = 0.51+3.73+3.99 = 8.23%("8% 초과" 서술과 정합) |
| FEVD IPCA 닭(3기) 대두/사료/생계/도매/자체 | 0.66 / 5.09 / 40.95 / 24.98 / 27.69 | % | 2000–2018 | p.14 표 3 | CONFIRMED |
| FEVD IPCA 돼지(3기) 대두/생돈/도매/자체 | 4.83 / 38.37 / 14.39 / 40.59 | % | 2000–2018 | p.14 표 4 | CONFIRMED (대두 비중이 육류 중 최대, 12기 5.14) |
| FEVD 수렴 시점 | 3–5기에 사실상 고정 | 월 | — | 표 3–10 | CONFIRMED (전이가 약 1분기 안에 끝남) |

**불일치·주의 플래그(원문 대조 결과)**
1. **"Ambos os testes"(p.10) 주장과 표 2 불일치.** 닭고기 λmax r=0 통계량 36.29 < 5% 임계 40.30, 수산물 26.09 < 34.40이므로 λmax로는 공적분이 없다. trace만 기각한다. 대두유 식은 λmax 45.91 > 33.24(1%)로 1개, trace는 5% 기준 2개 / 1% 기준 1개다.
2. **DF-GLS(표 1) I(1) 판정이 경계선이다.** 1차 차분 상수 모형에서 닭(-0.678)·육계육(-1.108)·돼지고기(-0.899)·IPCA 닭(-0.875) 등은 5% 임계(-1.94)에서 기각되지 않는다. 추세 모형에서도 상당수가 1% 임계(-3.48)를 넘지 못한다. 반대로 수준변수 추세 모형에서 생돈 -3.851과 돼지고기 -3.634는 1%에서 단위근을 기각한다(추세정상 가능). 대두유 사슬(대두 -4.37/-4.58, 정제유 -2.597/-3.511, IPCA 대두유 -3.281/-3.680)은 상대적으로 양호하나, 조유(-2.564 vs 1% 임계 -2.57)는 경계다.
3. 표 2의 "p − r" 열이 식별 변수 수와 맞지 않는다. 식 1은 변수 6개인데 7부터, 식 5는 5개인데 7부터, 식 6은 4개인데 5부터 시작한다. 결정항이 포함된 것인지 불명이며 해석에 주의해야 한다.
4. 초록(p.1)은 분석 품목에 "biodiesel"을 넣었지만 본문(p.4, p.10)의 소매 품목은 **óleo diesel(IPCA 경유)**이다.
5. p.16은 "preços a jusante ... com destaque para o preço da soja"라고 썼으나 대두는 상류(montante)이므로 용어 오기다.
6. 그림 2–9는 "1 desvio padrão" 충격, 그림 10은 "1%" 충격, 본문은 "10%"로 서술한다. 탄성치는 본문 수치만 인용한다(그림에는 판독 가능한 숫자가 없다).
7. 혼합의무 경로는 B3/B4/B9를 생략했고 2019·2020 단계는 자료 기간 밖이다. 공포일과 시행일도 구분하지 않는다(§5 C-04).

**선행 검토(2026-11-17 Paper 6) 정정**
- (정정) "Domestic consumption share includes stocks change per USDA definitions"는 부정확하다. USDA PSD의 국내 소비는 재고 변동과 별도 항목이다. 정확히는 "1 − 국내 흡수 비중 ≠ 수출 비중(재고 변동·수입 차이)"이다.
- (정정) "CEPEA/ESALQ crude SBO (São Paulo) daily, the authors' own series" — 논문에는 계열과 출처(FGV-Ibre vs CEPEA)의 대응이나 산지·일별 여부가 **명시되어 있지 않다**(p.7) → DATA GAP. 사용된 대두 가격도 "mercado de lotes(produto limpo e seco)"(p.6)라고만 되어 있고 지역은 미기재다.
- (보완) 계절성 "3–5월 저가·11–1월 고가"는 Pino(2014)의 **원두 생산자가격**(1950–2014) 인용이다(p.6). 저자 추정이 아니며 SBO에 이전하면 안 된다.
- (보완) 혼합 경로는 논문 자체가 B3/B4/B9를 누락한 것이다. 선행 검토는 이를 표시하지 않았다. 수치 자체(2.0/1.7/1.2/0.8/0.5/0.28/0.25/0.16, FEVD 45.7/24.1/21.3/8.9)는 모두 원문과 일치한다.
- (누락 보완) 위 플래그 1–6(검정 불일치·메타 충돌·초록 오기)은 선행 검토에 없던 항목이다.

## 4. 대두유(SBO) 관련성 판정

- **SBO 직접(oil-specific)**: 조유 국내 흡수 58→82%(p.8), 조유 수율 19.2%(p.8), 혼합의무 단계(p.17), 바이오디젤 원료 중 SBO 약 70%(p.17), ANP 개입 시장(p.17), 식 6(대두→조유→정제유→IPCA 대두유) 탄성 0.20과 FEVD(p.17, p.19), 식 7·8의 조유 경로.
- **SBO 간접(공급량 결정 변수)**: 압착 증가율 3.47%/년(p.2). 브라질 대두유 산출량은 압착 물량×수율이므로 TERM-033 해석 규칙과 정합한다.
- **원두(bean) — SBO로 이전 금지**: 생산·면적·단수 증가율, 원두 수출 9.62%/년과 60%, 가격수용자·CBOT 연동(p.4), 계절성(p.6), Lei Kandir(p.3).
- **범위 밖**: 육류·계란·수산물·마가린 소매 탄성(브라질 소비자물가). 한국 수입 CIF와는 다른 가격 층위다(NOT COMPARABLE).
- **주의**: 식 6의 "óleo de soja"는 브라질 국내 조유 **명목 BRL** 가격이다. 국제 SBO(CBOT ZL, FOB Paranaguá)와 같은 계열로 취급하면 안 된다.

## 5. 전문가 관점 검토

**P1-04 공급망·물류.** *채택*: 2000–2019년 "압착 3.47%/년 vs 원두 수출 9.62%/년" 구조와 "조유 국내 흡수 82%"는 브라질발 대두유 수출 가용성이 구조적으로 얇다는 공급망 사실로 쓴다. 한국의 원산지 다변화(브라질 조유 비중) 해석의 배경이 된다. *주의*: 원두 수출 확대는 중국 등 수입국 압착으로 착유 위치를 옮길 뿐이므로 세계 대두유 공급 총량의 축소가 아니다. 따라서 브라질 FOB 프리미엄·원산지 가용성 축이지 국제가 축이 아니다. 자료는 2018년에 끝나며, 이후 브라질의 압착 확장(CE-023 기존 근거: COFCO 확장, Argus 2026 수출 2.0 Mt 전망)이 이 구조를 약화시켰을 수 있다. *근거*: p.2, p.8, ontology CE-023 기존 evidence note.

**P1-06 시맨틱 레이어·온톨로지.** *채택*: CE-023의 "내수 흡수 증가 → 수출 잉여 축소" 구간에 정량적·구조적 근거를 처음 제공한다(현재 근거는 뉴스·업계 전망뿐). *주의*: 논문은 흡수 증가를 바이오디젤 때문이라고 **인과 검정하지 않았다**. 흡수 상승과 혼합 B2→B10이 시기상 겹치는 동행 근거일 뿐이다. 결과 노드 SBO_INTL_PRICE는 전혀 검증되지 않았으므로 status는 candidate를 유지해야 한다. 별도 발견으로, **CE-023의 entity_terms에 TERM-071(B40)이 들어가 있는데 브라질 B15 엣지와 맞지 않는다.** TERM-068(Biodiesel Blend Mandate)과 TERM-065(Biodiesel Feedstock)로 교체를 권고한다. 신규 TERM은 불필요하다. TERM-068의 해석 규칙("Bxx의 기준·시행일·적용지역 저장")이 이미 이 개념을 포괄한다. *근거*: p.8, p.17, entities.yaml TERM-065/068/071.

**P1-02 지정학·정책.** *채택*: 브라질 혼합의무는 행정 결정(CNPE·ANP)으로 단계적으로 바뀌는 정책 변수이고, 원료의 약 70%가 SBO라서 정책 → 대두유 산업수요 경로가 직접적이다. ANP 경매 구조(정부 개입 시장)는 바이오디젤 가격이 시장 청산가가 아니라는 점에서 경유 탄성(0.05)이 작은 이유의 맥락이 된다. *주의*: 70%는 기간이 명시되지 않은 단일 값이므로 연도별 ANP 원료 통계로 대체해야 한다. ANP 경매 체제는 논문 이후 바뀌었다고 알려져 있으므로(외부 지식, 미검증) 2018년 이전 구조를 현재에 적용하면 안 된다. Lei Kandir(수출 ICMS 면제)는 원두 수출 편향의 정책 배경으로 언급될 뿐 방향성이 검정되지 않았다(INFERENCE). *근거*: p.3, p.17.

**C-04 문서 인텔리전스.** *채택*: 텍스트로 서술된 탄성치와 표 1–10은 판독 가능하며 본문 서술과 반올림 수준에서 일치함을 확인했다(표 8·10 합계 검산 포함). *주의*: (i) **명목·비디플레이트** 계열이므로(p.7) 탄성은 인플레이션 전이를 포함하고 실질 전이로 읽으면 안 된다. (ii) **as-of**: 혼합 단계는 "passou a vigorar"(시행) 기준으로 서술된다. 공포일(법률·CNPE 결의)과 시행일 사이에는 수개월의 간격이 있다. 예를 들어 B10은 2016년 법률 일정상 2019년이었으나 2017년 말 CNPE 결의로 2018-03에 앞당겨진 것으로 알려져 있다(외부 지식, ANP/CNPE 원문 대조 필요). 계열화할 때 `published_at`(available_at 기준)과 `effective_from`(레짐 더미 기준)을 분리 저장해야 D-023 누수 규율에 맞는다. (iii) 구조 통계는 USDA PSD 2020-04-07 빈티지이므로 이후 개정으로 값이 달라질 수 있다. (iv) p.1의 2018 템플릿 메타와 Figure 1(p.9 회전 텍스트)은 판독할 수 없다. *근거*: p.1, p.7, p.17, p.23.

**C-03 데이터 과학.** *채택*: FEVD가 3–5기에 수렴한다는 사실은 브라질 국내 대두 → 조유 → 소매 명목 전이가 약 1분기 안에 끝난다는 정성 근거다. AM-05(국소투영) 진단 결과를 해석할 때 대조 사례로 쓸 수 있다. *주의*: 1시차 VEC, 선험적 동시점 제약, λmax/trace 불일치(닭·수산물), I(1) 경계 판정, 짧은 경유 표본(96개월)을 감안하면 탄성 수치의 신뢰구간이 제시되지 않은 점은 치명적이다(IRF 오차대 없음). **탄성은 한국 CIF·국제 SBO로 이전할 수 없다.** 국가·가격 층위·통화(BRL 명목)가 모두 다르다. CE-023의 lag(20–120 거래일) 근거로도 쓰면 안 된다. 이 논문이 측정한 것은 "의무 → 국제가"가 아니라 "원두 → 국내 소매" 시차다. methods.yaml에는 '배경' 선례로만 등재할 수 있고 AM 신설(VEC 기법 채용)은 근거가 부족하다. 우리 스택은 VEC를 쓰지 않으며 승격 게이트(c03 §4)를 거친 비교도 없다. *근거*: p.10–20, 표 1·2.

## 6. 시맨틱 레이어 반영안 (YAML 초안, 미적용)

(a) CE-023 evidence 추가. C7 필수 필드는 source_type/ref/locator이며, exact_quote와 note는 부가 필드다.
```yaml
    - source_type: research_doc
      ref: docs/research_desk/references/summaries/Alves_2022_cadeia_soja_transmissao_precos.md
      locator: "Alves et al. 2022, Desenvolvimento em Questão 20(58) e12723, p.8 — 조유 국내 흡수 58%(2001–05)→82%(2014–18), USDA PSD 2020-04 빈티지"
      exact_quote: "para o óleo bruto, o consumo interno passou a representar 82% da produção nacional de 2014 a 2018, enquanto absorvia cerca de 58%"
      note: "구조적 동행 근거(인과 미검정) — 흡수 상승기가 B2(2008)→B10(2018-03)과 겹침. 1−흡수=수출여력 ≈42%→≈18%는 INFERENCE(재고·수입 무시). 결과 노드(국제가)는 미검증 → candidate 유지"
    - source_type: research_doc
      ref: docs/research_desk/references/summaries/Alves_2022_cadeia_soja_transmissao_precos.md
      locator: "同 p.17 — 혼합 단계(2005 B2 허용·2008 의무·2010 B5·2014 B6→B7·2017-03 B8·2018-03 B10·2019 B11·2020 B12) · 원료 SBO ≈70%(기간 미기재) · ANP 개입 시장"
      exact_quote: "Do total de biodiesel produzido no Brasil, cerca de 70% têm como base o óleo de soja."
      note: "의무→SBO 산업수요 경로의 원료 비중 근거. B3/B4/B9 누락·시행일 기준 서술(공포일 미기재) — 단계 시계열은 ANP/CNPE 원문으로 대조 후 사용. 70%는 연도별 ANP 원료 통계로 대체 권고(DATA GAP)"
```
아울러 `entity_terms: ["TERM-071", "TERM-033"]`를 `["TERM-068", "TERM-065", "TERM-033"]`로 바꿀 것을 권고한다(B40 불일치 정정, P1-06 서명 필요).

(b) 신규 후보 엣지 — **선택**. 국제가 축이 아닌 원산지 가용성 축으로 한정한다.
```yaml
- edge_id: CE-0XX   # 열람 시점 최종 번호 CE-024 → 차기 CE-025 확인 후 부여
  label_ko: "브라질 압착 증가가 원두 수출 증가에 뒤처짐 → 브라질발 대두유 수출 여력 축소 → 한국 조유 원산지 대체(아르헨·미국) 압력"
  category: "시장 구조"
  cause: {node: BR_CRUSH_GROWTH_LAG_VS_BEAN_EXPORT, entity_terms: ["TERM-033"]}
  mechanisms:
    - {node: BR_SBO_DOMESTIC_ABSORPTION_SHARE_UP, relation: CAUSES_MECHANISM}
    - {node: BR_SBO_EXPORTABLE_SURPLUS_DOWN, relation: PROPAGATES_TO}
  outcome: {node: KR_SBO_ORIGIN_MIX, relation: MECHANISM_AFFECTS_OUTCOME}
  direction: CONTEXT     # 착유지 이전일 뿐 세계 공급 총량 감소 아님 — 국제가 방향 부여 금지
  lag_basis: "연 단위 구조 변수(작물연도). 일·주 단위 신호 아님"
  indicators: ["PSD_SOY_CRUSH"]
  status: candidate
  evidence:
    - source_type: research_doc
      ref: docs/research_desk/references/summaries/Alves_2022_cadeia_soja_transmissao_precos.md
      locator: "p.2 — 압착 3.47%/년 vs 원두 수출 9.62%/년(2000–2019) · p.8 — 조유 흡수 82%"
      exact_quote: "Entre os anos 2000 e 2019 o processamento de soja no Brasil cresceu a uma taxa de 3,47% a.a., bem abaixo do ritmo de produção."
      note: "2018~2019년까지의 레짐 사실. 이후 브라질 압착 확장(CE-023 note·Argus 2026)으로 약화 가능 — 등록 전 PSD 최신값으로 재확인. CE-023과 중복 우려 시 별도 엣지 대신 CE-023 note로 흡수하는 대안이 더 보수적"
```

(c) 엔티티·지표.
- 신규 TERM은 **추가하지 않는다**. TERM-068이 이미 이 개념을 포괄한다.
- 대신 **지표 계열** `BR_BIODIESEL_BLEND_PCT`(계단 함수)를 지표 레지스트리 후보로 둔다.
  - 필드: `pct`, `legal_instrument`(Lei/CNPE 결의 번호), `published_at`, `effective_from`, `source: ANP/CNPE`, `label`
  - 이 논문의 값은 seed 대조용으로만 쓴다. 월이 확인된 값은 2017-03(B8)과 2018-03(B10)뿐이고 나머지 월은 DATA GAP이다.
  - 모델 입력의 available_at은 `published_at`으로 한다.
- CEPEA 조유 가격원은 이미 DS-07의 free_alternative(후보, 미구현)에 있다. 이 논문은 해당 계열의 사양(산지·일별·세금 포함 여부)을 밝히지 않으므로 **신규 엔티티나 DS 근거로 삼지 않는다.**

(d) methods.yaml 선례(등재 시 references에 원문 PDF와 요약 md를 둔 뒤 C13 통과).
```yaml
  - id: MP-19
    title: 구조 VEC 기반 대두→소매 가격전이(브라질, 명목)
    authors_year: Alves·Sanches·Adami·Barros·Osaki (ESALQ/USP·CEPEA), Desenvolvimento em Questão 20(58), 2022
    ref: summaries/Alves_2022_cadeia_soja_transmissao_precos.md
    method: DF-GLS·Johansen → 동시점 제약 구조 VEC(1시차) → 12개월 누적 충격반응 탄성·FEVD
    target_goal: ['배경']
    verdict: 배경
    applies_to: ['AM-05']
    constraints:
      - '브라질 명목 BRL 소매(IPCA) 층위 — 한국 CIF·국제 SBO로 탄성 이전 금지'
      - 'IRF 신뢰구간 미제시·λmax/trace 불일치(닭·수산물)·I(1) 경계 판정 — 수치 인용은 본문 서술값만, 파라미터 사용 금지'
      - '전이 지속기간(FEVD 3~5기 수렴) 정성 대조에 한정 — CE 엣지 lag 근거 아님'
    evidence:
      locator: Alves_2022 요약 §3 표 8(p.19)·p.17
      quote_ko: 대두 10% 충격은 12개월 누적 소매 대두유 +2%로 품목 중 최대이며, 분산분해는 3기 이후 사실상 고정된다.
    linked_contract: AM-05 국소투영 — 시차별 반응 지속기간 해석의 대조 사례
    status: 대기
```

**추가하지 말 것**: 소매 탄성(0.20 등)을 엣지 강도·모델 파라미터로 쓰는 것 · FEVD 비중을 가중치로 쓰는 것 · 원두 계절성(3–5월 저가)을 SBO 계절 prior로 쓰는 것 · "2/3 교역" 비율을 한국 맥락에 적용하는 것 · 육류/마가린/경유 소매 엣지 · VEC를 AM 신설 · Lei Kandir 방향성 엣지 · 바이오디젤 70%를 시점 무관 상수로 쓰는 것 · CE-023을 validated로 올리는 것.

## 7. 정직 분류

| 대상 | 분류 | 사유 |
|---|---|---|
| 조유 흡수 58→82%, 압착 3.47% vs 수출 9.62%, 수율 19.2% | **채용**(구조 사실·CE-023 evidence) | 원문 수치가 명확하고 SBO 직결(p.2, p.8). 단 2018년까지의 레짐 사실로 시점 태깅 |
| 혼합의무 단계(p.17)와 SBO 70% | **채용**(seed·evidence) + **인용 주의** | 월 미기재·B3/B4/B9 누락·기간 미기재 → ANP/CNPE 원문 대조 전 시계열 확정 금지 |
| CE-023 entity_terms 정정(TERM-071→TERM-068/065) | **채용 권고**(P1-06 서명) | B40은 브라질 B15 엣지와 불일치 |
| 신규 엣지(압착 지연 → 원산지 가용성, CONTEXT) | **Challenger 검토 대기** | 착유지 이전 효과로 국제가 방향 부여 불가. 최신 PSD 재확인 필요 |
| 구조 VEC 방법(MP-19) | **배경** | 우리 스택 미사용. 전이 지속기간 정성 대조에만 활용 |
| 소매 탄성·FEVD 수치 | **배경 / 인용 주의** | 브라질 명목 소매·IRF 오차대 없음·검정 불일치 |
| 가격수용자·CBOT 연동·계절성 | **배경** | 원두 대상이며 타 문헌 인용(Pino 2014)을 재서술한 것 |
| "Ambos os testes" 서술·초록 'biodiesel' 표기 | **반면교사** | 표와 본문의 불일치를 그대로 인용하면 오류가 전파된다. 표를 직접 검산하는 규율의 사례 |
