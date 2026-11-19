# P1 6관점 검토 — Batch C (doc26·27·28·31 전면 + 포르투갈어 4편 델타)

> 작성 2026-11-19 · 읽기 전용 검토(저장소 무변경). 입력은 MinerU 파싱본(`_pdfparse_cache/corpus/out_mineru/`)이며 locator `p.N`은 `<!-- page N of M -->` 표지 기준 PDF 쪽이다.
> 중복 대조 대상: `docs/research_desk/2026-11/market_structure_pdf_review_2026_11_17.md`(이하 "11/17 리뷰" — 4편 모두 Paper 3·4·5·7로 이미 검토됨), `src/semantic/{ontology,entities,methods}.yaml`, `docs/research_desk/2026-08/extraction_technology_by_country_2026_08_25.md`, `docs/memory_archive/2026-08~11.md`.
> 확인 결과 11/17 리뷰의 후보(CAND-Q1/Q2·A1/A2·W1, 크러시 상수 등)는 **semantic layer에 아직 반영되지 않았다**(ontology·entities에 Flores·Haro Sly·Cravotto·FFA·silo 검색 0건, CE-009 evidence는 causal_chains.md 1건뿐). 따라서 본 배치는 11/17 리뷰 후보를 **승인 전에 교정**하는 항목과 표 구조 복원으로 새로 드러난 항목만 제안한다.

## 1. 문서별 3줄 요약

**doc26 — Khan et al. 2024, Edible Oilseeds (IntechOpen 장)** · SBO 관련성 **하**
- 유지작물 전반의 역사·육종·영양 서술이며, 대두 관련 수치는 2008/09~2020 혼합 빈티지의 2차 인용이다(p.5, p.8–9).
- 표 구조 복원 후에도 새 정보는 없고 오히려 결함이 추가로 확인된다. 표 1의 카놀라 행(지방 94.5 g·884 kcal)은 종자가 아니라 기름 값이다(p.2).
- 11/17 리뷰의 "인용 금지" 판정을 유지한다. 근거를 보강하는 항목만 C-13으로 제안한다.

**doc27 — Flores·Pope·Doehring 2026, JAOCS 103:3–11 (USSEC 재정 지원)** · SBO 관련성 **상**
- 아시아 압착공장 1곳의 브라질·미국산 대두와 탈검 조유 304쌍을 비교했다. 브라질산은 FFA 1.32% vs 0.44%, NOL 1.50% vs 1.01%, P 219.93 vs 116.83 ppm으로 높다(표 3, p.4).
- 이전 추출에서 깨졌던 **표 4·5가 복원되었다**. 원산지 더미 하나만으로 FFA 조정 R²가 0.888이다(표 4, p.5). 반면 콩 성분 변수만 쓰면 0.543(표 6, p.6), 상호작용을 넣으면 0.900(표 7, p.7)이다.
- 따라서 11/17 리뷰가 CAND-Q2 근거로 쓴 pooled 계수(수분→FFA +0.172)는 원산지 차이를 흡수한 값이다. 브라질 내부만 보면 수분→FFA 계수는 −0.025다(표 7). 교정이 필요하다(C-01·C-02).

**doc28 — Cravotto et al. 2023, Molecules 28:5973 (저자 2인 Pennakem/EcoXtract 소속)** · SBO 관련성 **중**
- 저장·건조·압착·용매 추출을 기술 중심으로 검토한 리뷰다. 안전 저장 수분 <13%(p.3), 수분 14–15%에서 FFA 증가(p.4), 63 °C 초과 건조 시 비수화성 인지질 증가(p.4)를 서술한다.
- 비용 수치는 시뮬레이션 인용이다. 헥산 공정은 EUR 30/t 대두(p.30), 고온 에탄올은 EUR 47.4/t(p.29)이며 표 1(p.2)은 11/17 리뷰 값과 일치한다.
- 새로운 점은 11/17 리뷰의 가공비 환산("EUR 160/t oil")이 보드 크러시 산식과 맞지 않는다는 것이다(C-06).

