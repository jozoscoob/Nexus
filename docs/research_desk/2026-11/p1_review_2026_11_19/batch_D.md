# 배치 D — Cargill 대두 보고서 9건 6관점 재검토 (P1-01~P1-06)

- 대상: doc01~doc09 (MinerU 파싱본, `_pdfparse_cache/corpus/out_mineru`). id↔원문은 `corpus/map.tsv`.
- 표기: `doc·p.N` = PDF 쪽(`<!-- page N of M -->` 기준). 인포그래픽 숫자는 MinerU에서 빠지거나 순서가 뒤섞여 있어, 원본 PDF의 `pdftotext -layout` 출력으로 다시 확인했다(읽기 전용).
- 중복 대조: A-210·A-211(memory_archive/2026-08), TERM-155·TERM-115(entities.yaml), ontology.yaml(SC-CARGILL·CE-004·concentration), errata 2026-08-19, reverify_pack 2026-08-19, deep_verify 2026-08-19, Cargill/README.md, reference_gap_list 2026-08-25, extraction_technology_by_country 2026-08-25.

## 1. 보고서별 요약과 연도별 핵심 지표

| id | 보고서 | 2줄 요약 |
|---|---|---|
| doc05 | SA Soy Progress Report 2019 (22p) | 남미 사업 시설 현황(엘리베이터 145·공장 10·항만 14·사무소 28)과 4개국 직·간접 소싱 비중이 처음 공개됐다(p.7, p.14). 매핑은 단일점(single-point) 단계였고 DCF 수치는 아직 없다. |
| doc07 | 2020 상반기 업데이트 (17p) | 실행계획 진척을 서술 중심으로 다룬다. ProTerra 분리유통 등 인증 상품만 언급하고 공급망 수치표는 없다(p.12). |
| doc06 | SA Soy Progress Report 2020 (21p) | 국가별 공급자 수(BR 15,000·AR 5,200)와 섹터 평균 기반 DCF(BR 96.1·AR 98.8)를 처음 냈다(p.5–6). 브라질 RTRS 인증 시설은 43개이며, Santarém·Itaqui 두 경로와 Miritituba 환적터미널(2017 개장)이 나온다(p.12, p.17). |
| doc09 | 2021 상반기 업데이트 (25p) | 연말·상반기 보고 항목을 표준화하고 역년(calendar year) 기준으로 맞추겠다고 했다(p.5). 수치는 차단 농장 407건(상반기)뿐이다(p.14). |
| doc08 | SA Soy Sustainability Report 2021 (27p) | CY2021 대시보드에 공급자 BR 14,800·AR 5,600, 직접 58/54%, 폴리곤 92.3/88.6%, DCF 96/99%가 실려 있다(p.5). MinerU가 'Argentina' 제목을 14,800 앞에 배치해 국가가 뒤바뀌어 읽히기 쉬운 쪽이다. |
| doc01 | ESG Report 2022 Soy 챕터 (13p) | CY2021 KPI 표를 다시 실었고(p.4), 자산 패널은 엘리베이터 145·공장 13·항만 14·사무소 26이다(p.3). 각주 i에 따르면 자산에는 JV와 제3자 위탁가공(toll) 설비도 포함된다(p.13). |
| doc02 | ESG Report 2023 Soy 챕터 (23p) | CY2022 표가 5개국으로 확대됐다(p.5). 다만 DCF 기준이 "since 2008"이라 이후 연도(기준일 2020)와 비교할 수 없다. 자산은 135·9·14·26(p.4)이고, 아르헨 ViSeC 추적 플랫폼은 2020-12-31을 기준으로 한다(p.12). |
| doc03 | Impact Report 2024 Soy 챕터 (14p) | CY2023 표: AR 생산 25.01Mt(가뭄 연도), 폴리곤 98~100%, DCF(기준일 2020)(p.3). 자산은 133·12·20에 행정 사무소 7·상업 사무소 42이고(p.2), 'EUDR 대비' 절이 있다(p.14). |
| doc04 | Impact Report 2025 Soy 챕터 (15p) | CY2024 표: BR 공급자 15,000·직접 58%·DCF 99.29%(p.3). 자산은 136·14·13에 사무소 12/42이다(p.2). **cut-off 2025-01-01을 2026-01-01부터 적용**한다(p.4). 2024년에 NL 당국과 대두박 선적으로 EUDR 시범(dry run)을 했다(p.11). |

