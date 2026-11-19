# 전쟁·지정학 충격의 공급·수요·가격 파급 정량화 — 방법 조사와 선정 근거 (R-039)

**작성**: 2026-09-25 · **요청**: 최종 결정자 — "정유시설 파괴·지정학 분쟁(EU–러시아, 미국–이란, 캐나다)이 공급·수요·가격에 미치는 영향의 범위와 메커니즘을 수치(범위)로 정량화하는 방법을 선례와 함께 조사하고, 현재 보유 데이터에 맞는 방법을 선정해 근거를 정리"
**관점 협의**: 시장 조사(선례·전달 경로) · 데이터 과학(방법 적합성·누수 규율) · 조달 실무(도착가 번역·오용 위험) · PM(범위·결정 대기)
**판독 규율**: CONFIRMED(1차·공식·동료심사) / INFERENCE(2차·추정) / DATA GAP(미확인). 본 문서는 **과거 충격에서 관측된 반응과 방법 설명**만 담으며, 향후 방향·확률 주장은 하지 않는다(A-191). '캐나다'는 승인자 확인에 따라 **①미국·중국–캐나다 통상 분쟁(카놀라·원유 교역 전환)**과 **②캐나다 정유·오일샌드 공급 차질(산불·사고)** 두 시나리오를 함께 다룬다.

---

## 1. 한 줄 결론

- **메커니즘은 다섯 경로로 정리되며 그중 셋은 이미 검증된 인과 경로(온톨로지)로 등재돼 있다** — ①원유·정제 차질 → 경유 크랙 → 바이오디젤 경제성 → 대두유 산업 수요(검증됨), ②해협·항로 위험 → 탱커 운임·전쟁위험보험료 → 한국 도착가(검증됨), ③흑해 회랑 차단 → 해바라기유 공급 → 대체 유지 수요(후보), ④관세·무역 전환 → 대체 유지(카놀라) 흐름 재편(후보), ⑤원유 생산 차질(오일샌드) → 원유가 → ①.
- **외부 문헌은 원유·크랙·보험료·운임 반응은 정량으로 주지만, 대두유·한국 도착가의 직접 반응 수치는 거의 주지 않는다(DATA GAP)**. 그 공백은 자체 보유 계열(시카고 정산가 15개년·에너지·운임 일별·관세청 월별 도착가)로 **사건 연구(M1)·국소투영(M2)·유사 국면 조건부 분포(M5)**를 돌려 채울 수 있다 — 세 방법 모두 지금 실행 가능하다.
- **선정: 하이브리드 = M5(범위) + M2(시차·크기) + M6(도착가 시나리오 층)**, M1은 선례 검증용. 구조 VAR(M3)은 외부 월별 원유 생산·실물활동 지수가 없어 부분 가능(Challenger), 일반균형(M7)은 범위 밖.
- 첫 산출(프로토타입)은 `reports/market/shock_response_prototype_2026-09-25.md`에 실었다(§8) — 진단 계열(정산가 아님) 기준의 1차 수치이며, 정본 계열로 재산출은 CI 통합 표에서 후속.

---

## 2. 질문 정의와 범위

| 요인 | 무엇이 바뀌나(물리) | 대두유·도착가로 가는 경로 | 온톨로지 상태 |
|---|---|---|---|
| 정유시설 파괴(러시아 정유소 피격, 미 걸프 허리케인, 캐나다 정유소 사고) | 정제 능력 정지 → 경유·휘발유 공급 감소 → 크랙 스프레드 확대 | 경유 가격 ↑ → 바이오디젤·재생디젤 혼합 경제성 ↑ → 식물성유지 산업 수요 ↑(미국 RFS/45Z·EU RED) | CE-020 검증됨 |
| EU–러시아(제재·금수·흑해) | 러시아산 제품 금수·수출 금지 → 유럽 경유 부족; 흑해 항만 공격 → 회랑 차단 | ①경유 경로 + ③해바라기유 수출 차단 → 대체 유지 수요 | CE-020 검증됨 · CE-014 후보(대두유 가격 서술 금지) |
| 미국–이란(호르무즈) | 탱커 통항 감소·공격·전쟁위험보험료 급등, 원유·제품 공급 교란 | ②탱커 운임·보험료 → 한국 도착가 잔차(운임층) + ①원유가 경로 | CE-010·CE-013 검증됨 |
| 캐나다 ① 통상 분쟁 | 중국의 카놀라유·박 100%(2025-03)·카놀라씨 75.8%(2025-08) 관세, 미국 관세 | 카놀라유가 북미 바이오연료 원료로 전환 → 대두유 대체·경합 수요 | CE-011 후보(무역 정책) |
| 캐나다 ② 공급 차질 | 산불(2016 포트맥머리 1.0~1.5 mb/d 정지)·정유소 사고(2018 어빙) | 원유가·미 북동부 제품 공급 → ① | 배경(직접 엣지 없음) |

---

## 3. 선례 인벤토리 (요약 — 상세·출처는 부록 A)

| 선례 | 물리 충격 | 관측된 가격·운임 반응 | 시간 구조 | 라벨 |
|---|---|---|---|---|
| 2019-09 아브카이크 공격 | 원유 5.7 mb/d(세계 ~5%) 일시 정지 | Brent +14.6%(1일) | 2 mb/d 48시간 내 복구, 가격은 약 2주 내 복원 | CONFIRMED |
| 2022-02 러–우 전쟁 | 해바라기유 수출국 점유 ~75%(UA 50·RU 25) 차단 | FAO 식물성유지 지수 251.8(사상 최고, +23.2% m/m) · 시카고 대두유 ~87¢/lb(2022-05) · 흑해 전쟁보험 선가 10% → 1~5% | 급등 후 수개월 고점, 2022 하반기 되돌림 | CONFIRMED/INFERENCE |
| 2023-02 EU 러시아 제품 금수 | EU 경유 수입의 약 절반 차단 | 유럽 경유 크랙 ~$8 → $40 → $63/bbl | 금수 전후 수개월 | INFERENCE(시장 데이터 인용) |
| 2023-09 러시아 경유 수출 금지 | 최대 수출국 공급 차단 | 국내 재고 +14% 후 2개월 만에 해제 | 단기 | INFERENCE |
| 2024~26 러시아 정유소 피격 | 정제 능력 약 1/4 정지(2026-05, Reuters 집계) | 러시아 휘발유·경유 공급 축소, 수출 금지 재발(2026-07) | 반복·누적 | INFERENCE |
| 2023-11~ 홍해 후티 | 수에즈 통과 −50~60%, 희망봉 우회 +10~14일 | 전쟁보험료 0.05% → 0.7~2% 선가, 운임 +30~40% | 6개월 이상 지속 | INFERENCE |
| 2026 호르무즈(미–이란) | 통항 1척/일(기준 85), 원유·제품 10~15 mb/d 교란 | Brent 기록 $144.42(4/7), 현물–선물 백워데이션 >$25/bbl, 전쟁보험 평시 ~40배 | 개전 2월 말 → 6월 완화 → 7월 말 재격화 → 9월 지속(207일째) | INFERENCE(LMA 성명만 1차) |
| 2005 카트리나·리타 | 미 정제 능력 최대 4.9 mb/d(29%) 정지 | 휘발유 −1 mb/d, 크랙 급등 | 해상 생산 10개월 차질 | CONFIRMED |
| 2017 하비 | 걸프 가동률 96 → 63%, 투입 −3.2 mb/d | 미 휘발유 소매 +28¢/gal(1주) | 수 주 | CONFIRMED |
| 2025 중–캐나다 카놀라 관세 | 카놀라유·박 100%, 카놀라씨 75.8% | 카놀라 −9%(발표 직후), 2025-09 CAD 610/t 하회, 제3국 전환 +161% | 반년 이상 | INFERENCE |
| 2016 포트맥머리 산불 | 오일샌드 1.0~1.5 mb/d 감산(8월 복구) | WTI 반응 미미(회복 국면과 중첩 — 단독 효과 분리 불가) | 3개월 | CONFIRMED(물량)/INFERENCE(가격) |
| 2010-08 러시아 곡물 수출 금지 | 밀 수출 전면 금지 | 밀 +35.1%(2010)·+19.3%(2011H1); 대두유 저점 38.0 → 고점 57.4¢/lb 약 9개월 +51%(자체 위기 사례 문서 — 외부 교차 확인은 프록시 차단으로 미완) | 9개월 | CONFIRMED(밀)/INFERENCE(대두유) |

**전달 계수(문헌)**: 발틱운임지수 2배 → 46개국 소비자물가 +0.7%p(정점 12개월, 지속 18개월 — 동료심사) · 운임 상승률 1%p → 미국 수입물가 +0.068%p(식품 +0.072%p — 동료심사) · 지정학 위험 지수 충격 → 밀 +2%·옥수수 +1%·유럽 가스 +7.5%(일별 사건 SVAR — 2차 요약). 원유→식물성유지 교차 탄력성(ICCT 2017·ARER 2022)은 원문이 프록시 차단으로 **미열람(INFERENCE)** — 사내망 열람 후 이식.

---

## 4. 메커니즘 도식 (경로별 정량 자리)

```
[정유시설 파괴 · 제재 · 수출 금지]
   → 경유 공급 ↓ → 경유 크랙 ↑ ($8→$40→$63/bbl, 2022~23)
   → 바이오디젤·재생디젤 경제성 ↑ → 식물성유지 산업 수요 ↑ → 대두유 가격 상방 압력   [CE-020 검증됨]

[호르무즈 · 홍해 · 흑해 항로 위험]
   → 통항 감소(85→1척/일) · 우회(+10~14일) · 전쟁위험보험료(선가 0.05%→2%, 평시 40배)
   → 탱커 운임층 ↑ → 한국 도착가 = 시카고 가격층 + 실측 차이층(운임·프리미엄) ↑   [CE-010·CE-013 검증됨]

[흑해 회랑 차단]
   → 해바라기유 수출 −(2022: 세계 교역 75% 차단) → 대체 유지 수요 이동 → (대두유 서술 금지 — 후보 경로)   [CE-014 후보]

[캐나다 통상 분쟁]
   → 카놀라유·씨 관세(100%·75.8%) → 북미 바이오연료 원료 전환·제3국 수출 +161% → 대두유 경합·대체   [CE-011 후보]

[캐나다 공급 차질]  → 오일샌드·정유 정지(1.0~1.5 mb/d) → 원유·제품 가격 → 첫 경로로 합류   [배경]
```