**doc31 — Haro Sly 2017, Palgrave Communications 3:17095** · SBO 관련성 **중**
- 아르헨티나 대두 체인의 독과점 구조를 다룬다. 압착 능력의 약 93%를 6사가 보유하고, 정제 능력은 압착보다 작다(p.7).
- 수출세는 2008년 가변세 시도 실패와 35→30% 인하(p.7), 중국의 아르헨산 수입 −29%(2016년 1~7월, p.9)가 사건으로 기록된다.
- 체인 흐름 도식은 MinerU에서도 이미지 블록으로만 나와 수치를 검증할 수 없다(p.4). 사일로백 저장 30%(p.7)는 11/17 리뷰가 사실만 적고 메커니즘으로 연결하지 않은 항목이다(C-10).

## 2. 제안 목록

라벨: CONFIRMED(원문 수치) · INFERENCE(본 검토 추론) · DATA GAP(원문·저장소에 없음) · NOT COMPARABLE(정의·분모 상이).

| ID | 문서 | 제안 내용 | 반영 위치 | 주관 관점 | 다른 관점 의견 | 우선순위 | 라벨 | 근거 locator (인용 ≤20단어) | 이미 반영 여부 |
|---|---|---|---|---|---|---|---|---|---|
| C-01 | doc27 | **CAND-Q2 계수 교정.** 11/17 리뷰는 pooled 표 6 계수(수분→FFA +0.172, 열손상→FFA +0.175)를 브라질 우천 수확 경로의 근거로 썼다. 원산지 상호작용 모형(표 7)에서 브라질 내부 계수는 수분→FFA −0.025(p<0.1), 수분→NOL +0.070, 열손상→FFA +0.076, 열손상→NOL +0.151이다. 따라서 경로는 "열손상→FFA·NOL"과 "수분→NOL"로 좁히고, "수분→FFA"는 삭제한다. | CE-009 품질 분기 후보(CAND-Q2) evidence·note | P1-03 | P1-04: 동의하며 NOL 경로만으로도 정제 손실 비용 논리는 유지된다. P1-06: evidence에 표 7 셀 provenance 필수. P1-01: 가격 엣지 아님에 동의 | Must | CONFIRMED(계수) / INFERENCE(경로) | doc27 p.7 표 7 · p.6 표 6 · "The main coefficients represent effects for Brazilian soybeans" (p.6) | 미반영(CAND-Q2는 11/17 후보 단계 — 승인 전 교정 가능) |
| C-02 | doc27 | **품질 격차는 대부분 원산지 고정효과다.** 원산지 더미 단독 FFA 조정 R² 0.888(표 4)은 성분+상호작용 0.900(표 7)과 거의 같다. 콩 성분이 추가로 설명하는 부분은 약 0.01이다. 그러므로 품질 prior는 **시간 불변 원산지 할인**(G3 시나리오 상수)으로 두고, 기상→품질 동적 경로(CAND-Q2)는 보조 가설로 강등한다. | G3 원산지 선택 파라미터 · landed cost 품질 prior(CAND-Q1) | P1-04 | P1-03: 2개 MY·공장 1곳으로는 해별 기상 차이를 식별할 수 없다(DATA GAP). P1-01: G2 피처로 쓰지 않는다는 11/17 결론과 정합 | Must | CONFIRMED(R²) / INFERENCE(해석) | doc27 p.5 표 4(FFA R² Adj. 0.888) · p.6 표 6(0.543) · p.7 표 7(0.900) | 미반영(표 4는 이전 추출에서 판독 불가였던 신규 정보) |
| C-03 | doc27 | **품질조정 CFR 스프레드는 점추정 대신 범위로.** NOL 원산지 차 −0.505(표 4)를 설명하는 원산지 더미의 R²는 0.411에 그친다. 브라질 NOL 범위는 0.71–2.43%(SD 0.34)다. 11/17 리뷰의 "ΔNOL×가격 ≈ USD 6/MT"는 평균값 하나이므로, P1-04 >USD 20/MT 경보 보정에는 NOL P10–P90 범위를 쓴다. | P1-04 Brazil–US CFR spread 경보 보정안 | P1-04 | P1-01: 범위 폭이 경보 임계보다 작아야 의미가 있으므로 관세청 원산지별 CIF 잔차로 먼저 검증해야 한다. P1-06: QUDT 단위 %·ppm 분리 | Should | CONFIRMED(분포) / INFERENCE(적용) | doc27 p.4 표 3(BR NOL 0.71–2.43) · p.5 표 4(NOL −0.505, R² 0.411) | 미반영(11/17 Must #2의 정밀화) |
| C-04 | doc27·doc28 | **원산지 효과와 계절이 교락된다.** 공장은 원산지별로 연중 특정 시기에만 가공하므로(각주 2) 원산지 더미에 가공 계절·저장 기간·해상 운송 기간이 함께 섞인다. 브라질 콩 수분은 평균 12.20%·최대 14.20%(표 2)로 안전 저장 기준 <13%(doc28)에 근접한다. 해석 규칙으로 "BR 품질 할인은 운송·저장 경로 의존"을 명시하고, 현지 압착 아르헨 조유로 전이하는 것을 금지한다. | entities TERM-045(탈검 조유) interpretation_rules · CAND-Q1 note | P1-04 | P1-03: 수분 14–15%에서 리파아제 FFA 가속(doc28 p.4)과 정합. P1-02: 무관 | Should | INFERENCE | doc27 p.9 각주 2 "processes either US or Brazilian origin soybeans... at specific times of the year" · p.3 표 2 · doc28 p.3 "less than 13%" | 미반영(11/17은 운송 중 수분만 언급, 계절 교락은 미지적) |
| C-05 | doc27 | **내부 불일치는 provenance에 플래그로 남긴다.** ① 불검화물: 표 3·4는 US가 높다(+0.05, +0.058). 본문·결론은 "US lower"라고 쓴다. ② 요오드가: BR 최소 12.60(SD 9.51)은 이상치로 의심된다. ③ 표 7 유의성 별표와 SE가 맞지 않는다(Oil −0.034*** SE 0.059). ④ 본문 p.7 "BR에서 수분 영향 더 강함" 서술과 표 7 US 수분 상호작용 +0.116이 상충한다. ⑤ n은 BR 155/US 160(표 2·3), 회귀는 304다. 불검화물·요오드·표 7 별표는 EvidenceSpan 사용 금지로 둔다. | `provenance.yaml` EvidenceSpan 메타 · references README | P1-06 | P1-05: 품질 기사 추출 시 "US oil has lower unsaponifiables" 류 문구를 원문 근거로 쓰지 않는다 | Could | CONFIRMED(불일치 사실) | doc27 p.4 표 3 · p.5 표 4 · p.7 표 7 · p.8 "lower NOL, FFA, mineral content, and unsaponifiable matter" | 미반영 |
| C-06 | doc28 | **가공비 환산을 정정한다.** 11/17 리뷰의 "EUR 30/t seed ≈ EUR 160/t oil"은 가공비 전액을 기름에 배분한 값이다. 보드 크러시는 대두 1톤(부셸) 기준으로 기름+박 가치에서 원료가를 빼므로, 가공비도 **대두 톤당 EUR 30**을 그대로 차감해야 한다. per-t-oil 환산은 금지한다. 기름 가치가 박의 2–3배라는 서술(p.13)도 배분 근거가 아니다. | CE-018/019 순압착마진 계산 가정 · 11/17 리뷰 top-10 #9 | P1-01 | P1-04: 상수 자체의 쓸모는 낮다는 기존 입장 유지. P1-06: "simulation" 태그와 EUR/t-seed 단위 고정 | Should | CONFIRMED(EUR 30/t seed) / INFERENCE(정정 논리) | doc28 p.30 "than the cost of a conventional hexane process (EUR 30/tonne)" · p.29 "EUR 47.4 per tonne of seed processed" | 미반영(11/17 리뷰 오류 — 저장소 미적용이므로 문서 정정만 필요) |
| C-07 | doc28 | **품질 메커니즘 임계 상수(해석 규칙용).** 안전 저장 수분 <13%(p.3), 수분 14–15%와 높은 aw에서 FFA 증가(p.4), 건조 63 °C 초과 시 비수화성 인지질 증가(p.4). C-01로 좁혀진 "열손상→FFA·NOL" 경로의 물리적 근거로 붙인다. | CAND-Q2 note · TERM-045 interpretation_rules | P1-06 | P1-03: ERA5-Land 수확기 강수와 연결할 수 있으나 skill 검증 전 경보 등재 금지. P1-04: 계약 스펙(FFA·P) 조항 근거로 활용 | Could | CONFIRMED | doc28 p.4 "temperatures above 63 °C... increase the content of non-hydratable phosphatides" | 미반영(추출 기술 보고서 2026-08은 FFA·인 정성 언급만) |
| C-08 | doc31 | **체인 흐름 locator 정정.** 11/17 리뷰는 2010 체인 수치(생산 52,680 kt·조유 수출 67%)를 "Fig. 2, p.4"로 적었다. 그러나 Figure 2는 소득 분배 차트이고, 체인 도식은 번호 없는 이미지다(p.4, 본문은 "page 5" 지칭). MinerU도 이미지 블록만 추출했으므로 수치는 여전히 미검증이다. 반입 금지를 유지하고 locator는 "unnumbered chain scheme, p.4"로 고친다. | 11/17 리뷰 Paper 7 §2·(b)4 · provenance | P1-06 | P1-04: 67% 조유 수출 비중 사용 희망은 이미지 수동 판독 후로 연기 | Should | DATA GAP | doc31 p.3 "An entire scheme... is presented on page 5" · p.4 "Data correspond to 2010. Percentage of the Volume." | 미반영(교정) |
| C-09 | doc31 | **아르헨 농가 보유(출하 지연) 메커니즘 후보.** 사일로백이 저장 능력의 약 30%(2007)이고, 고정 저장의 54%를 민간 1,200사·조합 500곳이 보유한다. 이는 농가가 수출세 인하·환율 기대에 따라 출하를 늦출 수 있는 물리적 여력이다. 후보 경로: 수출세 단계 인하 기대(Decreto 423/2026 일정) → 농가 출하 지연 → 압착 원료 지연 → AR 조유 선적 지연 → AR 채널 CIF 단기 상방. 논문은 저장 용량만 제시하며 행동은 INFERENCE다. | ontology 메커니즘 노드 후보 `AR_FARMER_RETENTION`(CE-003 역방향 note) · P1-04 Rosario 리드타임 리스크 | P1-04 | P1-02: 단계 인하 일정이 "인하 대기" 유인을 만든다는 데 동의. P1-01: 엣지 등재 전 CIARA 월별 압착·BCR 농가 판매 진도 계열 필요(DATA GAP). P1-06: 직접 Cause→Price 금지에 따라 3단 구조 유지 | Should | CONFIRMED(용량) / INFERENCE(경로) | doc31 p.7 "plastic silos, which in 2007 represented approximately 30% of the total capacity" | 미반영(저장소 silo·hoarding 검색 0건) |
| C-10 | doc31 | **P1-05 ABSA 키워드 확장.** `ARG_EXPORT_TAX_SENTIMENT`에 "silo bolsa", "retención de granos/venta de productores" 계열 및 2008년 가변세("retenciones móviles") 키워드를 추가한다. C-09 경로의 뉴스 측 관측 변수다. | `.claude/agents/p105` Stage 2 aspect 키워드 · entities TERM-105 synonyms | P1-05 | P1-06: 동의어는 TERM-105에 묶고 새 TERM은 만들지 않는다. P1-02: 정책 발표와 농가 행동 기사를 극성상 분리해야 한다 | Could | INFERENCE | doc31 p.7 "implement a mobile progressive export tax based on fluctuations in soy prices" | 미반영 |
| C-11 | doc31 | **아르헨 바이오디젤 집중도를 공급자 KB에 등재.** 생산자 23사 중 22%가 생산의 60% 이상을 차지하고, 대형 압착사가 수출용 바이오디젤 설비를 보유한다. AR B15 인상 협의(R-022)가 확정되면 조유 수출 잉여와 경합한다. 빈티지는 MECON 2011이다. | ontology `concentration` 블록(basis: producers, as_of 2011) | P1-04 | P1-06: capacity·producer 기준이므로 shipment CR4와 NOT COMPARABLE 표기. P1-01: 가격 영향은 B15 확정 전 CONTEXT | Could | CONFIRMED(2차) / NOT COMPARABLE | doc31 p.7 "22% of the biodiesel producers account for more than 60%" | 미반영(11/17은 "23 biodiesel producers"만 기재) |
| C-12 | doc31 | **소득 분배 35/43/22%에 레짐 태그를 단다.** 이 분배는 대두 USD 540/t·수출세 35% 시점(TELAM 2014)의 예시다. 임차인 몫은 p.3에서 $270,000, p.5에서 $220,000으로 논문 안에서 다르다. 수출세 전가율의 일반 근거로 쓰지 않고, 2014 레짐 사례로만 인용한다. | 11/17 리뷰 Paper 7 §2 · CE-003 evidence 후보 시 | P1-02 | P1-01: 동의하며 현행 세율(대두 24%→15%)과 혼용 금지 | Could | CONFIRMED(불일치) | doc31 p.3 "considering a soybean price of USD540 per ton and a 400 Ha farm" · p.5 | 미반영 |
| C-13 | doc26 | **"인용 금지" 근거 보강 후 references README에 등재.** ① 표 1 카놀라 행은 기름 값(지방 94.5 g/100 g)이다. ② 대두의 식용유 점유가 25%(p.5)로, doc28 28.8%(표 1 p.2)·doc27 "nearly a third"(p.1)와 다르다. ③ 기존 지적(57 vs 61%, 32 vs 38%)도 함께 기록한다. ML_2025_WCO와 같은 등급으로 분류한다. | `docs/research_desk/references/README.md` | P1-06 | 전 관점 동의(수치 인용 0) | Could | NOT COMPARABLE / CONFIRMED(결함) | doc26 p.2 표 1 · p.5 "accounts for 25% of the edible oil produced at the global level" | 미반영(README에 Khan 항목 없음) |

## 3. 포르투갈어 4편 델타 결과 (R-045 대비)

- **doc18 Aguiar 2024 (Guerra das Rotas): 델타 없음.** MinerU 출력에 표가 0개이고 그림·그래프 7개는 이미지 블록이다. 그래프 1(Centro-Sul vs Arco Norte 수출량, p.16)은 요약에 이미 "판독 불가 DATA GAP"으로 기록되어 있으며, 이번 파싱으로도 값이 나오지 않았다.
- **doc20 Miranda 2025 (Agronegócio no Cerrado): 델타 없음.** 표가 0개다. 그래프 1(마라냥 대두 생산 추이, p.12)은 이미지이고, 10년 단위 평균 면적·생산은 본문 서술이라 이전 텍스트 추출과 같다. 압착·대두유 수치 부재(DATA GAP)는 요약 판정 그대로다.
- **doc23 Figueira 2023 (CMS): 델타 없음.** 표 1(중국 191.91→626.19 Mt, BR→중국 55.69→278.18 등, p.10)과 표 2(CMS 효과 BR +86.07·US −26.5·AR −98.19 Mt, p.12)가 요약의 재계산값·불일치 판정(US 행 합 411.16 vs Mundo 411.75 등)과 셀 단위로 일치한다.
- **doc30 Alves 2022 (전이·CE-023): 델타 없음.** 표 8 FEVD(3기 8.87/24.08/21.34/45.71, p.19)와 표 2 Johansen(닭 λmax 36.29 < 40.30 등)이 요약 §3의 CONFIRMED 값·검정 불일치 지적과 일치한다. 조유 흡수 58→82%, 원곡 60→41.5%(p.8)도 본문 서술 그대로다.

## 4. 관점 간 이견과 결론 · 반영하지 말아야 할 것

**이견 1 — 원산지 품질 격차를 정적으로 볼 것인가, 동적으로 볼 것인가 (P1-04 ↔ P1-03).**
- P1-04는 C-02에 따라 품질 격차를 원산지 고정 할인으로 단순화하자고 본다.
- P1-03은 브라질 우기 수확(1~3월) 이상 기상이 열손상을 늘리는 경로를 버리지 말자고 본다. 다만 표본이 2개 MY·공장 1곳이라 해별 변동을 식별할 수 없다는 점은 인정한다.
- **결론**: CAND-Q1(정적 원산지 할인)을 주 경로로 하고, CAND-Q2는 "열손상→FFA·NOL, 수분→NOL"로 범위를 좁힌 보조 후보로 둔다(C-01). 둘 다 G2 피처가 아니라 G3·landed cost의 시나리오 prior로만 쓴다. 승격 조건은 관세청 원산지별 CIF 잔차에서 브라질 수확기 효과가 관측되는 것이다.

**이견 2 — 가공비 상수의 쓸모 (P1-01 ↔ P1-04).**
- P1-04는 상수의 운영 가치가 낮다고 본다.
- P1-01은 순압착마진 해석에 필요하다고 본다.
- **결론**: 쓴다면 반드시 EUR 30/t-seed 단위로 차감하고 "simulation·이해상충" 태그를 단다(C-06). 우선순위는 낮다.

**이견 3 — 아르헨 농가 보유 경로의 등재 시점 (P1-02 ↔ P1-01).**
- P1-02는 Decreto 423/2026의 월별 인하 일정이 출하 지연 유인을 만든다며 즉시 후보 등재를 원한다.
- P1-01은 출하 진도 계열 없이 등재하면 인과 근거가 없다고 본다.
- **결론**: 노드는 candidate·evidence 1건(용량 사실)으로만 두고 direction·lag는 공란으로 둔다. P1-05 키워드 확장(C-10)으로 먼저 관측 근거를 쌓고, CIARA/BCR 계열이 확보되면 재심한다.

**반영하지 말아야 할 것**
- doc26의 모든 수치(내부 모순·빈티지 혼합). README에 "인용 금지"로 등재하는 것만 허용한다.
- doc27 표 6 pooled 계수를 브라질 기상 경로 강도로 쓰는 것(C-01). 불검화물·요오드가·표 7 유의성 별표 인용(C-05). 결과를 아르헨티나 조유나 브라질 현지 압착 수출 조유로 전이하는 것(C-04).
- doc28 per-t-oil 가공비 환산(EUR 160/t oil). 고온 에탄올 EUR 47.4/t·NPV +10.2%를 실측 비용으로 쓰는 것. 헥산 STOT RE 1 재분류를 인과 엣지로 만드는 것(11/17 CAND-W1 판정 유지, 60거래일 의사결정 창 밖).
- doc31 체인 흐름 수치(52,680 kt·74%·67%). 이미지 수동 판독 전에는 반입하지 않는다(C-08). 소득 분배 35/43/22%를 수출세 전가율의 일반 근거로 쓰는 것(C-12). 압착 능력 93%를 shipment 기준 CR4와 비교하는 것(NOT COMPARABLE).
- 포르투갈어 4편: R-045 이후 추가 반영 사항이 없다. 원곡·복합체 수치를 대두유로 인용하지 않는다는 기존 규율을 유지한다.