### 1-a. 남미 자산 패널 (보고서 판별, 자사 공시)

| 지표 | 2019판 | 2022판 | 2023판 | 2024판 | 2025판 | locator |
|---|---|---|---|---|---|---|
| 내륙 엘리베이터(country elevators) | 145 | 145 | 135 | 133 | 136 | doc05·p.7 / doc01·p.3 / doc02·p.4 / doc03·p.2 / doc04·p.2 |
| 가공공장(processing plants) | 10 | 13 | 9 | 12 | **14** | 동상 |
| 항만(ports) | 14 | 14 | 14 | 20 | **13** | 동상 |
| 사무소 | 28 | 26 | 26 | 행정 7 + 상업 42 | 행정 12 + 상업 42 | 동상 |
| 범위 정의 | 미기재 | 자가·JV·toll 포함 | 미기재 | 미기재 | 미기재 | doc01·p.13 각주 i |

### 1-b. 브라질·아르헨 KPI (데이터 연도 기준)

| 지표 | 2019 | 2019-20 | 2021 | 2022 | 2023 | 2024 | locator |
|---|---|---|---|---|---|---|---|
| 공급자 수 BR / AR | — | 15,000 / 5,200 | **14,800 / 5,600** | 14,900 / 4,800 | 14,200 / 4,700 | 15,000 / 5,550 | doc06·p.5 · doc01·p.4 · doc02·p.5 · doc03·p.3 · doc04·p.3 |
| 5개국 공급자 합 | — | 23,000 | 22,800 | 22,300 | 21,600 | 23,300 | 동상(합산) |
| 직접 소싱 비중 BR / AR (%) | 72 / 85 | 판독 불가 | 58 / 54 | 64 / 66 | 60 / 80 | 58 / 62 | doc05·p.14 · doc01·p.4 · doc02·p.5 · doc03·p.3 · doc04·p.3 |
| 직소싱 폴리곤 매핑 BR / AR (%) | (단일점 60 / 73) | — | 92.3 / 88.6 | 100 / 99 | 99.996 / 98.25 | 100 / 98.28 | 동상 |
| DCF BR / AR (%) | — | 96.1 / 98.8 (섹터 평균) | 96 / 99 (직소싱) | 94 / 98 (since 2008) | 99.3 / 99.8 (기준일 2020) | 99.29 / 99.96 (기준일 2020) | doc06·p.5 · doc01·p.4 · doc02·p.5 · doc03·p.3 · doc04·p.3 |
| 업계 생산량 BR / AR (Mt, CONAB·MAGYP 인용) | 122.3 / 55 | 122.6 / 55.9 | 135.9 / 46 | 125.6 / 43.9 | 154.63 / 25.01 | 147.43 / 48.21 | doc05·p.14 · doc06·p.5 · doc01·p.4 · doc02·p.5 · doc03·p.3 · doc04·p.3 |

주: DCF는 해마다 산식과 기준이 바뀌었다(섹터 평균 → 직소싱 → since 2008 → 기준일 2020). 따라서 같은 행 안에서도 연도 간 비교는 할 수 없다(NOT COMPARABLE). 2020 보고서의 원그래프 값(doc06·p.5–6)은 판독이 깨져 표에서 뺐다.

## 2. 제안 목록