---

## 5. 방법 후보 비교

| ID | 방법 | 무엇을 추정하나 | 필요 데이터 | 산출 형태 | 핵심 가정·한계 | 현 데이터 적합성 |
|---|---|---|---|---|---|---|
| M1 | 사건 연구(event study) | 사건일 전후 비정상 수익률(크기·지속·소멸) | 일별 가격 + 사건일 목록 | 사건별 ±1·5·20·60일 변화율, 백분위 | 단일 사건 추론·동시 사건 혼재 | **가능** — 선례 11건 전부 자체 계열로 계산 가능 |
| M2 | 국소투영(Jordà 2005) | 충격 1σ에 대한 지평별 반응(IRF)·신뢰구간 | 충격 대리(지정학 지수·Brent·운임·경유 크랙) + 반응변수 | h=1/5/20/60 계수·구간 | 충격 식별은 대리 변수 품질에 의존; 60일은 겹침 큼(HAC 필요) | **가능** — 일별 2010~2025; 호르무즈 범주(2026-08~)는 표본 부족 → 지정학 지수·Brent 대용 |
| M3 | 구조 VAR(Kilian 공급·수요 분해, 내러티브 부호 제약) | 유가 변동을 공급·수요·예비수요 충격으로 분해 후 유지류 반응 | 월별 세계 원유 생산·실물활동 지수·재고 | 충격별 IRF·역사 분해 | 식별 가정 강함, 표본 192개월은 경계 | **부분** — 외부 월별 계열 미보유(EIA/IEA·댈러스 연은) → Challenger |
| M4 | 채널 전이 계수 보정(부분균형) | 원유→원료, 운임·보험→도착가, 공급 손실→재고사용비율 탄력성의 곱셈 연쇄 | 탄력성 문헌값 + 자체 회귀(공적분·잔차 회귀) | 시나리오별 $/t 범위 | 문헌 탄력성은 시장·기간 의존(RD붐 전후 분리 필요) | **부분** — 자체 회귀 가능, 문헌 원문 미열람 |
| M5 | 유사 국면 조건부 분포 | 현재 상태와 같은 구간이었던 과거 시점의 이후 실측 분포(P10/P50/P90) | 통합 표(상태 변수·전방 수익률) | 지평별 실측 범위·사례 수 | 통계 검정 없음, 표본 8회 미만 보류 | **가능** — 기구현(`analogue_g1`) 확장: 상태 변수에 Brent·경유 크랙·운임·지정학 지수 추가 |
| M6 | 도착가 시나리오 층(무작위 결합) | 시카고 가격층 ⊕ 운임층 ⊕ 보험층 ⊕ 실측 차이층의 합성 분포에 충격 시나리오 주입 | 관세청 CIF−CBOT 잔차, 운임·보험 선례 % | 시나리오별 도착가 범위 $/t | 층간 의존(위기 구간 코퓰라) 미반영 시 과소분산 | **가능** — 기구현(`landed_cost`) 확장 |
| M7 | 일반균형·네트워크(GTAP·CGE) | 수출 차단·관세의 세계 재배분 | GTAP DB·MRIO | 시나리오 균형가격 | 캘리브레이션 탄력성 의존 | **불가**(범위 밖·Phase B 배경) |

---

## 6. 선정과 근거

**선정: 하이브리드 — M5(범위) + M2(시차·크기) + M6(도착가 번역), M1은 선례 검증·보고 표준.**

1. **데이터 적합성이 결정한다.** 보유 데이터는 일별 15개년 가격·에너지·운임(정산가·TE)과 월별 관세청 도착가이며, 호르무즈 위협 수준 같은 범주 변수는 2026-08 이후만 있다. M5·M2·M1은 이 데이터로 즉시 돌아가고, M3·M7은 외부 월별 계열이나 모델 DB가 필요하다.
2. **산출 형태가 브리프 계약과 같다.** M5는 이미 브리프 '과거 비슷한 시기'가 쓰는 산식(십분위 슬라이스 → 실측 분포)이라, 상태 변수에 Brent·경유 크랙·운임·지정학 지수를 더하면 **"이런 충격 국면에서 과거 대두유가 1주·1개월·3개월 뒤 어떻게 움직였나"**를 같은 형식으로 낸다. 전망·확률 주장 금지 규율(A-191)과 충돌하지 않는다.
3. **M2가 방향·시차·크기의 근거를 준다.** 국소투영은 방법론 정본(modeling.md — 충격 반응)에 이미 등재돼 있고, 충격 대리(Brent 1σ·운임 1σ·지정학 지수 급등)에 대한 지평별 반응과 신뢰구간을 낸다. 구조 VAR보다 식별 가정이 약하고 오지정에 강하다(Jordà·Taylor 2024).
4. **도착가로의 번역은 M6가 맡는다.** 운임·보험 선례(%·배수)를 선가·적재량 가정으로 $/t 환산해 시나리오 층으로 넣으면, 조달 실무가 읽는 단위(달러/톤 도착가)로 나온다. 기존 무작위 결합 계산에 '위기 구간 실측 차이층(2022-03~06·2024-01~06·2026-03~07)'을 스트레스 대안으로 추가한다.
5. **M1은 보고 표준이다.** 선례 11건의 ±1·5·20·60일 실측 변화율과 백분위를 표로 고정하면, 새 충격이 발생했을 때 "과거 어느 선례와 크기가 비슷한가"를 즉시 대조할 수 있다.

**기각·보류 근거**: M3은 세계 원유 생산 월별·실물활동 지수 미보유 + 유지류 SVAR 선례 희소 → Challenger로 등재하되 내러티브 부호 제약(위기 사례 1~4·2026)은 M3 채택 시 우선 검토. M7은 데이터·라이선스 부재. M4는 문헌 원문(ICCT 2017·ARER 2022) 열람 후 자체 회귀와 대조해 보정 계수만 차용.

**캐나다 요인 처리**: ① 통상 분쟁은 M1(2025-03-20·08-12 사건일)과 M5(카놀라−대두유 가격 차이 상태 변수)로, ② 공급 차질은 M1(2016-05-03·2018-10-08)과 M2의 원유 충격 경로로 다룬다. 두 시나리오를 한 변수로 합치지 않는다.

---

## 7. 구현 청사진 (기존 모듈 확장 — 새 시스템 없음)

| 단계 | 내용 | 모듈 | 산출 |
|---|---|---|---|
| S1 | 사건 연구 + 국소투영 프로토타입(진단 계열) | `scripts/shock_response_prototype.py`(신설) | `reports/market/shock_response_prototype_2026-09-25.md` |
| S2 | 유사 국면 상태 변수 확장 — Brent·경유 크랙(난방유−WTI)·운임·지정학 지수 편차 | `src/forecasting/analogue_g1.py` | 브리프 '과거 비슷한 시기' 카드에 충격 국면 항목 |
| S3 | 도착가 시나리오 층 — 위기 구간 실측 차이층·보험료 %→$/t 환산 | `src/forecasting/landed_cost.py` | 참고 도착가 범위의 스트레스 대안 |
| S4 | 정본 계열(정산가·통합 표)로 S1 재산출 + 통계 검정 사전 등록(다중 검정 보정) | CI 분석 잡 | 월별 심층판 부록 |
| S5 | 문헌 탄력성 이식(사내망 열람) → M4 보정 계수 | 연구 문서 | 방법론 정본 각주 |

---

## 8. 프로토타입 1차 산출 (진단 계열 — 정산가 아님)

> 산출물: `reports/market/shock_response_prototype_2026-09-25.md`. 입력은 Databento UTC 일봉 종가(정산가 대비 중앙값 괴리 0.10%)와 TE 일별 계열이며, **정본 정산가·통합 표로의 재산출은 S4에서 수행**한다. 아래 수치는 과거 충격 전후에 관측된 반응의 요약이며 향후 방향·확률 주장이 아니다.

**입력**: 시카고 대두유 UTC 일봉 3,966거래일(2010-06-07~2026-08-10) · TE 일별 26지표(Brent·난방유·운임지수·팜유 확인). 2026년은 미완결 구간이라 M2 표본에서 제외(M-008).

**M1 사건 연구(대두유, 사건 전일 종가 대비 로그 변화율 · 백분위는 같은 길이 창의 무조건부 분포 대비)**

| 사건 | 당일 | +5일 | +20일 | +60일 | 백분위(5·20·60) | 60일 내 최대 상승/하락 | 사건 전 수준 재통과 |
|---|---|---|---|---|---|---|---|
| 러시아 우크라이나 침공(2022-02-24) | +1.78% | +10.34% | +5.09% | +13.47% | 99·77·84 | +24.81% / −2.67% | 25거래일 |
| 아브카이크 피격(2019-09-16) | +3.76% | +0.52% | +4.88% | +9.72% | 56·76·79 | +9.72% / −1.49% | 7거래일 |

선례 11건 전체: 9건은 사건 전 수준을 재통과(중앙 6거래일), 2건(2023-09 러시아 경유 수출 금지·2025-03 중국 카놀라유 관세)은 120거래일 내 미복귀. 전체 표는 산출물 파일 참조.

**M2 국소투영(2010~2025 · HAC 표준오차 · 통제: 대두유·충격 각 5시차) — Brent 1σ(일 2.28%) 충격에 대한 대두유 누적 로그 변화율**

| 지평 | 계수 | 90% 구간 | 표본 |
|---|---|---|---|
| 5거래일 | +0.50% | [+0.40%, +0.61%] | 3,811 |
| 20거래일 | +0.58% | [+0.41%, +0.75%] | 3,796 |
| 60거래일 | +0.43% | [+0.11%, +0.75%] | 3,756 |

2020~2025 부분표본에서는 5/20/60일 +0.57 / +0.72 / +0.73%로 다소 큼. 비대칭: Brent +2σ 초과일(69건)의 20일 반응 +2.98% vs −2σ 미만일(91건) −0.08%. 난방유(경유 대리)는 Brent와 유사(20일 +0.65%, 구간이 0 제외), 건화물 운임지수는 전 지평에서 0 부근(20일 −0.26%). 선형 추정 24건 중 17건의 90% 구간이 0을 제외.

**판독**: 에너지 충격은 대두유에 **같은 방향·수 주 내** 반영되고 크기는 1σ당 0.5%대(대형 충격은 20일 +3%)로 관측됐다. 운임 충격은 시카고 가격이 아니라 **도착가 실측 차이층**에서 잡아야 한다는 온톨로지 경로(CE-010·013)와 정합한다. 이는 과거 관측의 요약이며 향후 방향·확률 주장이 아니다.

