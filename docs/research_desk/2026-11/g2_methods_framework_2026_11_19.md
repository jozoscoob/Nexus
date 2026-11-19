# G2 확률 가격밴드·조달 계층 방법론 검토와 기초 프레임워크 (2026-11-19)

- 작성: 검토 패널(데이터 과학·원자재 분석·공급망·조달 실무·PM 관점 합성)
- 대상: 금융공학 논문 16편(`_pdfparse_cache/refs_g2g3/out_odl/g2_01~16.md`, 매핑 `map.tsv`) — 원문 전문은 로컬에만 두고 본 문서에는 요지와 위치(절·표·그림·식)만 인용함
- 선행 문서: `.claude/rules/modeling.md` §G2 · `procurement_financial_engineering_review_2026_11_19.md`(이하 "선행 검토") · `.claude/agents/c03-data-scientist.md` §4·§5
- 범위 제한: 본 문서는 방법·검증 설계 문서이며 구매·보류 권고, 확률 약속, 가격 전망을 제시하지 않음. 7IF·백테스트 수치는 2026-11-19 호출자 제공 사실이며 문헌 인용이 아님

---

## 1. 한 줄 결론

> 표기 정정: 기존 백테스트의 B3(계절 naive)와 겹치지 않도록 제안 기준선을 B4로 표기함.

G2는 "중심은 무변화(동일 계약 선물가), 폭은 EWMA→HAR 변동성, 모양·보정은 꼬리별 롤링 컨포멀"의 3층 기준선(B4)을 B2 대신 챔피언 기준선으로 세우고, 그 위에 basis·도착원가 층(참고 범위)과 CVaR 기반 조달 시뮬레이션 층을 얹는 구조가 16편의 증거와 오늘 백테스트(60일 80% 구간 coverage B2 63.5% → EWMA+컨포멀 77.6%)에 가장 정합함.

---

## 2. 논문별 적용성 표

판정: **채택**(기초 프레임워크에 바로 반영) · **조건부**(전제 충족·데이터 확보 후 챌린저) · **참고**(설계 근거·평가 관점만 차용) · **부적합**(현 데이터·목적과 불일치). 관점 약어: DS(C-03) · CA(P1-01) · SC(P1-04) · PM(C-01).