| ID | 문서 | 제안 내용 | 반영 위치 | 주관 | 다른 관점 의견 | 우선 | 라벨 | 근거 locator (인용 ≤20단어) | 이미 반영 |
|---|---|---|---|---|---|---|---|---|---|
| D-01 | doc03·doc04 | **정오표 B-2 해소.** '가공 14·항만 13'은 Impact Report **2025**판(CY2024), '12·20'은 **2024**판이다. 둘 다 Cargill 자사 공시이며 서로 상충하지 않는다. 판이 달라서 생긴 차이다. 브리프 값이 최신판과 일치한다 | errata 2026-08-19 §1 해당 행 → ✅해소, reverify_pack '잔여 4', reference_gap_list B-2 | P1-04 | P1-06: 판·연도 병기를 의무화한다. P1-01: 가격 영향 없음, 기록 정정만 | Must | CONFIRMED | doc04·p.2 "14 processing plants … 13 ports" / doc03·p.2 "12 processing plants 20 ports" | 아니오. 반대로 deep_verify는 12·20을 '올바른 값'으로, 14·13을 ❌로 판정했다(오판) |
| D-02 | doc04·doc01 | TERM-155 `interpretation_rules`의 "자사 공시와 외부 집계가 상충" 문구를 "자사 공시의 판별 차이(2024판 12·20 → 2025판 14·13)"로 고친다. 출처·판 병기 규칙은 그대로 둔다 | entities.yaml TERM-155 | P1-06 | P1-04: 최신 기준값은 2025판(CY2024 데이터)으로 둔다 | Must | CONFIRMED | doc04·p.2 (자산 패널) · doc03·p.2 | 아니오 |
| D-03 | doc01·doc08 | **공급자 수 국가 뒤바뀜 교정.** CY2021은 **BR 14,800·AR 5,600**이 맞다. README와 A-210의 'AR 14,800·BR 5,600'은 반대로 적혀 있다. 원인은 MinerU가 doc08·p.5에서 국가 제목 순서를 바꿔 놓은 것으로 추정한다 | Cargill/README.md L21, extraction_technology_by_country L302, memory에 정정 행 추가(아카이브 본문은 이력이라 보존) | P1-04 | P1-06: 동일 오류의 전파 경로 2곳을 점검한다. P1-05: 추출 QA에 표 우선 원칙을 둔다 | Must | CONFIRMED | doc01·p.4 표: Brazil 열 "14,800", Argentina 열 "5,600" | 아니오 |
| D-04 | doc04 | **DCF 날짜 의미 교정.** "2025-01-01부터 컷오프 전환"이 아니다. **cut-off date는 2025-01-01이고, 이 기준으로 측정하는 것은 2026-01-01부터**다(AR·BR·UY). 아마존 바이옴은 2008-07을 유지한다. 발표일·시행일·기준일을 분리한다 | README L40, A-211 정정, P1-02 정책 캘린더 | P1-02 | P1-04: 2026년 구매 기준이 바뀌면 간접 공급선 조달이 마찰을 겪을 수 있다(INFERENCE) | Must | CONFIRMED | doc04·p.4 "Beginning January 1, 2026, DCF will be measured based on a cut-off date of January 1, 2025" | 아니오. 날짜가 섞여 있다 |
| D-05 | doc02·doc04 | README의 'EUDR 정합' 표현을 바로잡는다. EUDR 기준일 2020-12-31은 Cargill의 '기준일 2020'(산정용)과 대응한다. 반면 cut-off 2025-01-01은 전환(conversion)까지 포괄하는 자사 구매 기준이라 EUDR과 같은 것이 아니다 | README L40–41, TERM-115 interpretation 보강 | P1-02 | P1-04: 'EUDR 브라질 원산지 추적성' 데이터 갭을 일부 채운다(BR 직소싱 폴리곤 100%·DCF 99.29%). 잔여 위험은 간접 42% 채널에 있다 | Should | INFERENCE | doc02·p.12 "not deforested after December 31, 2020" · doc04·p.3 BR Indirect "42%" | 아니오 |
| D-06 | doc01 | 시설 수 사용 규칙을 추가한다. 자산에는 **JV와 제3자 toll 가공 설비가 포함**된다. 따라서 '보유 공장 수'나 '압착능력'으로 읽으면 안 된다(capacity≠ownership≠throughput). 공장 수가 10→13→9→12→14로 오르내리는 것은 정의나 범위가 바뀐 탓일 가능성이 있다 | TERM-155 interpretation, README L3(판 병기), D-047 브리프 규율 | P1-04 | P1-06: `scope: owned+JV+toll(2022판만 명시)` 속성을 단다. P1-01: 추세 피처로 쓰는 것은 금지 | Should | CONFIRMED(각주) / INFERENCE(변동 원인) | doc01·p.13 "Includes assets owned by Cargill, by Cargill joint ventures, and by third parties … toll" | 아니오 |
| D-07 | doc01~05 | ontology SC-CARGILL에 `sa_soy_assets_by_edition`을 데이터 전용으로 등재한다(표 1-a, 5개 판). CE 엣지와는 연결하지 않는다 | ontology.yaml company 블록 | P1-06 | P1-04 동의. P1-02: 시설 수만으로 지정학 노출을 계산하지 않는다 | Should | CONFIRMED | 표 1-a locator 5건 | 아니오. Regina·Nantong만 있음 |
| D-08 | doc01~05 | 직·간접 소싱 비중 시계열(BR 72→58→64→60→58%)을 README에 넣어 '브라질 물량의 약 40%는 협동조합·타 트레이더 경유'라는 채널 구조 맥락으로 쓴다. 모델에는 넣지 않는다 | Cargill/README.md, D-047 브라질 축 | P1-04 | P1-01: Cargill 한 회사의 수치라 시장 전체를 대표하지 않는다 | Could | CONFIRMED / NOT COMPARABLE(2019) | doc04·p.3 BR "Direct 58% / Indirect 42%" · doc05·p.14 "72%" | 아니오 |
| D-09 | doc04 | EUDR 시범(2024년, NL 당국, 대두박 선적)을 TERM-115 evidence로 등재한다. 주요 트레이더는 준비가 진행 중이므로 'EUDR발 대두 공급 단절' 서사를 약화하는 신호로 읽는다 | TERM-115 evidence, P1-05 ABSA 이벤트 사전 | P1-05 | P1-02: 시범 1건으로 업계 전체 준비가 끝났다고 단정하지 않는다. CE-004(팜 경로) 강도 근거로는 쓰지 않는다 | Could | INFERENCE | doc04·p.11 "'dry run' on EUDR compliance for a soybean meal shipment" | 아니오 |
| D-10 | doc02 | 아르헨 ViSeC 추적 플랫폼(CIARA·Rosario 거래소 참여, 2020-12-31 기준)을 아르헨 채널의 EU 적격성 맥락으로 등재한다 | TERM-115 / 아르헨 채널 노트 | P1-02 | P1-04: 한국향 물량과의 관련은 간접적이다 | Could | CONFIRMED(계획) | doc02·p.12 "keep their soy eligible for export to this key market" | 아니오 |
| D-11 | doc06 | Miritituba 환적터미널(2017 개장)과 브라질 RTRS 인증 시설 43개(공장·항만·창고)를 TERM-155 `history_notes`에 넣는다. Arco Norte 엔티티 members는 이미 있다 | TERM-155 history_notes | P1-04 | P1-06: Itaqui는 Cargill 소유라고 명시되지 않았다("the export terminal") | Could | CONFIRMED | doc06·p.17 "We opened the port in 2017" · doc06·p.12 "total countrywide to 43" | 부분. Santarém 2003만 있음 |
| D-12 | doc03·doc04 | 사업부 명칭이 'agricultural supply chain'에서 'agriculture and trading business'로 바뀌었다(2025판). TERM-155 synonyms에 추가하고, 조직 재편 시점 기술과 맞춘다 | TERM-155 synonyms | P1-06 | — | Could | CONFIRMED | doc04·p.2 "Our South American agriculture and trading business" | 아니오 |
| D-13 | doc04 | README의 '폴리곤 98%·DCF 99%' 합산값은 표에 근거가 없다. 표는 국가별 값만 제시한다. 국가별 값으로 바꾸거나 locator를 붙인다 | Cargill/README.md L39–41 | P1-06 | — | Could | DATA GAP | doc04·p.3 (국가별 값만 수록) | — |