---

## 9. 한계 · 데이터 갭 · 결정 대기

- **대두유·한국 도착가 직접 반응의 외부 수치 부재(DATA GAP)** — 자체 산출로 대체하되 통계 검정은 사전 등록 하에서만.
- **호르무즈 범주 변수의 짧은 이력(2026-08~)** — 상태 의존 국소투영 불가; 2019·2024 해협 사건 수동 라벨링 시 확장 가능.
- **탱커 운임·전쟁보험료 시계열 부재** — 건화물 운임(BDI)이 대리; 실측 도입은 결정 대기 DQ-1(basis 호가)·DQ-2(식물성유지 탱커 운임).
- **문헌 원문 프록시 차단**(EIA·ERS·Cambridge·ICCT·NBER·arXiv·ScienceDirect·Wiley·FRED) — 탄력성 수치는 INFERENCE 유지, 사내망 열람 후 대조.
- **호르무즈 2026 수치의 출처 등급** — 대부분 트레이드 프레스(INFERENCE), 1차는 LMA 성명뿐.
- 오용 위험: 조건부 분포·국소투영 결과를 '예측'으로 읽는 순간 조달 판단에 투입될 위험 — 화면 문구는 '과거 관측 요약'으로 고정, 사람 승인 절차 유지.

## 10. 다음 단계

1. S1 프로토타입 결과 검토 → 교차검증(자동) 판정 반영.
2. S2·오브젝트 스토리지 구현(브리프 카드·도착가 스트레스 대안) — 9월 말 전 1차.
3. DQ-1·DQ-2 결정 시 운임·보험 층을 실측으로 교체.
4. 사내망에서 ICCT 2017·ARER 2022 원문 열람 → M4 계수 이식.

---

## 부록 A — 선례 증거 목록·방법 문헌·데이터 적합성 (시장 조사 관점 원문, 2026-09-25)

# 전쟁·지정학 충격의 유지류·대두유·한국 도착가(CIF) 파급 — 선례 증거 목록 + 정량화 방법 조사

> 작성일 2026-09-25 · 작성 관점: 시장 조사 관점(외부 공개 자료 전용, D-021 정합) · 상태: **1차 완료**(약 40분 시간상자 — 학술 원문 다수는 프록시 차단으로 초록·2차 요약 기준)
> 핵심 판정 요약: ① 원유·정제 충격의 **원유·크랙·보험료 반응은 선례별로 정량 확보**(A.1~A.3) ② **대두유·한국 CIF의 직접 반응 수치는 외부 문헌에서 거의 미확보(DATA GAP) — 자체 보유 계열(CBOT 정산가·TE·관세청 CIF)로 M1/M2/M5 방식 산출이 즉시 가능** ③ 탄력성 문헌(ICCT 2017·ARER 2022)은 존재 확인·수치 미열람 ④ 방법론은 M1·M2·M5·M6이 현 데이터로 실행 가능, M3는 외부 월별 원유생산·실물활동지수 확보 후, M7은 범위 밖.
> 라벨: **CONFIRMED**(1차·공식·동료심사) / **INFERENCE**(2차·추정) / **DATA GAP**(미확인·미확보). 예측·확률 주장 없음 — 관측된 과거 반응과 방법 설명만 수록.

## A 선례 표

### A.1 원유·정제 인프라 파괴 / 해협 봉쇄 계열

| # | 사건 | 기간 | 물리적 충격 규모 | 가격·운임 반응(크기·타이밍·지속·복귀) | 전달 경로 | 출처(라벨) |
|---|---|---|---|---|---|---|
| 1 | Abqaiq–Khurais 드론·미사일 공격 | 2019-09-14 | **5.7 mb/d** 일시 중단(사우디 생산의 절반 이상·세계 공급의 약 5%) [CONFIRMED — CRS IN11173] | Brent 9/16 +$8.80(**+14.6%**, $69.02/bbl — 1988년 이후 최대 일간 상승) [CONFIRMED — Al Jazeera/Reuters 2019-09-16]. 복구: 48시간 내 2 mb/d 재가동, 9월 말 전량 복구 발표 → 가격은 2주 내 사건 전 수준으로 복귀(EIA) [CONFIRMED — EIA TIE #41413] | 원유 공급 충격 → 에너지 비용·바이오디젤 경제성 → 유지류(간접·소폭). 유지류 직접 반응 정량은 **DATA GAP**(당시 CBOT ZL 일간 반응은 자체 데이터로 산출 가능) | congress.gov/crs-product/IN11173 (2019-09); eia.gov/todayinenergy/detail.php?id=41413 (2019-09); aljazeera.com/ajimpact/price-oil-jumps-15-percent… (2019-09-16) |
| 5 | 호르무즈 해협 위기(2026 미–이란) | 2026-02 말 개전 → 6월 휴전 기대·완화 → 7월 말 재격화 → 9월 사우디 인프라·상선 공격(straits.live 기준 봉쇄 207일째, 2026-09-25) | 호르무즈 경유 원유·제품 **10~15 mb/d** 교란(세계 공급의 ~20%) [INFERENCE — Investing.com 분석/Dallas Fed 시나리오; Wikipedia 집계 14 mb/d]; IMF PortWatch: 2026-09-20 통과 **1척**(위기 전 기준 85척/일) [INFERENCE — 2차 집계 사이트 인용, 원천 PortWatch 직접 확인 필요]; Lloyd's List 9/9 상품선 7척 통과 [INFERENCE] | **원유**: Brent 개전 직후 +10~13%($80~82, 3/2) → 3월 말 ~$118 → 7/1 ~$70 → 7월 말 $100+ → 8월 $87~97 → 9월 초 최대 $109, 9/18 근월물 $104.82 [INFERENCE — Wikipedia 연대기·Al Jazeera·Investing.com 종합]; Dated Brent 4/7 **$144.42 사상 최고**, Dated–근월물 프리미엄 **$25/bbl 초과**, 커브 앞–뒤 스프레드 ~$50(2022-06 러–우 이상) [INFERENCE — Investing.com/Parameta 트레이드 분석 — 정산 데이터 미대조]. **전쟁보험료**: 평시 대비 ~40배, VLCC 항차당 $250K → 최대 $10M 호가(선가 5% 시 $5~7.5M/항차) [INFERENCE — hormuzstraitmonitor.com; Lloyd's List "double-digit millions per trip"]; LMA: 통항 감소는 보험 가용성이 아닌 안전 우려가 주도, 런던 시장 전쟁보험 인수 가능 [CONFIRMED — LMA 성명]. **유지류**: 3/9 Brent 급등(~+20% 보도) 당일 Bursa CPO **+9.32%** [INFERENCE — FinancialContent MarketMinute 2026-03-09 — 거래소 정산으로 재확인 필요]; 8/21 CPO 20개월 고점(인니 B50 동반), 9/23 RM4,810(8월 이후 최저) [INFERENCE — Palm Oil Magazine]. **대두유(CBOT ZL) 직접 반응 코멘트·한국 CIF 반응은 미확보(DATA GAP) — 자체 Databento/관세청 계열로 산출 가능** | 원유·석유제품 공급 차단 → 디젤 크랙·원유 → 바이오디젤 경제성 → 팜유·대두유 수요; 탱커 운임·전쟁보험 → 중동 경유 물류; 현물 프리미엄(백워데이션)이 도착가에 선반영 | lloydslist.com/LL1156485 (2026-09); lloydslist.com/LL1156586; lmalloyds.com/safety-concerns… (2026-09); straits.live/report (2026-09-25 열람); en.wikipedia.org/wiki/2026_Iran_war_fuel_crisis; aljazeera.com/economy/2026/9/7/…; investing.com/analysis/oil-trading-in-august-2026-backwardation… (2026-08); parametasolutions.com/insights/extreme-brent-backwardation…; markets.financialcontent.com/…/marketminute-2026-3-9-palm-oil-prices-spike…; palmoilmagazine.com/cpo-price/2026/09/23/…; dallasfed.org/research/economics/2026/0320 |

### A.2 러시아–우크라이나 / EU–러시아 에너지 계열