| # | 논문(약칭) | 방법 | 주장(위치) | G2 / 조달 판정 | 근거 | 주 관점 |
|---|---|---|---|---|---|---|
| 01 | Conformal Feature-based Newsvendor (Cao 2024) | 분위수 예측 + 편향 컨포멀 보정(CQPC), 전역 학습·국소 보정 | 임의 분위수 모델의 편향을 보정집합 잔차로 교정하고 임계분위수 coverage 보장(Abstract, 알고리즘 1·식(6)); 국소 보정이 손실을 최대 47.3% 줄임(§1.1 (III)); 최적 pooling 크기 15~25(§6, Fig.5) | G2 **조건부** / 조달 **채택(구조)** | 꼬리별 단측 보정과 "품질-수량" pooling 상충은 변동성 레짐별 보정 설계에 직결. 다만 보장은 i.i.d. 전제(§3.1, Theorem 1)라 중첩 60일 라벨에는 근사에 그침. 수요 측은 내부 데이터 금지(D-021)로 가격 분위수(예산가) 결정에만 적용 | DS·SC |
| 02 | Data-Driven Commodity Procurement (Mandl·Minner 2023) | 정책 구조를 유지한 매개변수 구매규칙을 MILP+정규화로 직접 학습(DDA) | 표본외 처방오차 DDA-ML1 5.68% vs 1/N 10.47%·REO 6.88%·과적합 DDA-BD 7.07%(§6.4, Table 4); 1/N 대비 연 4.33% 절감(§6.4, Table 5); S&P500 피처가 성과를 주도(§6.5) | G2 부적합 / 조달 **조건부** | 선도·현물 다채널 구조가 CIF 선적월 커버와 유사. 단 천연가스(TTF) 사례, 피처 우연상관(§6.5) 위험, 원산지 프리미엄 곡선 부재. G2 보정 완료 후 G3 챌린저 정책 | SC·DS |
| 03 | Distilling Large Information Sets (Guidolin·Pedio 2020) | HMM·단계적 회귀 + 132개 거시변수 PCA | 14개 상품(대두 포함) 월간 수익률에서 HMM·stepwise가 RMSFE·MAFE로 AR 기준선을 체계적으로 못 이김(Abstract, §6); 고변동 2008~2012에는 불가(§4, Table 1 논의) | 방법 **부적합** / 중심=무변화 **근거로 채택** | 중심(드리프트) 예측 투자 대비 이득이 없다는 직접 증거. 경제적 가치는 거래비용 포함 포트폴리오에서만 나타나 조달 목적과 다름 | DS·PM |
| 04 | Lump-sum vs DCA (Lu·Hoang·Wong 2021) | GBM 몬테카를로, Sharpe vs 경제성과척도(EPM) | 상승추세에서도 변동성 크고 기간 길면 DCA가 자주 우위, DCA 수익은 양의 왜도라 SR이 이를 놓침(Abstract Findings; §4 식(10)·(11); §5 Table 1~8) | G2 부적합 / 조달 **참고** | 투자자 부 축적 문제이며 고정 톤수 조달과 손익 구조가 다름. 차용할 것은 "왜도 인지 지표로 분할구매 평가"라는 평가 관점(→ regret CVaR) | SC·DS |
| 05 | Cross Hedging CPO (Ahmad 외 2018) | OLS·VAR·VECM 헤지비율, R²=헤지효과 | VECM 기준 FCPO 약 58%, CBOT 대두유 교차헤지 약 28%(CONCLUSION, Table 6); 주간 평균가·최근월(METHOD) | G2 부적합 / 조달 **참고** | 아시아 실물 대비 CBOT 유지 선물의 헤지효과가 낮을 수 있다는 정성 근거. 표본내 추정·평균가 사용으로 수치 이전 불가. 방법(ΔCIF 대리변수의 ΔZL 회귀 R²)은 basis 층 진단에 차용 | SC·CA |
| 06 | EnCQR (Jensen·Bianchi·Anfinsen 2022) | 분리 블록 앙상블 QR + 슬라이딩 잔차 컨포멀 | 교환가능성 없이 근사 유효·국소적응 구간(Abstract, §III 알고리즘 2); QR 단독은 과소포괄, CP 단독은 고정폭(§V); 시간당 에너지 5개 자료·α=0.10·B=3(§IV-A·§IV) | G2 **조건부 채택** / 조달 해당 없음 | modeling.md 챔피언 보정층과 정합. 다만 일별·h=60 중첩 라벨에서는 블록 경계에 h일 purge가 필요하고 B개 블록이 서로 다른 레짐을 학습함. 분위수 LightGBM 등 QR 챌린저의 보정층으로 쓰고, 기준선에는 더 단순한 정규화 컨포멀을 씀 | DS |
| 07 | Hedging: Anything Beat Naïve? (Wang·Wu·Yang 2015) | 최소분산 헤지 18모형 vs 1:1 naive, DM·MCS | 24개 선물(대두유 포함) 주간 1994~2011에서 naive가 MCS에 23/24 포함, 대두유는 MCS가 거의 전 모형 포함(§5.1, Table 4·5); 거래비용 고려 시 시변 헤지 열위(§6) | G2 부적합 / 조달 **채택(기준선)** | 헤지 오버레이의 기준선은 naive 1:1과 롤링 OLS로 충분. 단 대두유 현물은 Decatur 조유(Table 2)로 미국 내 basis라 아시아 CIF basis 불일치는 미반영 | SC·DS |
| 08 | LLM-Enhanced Black-Litterman (Lee 외 2025) | LLM 반복응답 평균=뷰, 분산=Ω | S&P500 상위 50종목·13개월(2024.6~2025.6, §3.1); Ω=N=100 반복 예측 분산(§3.3); 상위 LLM 포트폴리오가 기준선 상회(§5) | **부적합** / **부적합** | 평가 기간이 LLM 학습 기간과 겹쳐 #15의 비식별 문제에 정면으로 걸림; 13개월·주식 대상. Ω=예측분산이라는 아이디어만 원산지 BL 후보에 메모 | DS·PM |
| 09 | Bayesian VaR/CVaR (2023) | GPD 꼬리 + 기반분포 연계 고정보 사전, MH | 표본 부족 시 IPBMH가 가장 정확·정밀, 표본 증가 시 방법 간 차이 소멸(§6 결론 4); 실데이터 IBEX35 2020·2022(§5) | G2 **조건부** / 조달 **조건부** | h=60 독립 표본 약 56개로 95% 꼬리·CVaR 추정이 불안정하므로 표준화 잔차 꼬리의 안정화 챌린저로 적합. i.i.d.·기반분포 가정 필요, 구현비 중간 | DS·PM |
| 10 | Operational vs Financial Hedging (Xing 외 2022, POMS) | 경쟁 2제조사 게임, 금융헤지·현물거래·결합 | 결합전략이 현물거래 단독을 지배하나 금융헤지 단독을 늘 이기지는 못함(Abstract, §8); 중국 대두 압착업체 보정(§7.1)에서 시장규모·변동성·수요불확실성이 커질수록 금융헤지 단독으로 이동(§8) | G2 부적합 / 조달 **참고** | 금융헤지와 운영적 유연성이 보완관계라는 정성 근거. 수요·경쟁 파라미터는 내부 데이터 금지로 보정 불가 | SC·CA |
| 11 | Procurement in Assembly Systems (Yang 외 2020, AOR) | GBM 가격, 리드타임, 시점 유연 계약 → 최적정지 | 시점 유연 계약 가치는 μ≤0에서 0에 가깝고 μ>0에서 큼(§7); 최적정책은 상·하향 기준가격(base-price) 정책(§5, Abstract); 리드타임 불확실 시 물량 보수·시점 공격(Abstract) | G2 부적합 / 조달 **참고** | "임계가격 규칙"이 구조적으로 최적이라는 근거(D-051 ② 사전 그리드와 정합). 그러나 가치가 드리프트 부호에 달려 있고 드리프트는 예측 불가(#03) → 유연성 가치는 시나리오로만 제시 | SC·DS |
| 12 | Procurement Portfolio VoI (Merzifonluoglu 2026, AOR) | 선도·옵션·현물 3채널 다단계 확률계획, CVaR, 정보가치 | 정보 갱신 반영 3단계 모형(§3, Fig.1)·CVaR 모형(§3.2.1); 위험회피자의 수요·공급차질 정보가치는 위험중립자보다 현저히 작음(§5.3, Fig.4·5); 차질-현물가 상관이 백업 공급원 가치를 높임(§6) | G2 **참고** / 조달 **채택(설계 정본)** | modeling.md G3 정본과 동일. 시사점: 위험회피 조달자에게는 "더 날카로운 예측"보다 "정직한 꼬리 보정"의 가치가 큼 → G2 우선순위를 보정에 둠 | SC·PM |
| 13 | RV Forecasting Agri Futures (Tian·Yang·Chen 2017) | MS-ARFIMA(장기기억+레짐전환) 실현변동성 | 5분 자료 기반 RV가 장기기억과 레짐전환을 동시에 보임(Abstract, DATA 절); 롤링 N=1000, h=1·5·20 밀도예측에서 우위(FORECAST EXERCISE, WLR 검정); 대두유 포함(Table 1) | G2 **조건부** / 조달 해당 없음 | 폭 층에 장기기억+레짐 성분이 필요하다는 근거. 단 중국 시장 2006~2012, 경쟁모형이 자기 모형의 중첩형뿐(HAR 미비교), h=60 없음, 일중 자료·MCMC 필요 → HAR(장기기억 근사)+2상태 레짐을 먼저 쓰고 MS-ARFIMA는 챌린저 | DS·CA |
| 14 | Contingent Option Contracts (Fu 2015, IJPE) | 예약가+시가할인 행사 옵션 계약 포트폴리오, 위험중립 vs CVaR | CVaR 해는 예약 비용을 더 써 최악 비용을 막고 평균을 약간 희생(§7); 반복 결정과 1회성 결정을 구분해 목적함수를 고를 것(§7); 변동성 영향(§6.3) | G2 부적합 / 조달 **조건부** | ZL 콜옵션 상한(cap)·공급자 가격상한 계약 비교의 틀. ZL 옵션 데이터(Databento 승인) 확보 후 G3 시뮬레이션에 반영. 월별 반복 조달은 평균, 연간 예산은 CVaR로 병기 | SC·PM |
| 15 | The Memorization Problem (Lopez-Lira 외 2025) | LLM 경제예측의 사전기억 검정 | 학습기간 내 예측력은 비식별(Abstract, §2.2); 가짜 컷오프 지시 후에도 정확도 98% 유지(§5.5, Table 6); 마스킹 실패(§5.6); 컷오프 이후만 평가(§6) | G2·조달 **채택(거버넌스 규칙)** | P1-05 ABSA·Perplexity 등 LLM 파생 피처는 2012~2025 백테스트에서 오염 가능 → 컷오프 이후 shadow 구간에서만 평가 | DS·PM |
| 16 | Deep Black-Litterman Supplier Allocation (2024) | STGNN 뷰 생성 BL, 순위 감독 | 401개 공급자 240주·218개 731일 자료(§5.1.1); HR@K·MRE 평가(§5.1.3) | **부적합** / **부적합** | 원산지 3~4개·내부 공급자 데이터 금지(D-021) 조건과 규모·데이터 불일치; 평가지표도 조달원가와 무관 | PM·SC |

### 2.1 관점 간 이견과 해소

1. **중심(드리프트)** — 원자재 분석 관점: RFS/45Z 정책 레짐·남미 수확 계절성이 분포를 이동시킴. 데이터 과학 관점: 중심 예측은 AR·무변화를 못 이김(#03 §6), B2의 현재 상방 치우침은 창 안의 2026년 랠리(+40%)가 드리프트로 들어간 결과임. **해소**: 기준선 중심은 무변화(동일 계약 선물가)로 고정하고, 정책·계절성은 ① 폭(변동성 레짐·월별 승수)과 ② 별도 사건 오버레이로만 반영함. 드리프트 피처는 §4 게이트를 통과할 때까지 챌린저.
2. **coverage 대 폭** — 조달 실무 관점: 현재 60일 밴드가 가격의 43~51%라 의사결정에 쓰기 어려움. 데이터 과학 관점: B2는 coverage 부족 16.5%p로 c03 §4 기준(5%p 이내)을 위반, 넓은 밴드가 정직한 상태임. **해소**: 보정 우선. 의사결정에는 80% 대신 50% 구간(P25~P75)과 단측 분위수(P75·P90 초과확률)를 쓰고, 폭이 넓은 이유(현재 EWMA 변동성 분위)를 함께 표시함. ZL 옵션 내재변동성은 교차점검용 폭으로 병기.
3. **창 길이** — 원자재 분석 관점: 짧은 창이 2026 레짐에 빨리 적응. 데이터 과학 관점: B2-120은 coverage 51.2%로 더 나쁨, FHS-750은 폭 33.9%로 과대. **해소**: 규모(scale)는 짧은 기억의 EWMA, 모양(shape)은 긴 창의 표준화 잔차로 분리함(#06 §V의 QR·CP 상보성과 같은 논리).
4. **futures-only 대 도착원가** — 조달 실무 관점: ZL과 7IF가 2026-04 이후 괴리, 100 MT 인도 수입자 ZL 헤지 손실 USD 9,160(톤당 약 91.6) 대 7IF 0이라는 사실은 선물 밴드만으로 CIF 위험을 설명 못함을 뜻함. PM 관점: 7IF 이력 약 8개월, 관세청 CIF는 월별·지연. **해소**: 2층 구조로 분리 출력, basis 층은 "참고 범위"(A-191) 지위로 시작하고 7IF 이력 12개월 이상 누적 시 재평가.
5. **헤지비율** — 데이터 과학 관점: naive가 거의 지지 않음(#07 Table 5). 조달 실무 관점: basis 불일치 하에서는 h<1이 분산 최소일 수 있음. **해소**: naive 1:1과 롤링 OLS(CIF 대리변수 기준)를 함께 기준선으로 두고, 정교화 모형은 거래비용 차감 후 DM/MCS로 둘 다 이길 때만 추가.
6. **LLM 활용** — 원자재 분석·PM 관점: 뉴스·정책 신호 자동화 수요. 데이터 과학 관점: #15로 학습기간 내 평가는 비식별. **해소**: LLM 파생 신호는 G2 학습 표본에 넣지 않고 모델 컷오프 이후 shadow 평가로만 승격 판단.

---

## 3. 기초 프레임워크(층 구조)

```
(a) 중심   : log F_t(동일 계약) , μ_h = 0                       ─┐
(b) 폭     : σ_{t,h}  = EWMA(λ_h) → HAR-direct → 레짐 보정        ├─ G2 선물 밴드 P10~P90 (1/5/20/60)
(c) 모양·보정: z = r_h/σ_{t,h}, 꼬리별 롤링 컨포멀(+레짐 Mondrian) ─┘
(d) 2층 범위: 선물 밴드 ⊗ basis·운임·환율 결합 시뮬레이션 → 도착원가 밴드(참고)
(e) 조달 계층: 정책 묶음 × 경로 시뮬레이션 → 톤당 regret 평균·CVaR·VoI (권고 아님)
```

### (a) 중심·드리프트
- 타깃은 동일 계약 로그수익률 r_{t,h} = ln(F_{t+h}/F_t)(R-046 라벨 규칙), P50 기준 = F_t·exp(σ_{t,h}·ẑ_{0.5})(보정된 잔차 중앙값만 허용, 추세 외삽 금지).
- 근거: #03(중심 예측 무가치), 선행 검토의 무변화 기준선 지배 결론. B2가 과거 수익률 경험분위를 그대로 쓰는 구조는 창 안 추세를 드리프트로 수입하므로 폐기 대상임.
- 계절성·정책은 중심에 넣지 않음. 챌린저로만 "월 더미·정책 사건 더미의 수익률 효과"를 §4 게이트와 지터 검정(modeling.md 6-1)으로 시험.

### (b) 변동성·폭
- 1단계(B4 기본): EWMA 일분산 σ²_t = λσ²_{t−1} + (1−λ)r²_{t−1}, 지평 분산 σ²_{t,h} = h·σ²_t. 오늘 백테스트에서 이미 B2를 크게 이김(60일 coverage 75.9% vs 63.5%, pinball 22.2 vs 25.2).
- 2단계(챌린저): HAR-direct — 지평별로 log(RV_{t→t+h}/h)를 log RV_d·RV_w(5)·RV_m(22)·RV_q(66)에 회귀. 장기기억을 근사하고(#13의 장기기억 증거), 60일에서 변동성 평균회귀를 반영해 EWMA×√h 과대·과소를 교정함. RV 대리변수는 일중 자료 확보 전까지 일별 수익률 제곱(가능 시 OHLC 범위 추정량).
- 3단계(챌린저): 2상태 레짐(log RV_22에 대한 Markov switching 또는 EWMA 변동성 분위 임계) — 폭 승수와 (c)의 Mondrian 보정 기준으로 사용. MS-ARFIMA(#13)는 일중 자료 확보 후 별도 챌린저.
- 교차점검: ZL 옵션 만기 정합 내재변동성 σ_IV·√(h/252)를 위험프리미엄 축소비(as-of 추정 실현/내재 비율)로 조정한 폭을 병기(선행 검토 G2 3순위).

### (c) 분포 모양·보정
- 표준화 잔차 z = r_{t,h}/σ_{t,h}에 대해 **하단·상단 꼬리를 따로** 분할 컨포멀 분위수를 계산(#01 단측 임계분위수 보정, #06 CQR의 비대칭 구간). 산출 분위수 q_τ = σ_{t,h}·ẑ_τ, τ ∈ {0.10, 0.25, 0.50, 0.75, 0.90}, 95% 구간(0.025/0.975)은 보고 전용.
- 보정집합에는 **결과가 이미 실현된 쌍만** 넣음(예측일 s, s+h ≤ t). h=60에서 최근 60일 잔차를 넣으면 미래 정보 누출임 — 오늘 백테스트 코드도 이 조건을 재확인해야 함.
- 레짐 Mondrian: 저·고변동 두 칸으로 나눠 보정하되 칸별 실현 쌍이 하한 미만이면 통합(#01 §5의 품질-수량 상충).
- 적응 갱신(선택): 실현 coverage 오차로 τ를 조정하는 ACI형 갱신(선행 검토 근거)을 h일 지연 피드백으로만 적용.
- QR 챌린저(분위수 LightGBM 등)는 EnCQR(#06)로 보정하되, 블록 경계마다 h일 purge·embargo를 둠.
- 꼬리 안정화 챌린저: 95% 꼬리·CVaR에 GPD 고정보 사전 베이지안 추정(#09) — 표본 부족 시에만 의미가 있음(#09 §6 결론 4).

### (d) 2층 범위 = 선물 범위 + basis·도착원가 범위
- 도착원가(USD/MT) = ZL(¢/lb)×22.0462 + 원산지 basis(FOB 프리미엄 또는 CFR 스프레드) + 운임, 원화 환산은 KRW/USD(T+2, M-002), 관세·부대비용은 정책 상수(별도 확인).
- basis 대리변수 우선순위: ① 7IF(CFR India)−ZL 환산 스프레드(아시아 CFR 직접 대리, 2026-03 상장·이력 짧음 → 실시간 감시·스트레스 시나리오용) ② 관세청 원산지별 CIF 단가−선적 리드타임(40~50일) 정렬 ZL = "CIF 잔차"(월별·장기 이력, 계약시점 불일치 잡음) ③ 품질조정 CFR 스프레드 범위(modeling.md G3 원산지 prior).
- 결합: (ZL 표준화 잔차, Δbasis, ΔFX) 과거 삼중항을 같은 날짜 블록으로 부트스트랩해 상관을 보존하고, ZL은 (c)의 보정 분위 함수로 재척도화한 N=10,000 경로 시뮬레이션. basis는 분기(남미 수확기 4~7월 등) 일치 블록에서만 추출.
- 진단: ΔCIF 대리변수의 ΔZL 회귀 R²를 헤지효과 상한으로 보고(#05 방법). 7IF 괴리 사례(톤당 약 USD 92)는 basis 층 스트레스 시나리오의 하한 사례로 등록.
- 지위: 도착원가 밴드는 "참고 범위"(A-191)이며 G2 승격 대상이 아님. 과점적 실물 교역은 선물보다 basis에 영향을 준다는 점(선행 검토)을 근거로 basis 층의 꼬리를 선물 층과 독립 점검함.

### (e) 조달 의사결정 계층(시뮬레이션·지표만, 권고 없음)
| 구성 | 설계 | 근거 |
|---|---|---|
| 예산 분위 (newsvendor-conformal) | 최종 결정자가 정한 비용 비대칭 c_u(예산 초과 비용)·c_o(과대 예산 비용)로 τ* = c_u/(c_u+c_o) 산출, 도착원가 P_τ*를 단측 보정으로 별도 검증 | #01 알고리즘 1 |
| 일시 vs 분할 | LS(즉시 전량) · 균등 톤수 k=2/3/4 분할(60일 내) · 고정금액 DCA · 임계가격 규칙을 정책 묶음으로, 톤당 regret 평균·SD·왜도·CVaR95 보고 | #04 평가 관점, #11 base-price 구조, D-051 |
| 헤지 vs naive | 헤지비율 {0, 1:1 naive, 롤링 OLS(104주, CIF 대리변수)}; 헤지효과 = 1−Var(헤지)/Var(무헤지), DM·MCS | #07 Table 4·5, #05 |
| 옵션 계약 | ZL 콜 상한(행사가 = G2 P75·P90 근방) 프리미엄 비용 대 꼬리 절감을 위험중립·CVaR 두 목적함수로 병기 | #14 §7, #12 3채널 |
| 데이터 기반 규칙 | 선적월 커버 비율을 피처 함수로 학습하는 DDA(정규화 필수, 결정단위 거칠게) | #02 §6.4 |
| 원산지 배분 | 평균-CVaR 배분은 basis 층 데이터 확보 후; BL은 뷰가 as-of 신호·Ω가 예측오차 분산일 때만, LLM 뷰 금지 | #08·#16 부적합, #15 |
| 정보가치(VoI) | 완전정보 경로 대비 regret 감소분으로 "더 나은 예측"의 가치 상한 산출, 위험회피도별 비교 | #12 §5.3 |
| VaR/CVaR | 톤당 regret·도착원가의 VaR95·CVaR95, 표본 부족 시 #09 베이지안 꼬리 챌린저 | #09, #12 §3.2.1 |
| 운영 유연성 | 현물 보충·금융헤지 결합은 정성 시나리오로만(수요 데이터 금지) | #10 §8 |

---

## 4. 구체 파라미터

| 항목 | 기본값(B4) | 탐색 그리드·챌린저 | 비고 |
|---|---|---|---|
| 타깃 | 동일 계약 정산가 로그수익률, h ∈ {1, 5, 20, 60} 직접 예측 | 롤 걸친 구간 coverage 별도 | R-046, Databento 정산가 |
| 분위수 집합 | P10·P25·P50·P75·P90(+P2.5·P97.5 보고 전용) | CRPS 계산용 내부 19분위(0.05~0.95) | 출력 계약 유지 |
| 중심 | μ_h = 0 | 월·정책 더미 드리프트(챌린저) | 추세 외삽 금지 |
| EWMA λ | h=1·5: 0.94(반감기 약 11일), h=20·60: 0.97(약 23일) | {0.94, 0.97, 0.985(약 46일)} 내부 walk-forward pinball로 지평별 선택 | 초기값 60일 표본분산 |
| HAR 시차 | RV_d(1)·RV_w(5)·RV_m(22) + h=60에 RV_q(66), 로그 회귀 | 월 더미(계절 승수) 추가 | 확장창, 월 1회 재적합 |
| 레짐 | 미사용 | 2상태 MS(log RV_22) 또는 EWMA 변동성 3년 분위 67% 임계 | 분기 재적합 |
| 컨포멀 보정창(실현 쌍) | h=1·5: 500, h=20: 750, h=60: 1000 | {500, 750, 1000}, 점수 지수가중(반감기 250) 챌린저 | s+h ≤ t 쌍만, 유한표본 보정 ⌈(n+1)(1−α)⌉/n |
| Mondrian 칸 | 통합 | 저·고변동 2칸, 칸당 실현 쌍 ≥150일 때만 | #01 품질-수량 |
| ACI 갱신 | 미사용 | γ ∈ {0.005, 0.01}, h일 지연 피드백 | 챌린저 |
| coverage 목표 | 80% 구간 수용 75~85%, 50% 구간 45~57% | 95% 구간 보고 | c03 §4: 부족 5%p 이내, 과대 +7%p 초과 시 "과폭" 표시 |
| 재적합 주기 | EWMA·보정집합 일별, λ·HAR 월 1회(첫 거래일), 레짐 분기, QR 챌린저 월 1회 | — | 스냅샷 매니페스트 동결 |
| 검증 방식 | expanding walk-forward 2012~, 지평별 h일 purge | sliding 3년 병행 | random split 금지(M-001) |
| lockbox | 2026-11-20 이후 사전 등록 전향 기록(완전 미사용) + 2026 YTD shadow | — | 2025는 오늘 비교에 이미 사용되어 lockbox 자격 상실 |
| coverage 검정 | 꼬리별 Kupiec POF(하단 10%·상단 10%), Christoffersen 독립성 | h=20·60은 h개 엇갈린 비중첩 부분표본별 검정 후 p값 중앙값·최솟값 보고 | 중첩 위반은 구조적 자기상관 |
| 점수 | pinball(분위별·평균), CRPS(19분위 근사), Winkler(80%·50%), 평균 폭(가격 대비 %) | 레짐·stress slice별 | 단일 평균 점수 금지 |
| 유의성 | DM(HAC, Newey–West 시차 h−1) | MCS(블록 부트스트랩) | 60일 독립 표본 약 56개 → coverage 표준오차 약 ±5%p |
| 승격 규칙 | ① 4개 지평 중 60일 포함 3개 이상에서 coverage 수용 범위 ② pinball·CRPS가 현 챔피언 대비 3개 지평 이상 비열위, 1개 이상 DM p<0.10 ③ stress slice 80% coverage 60% 미만 없음 ④ 폭 >1.25×챔피언이면 coverage 개선분 입증 ⑤ c03 §4 나머지 조건 | — | B2는 ①에서 탈락(60일 63.5%) |

**오늘 수치에 대한 판정**: 60일에서 EWMA-정규(75.9%, 폭 29.2%, pinball 22.2)와 EWMA+컨포멀(77.6%, 33.6%, 22.2)은 모두 수용 범위이며 pinball이 같음. 두 coverage 차이 1.7%p는 표준오차(약 5%p) 안이라 통계적으로 구분되지 않음. 분포 가정 없이 coverage를 지키는 장치라는 점에서 EWMA+컨포멀을 B4 챔피언 기준선으로, EWMA-정규를 B4a 병행 비교군으로 두고 Winkler·CRPS·stress slice 결과로 확정할 것을 제안함. 현재 51% 폭은 2026년 실현변동성이 보정집합에 들어간 결과이며, 충격 직후 과대포괄은 컨포멀의 알려진 성질(선행 검토)이므로 옵션 내재변동성 폭과 병기해 해석함.

---

## 5. 순차 로드맵·데이터·위험·결정 사항

### 5.1 로드맵(앞 단계가 뒤 단계의 승격 기준)
| 단계 | 내용 | 산출·완료 조건 | 의존 |
|---|---|---|---|
| 0 (1~2일) | 평가 하네스 동결: 동일 계약 라벨, 실현 쌍 규칙(s+h ≤ t) 점검, Kupiec·Christoffersen(엇갈린 부분표본)·pinball·CRPS·Winkler·DM-HAC, stress slice, 전향 lockbox 등록 | `metrics.json` 스키마·매니페스트, 오늘 결과 재현(차 <0.5%) | 없음 |
| 1 (1~2주) | B4 = EWMA(λ_h)+꼬리별 롤링 컨포멀을 챔피언 기준선으로 등록, B2 강등, G2 preview 표시 교체(50% 구간·폭 사유 병기) | 4개 지평 coverage·폭 표, 레짐별 coverage | 0 |
| 2 (2~3주) | HAR-direct 폭, 레짐 Mondrian, 월 계절 승수 챌린저 | §4 승격 규칙 판정 | 1 |
| 3 (병행) | ZL 옵션 EOD 수집 → 만기 정합 IV, 위험프리미엄 축소비 as-of 추정, IV 폭 챌린저(20·60일 중심) | IV 폭의 coverage·Winkler | 데이터 확인 |
| 4 (병행) | basis 층: 관세청 원산지별 CIF 잔차 구축, 7IF 가용성·이력·유동성 확인, 2층 도착원가 시뮬레이션(참고 범위) | ΔCIF~ΔZL R², 분기별 basis 분포 | 1, 데이터 |
| 5 | 조달 계층 시뮬레이션(G3): LS·k분할·DCA·임계가격 규칙, naive·OLS 헤지, 콜 상한, regret CVaR, VoI | 정책별 톤당 regret 분포표(권고 문구 없음, HITL §6) | 1, 3, 4 |
| 6 (후순위) | 분위수 LightGBM+EnCQR, MS-ARFIMA(일중 자료 시), DDA 구매규칙, 베이지안 GPD 꼬리 | 각 챌린저 §4 판정 | 2~5 |
| 동결 | LLM-BL(#08), DBLM(#16), 학습기간 내 LLM 예측·LLM 파생 피처 백테스트 | — | #15 규칙 |

### 5.2 데이터 요구
- 보유·승인: Databento ZL 정산가(타깃), ZL 옵션(승인) — 확인 필요 항목: 옵션 EOD 이력 연수, 행사가·만기 범위, 정산 IV 제공 여부(없으면 Black-76 역산), 근월 외 유동성.
- 확인 필요: **7IF(CBOT South Asia Soybean Oil, CFR India)** — Databento CME Globex 데이터셋 포함 여부, 상장(2026-03) 이후 일별 정산가·미결제약정, 라이선스 비용. 이력이 짧으므로 분포 추정이 아니라 실시간 basis 감시·스트레스 시나리오에만 사용.
- 구축 필요: 관세청 원산지별(미·브라질·아르헨티나) 대두유 수입 단가·물량 월별(vintage 적재), KRW/USD(ECOS, T+2), 운임 대리변수(BDI; BCAA는 미구매), EPA RFS·45Z 사건 달력(published_at·effective_from 분리, D-023).
- 선택: ZL 일중(5분) 자료 — HAR·MS-ARFIMA의 RV 품질 개선용, 비용 대비 효과는 2단계 결과를 보고 판단.

### 5.3 위험
1. **유효 표본 부족**: 60일 비중첩 표본 약 56개 → coverage 판정 오차 ±5%p 수준. 2~4%p 차이로 모형을 바꾸지 않음.
2. **누출**: 미실현 라벨의 보정집합 유입, 중첩 라벨의 EnCQR 블록 경계, 전체기간 λ 선택, LLM 사전기억(#15).
3. **구조변화**: 바이오연료 정책 레짐 전환 시 충격 직후 과소, 이후 과대포괄(컨포멀의 시차). 2026 shadow slice와 사건 오버레이로 분리 보고.
4. **basis 불일치**: 선물 밴드가 CIF 위험을 과소 대표(7IF 사례). 도착원가 층 없이 선물 밴드만으로 예산을 말하지 않도록 표시 규칙 필요.
5. **내재변동성 편향**: 위험프리미엄으로 과대 폭, 원 그대로 쓰면 과대포괄(선행 검토).
6. **데이터 가용성**: 7IF 이력·유동성, 관세청 CIF의 월별 지연과 계약시점 불일치, 옵션 원가.
7. **과설계**: #02·#13류 복잡 모형은 표본내 우위가 표본외에서 소멸하는 사례가 반복됨(#02 Table 4 DDA-BD, #07 §6).

### 5.4 최종 결정자 결정 필요 사항
1. B2 → B4(EWMA+꼬리별 롤링 컨포멀) 챔피언 기준선 교체와 §4 승격 규칙 채택 여부(modeling.md "Champion" 표기 조정은 별도 결정 사항).
2. coverage 수용 범위(80%: 75~85%, 50%: 45~57%)와 G2 화면의 주 표시 구간(50% 대 80%).
3. 전향 lockbox 시작일(2026-11-20)과 "2025 lockbox 자격 상실" 처리 승인.
4. 7IF 데이터 가용성 확인과 비용 지출 여부, basis 층을 "참고 범위"로 공개할지 여부.
5. ZL 옵션 EOD 이력 수집 범위(연수)와 일정.
6. LLM 파생 피처를 G2 학습·검증 표본에서 배제하고 컷오프 이후 shadow로만 평가하는 규칙 승인.
7. 조달 계층 시뮬레이션 정책 묶음 범위(LS·k분할·DCA·임계가격·naive/OLS 헤지·콜 상한)와 예산 분위 τ*에 쓸 비용 비대칭(c_u : c_o) 기준.

---

## 부록. 검토 논문 목록(파일 ↔ 원제)

| 파일 | 원제 |
|---|---|
| g2_01 | A Conformal Approach to Feature-based Newsvendor under Model Misspecification |
| g2_02 | Data-Driven Optimization for Commodity Procurement Under Price Uncertainty |
| g2_03 | Distilling Large Information Sets to Forecast Commodity Returns: Automatic Variable Selection or Hidden Markov Models? |
| g2_04 | Do lump-sum investing strategies really outperform dollar-cost averaging strategies? |
| g2_05 | Effective Cross Hedging: Evidence from Physical Crude Palm Oil and its Inter-Related Agricultural Futures Contracts |
| g2_06 | Ensemble Conformalized Quantile Regression for Probabilistic Time Series Forecasting |
| g2_07 | Hedging with Futures: Does Anything Beat the Naïve Hedging Strategy? |
| g2_08 | LLM-Enhanced Black-Litterman Portfolio Optimization |
| g2_09 | New Bayesian method for estimation of Value at Risk and Conditional Value at Risk |
| g2_10 | Operational hedging or financial hedging? Strategic risk management in commodity procurement |
| g2_11 | Optimal procurement strategies for contractual assembly systems with fluctuating procurement price |
| g2_12 | Procurement portfolio management for resilient supply chains: value of information for risk averse decision making |
| g2_13 | Realized Volatility Forecasting of Agricultural Commodity Futures Using Long Memory and Regime Switching |
| g2_14 | The impact of alternative performance measures on portfolio procurement with contingent option contracts |
| g2_15 | The Memorization Problem: Can We Trust LLMs' Economic Forecasts? |
| g2_16 | Time Series Supplier Allocation via Deep Black-Litterman Model |

위치 표기는 변환 Markdown에 쪽 번호가 없어 절·표·그림·식 번호로 대체했음. 정밀 인용(설계 문서·외부 보고) 전에 PDF 원문의 쪽 번호와 대조가 필요함.