## 3. 정오표 B-2(시설 수) 재판정

**판정: 검증 가능해졌고, 결과는 '상충 아님(판 차이)'이다. 해소 처리를 권고한다.**

1. 이전에 "시설 수 미수록"이라고 판정한 것은 오류다. 9건 가운데 5건(doc05·doc01·doc02·doc03·doc04)에 남미 자산 패널이 있다. 이전 추출에서 인포그래픽 숫자가 빠져 오판했다. MinerU 본문에서도 숫자 일부(예: doc04 전부, doc03의 12)가 빠져 있었고, PDF 텍스트 층에서 다시 확인했다.
2. 브리프 '가공 14·항만 13'은 Impact Report 2025(CY2024)의 값과 정확히 같다(doc04·p.2). 검증자 '12·20'은 Impact Report 2024의 값이다(doc03·p.2). reverify_pack이 남긴 "판(2024 vs 2025)에 따라 달라졌을 가능성"이 원문으로 확인됐다.
3. deep_verify(2026-08-19)는 2024판만 보고 '❌불일치, 올바른 값 12·20'이라고 판정했다. 이 판정은 철회해야 한다. 최신값은 14·13이다.
4. 단서가 두 가지 있다. ① 자산에는 JV와 toll 설비가 포함된다(2022판 각주, doc01·p.13). 이후 판에는 정의가 적혀 있지 않다. ② 항만 수가 14→14→14→20→13으로 출렁이는데, 이는 범위가 바뀌었을 가능성을 시사한다(INFERENCE). 그래서 시설 수를 '능력'이나 '추세'로 쓰는 것은 금지하고, 값을 쓸 때는 반드시 판·연도를 병기해야 한다.
5. errata 정정문 제안: "✅ 해소 — 14·13 = Cargill Impact Report 2025 p.2(CY2024), 12·20 = 2024판 p.2. 판 차이, 상충 아님."