| # | 사건 | 기간 | 물리적 충격 규모 | 가격·운임 반응 | 전달 경로 | 출처(라벨) |
|---|---|---|---|---|---|---|
| 2a | 러–우 전쟁: 해바라기유 수출 붕괴 | 2022-02-24~ | 우크라이나·러시아가 세계 해바라기유 교역의 약 **50%·25%** [INFERENCE — Efeca 2022-09 브리핑 노트, FAO 인용] | FAO 식물성유지 가격지수 2022-03 **251.8**(사상 최고, 전월 대비 **+23.2%**) — 해바라기유 주도, 팜·대두·유채유 동반 상승 + 원유가 상승 [CONFIRMED — FAO 2022-04-08 보도자료/UN News] | 흑해 물량 이탈 → 대체유 수요 전이(대체탄력) + 원유가 → 바이오디젤 | fao.org/newsroom/detail/fao-food-price-index-up-for-third-consecutive-month… (2022-04-08); news.un.org/en/story/2022/04/1115852 (2022-04-08); efeca.com Vegetable-oil-report-Final-Sept-22.pdf (2022-09) |
| 2b | 러–우 전쟁: CBOT 대두유 | 2022-04~06 | (수요 측: 미국 바이오연료 + 흑해 대체) | CBOT ZL **~87¢/lb**(2022-05, 사상 최고) [INFERENCE — 검색 요약; 자체 Databento/CME 계열로 정확 일자·수준 확정 권장]. USDA ERS: 2021년 미국 대두유 가격 +50% 이상, 2022년 추가 상승 [CONFIRMED — ERS Amber Waves 2022-12] | 해바라기유 부재 → 대두유·팜유로 대체 → 국제 유지류 동반 상승; 바이오연료 수요 경직성 | ers.usda.gov/amber-waves/2022/december/examining-record-soybean-oil-prices-in-2021-22 (2022-12) |
| 2c | 러–우 전쟁: 흑해 전쟁보험(AWRP) | 2022-02~ | — | 침공 직후 추가전쟁보험료 선가의 **10%(일부 20% 호가)** → 수주 내 완화 → 2022년 중 7일 항차당 **1~5%** [INFERENCE — Fortune 2022-04-08, World Finance, agroreview 종합]; 러시아 흑해 항만 상향(2025~26 탱커 피격 후 재상승) [INFERENCE — OFI Magazine, Insurance Business] | 보험료 → 운임 → FOB–CIF 격차(도착가 잔차층) | fortune.com/2022/04/08/merchant-ships-insurance-costs-10-percent…; worldfinance.com/special-reports/the-business-of-insuring-conflict; agroreview.com/en/newsen/overview-war-risk-premiums-trends/ |
| 3a | EU 러시아산 석유제품 금수 | 2023-02-05 | 러시아산이 EU 디젤 수입의 **약 절반** [CONFIRMED — ECB Economic Bulletin 2023/2] | 유럽 ULSD 크랙: 2021 평균 **~$8/bbl** → 침공 첫 달 **$40/bbl** → 금수 발표 후 **$63/bbl** [INFERENCE — OPIS 블로그 2024, 시장 데이터 인용] | 디젤 크랙 확대 → 바이오디젤(FAME/HVO) 혼합 경제성 개선 → 유채유·팜유·대두유 수요 | ecb.europa.eu/press/economic-bulletin/focus/2023/html/ecb.ebbox202302_02… (2023-03); opis.com/blog/true-costs-of-eus-russian-diesel-ban-emerge-one-year-later/ (2024) |
| 3b | 러시아 디젤 수출 금지 | 2023-09-21~11-22(약 2개월) | 러시아 디젤 수출 세계 최대급(구체 물량 DATA GAP) | 국내 재고 +14% 후 해제 [INFERENCE — Malay Mail/Reuters 2023-11-23]. 2026-07 재차 전면 금지(드론 타격 후) [INFERENCE — Kpler 2026-07-09, OGJ] | 디젤 공급 차단 → 크랙 → 바이오디젤 | malaymail.com/news/money/2023/11/23/russia-lifts-temporary-ban-on-diesel-exports/103615; kpler.com/blog/russias-diesel-export-ban-adds-fresh-fuel-to-rising-prices (2026-07-09) |
| 3c | 우크라이나 드론의 러시아 정유소 타격 | 2024-03~2026-09 | Reuters 집계(2026-05): 정지·감산 정유 능력 **83 Mt/yr(≈238kt/d, 러시아 총 정제능력의 약 1/4)**; 2026-09 RBC-Ukraine: **45% 이상** 오프라인 주장 [INFERENCE — 2차 보도; 45%는 우크라이나 측 추정으로 교차검증 필요]. 해당 설비가 러시아 휘발유 30%·디젤 25% 생산 | 디젤 크랙·러시아 수출 규제 연쇄(3b 2026-07) — 정량 크랙 수치 DATA GAP | 정제 능력 손실 → 제품 수출 감소 → 글로벌 디젤 크랙 → 바이오디젤 | themoscowtimes.com/2026/05/20/… (Reuters 인용); newsukraine.rbc.ua/news/ukraine-has-taken-nearly-half-of-russia-s-1790000936.html (2026-09) |

### A.3 홍해 / 허리케인 / 캐나다 / 2010–11