## 4. 반영하지 말아야 할 것

- **업계 생산량 수치(CONAB·MAGYP 인용)를 G1 피처나 유사 국면(analogue) 원천으로 쓰지 않는다.** 2차 인용이고 연도 라벨이 역년인지 작물년인지 섞여 있다. 예컨대 AR 25.01Mt는 'CY2023' 표에 있지만 실제로는 2022/23 작물년 값이다. 원천은 PSD를 유지한다(NOT COMPARABLE).
- **DCF %나 폴리곤 %를 가격 피처나 CE 엣지 근거로 쓰지 않는다.** 산식이 네 번 바뀌었고(doc06 섹터 평균 → doc02 since 2008 → doc03·doc04 기준일 2020), 값이 99% 근처에 포화돼 있으며, 가격으로 이어지는 메커니즘도 없다.
- **공급자 수를 공급 물량의 대리지표로 쓰지 않는다.** 수(count)는 물량(volume)이 아니고, 2019판 볼리비아는 농가 수 기준이었다(doc05·p.14 각주 *).
- **차단 농장 수를 추세로 해석하지 않는다.** 예: 2024년 총 4,537건(doc04·p.8). 2024판부터 목록 분류(보전지역·원주민 토지)가 추가돼 연도 간 비교가 불가능하다(NOT COMPARABLE).
- **시설 수에서 압착능력이나 물량을 역산하지 않는다.** 능력, 소유, 처리량은 서로 다른 개념이다(D-06).
- **2020 보고서 원그래프 판독값은 쓰지 않는다.** 예: "663199+31P"(doc06·p.5–6). OCR이 깨진 값이다.
- **Cargill 전사 수치는 남미 대두 맥락에 쓰지 않는다.** 155K 직원·125개국(doc08)은 전사 기준이고, 4.25백만 ha 모니터링(doc03·p.14)은 인증 프로그램 면적이다.
- **볼리비아 간접 공급선(주요 압착사, 물량 거의 100%; doc03·p.14)은 등재하지 않는다.** 한국 조달 채널과 무관하다.