| # | 사건 | 기간 | 물리적 충격 규모 | 가격·운임 반응 | 전달 경로 | 출처(라벨) |
|---|---|---|---|---|---|---|
| 4 | 홍해 후티 공격·희망봉 우회 | 2023-11~2025(2026-07 후티 봉쇄 재개, 2026-09 Bab al-Mandeb 장악 보도) | 수에즈 통과량 전년비 **−50~−60%**(컨테이너 −90%, 2024) [INFERENCE — 수에즈운하청 데이터를 인용한 2차 자료]; 희망봉 우회 왕복 **+3,500 nm, +10~14일** [INFERENCE — S&P/Coface 등] | 추가전쟁보험료(AWRP): 전쟁 전 **0.05%** → 2023-12 **0.7%** → 2024-초 **1%** → 2024-02 최대 **2%**(선가 대비) [INFERENCE — AGBI 2024-02, Policyholder Pulse 2024-02-26, Lloyd's List]; 2025-07·2026-07 재상승 [INFERENCE — Bloomberg 2025-07-11, Insurance Journal 2026-07-21]. 컨테이너 운임(SCFI·FBX)은 자체 TE 데이터 부재 → **DATA GAP**; 탱커 운임(BCAA) 부재 → DATA GAP | 우회 → 톤마일 증가 → 운임·보험 → 유럽향 팜유·아시아향 정제유 CIF. 대두유 직접 반응 정량 DATA GAP | agbi.com/logistics/2024/02/cost-of-red-sea-shipping-insurance-rises-20-fold/ (2024-02); policyholderpulse.com/red-sea-transit-insurance-premiums-coverage-exclusions/ (2024-02-26); lloydslist.com/LL1147831 (2024-01); insurancejournal.com/news/international/2026/07/21/878345.htm; spglobal.com/market-intelligence/…/2026/02/red-sea-shipping-reopens; coface.com/…/houthi-attacks-in-the-red-sea… |
| 6a | 허리케인 Katrina(+Rita) | 2005-08-29(Rita 9/24) | 상륙 직전 **1.9 mb/d** 정제 정지 → Rita 후 최대 **4.9 mb/d(미국 정제능력의 ~29%, 걸프 60%+)** 정지(9/22~25); 10/10에도 2 mb/d 이상 정지, 멕시코만 해상 생산 차질 **10개월**(2005-08~2006-06) [CONFIRMED — CRS RL33124/RS22233, EIA STEO 2005-09] | 휘발유 생산 −1 mb/d(미국 소비의 ~10%); 8/31 휘발유 크랙이 디젤 크랙을 **~$51/bbl** 상회(기록상 최대 격차) [INFERENCE — 2차 해설 사이트; TE 휘발유·난방유 계열로 자체 재산출 가능]. 원유는 상대 약세(정제 수요 감소) | 정제 능력 상실 → 제품 크랙 급등(원유는 상대적 약세) → 바이오디젤 경제성. 2005년은 미국 바이오디젤 규모가 작아 유지류 전이 미미(INFERENCE) | everycrsreport.com/reports/RL33124.html (2005-10); everycrsreport.com/reports/RS22233.html (2005-09); eia.gov/outlooks/steo/archives/sep05.pdf; eco3min.fr/en/diesel-gasoline-crack-spreads-divergence/; minneapolisfed.org/article/2005/gasoline-prices-climb-in-response-to-hurricanes |
| 6b | 허리케인 Harvey | 2017-08-25 | 미국 정제능력 **20% 이상** 오프라인; 걸프(PADD 3) 가동률 **96% → 63%**, 투입 −3.2 mb/d(−34%, 9/1 주) [CONFIRMED — EIA TIE #32852, 2017-09] | 미국 평균 휘발유 소매 **+28¢/gal**(2.40→2.68, 8/28→9/4); 걸프 +35¢, 텍사스 +40¢; Colonial 파이프라인 9/6 감량 재개 [CONFIRMED — EIA]. 원유(WTI)는 오히려 약세(정제 수요 감소) — 크랙 확대(수치 DATA GAP, 자체 산출 가능). 복귀: 수 주 | 정제 정지 → 제품 크랙 ↑·원유 ↓ 비대칭 | eia.gov/todayinenergy/detail.php?id=32852 (2017-09-11); congress.gov/crs-product/IN10767 (2017-09) |
| 7a | 캐나다 카놀라 — 중국 관세 | 2025-03-20(카놀라유·박 **100%**), 2025-08-12(카놀라씨 **75.8%** 반덤핑 보증금) | 중국은 캐나다 카놀라씨 최대 수출처(물량 DATA GAP) [CONFIRMED — Canola Council, EDC] | 발표 후 사스캐처원 벤치마크 카놀라가 **약 −9%** [INFERENCE — EDC 기사]; 2025-09 말 ICE 카놀라 **CAD 610/t 하회**(3월 이후 최저 — 수출 수요 약세·무역장벽·증산 전망·타 유지 파급 복합) [INFERENCE — Trading Economics 뉴스]. **무역 전환**: 2025년 캐나다 카놀라유 對미 수출 **C$4.2B**·박 C$1.4B(2020년 이후 미 바이오연료 수요로 증가 추세) [INFERENCE — Producer/EDC]; 중국·미국행 감소분이 제3국으로 **+161%** 전환 [INFERENCE — S&P Global 2025-09-19]; 2022년 이후 對미 카놀라유 수출단가 하락(무역분쟁·규제 불확실·글로벌 유지 공급 증가 복합) [INFERENCE — USDA FAS GAIN CA2026-0008]. 카놀라유 베이시스 할인 수치·45Z 효과 분리는 **DATA GAP** | 수출 차단 → 캐나다 FOB 베이시스 약세 → 카놀라유 할인 → 유지류 상대가격(대두유−유채유) | canolacouncil.org/china-update/ (2025); edc.ca/en/article/china-tariffs-canola-exports.html (2025); tradingeconomics.com/commodity/canola/news/486943 (2025-09); ofimagazine.com/news/china-announces-100-tariff-on-rapeseed-oil-and-meal-from-canada (2025-03) |
| 7b | Fort McMurray 산불 | 2016-05-03~(생산 8월 완전 복구) | 오일샌드 **1.0~1.5 mb/d** 감산(오일샌드 40~65%, 캐나다 원유 25~40%) [CONFIRMED — CER Market Snapshot 2016]; Conference Board 추정 1.2 mb/d [INFERENCE] | WTI 5/4 +0.3%($43.78); 주간 +약 $1 → 5월 말 $50 돌파(2월 저점 $26.21 대비 회복 국면과 중첩 — 산불 단독 효과 분리 불가) [INFERENCE — CBC/Yahoo]. 설비 손상 없어 장기 손실 없음, 수출 영향 단기 [CONFIRMED — CER 2016 Review] | 중질원유 공급 감소 → WCS–WTI 차 축소 → 미 중서부 정제 → 디젤(간접). 유지류 영향 무시 가능 수준(INFERENCE) | cer-rec.gc.ca/…/market-snapshot-impacts-fort-mcmurray-wildfires… (2016-05); cer-rec.gc.ca/…/2016-review-short-lived-effect-crude-oil-exports… (2017); eia.gov/todayinenergy/detail.php?id=26572 (2016-05) |
| 7c | Irving Oil Saint John 정유소 폭발 | 2018-10-08 | 320 kb/d(캐나다 최대, 절반 이상 미 북동부 수출) 일부 유닛 정지 [CONFIRMED — CNBC/CBC] | 가격 반응 수치 미확인 → **DATA GAP** | 미 북동부 제품 공급 | cnbc.com/2018/10/08/explosion-reported-at-irving-oils-st-john-refinery… ; cbc.ca/news/canada/new-brunswick/timeline-saint-john-refinery-irving-oil-1.4855395 |
| 8 | 러시아 곡물 수출 금지 + 라니냐 | 2010-08-15~2011-07-01 | 러시아 130년 만의 폭염·가뭄 → 밀·보리·호밀·옥수수 수출 전면 금지 [CONFIRMED — Oxfam 2011, USDA ERS WRS-1103] | 밀 2010년 **+35.1%**, 2011 상반기 **+19.3%**(BLS 수출물가) [CONFIRMED — BLS]; 밀 랠리가 옥수수·귀리·대두 동반 상승 견인 [INFERENCE — France24/BLS]. 미국 대두유 2010/11 마케팅연도 평균 **53.20¢/lb**(ERS Oil Crops Outlook) [CONFIRMED — ERS]; FAO 식품가격지수 2011-02 사상 최고(당시) — 유지류 지수 동반 [CONFIRMED — FAO 2011-03 보도]. **내부 수치 '대두유 +51%/약 9개월'은 외부 월별 계열(FRED PSOILUSDM·IndexMundi·ERS Amber Waves 2011-09)이 모두 프록시 차단으로 미열람 → 외부 교차확인 미완(DATA GAP). 단, 자체 TE 대두유 일별 계열(2010~)로 2010-06→2011-02 변화율을 직접 산출해 대체 검증 가능** | 곡물가 → 대두 파종 경쟁·사료 → 대두유; 라니냐 → 남미 작황 → 대두 | ers.usda.gov/…/7392_wrs1103.pdf (2011); oxfam.org/en/research/impact-russias-2010-grain-export-ban (2011-06); bls.gov/opub/btn/archive/us-export-prices-up-as-world-grain-stockpiles-decline.pdf |

### A.4 전달 경로별 정량 근거(9번 항목 — 탄력성·패스스루)

| 경로 | 추정치 | 표본·방법 | 라벨 | 출처 |
|---|---|---|---|---|
| 원유 → 바이오디젤 원료(대두유·팜유·유채유) | 원료 가격과 원유가 **공적분**(장기 관계) — 정책(RFS·RED)과 셰일 확장이 관계 강도를 변화시킴; 탄력성 수치는 본 검색 요약에 미표기 → 원문 확인 필요 | 시계열 공적분·구조변화 | INFERENCE(원문 미열람) | cambridge.org/…/biodiesel-feedstock-and-crude-oil-price-relationships… (Agricultural and Resource Economics Review, 2022) |
| 유지류 간 교차가격 탄력성(대두유·팜유·유채유·해바라기유·우지) — 미국·EU | ICCT 위탁(Santeramo, 2017): 미국 시장에서 대두·팜·카놀라유 **장기 강한 동행·고도 통합**; 개별 교차탄력성 수치는 원문 표 참조 필요 | 수요 체계 추정 | INFERENCE(원문 미열람) | theicct.org/…/Cross-price-elasticities-for-oils-fats-US-EU_ICCT_consultant-report_06032017.pdf (2017-06) |
| 미국 바이오디젤 의무 → 세계 유지류 시장 | 부분균형 시뮬레이션(Energy Economics 2017) — 의무 증가가 세계 유지류 가격을 상승시키고 팜유로 전이 | 부분균형 모델 | INFERENCE(초록만) | sciencedirect.com/science/article/abs/pii/S0140988317301172 (2017) |
| 바이오연료 가격의 원유·원료 반영 | OECD-FAO Outlook: 바이오연료 가격은 원료·원유·유통비를 **부분적으로만** 반영, 의무·세액공제가 경로 결정 | 구조 모델(Aglink-Cosimo) | CONFIRMED(공식 전망 문서의 정성 서술) | openknowledge.fao.org/…/OECD-FAO Agricultural Outlook 2022–2031 |
| 해상운임(BDI) → 수입물가·CPI | BDI **2배** → 46개국 헤드라인 CPI **+0.7%p**(정점 12개월, 지속 18개월); 수입물가·PPI에도 유의 [CONFIRMED — 동료심사 JIMF 2023] | 패널 국소투영(143국, 1992~2021) | CONFIRMED | Carrière-Swallow et al., J. Int. Money & Finance 130 (2023) — sciencedirect.com/…/S0261560622001747; IMF WP 2022/061 |
| 해상운임 → 미국 수입물가(품목별) | 팬데믹 후 운임 상승률 1%p → 수입물가 상승률 **+0.068%p**; 식품 **+0.072%p** [CONFIRMED — Review of World Economics 2025, 센서스 수입 데이터] | 품목별 패널 회귀 | CONFIRMED | link.springer.com/article/10.1007/s10290-025-00601-8 (2025) |
| 전쟁보험 → 도착가 | 선가 %(위 2c·4·5 행) × 선가 / 적재량으로 $/MT 환산 가능 — **유지류 전용 추정 문헌 미발견(DATA GAP)**; 관세청 CIF−CBOT 잔차(자체 landed_cost 계열)로 사후 역산 가능 | — | DATA GAP | — |
| 지정학 리스크(GPR) → 농산물 선물 | 러–우 개전 이벤트 기반 **일별 SVAR**: 지정학 충격이 밀 **+2%**·옥수수 **+1%**·유럽 천연가스 **+7.5%**(대두유·유지류 결과 여부는 원문 미열람) | 일별 이벤트 SVAR | INFERENCE(초록·2차 요약) | NBER w31950 / European Journal of Political Economy 2024 — sciencedirect.com/science/article/pii/S0176268024000764 |
| GPR → 옥수수·대두 선물 | TVP-VAR: GPR이 옥수수·대두 선물가격·시장행태에 단·중기 유의(맥락 의존) | TVP-VAR | INFERENCE(초록) | Steinbach, AEPP 46(4) 2024 — onlinelibrary.wiley.com/doi/10.1002/aepp.13481 |
| GPR → 농산물 변동성 | GJR-GARCH-MIDAS: 모든 농산물 시장이 GPR 충격에 반응하나 품목별 강도 상이; 롤링윈도 모델이 밀·옥수수·대두·쌀 변동성 설명력 우위 | GARCH-MIDAS | INFERENCE(초록) | arxiv.org/abs/2404.01641 (2024) |
| GPR → 인플레이션·상품가격(글로벌) | 1900년 이후 44개국 패널 + 1970년대 이후 월별 VAR: GPR 충격 → 상품가격 상승·통화 약세가 심리 위축 효과를 상회해 순인플레이션; GPT(위협)/GPA(행위) 분해 | 패널 LP + 월별 VAR | CONFIRMED(동료심사 JIE 159, 2026) | Caldara·Conlisk·Iacoviello·Penn, J. Int. Econ. 2026 — matteoiacoviello.com/research_files/JIE_2026.pdf |
| 러–우 개전 이벤트 스터디 | 개전 후 1주까지 상품 전반 양(+)의 비정상수익률, 2주차에 대부분 소멸(옥수수 예외) | 이벤트 스터디(GARCH 기반) | INFERENCE(초록) | mdpi.com/1911-8074/16/5/256 (JRFM 2023) |

## B 방법 표

> 각 방법에 대해 **무엇을 추정하나 / 필요 데이터 / 표본 요건 / 전형적 산출 / 핵심 가정·한계 / 문헌 예시**를 정리함. 문헌 링크는 검색 결과의 URL을 그대로 옮겼으며, 학술 도메인(sciencedirect·wiley·cambridge·nber·arxiv·eia·ers)은 본 세션 프록시에서 **본문 열람 차단** — 초록·2차 요약 기준으로 기술했으므로 인용 전 원문 대조 필요.

| ID | 방법 | 무엇을 추정하나 | 필요 데이터 | 표본 요건 | 전형적 산출 | 핵심 가정·한계 | 문헌 예시(URL) |
|---|---|---|---|---|---|---|---|
| **M1** | 이벤트 스터디(event study) | 특정 사건일(공격·금수·봉쇄 발표) 전후 **비정상수익률(AR/CAR)** — 크기·지속·소멸 시점 | 일별 가격(CBOT ZL·Brent·팜유·BDI), 사건일 목록, 정상수익 모형(상수평균·시장모형·GARCH) | 사건당 추정창 120~250 거래일, 사건창 ±1~10일; 사건 수가 적어도 가능(단일 사건 서술도 허용) — 통계 검정은 사건 10건+ 권장 | 사건별 AR·CAR 표, 누적 반응 곡선, 소멸일 | 사건일이 외생·명확해야 함(전쟁은 점진적 → 사건일 정의 자의성); 겹치는 사건 분리 곤란; GARCH 오차 필요(농산물 선물 변동성 군집) | Russia–Ukraine 이벤트 스터디: mdpi.com/1911-8074/16/5/256 (2023); 원유 선물 이벤트 반응 모형: researchgate.net/publication/345559421 |
| **M2** | 국소투영(Local Projections, Jordà 2005) — GPR·석유공급뉴스 충격 적용 | 충격 1단위(또는 1σ)에 대한 **h-스텝 반응 IRF**(h=1·5·20·60일 등 각 지평 직접 회귀) — VAR 없이 지평별 OLS | 충격 계열(GPR 월/일별, Känzig 석유공급뉴스 충격, 이벤트 더미) + 반응변수(ZL·CIF·BDI) + 통제변수 | 월별이면 20년+(240obs), 일별이면 수천 obs; **지평별 관측치가 h만큼 줄어드므로 60일 지평은 표본 여유 필요**; 충격 계열의 외생성이 핵심 | 지평별 점추정·신뢰대(IRF), 상태 의존(레짐별) IRF, 누적 패스스루 | 오차의 자기상관(HAC/Newey-West 필수); 충격 식별은 외부 계열에 의존(GPR은 뉴스 기반 — 실제 공급 충격과 혼재); 소표본에서 장기 지평 편향; 비선형(상태 의존) 확장 용이 | Jordà 2005 AER: aeaweb.org/articles?id=10.1257/0002828053828518; Jordà–Taylor 2024 NBER w32822: nber.org/system/files/working_papers/w32822/w32822.pdf; Carrière-Swallow et al. 2023(패널 LP, BDI→CPI): sciencedirect.com/science/article/abs/pii/S0261560622001747; Caldara 등 2026 JIE(GPR→인플레·상품): matteoiacoviello.com/research_files/JIE_2026.pdf; Känzig 2021 AER(석유공급뉴스 충격 데이터 공개): github.com/dkaenzig/oilsupplynews |
| **M3** | 구조 VAR(Kilian 2009 공급/수요 분해; Baumeister–Hamilton 2019 베이지안 부분식별; 내러티브 부호제약) | 유가 변동을 **석유공급 충격·총수요 충격·예비수요(precautionary) 충격**으로 분해 → 각 충격의 유지류·CIF 반응 IRF·역사분해 | 월별: 세계 원유생산, 실물경제활동지수(Kilian 해운운임 기반), 실질유가, 재고(BH); 확장 시 ZL·팜유·BDI·CIF 추가 | 월별 30년+(Kilian 1973~), 변수 5~6개 초과 시 차원 저주; 일별 이벤트 SVAR(NBER w31950)은 짧은 창 가능 | IRF·분산분해·역사분해(각 사건이 어느 충격이었는지), 부호제약 시 사후분포 | 식별 가정에 결과가 크게 좌우(Kilian vs BH 논쟁 — BH는 공급충격 중요성 더 큼); 선형·시불변 가정; 내러티브 부호제약(Antolín-Díaz & Rubio-Ramírez 2018)은 특정 사건(예: 1990 걸프전, 2022)에 대한 충격 부호를 사전 지정해 식별을 강화 — 단일 제약으로도 추론 급변 | Kilian 2009 AER: aeaweb.org/articles?id=10.1257/aer.99.3.1053; Baumeister–Hamilton 2019 AER: aeaweb.org/articles?id=10.1257/aer.20151569; Antolín-Díaz & Rubio-Ramírez 2018 AER: aeaweb.org/articles?id=10.1257/aer.20161852; 러–우 일별 SVAR: sciencedirect.com/science/article/pii/S0176268024000764 |
| **M4** | 경로 패스스루·부분균형 캘리브레이션(탄력성·투입산출) | 원유→바이오디젤 원료 가격 전이, 유지류 간 교차탄력성(대체), 운임·보험→CIF 전이를 **탄력성·비용 구조로 곱셈 연쇄** | 탄력성 문헌값(ICCT 2017 교차탄력성; 공적분 계수), 비용 구성(FOB·운임·보험·베이시스), 정책 파라미터(RFS RVO·RED 혼합률) | 추정 자체는 문헌 인용 시 표본 불필요; 자체 재추정 시 월별 15년+ 공적분 분석 | 시나리오별 ΔCIF($/MT) 분해표(원유층·운임층·보험층·베이시스층), 민감도 | 탄력성이 레짐 의존(RD붐 이후 원유–유지 결합 강화·정책이 지배 — OECD-FAO); 선형 근사; 동시성 무시; 문헌 탄력성 수치는 **원문 미열람 상태(DATA GAP)** | ICCT 교차탄력성(Santeramo 2017): theicct.org/publication/cross-price-elasticities-for-oils-and-fats-in-the-u-s-and-the-eu/; 바이오디젤 원료–원유 공적분(ARER 2022): cambridge.org/…/S1068280522000065a.pdf; 미 바이오디젤 의무→세계 유지류(Energy Econ. 2017): sciencedirect.com/science/article/abs/pii/S0140988317301172; 운임→수입물가 품목별(RWE 2025): link.springer.com/article/10.1007/s10290-025-00601-8 |
| **M5** | 유사국면·조건부 경험분포(레짐 조건부 분위수) | 현재 상태(예: GPR 십분위·Brent z·BDI z·해협 상태)와 유사했던 과거 시점들의 **이후 h일 실측 수익률 분포**(P10/P50/P90) — 모델 무가정 | 일별 mart(상태 변수 + target_ret{5,20,60}), 레짐 라벨(HMM/threshold) 또는 분위 슬라이스 | 레짐당 독립 에피소드 8건+ 권장(전방 창 중첩 제거); 60일 지평은 2010~ 데이터로 에피소드 ~30~60개 수준 | 조건부 분위수 표, 에피소드 목록, 사례 배지 | 과거=미래 가정 없음(요약만); **통계 검정 없음 명시**(다중검정 회피); 레짐 분류 자체의 사후성; 상태 변수 선택 자의성 → 사전 등록; 표본 부족 시 보류 | 레짐 의존 상품가격 예측(Crespo Cuaresma et al., J. Forecasting 2024): onlinelibrary.wiley.com/doi/full/10.1002/for.3152; 조건부 레짐 아날로그(CRAFT, 2026 arXiv): arxiv.org/pdf/2608.09534; 상품 패널 분위회귀(VaR): arxiv.org/pdf/1807.11823 |
| **M6** | 몬테카를로 시나리오 오버레이(비용 적층) | 기준 가격층(CBOT 분포) ⊕ 운임층 ⊕ 보험층 ⊕ 베이시스층의 **합성 도착가 분포** — 각 층에 충격 시나리오(예: AWRP 0.05%→2%, BDI +2σ) 주입 | 각 층의 경험분포(관세청 CIF−CBOT 잔차, BDI, 전쟁보험 % 선례표), 층간 의존구조(코퓰라 또는 독립 가정) | 층별 월별 5년+(잔차층), 시나리오는 선례표에서 차용 | 시나리오별 P10/P50/P90 도착가($/MT), 층별 기여 분해, 스트레스 상계 | 층간 독립 가정은 과소분산(운임·보험·베이시스는 위기 시 동행); 분위수 단순합은 통계적 분위가 아님(MC 컨볼루션 필수); 보험 %→$/MT 환산에 선가·적재량 가정 필요 | 조건부 몬테카를로(보험·금융 합): cambridge.org/…/conditional-monte-carlo-for-sums…; 농산물 하이브리드(확률 시뮬레이션 결합, 2025): sciencedirect.com/science/article/pii/S2214845025001553 |
| **M7** | CGE/GTAP·네트워크 모델 | 수출 차단·관세·운임 충격의 **일반균형 가격·교역 재배분**(누가 대체 공급하나) | GTAP 데이터베이스(연간·다지역·다부문), MRIO, 무역 네트워크(UN Comtrade) | 연간 기준연도 1개 + 충격 시나리오 — 시계열 불필요, 단 캘리브레이션 탄력성(Armington) 의존 | 시나리오별 세계·국가별 가격 %·교역량 %·후생; 네트워크 중심성·취약 노드 | 단기 동학 없음(비교정태), Armington 탄력성 민감, 유지류 세분(대두유·팜유·해바라기유) 부문이 GTAP 표준에서 통합돼 있어 분해 필요; 자체 구축 비용 큼 — Nexus 범위 밖(Phase B 배경) | GTAP 러–우 곡물 수출 교란(AEPP 2023): onlinelibrary.wiley.com/doi/full/10.1002/aepp.13351; ENVISAGE+GTAP 영양 모듈(Food Security 2025): link.springer.com/article/10.1007/s12571-025-01560-6; 해바라기유 무역 네트워크(Frontiers 2026): frontiersin.org/journals/environmental-science/articles/10.3389/fenvs.2026.1757181/full |

### B-보론: 'GPR 지수 충격'·'내러티브 부호제약'의 상품시장 적용 요점
- **GPR 지수(Caldara & Iacoviello 2022 AER)**: 미·영·캐나다 10개 신문 기사 비중 기반 1985~ 월별(및 1900~ 역사판, 일별판). 위협(GPT)/행위(GPA) 분해가 상품가격 반응 분리에 유용 — 위협은 즉시 금융·상품가격에, 행위는 실물 교역에 반영(JIE 2026). 농산물 적용은 TVP-VAR(Steinbach 2024)·GARCH-MIDAS(2024)·인과검정(MDPI Risks 2023 — mdpi.com/2227-9091/11/5/84) 등이 있으나 **대두유 전용 IRF 수치는 본 조사에서 미확보(DATA GAP)**.
- **내러티브 부호제약**: 전통 부호제약 SVAR에 "특정 월(예: 1990-08, 2022-03)에는 공급충격이 지배적·양(+)"이라는 역사 서술 제약을 추가 — 유가 SVAR에서 단일 제약만으로 사후분포가 크게 좁아짐(Antolín-Díaz & Rubio-Ramírez 2018). Nexus 위기 사례(Case 1~4·2026)를 제약으로 쓸 수 있는 구조라 M3 채택 시 우선 검토 대상.
- **석유공급뉴스 충격(Känzig 2021)**: OPEC 발표일 고빈도 선물가격 변화로 식별한 충격 계열이 GitHub에 공개(월별) — M2/M3의 외생 충격 계열로 직접 이식 가능.

## C 데이터 적합성

> 보유: CBOT 대두유 정산가 일별 2010~2026 · TE 일별 2010~2026(Brent·WTI·난방유·휘발유·천연가스·EU가스·탄소·BDI·팜유·유채·해바라기유·대두·대두박) · FRED FX · 관세청 월별 원산지별 CIF 2010~2026-07 · WASDE/PSD 월별 · GPR 월별 1985~/일별 · 호르무즈 위협수준(범주, 2026-08~). **미보유**: AIS 위치, 탱커 운임지수(BCAA), 베이시스 호가, 컨테이너 운임(SCFI/FBX), 전쟁보험료 시계열.

| 방법 | 현재 가능 여부 | 즉시 실행 가능한 범위 | 추가로 필요한 데이터 | 비고 |
|---|---|---|---|---|
| M1 이벤트 스터디 | **가능** | 선례표 A의 사건일(2019-09-16, 2022-02-24, 2023-02-05, 2023-09-21, 2023-11~, 2025-03-20, 2025-08-12, 2026-03-09 등)에 대해 ZL·팜유·유채·해바라기·Brent·디젤 크랙(난방유−WTI)·BDI의 AR/CAR 산출 | 없음(선택: 컨테이너·탱커 운임) | 사건일 정의를 사전 등록; GARCH 오차 사용; 관세청 CIF는 월별이라 사건창 ±1~2개월로 별도 설계 |
| M2 국소투영 | **가능(월별·일별)** | ① 월별: GPR(1985~ 또는 2010~)·Känzig 충격 → ZL·CIF·BDI 지평 1~12개월 IRF; ② 일별: 일별 GPR·Brent 충격(원유 수익률 또는 크랙 변화) → ZL·팜유 지평 1·5·20·60일 IRF; 레짐(호르무즈 위협 3단계는 2026-08~라 표본 부족 → GPR 십분위나 Brent 백워데이션 대용) | 호르무즈 범주 변수의 과거 확장(예: 2019·2024 사건 수동 라벨) 없이는 상태 의존 LP에 사용 불가; 전쟁보험 % 시계열 없음 | HAC 표준오차; 60일 지평은 겹침 큼 — 월별 병행 |
| M3 SVAR | **부분 가능** | Kilian 3변수(세계 원유생산·실물활동지수·실질유가)는 **외부 월별 공개 데이터 확보 필요**(원유생산=EIA/IEA, Kilian 지수=댈러스 연은) → 현재 미보유. 대안: TE 보유 계열만으로 축소 VAR(Brent·디젤크랙·BDI·ZL·팜유·CIF) + 부호제약/내러티브 제약(Case 1~4·2026) | 세계 원유생산 월별, Kilian 실물활동지수(또는 BDI 대용), 재고(BH 모형) | 유지류 SVAR은 원문 선례가 적음 — Challenger 성격; 식별 결과 민감도 보고 필수 |
| M4 패스스루 캘리브레이션 | **부분 가능** | 자체 추정: (a) 원유→ZL·팜유·유채 공적분/ECM(2010~ 월별·일별) (b) BDI→CIF−CBOT 잔차 회귀(월별, 2010~2026-07) (c) 유지류 간 스프레드 탄력성. 문헌 탄력성(ICCT·ARER 2022)은 **원문 미열람** — 사내망에서 열람 후 이식 | 문헌 원문(ICCT 2017 pdf, ARER 2022) 열람; 전쟁보험 %→$/MT 환산용 선가·적재량 가정표; BCAA(탱커 운임) 부재는 BDI 대용의 한계로 명기 | 레짐별(RD붐 전/후 2021 기준) 분리 추정 권장 |
| M5 유사국면 조건부 분포 | **가능(기구현 analogue_g1 확장)** | 상태 변수에 Brent z·디젤크랙 z·BDI z·GPR 십분위 추가 → 조건부 target_ret{5,20,60} 분포; 사례 배지에 2019-09·2022·2023-11·2026 추가 | 호르무즈 범주(2026-08~)는 표본 부족 → 사용 보류; 과거 해협 사건 수동 라벨링 시 확장 가능 | 통계 검정 없음·서술 계약(A-191) 유지 |
| M6 MC 비용 적층 | **가능(기구현 landed_cost 확장)** | 잔차층(CIF−CBOT)에 위기 국면 서브샘플(2022-03~06, 2024-01~06) 분포를 스트레스 대안으로; 보험층은 선례표 %(0.05→2%, 10→1~5%)를 선가·적재량 가정으로 $/MT 환산해 시나리오 주입 | 전쟁보험 % 시계열(런던 시장 JWC 목록·브로커 호가 — 유료), BCAA, 선가·용선 가정 | 층간 의존은 위기 서브샘플 코퓰라로 근사; 독립 가정 시 과소분산 명기 |
| M7 CGE/네트워크 | **불가(범위 밖)** | 문헌 결과 인용만(GTAP 2023·ENVISAGE 2025·해바라기유 네트워크 2026) | GTAP 라이선스·모델 구축 | Phase B 배경 |

### C-요약: 지금 당장 산출 가능한 '관측된 반응' 표(자체 데이터)
1. 선례 사건일별 ZL·팜유·Brent·디젤크랙·BDI **±1·5·20·60일 실측 변화율**(M1) — 선례표 A의 DATA GAP(대두유 직접 반응) 대부분을 자체 데이터로 채울 수 있음.
2. 관세청 원산지별 CIF의 **사건 전후 월별 변화 및 CIF−CBOT 잔차 확대폭**(2022-03~06·2024-01~06·2026-03~07) — 운임·보험층의 사후 역산.
3. GPR 월별 충격 → ZL·CIF 국소투영 IRF(2010~2026) — 대두유 전용 GPR IRF의 문헌 공백을 자체 산출로 보완(단, 통계적 유의 주장은 Bonferroni 등 사전 등록 하에서만).

## 출처 목록

### 1차·공식·동료심사(CONFIRMED로 인용한 항목)
- CRS, "Attacks on Saudi Oil Facilities: Effects and Responses" IN11173 (2019-09) — https://www.congress.gov/crs-product/IN11173
- EIA, "Saudi Arabia crude oil production outage affects global crude oil and gasoline prices" TIE #41413 (2019-09) — https://www.eia.gov/todayinenergy/detail.php?id=41413 (본문 프록시 차단 — 검색 요약 기준)
- FAO, "FAO Food Price Index up for third consecutive month largely on rising vegetable oil prices" (2022-04-08) — https://www.fao.org/newsroom/detail/fao-food-price-index-up-for-third-consecutive-month-largely-on-rising-vegetable-oil-prices/en ; UN News (2022-04-08) — https://news.un.org/en/story/2022/04/1115852
- FAO, "FAO Food Price Index rises to record high in February" (2011-03) — https://www.fao.org/newsroom/detail/fao-food-price-index-rises-to-record-high-in-february/en
- USDA ERS, "Examining Record Soybean Oil Prices in 2021–22" Amber Waves (2022-12) — https://www.ers.usda.gov/amber-waves/2022/december/examining-record-soybean-oil-prices-in-2021-22
- USDA ERS, Oil Crops Outlook (2010/11 시즌 평균 53.20¢/lb) — https://ers.usda.gov/sites/default/files/_laserfiche/outlooks/37966/34051_ocs12l.pdf
- USDA ERS WRS-1103 (러시아 2010 곡물 수출금지) — https://ers.usda.gov/sites/default/files/_laserfiche/outlooks/40481/7392_wrs1103.pdf
- ECB Economic Bulletin 2023/2 Box, "Oil price developments and Russian oil flows since the EU embargo and G7 price cap" — https://www.ecb.europa.eu/press/economic-bulletin/focus/2023/html/ecb.ebbox202302_02~59c965249a.en.html
- CRS RL33124 "Oil and Gas Disruption From Hurricanes Katrina and Rita" (2005-10) — https://www.everycrsreport.com/reports/RL33124.html ; RS22233 — https://www.everycrsreport.com/reports/RS22233.html ; EIA STEO 2005-09 — https://www.eia.gov/outlooks/steo/archives/sep05.pdf
- EIA TIE #32852 "Hurricane Harvey caused U.S. Gulf Coast refinery runs to drop, gasoline prices to rise" (2017-09) — https://www.eia.gov/todayinenergy/detail.php?id=32852 ; CRS IN10767 — https://www.congress.gov/crs-product/IN10767
- Canada Energy Regulator, Market Snapshot: Fort McMurray wildfires (2016-05) — https://www.cer-rec.gc.ca/en/data-analysis/energy-markets/market-snapshots/2016/market-snapshot-impacts-fort-mcmurray-wildfires-canadian-crude-oil-production.html ; 2016 Review (2017) — https://www.cer-rec.gc.ca/en/data-analysis/energy-markets/market-snapshots/2017/2016-review-short-lived-effect-crude-oil-exports-due-fort-mcmurray-wildfire.html ; EIA TIE #26572 — https://www.eia.gov/todayinenergy/detail.php?id=26572
- Canola Council of Canada, "Canola trade with China" (2025) — https://www.canolacouncil.org/china-update/
- USDA FAS GAIN, Oilseeds and Products Annual — Ottawa CA2026-0008 (2026-04) — https://www.fas.usda.gov/data/gain-report/2026/04/Oilseeds%20and%20Products%20Annual_Ottawa_Canada_CA2026-0008.pdf
- Lloyd's Market Association 성명(호르무즈 통항 감소 원인, 2026-09) — https://lmalloyds.com/safety-concerns-not-insurance-availability-driving-reduced-vessel-traffic-in-the-strait-of-hormuz/
- BLS, "U.S. Export Prices Up as World Grain Stockpiles Decline" — https://www.bls.gov/opub/btn/archive/us-export-prices-up-as-world-grain-stockpiles-decline.pdf ; Oxfam (2011-06) — https://www.oxfam.org/en/research/impact-russias-2010-grain-export-ban
- Carrière-Swallow, Deb, Furceri, Jiménez, Ostry, "Shipping costs and inflation," J. Int. Money & Finance 130 (2023) — https://www.sciencedirect.com/science/article/abs/pii/S0261560622001747 ; IMF WP 2022/061 — https://ideas.repec.org/p/imf/imfwpa/2022-061.html
- "International shipping costs pass through to inflation; evidence using census import data," Review of World Economics (2025) — https://link.springer.com/article/10.1007/s10290-025-00601-8
- Caldara & Iacoviello, "Measuring Geopolitical Risk," AER 112(4) 2022 — https://www.aeaweb.org/articles?id=10.1257%2Faer.20191823 ; Caldara, Conlisk, Iacoviello, Penn, "Do geopolitical risks raise or lower inflation?" JIE 159 (2026) — https://www.matteoiacoviello.com/research_files/JIE_2026.pdf
- Jordà, "Estimation and Inference of Impulse Responses by Local Projections," AER 95(1) 2005 — https://www.aeaweb.org/articles?id=10.1257%2F0002828053828518 ; Jordà & Taylor, "Local Projections," NBER w32822 (2024) — https://www.nber.org/system/files/working_papers/w32822/w32822.pdf
- Kilian, "Not All Oil Price Shocks Are Alike," AER 99(3) 2009 — https://www.aeaweb.org/articles?id=10.1257%2Faer.99.3.1053 ; Baumeister & Hamilton, AER 109(5) 2019 — https://www.aeaweb.org/articles?id=10.1257%2Faer.20151569 ; Antolín-Díaz & Rubio-Ramírez, "Narrative Sign Restrictions for SVARs," AER 108(10) 2018 — https://www.aeaweb.org/articles?id=10.1257%2Faer.20161852 ; Känzig, AER 2021 + 데이터 — https://www.aeaweb.org/articles?id=10.1257%2Faer.20190964 , https://github.com/dkaenzig/oilsupplynews
- OECD-FAO Agricultural Outlook 2022–2031 (바이오연료 장) — https://openknowledge.fao.org/server/api/core/bitstreams/1c5525c6-6288-4b5d-88c4-1daf0367887c/content

### 2차·트레이드 프레스·추정(INFERENCE로 인용한 항목)
- Al Jazeera, "Price of oil jumps nearly 15 percent…" (2019-09-16) — https://www.aljazeera.com/ajimpact/price-oil-jumps-15-percent-middle-east-volatility-190916220714951.html
- Efeca, Vegetable Oil Markets Briefing Note (2022-09) — https://www.efeca.com/wp-content/uploads/2022/09/Vegetable-oil-report-Final-Sept-22.pdf
- Fortune, "Merchant ships' insurance costs 10 percent…" (2022-04-08) — https://www.fortune.com/2022/04/08/merchant-ships-insurance-costs-10-percent-black-sea-ukraine-invasion ; World Finance — https://www.worldfinance.com/special-reports/the-business-of-insuring-conflict ; agroreview — https://agroreview.com/en/newsen/overview-war-risk-premiums-trends/ ; OFI Magazine(러 흑해 항만 보험료) — https://www.ofimagazine.com/news/war-risk-premiums-for-russian-black-sea-ports-rise ; Insurance Business — https://www.insurancebusinessmag.com/us/news/breaking-news/black-sea-tanker-strikes-push-warrisk-premiums-higher-as-underwriters-reassess-exposure-558492.aspx
- OPIS, "True Costs of EU's Russian Diesel Ban Emerge One Year Later" (2024) — https://www.opis.com/blog/true-costs-of-eu-russian-diesel-ban-emerge-one-year-later/
- Malay Mail/Reuters, "Russia lifts temporary ban on diesel exports" (2023-11-23) — https://www.malaymail.com/news/money/2023/11/23/russia-lifts-temporary-ban-on-diesel-exports/103615 ; Kpler (2026-07-09) — https://www.kpler.com/blog/russias-diesel-export-ban-adds-fresh-fuel-to-rising-prices ; OGJ — https://www.ogj.com/general-interest/economics-markets/news/55390017/russia-imposes-full-ban-on-diesel-exports-as-fuel-crisis-deepens
- Moscow Times(Reuters 인용, 2026-05-20) — https://www.themoscowtimes.com/2026/05/20/drone-strikes-force-central-russian-refineries-to-halt-or-cut-output-reuters-a92805 ; RBC-Ukraine(45%, 2026-09) — https://newsukraine.rbc.ua/news/ukraine-has-taken-nearly-half-of-russia-s-1790000936.html ; Kyiv Independent — https://kyivindependent.com/ukraines-drone-strikes-force-russias-6-largest-diesel-refineries-to-halt-or-slash-output-reuters-reports/
- AGBI, "Cost of Red Sea shipping insurance rises 2,700%" (2024-02) — https://www.agbi.com/logistics/2024/02/cost-of-red-sea-shipping-insurance-rises-20-fold/ ; Policyholder Pulse (2024-02-26) — https://www.policyholderpulse.com/red-sea-transit-insurance-premiums-coverage-exclusions/ ; Lloyd's List (2024-01) — https://www.lloydslist.com/LL1147831/Red-Sea-war-risk-rates-soften-as-insurers-price-in-Prosperity-Guardian ; Bloomberg (2025-07-11) — https://www.bloomberg.com/news/articles/2025-07-11/red-sea-insurance-premium-spikes-as-houthi-risks-return ; Insurance Journal (2026-07-21) — https://www.insurancejournal.com/news/international/2026/07/21/878345.htm ; S&P Global MI (2026-02) — https://www.spglobal.com/market-intelligence/en/news-insights/research/2026/02/red-sea-shipping-reopens ; Coface — https://www.coface.com/news-economy-and-insights/houthi-attacks-in-the-red-sea-why-maritime-trade-is-still-not-smooth-sailing ; Atlas Institute — https://atlasinstitute.org/the-red-sea-shipping-crisis-2024-2025-houthi-attacks-and-global-trade-disruption/
- 호르무즈 2026: Lloyd's List — https://www.lloydslist.com/LL1156485/Strait-of-Hormuz-transits-collapse-as-shipping%E2%80%99s-risk-appetite-is-tested , https://www.lloydslist.com/LL1156586/Gulf-war-risk-premiums-topping-double-digit-millions-of-dollars-per-trip ; straits.live (2026-09-25 열람) — https://straits.live/report ; hormuzstraitmonitor.com — https://hormuzstraitmonitor.com/insurance-explained/ ; Cyprus Shipping News (2026-09-18) — https://cyprusshippingnews.com/2026/09/18/the-war-premium-has-moved-into-the-balance-sheet/ ; Wikipedia "2026 Iran war fuel crisis" — https://en.wikipedia.org/wiki/2026_Iran_war_fuel_crisis ; Al Jazeera (2026-09-07) — https://www.aljazeera.com/economy/2026/9/7/oil-prices-surge-as-us-iran-strikes-intensify-in-strait-of-hormuz ; Investing.com (2026-08) — https://www.investing.com/analysis/oil-trading-in-august-2026-backwardation-crack-spreads-and-hormuz-risk-explained-200686148 ; Parameta — https://www.parametasolutions.com/insights/extreme-brent-backwardation-managing-curve-dislocation-with-otc-oil-data/ ; Dallas Fed (2026-03-20) — https://www.dallasfed.org/research/economics/2026/0320 ; World Bank blog — https://blogs.worldbank.org/en/opendata/strait-of-hormuz-disruption-sends-oil-prices-surging
- 팜유 2026: FinancialContent MarketMinute (2026-03-09) — https://markets.financialcontent.com/stocks/article/marketminute-2026-3-9-palm-oil-prices-spike-as-biofuel-demand-surges-amid-crude-rally ; Palm Oil Magazine (2026-08-21, 2026-09-23) — https://www.palmoilmagazine.com/cpo-price/2026/08/21/malaysian-palm-oil-futures-hit-20-month-high-as-b50-biodiesel-boosts-cpo-demand/amp/ , https://www.palmoilmagazine.com/cpo-price/2026/09/23/malaysia-cpo-prices-fall-to-rm4810-lowest-since-august/
- Katrina 크랙: eco3min — https://eco3min.fr/en/diesel-gasoline-crack-spreads-divergence/ ; Minneapolis Fed (2005) — https://www.minneapolisfed.org/article/2005/gasoline-prices-climb-in-response-to-hurricanes
- 캐나다: EDC — https://www.edc.ca/en/article/china-tariffs-canola-exports.html ; Trading Economics 카놀라 뉴스 (2025-09) — https://tradingeconomics.com/commodity/canola/news/486943 ; OFI Magazine — https://www.ofimagazine.com/news/china-announces-100-tariff-on-rapeseed-oil-and-meal-from-canada ; S&P Global (2025-09-19) — https://www.spglobal.com/energy/en/news-research/latest-news/agriculture/091925-canada-adds-1-mil-mt-canola-export-capacity-as-china-tariffs-redirect-flows ; Western Producer — https://www.producer.com/tariffs/canola-oil-exports-tariff-risk/ ; CBC/Yahoo(Fort McMurray 가격) — https://www.cbc.ca/news/canada/calgary/fort-mac-fires-oil-impact-1.3566457 ; CNBC(Irving 2018) — https://www.cnbc.com/2018/10/08/explosion-reported-at-irving-oils-st-john-refinery-candads-largest.html ; CBC 타임라인 — https://www.cbc.ca/news/canada/new-brunswick/timeline-saint-john-refinery-irving-oil-1.4855395
- 2010–11: France24 (2010-08-06) — https://www.france24.com/en/20100806-russia-ban-wheat-drought-exports-sends-global-prices-skyrocketing-europe-agriculture-commerce ; ERS Amber Waves 2011-09(프록시 차단, 미열람) — https://www.ers.usda.gov/amber-waves/2011/september/commodity-price-spike ; FRED PSOILUSDM(프록시 차단) — https://fred.stlouisfed.org/series/PSOILUSDM
- 탄력성·패스스루(원문 미열람): ICCT/Santeramo 2017 — https://theicct.org/sites/default/files/publications/Cross-price-elasticities-for-oils-fats-US-EU_ICCT_consultant-report_06032017.pdf ; ARER 2022 바이오디젤 원료–원유 — https://www.cambridge.org/core/services/aop-cambridge-core/content/view/0C37B3A23069B5628C4FDEDD7463710D/S1068280522000065a.pdf/… ; Energy Economics 2017 — https://www.sciencedirect.com/science/article/abs/pii/S0140988317301172
- GPR·농산물: NBER w31950 / EJPE 2024 — https://www.sciencedirect.com/science/article/pii/S0176268024000764 ; Steinbach AEPP 2024 — https://onlinelibrary.wiley.com/doi/10.1002/aepp.13481 ; arXiv 2404.01641 — https://arxiv.org/abs/2404.01641 ; MDPI Risks 2023 — https://www.mdpi.com/2227-9091/11/5/84 ; JRFM 2023 이벤트 스터디 — https://www.mdpi.com/1911-8074/16/5/256 ; Nature HSSC 2025(cross-quantilogram) — https://www.nature.com/articles/s41599-025-06072-4
- M5/M6/M7 문헌: Crespo Cuaresma et al., J. Forecasting 2024 — https://onlinelibrary.wiley.com/doi/full/10.1002/for.3152 ; CRAFT arXiv 2608.09534 — https://arxiv.org/pdf/2608.09534 ; Conditional MC (Annals of Actuarial Science) — https://www.cambridge.org/core/journals/annals-of-actuarial-science/article/conditional-monte-carlo-for-sums-with-applications-to-insurance-and-finance/3FC4A576C75607F46F9B7FF0238C5A94 ; GTAP AEPP 2023 — https://onlinelibrary.wiley.com/doi/full/10.1002/aepp.13351 ; Food Security 2025 — https://link.springer.com/article/10.1007/s12571-025-01560-6 ; Frontiers 2026 해바라기유 네트워크 — https://www.frontiersin.org/journals/environmental-science/articles/10.3389/fenvs.2026.1757181/full

### 접근 제한 기록(본 세션)
- WebFetch **프록시 차단(EGRESS_BLOCKED)**: eia.gov · ers.usda.gov · cambridge.org · theicct.org · nber.org · arxiv.org · sciencedirect.com · onlinelibrary.wiley.com · fred.stlouisfed.org · indexmundi.com. 해당 문헌은 WebSearch 요약·초록 수준으로만 반영 — 라벨을 INFERENCE로 유지했고, 수치 인용 전 사내망 원문 대조가 필요함.
- Reuters·IEA 원문은 검색 결과에 직접 노출되지 않아 2차 인용(Moscow Times·Kyiv Independent 등)으로 대체.
