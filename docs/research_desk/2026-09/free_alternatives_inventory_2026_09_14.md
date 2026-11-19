# 유료 서비스별 무료 대안 인벤토리 — 1차판 (2026-09-14) · 최종판 시한 2026-09-30

**요청**: 최종 결정자 — "유료 서비스 필요성은 추후 직접 판단. 9/30까지 가용한 무료 대안을 소스별 제공 데이터 유형·적시성·품질 등 상세 근거와 함께 정리."
**범위**: 사용 중 유료 5종(Trading Economics·Databento·Perplexity·OpenAI·Anthropic) + 후보 9종(BCAA·basis 호가·Reuters/AP·FCPO·APK-Inform·Kpler/Vortexa·WeatherNext·Open-Meteo 상용·장중 환율).
**판독 규율**: CONFIRMED(공식 페이지·저장소 실측) / INFERENCE(검색 발췌·2차 출처) / DATA GAP(미검증·대안 없음). 조회일 2026-09-14.
**주의**: 이 세션의 외부 접속 경로는 대부분의 원천 도메인을 차단해, 약관 문구 다수가 검색 발췌(INFERENCE)다. **최종판(9/30) 전에 Actions 러너에서 각 URL을 재열람해 라이선스 조항을 확정**한다(러너는 차단 대상이 아님). 단일 원천은 `src/semantic/ontology.yaml data_sources`(인과 지도 배지·사전집 DataSource 엔티티가 참조).

---

## 0. 한 줄 판정 (유료 서비스별)

| 유료 서비스 | 역할 | 무료 대안 판정 | 라벨 |
|---|---|---|---|
| Databento ZL 정산가 | 목표변수 | **라이선스 정합 무료 경로는 CME DataMine 무료 정산 파일뿐**(로그인·자정 CT 공개). yfinance는 야후 약관상 자동·상업 수집 위험, stooq는 약관 미확인 | INFERENCE |
| Trading Economics (BDI·CPO·유지 26종) | 운임·대체유 | **BDI: 라이선스 정합 무료 피드 없음**(발틱거래소 구독 필수, stooq 404·투자 포털 스크래핑 금지) → 저장소 xlsx 사본 폴백만 · 유지류: 세계은행 핑크 시트·IMF·FAO **월간**은 무료(CC BY) — 일별 밀도 대체 불가 | INFERENCE |
| Perplexity (실시간 프록시) | 뉴스·지정학·BCAA | 뉴스·지정학은 **GDELT(상업 이용 명시 허용)** + Google News RSS(회색)로 대체 가능(구현) · **BCAA 무료 대안 없음** | CONFIRMED / DATA GAP |
| OpenAI·Anthropic (교차검증·에이전트) | 검증 계층 | 오픈 가중치 모델(Qwen3-8B Apache-2.0 CONFIRMED) CPU 추론은 라이선스 안전하나 느리고 품질 열위 · 무료 API 티어는 일 50~1,000회 캡·약관 미확정 | INFERENCE |
| Baltic BCAA(후보) | 탱커 운임 | **없음** — Drewry/Clarksons/UNCTAD도 무료 주간 수치 없음 | DATA GAP |
| Platts/Fastmarkets basis(후보) | CFR 아시아 호가 | **아르헨티나 공식 FOB(일별) + CEPEA 대두유(일별) + USDA AMS 주간 현물** 3각 근사 — CFR 아시아와 NOT COMPARABLE | INFERENCE |
| Reuters/AP 유료 피드(후보) | 기사 | 3단 무료 체인(구현) · AP 무료 평가 티어는 공개 페이지에서 확인 불가 | DATA GAP(AP) |
| Bursa FCPO(후보) | 팜유 일별 | MPOB 월간(등록)·Bursa 15분 지연 화면(표시 전용) — 일별 가격 축 대체 불가 | INFERENCE |
| APK-Inform(후보) | 흑해 해바라기유 | FAO/GAIN 정성 + UkrAgroConsult RSS(구현) | CONFIRMED |
| Kpler/Vortexa(후보) | 화물 추적 | AISstream 무료 티어(구현) — 리드타임 분포는 문헌값 | CONFIRMED |
| WeatherNext 3(후보) | 예보 | Open-Meteo(구현·비상업 한정 CONFIRMED) · **ECMWF Open Data(CC BY 4.0·CONFIRMED)** · NOAA GFS/GEFS(공공) | CONFIRMED |
| Open-Meteo 상용(DQ-26) | 기후 관측·예보 | 무료 티어 "비상업 전용" 공식 문구 확인 → 회사 업무는 상업 이용 = Standard $29/월 또는 ECMWF/GFS·NASA POWER·CDS(CC-BY)로 이전 | CONFIRMED |
| 장중 환율(후보) | 원화 도착가 | **없음** — ECB·FRED·한국은행·Frankfurter·er-api 전부 일 1회 고정 | DATA GAP |

---

## 1. 시세 — 시카고 대두유 선물 (유료: Databento)

| 대안 | 제공 데이터 | 적시성 | 품질 | 라이선스·상업 이용 | 접근·한도 | 구현 | 라벨 |
|---|---|---|---|---|---|---|---|
| yfinance `ZL=F` | 전월물 연속 일별 OHLCV, 2000~(6,565일 실측) | CME 지연 ≥10분, 일봉 당일 | 심볼 폐지(BO=F)·429 재발, 종가=정산가 여부 미문서(저장소 대조 중앙값 괴리 0.10%) | 야후 약관: 자동 수집 금지 · yfinance 문서 "개인·연구용" | 키 없음·비공식 스로틀 | 구현(교차검증) | INFERENCE |
| CME 정산 페이지·DataMine 무료 정산 파일 | 계약월별 정산·거래량·미결제 | 웹 당일 · 파일 자정 CT(무료), 조기 EOD 파일은 유료 | 공식 | 웹 약관 재배포 금지 · 내부 분석용 무료 파일, Non-Display 라이선스 문의 권장 · 구 FTP 2024-01 폐지 | 무료 등록 | 미구현 | INFERENCE |
| Nasdaq Data Link CHRIS | — | — | 2024-09 폐기(공급사 회신) | — | — | 불가 | INFERENCE |
| stooq `zl.f` CSV | 일별 OHLCV | EOD | 비공개 일일 한도·심볼 소멸 사례 | 약관 문서 없음 → 상업 근거 부재 | 키 없음 | 미구현 | DATA GAP |
| Barchart | 웹 조회·CSV(로그인) | 지연 | 양호 | API 무료 없음(체험만·$500/월~) | — | 부적합 | INFERENCE |

## 2. 운임 — BDI (유료: Trading Economics)

| 대안 | 제공 | 적시성 | 품질 | 라이선스 | 구현 | 라벨 |
|---|---|---|---|---|---|---|
| 발틱거래소 공식 | BDI 일별(런던 13:00경) | 당일 | 정본 | "모든 지수 사용은 유효한 구독·라이선스 대상" — 무료 기계 피드 없음 | — | INFERENCE |
| stooq `^bdi` | 일별 | EOD | 2026-08 실측 404 | 약관 없음 | 체인 2순위(현재 무효) | DATA GAP |
| 투자 포털·TradingView | 화면 | 실시간 | — | 자동 수집 명시 금지 | 불가 | INFERENCE |
| 저장소 TE xlsx 사본 | 일별(스냅샷 append) | 평일 갱신 | 정정본 정본 | 기존 구독 범위 | **구현(3순위 폴백, 9/14)** | CONFIRMED |

## 3. 팜유·유지류 가격 (유료: Bursa FCPO·TE 유지 4종)

| 대안 | 제공 | 적시성 | 품질 | 라이선스 | 구현 | 라벨 |
|---|---|---|---|---|---|---|
| MPOB BEPI 월간 | 생산·재고·수출·가격(주별) | 매월 10일 12:30 MYT | 개정 있음·HTML·로그인 | 저작권·재발행 금지(내부 이용 허용 해석) | 미구현(egress 등재) | INFERENCE |
| Bursa Marketplace FCPO | 15분 지연 호가·정산 | 지연 | 양호 | 표시 전용 | 불가 | INFERENCE |
| 세계은행 핑크 시트 | 팜·대두유·유채·해바라기 월평균 1960~ (xlsx) | 월초 2~6일 | 월평균만 | **CC BY 4.0** | 미구현 | INFERENCE |
| FAO 식품가격지수 유지류 | 월간 지수 1990~ | 월 첫 주 | 지수(수준 아님) | CC BY 4.0(파일별 확인) | 미구현 | INFERENCE |
| IMF PCPS(+FRED 미러 PSOILUSDM·PPOILUSDM) | 월평균 1980~ | 첫 완전 주 수요일 | 월평균 | FRED 인용 조건(120회/분) | 미구현(FRED 키 보유) | INFERENCE |

## 4. 탱커 운임 BCAA (유료: 발틱거래소) — **무료 대안 없음(DATA GAP)**
BCAA는 2025-02 출시 주간 평가(식물성유지 40,000t 기준 포함)로 구독 전용. Drewry(유료 Chemical Forecaster)·Clarksons(설명 페이지)·UNCTAD(연간 리뷰)·LSEG(유료 팜유 탱커 평가) 어디에도 무료 주간 수치 없음. 현행 BDI 건화물 대리는 선종이 달라 방향 프록시로만(A-191 유지).

## 5. basis·CFR 아시아 호가 (유료: Platts/Fastmarkets)

| 대안 | 제공 | 적시성 | 품질 | 라이선스 | 구현 | 라벨 |
|---|---|---|---|---|---|---|
| **아르헨티나 농업부 공식 FOB**(Ley 21.453·Res.65/2025) | 대두 조유 등 일별 공식 FOB + 이력 | 영업일 당일 | 수출세 기준 참조가(거래가 아님) | 정부 공개(조항 미확인) | 미구현 — **최우선 후보** | INFERENCE |
| **CEPEA/ESALQ 대두유** | 상파울루 조유 일별 R$/t 1998~ | 당일 | BRL·세금 포함(정규화 필요) | 등록·인용(조항 미확인) | 미구현 | INFERENCE |
| USDA AMS 주간 현물(MARS API) | 지역별 조유 ¢/lb 주간 | 주간 | 자발 보고 | 공공 도메인·무료 키 | 미구현 | INFERENCE |
| USDA ERS Oil Crops Outlook | 월간 가격표·전망 | 월간 | 분석 | 공공 도메인 | 미구현 | INFERENCE |
| GAPKI·MPOB 수출가 | 월간 CPO 수출가 | 약 2개월 지연 | 보도자료 수준 | 인용 | 미구현 | INFERENCE |
| 다롄 DCE 대두유 `y` | 지연 호가·정산 | 지연 | CNY | 재배포 금지(표시용) | 불가 | INFERENCE |

## 6. 포지셔닝 — CFTC COT (무료·미구현 P0)
Legacy/Disaggregated/TFF, 대두유 코드 007601, 1986~ ZIP + Socrata API(`publicreporting.cftc.gov`, 토큰 시 1,000회/시·요청당 최대 50,000행). 화요일 기준 금요일 15:30 ET 공표(lag 3일 규칙). 공공 도메인. CE-017 근거 지표 후보.

## 7. 환율 (무료 일별 보유 · 장중 = DATA GAP)
ECB 참조환율(KRW 포함·16:00 CET·인용) · FRED H.10(주간 공표·120회/분) · 한국은행 ECOS(일별·상업 이용 출처 표기 조건·약 1,000회/일 2차 출처) · Frankfurter(ECB 기반·MIT 코드·호스팅 약관 미확인) · open.er-api(일 1회·인용·재배포 금지) · exchangerate.host(월 100회 — 부적합). 장중 원/달러 무료 소스는 없음.

## 8. 기후·예보 (유료 후보: WeatherNext 3 · Open-Meteo 상용)

| 대안 | 제공 | 적시성 | 라이선스 | 한도 | 구현 | 라벨 |
|---|---|---|---|---|---|---|
| Open-Meteo | 예보(다중 모델)·ERA5-Land 아카이브 | 시간별·아카이브 5일 지연 | **"오픈소스·비상업 무료 / 상업 이용은 문의"(공식 README) · Standard $29/월(1M)·Pro $99/월** | 무료 10,000회/일 | 구현 | CONFIRMED(약관)·INFERENCE(가격) |
| **ECMWF Open Data** | IFS·AIFS 0.25° 0~240/360h, 일 4회 | 실행 후 7~9시간(AIFS 지연 제거) | **CC BY 4.0** | 500 동시 연결·클라우드/클라우드/GCP 미러 | 미구현(GRIB 점 추출 필요) | CONFIRMED |
| NOAA GFS/GEFS | 0.25° 16일·31멤버 | 실행 후 ~4시간 | 공공 | NOMADS 120회/분 · 클라우드 무제한 | 미구현 | INFERENCE |
| NASA POWER | 일·시·월 기상 1981~ | 2~4일 지연 | 제한 없음·인용 | 명시 한도 없음 | 구현(6~12지역) | INFERENCE |
| Copernicus CDS ERA5-Land | 시간별 1950~ | ~5일(ERA5T) | **2025-07-02부터 CC-BY** | 등록 키·큐 | 미구현 | INFERENCE |

## 9. 뉴스 (유료: Reuters/AP · Perplexity)
GDELT DOC 2.0 — "학술·상업·정부 용도 무제한 무료, 인용·링크 조건"(INFERENCE) · 15분 갱신 · 약 5초당 1요청 스로틀 · 구현. Google News RSS — 비문서·자동 접근 회색(헤드라인·링크만 사용, 구현). AP Media API — 키는 고객지원 문의(무료 평가 티어 공개 확인 불가 → DATA GAP). NewsAPI 개발 티어 — 24시간 지연·100회/일·비상업 전용(부적합). Bing News RSS — PubHub 폐지 후 피드는 유지, 자동 상업 이용 약관 없음.

## 10. LLM 검증 (유료: OpenAI·Anthropic)
Qwen3-8B(Apache-2.0)·Llama 3.3(커뮤니티 라이선스 — "Built with Llama" 표기) CONFIRMED. GitHub 러너(4 vCPU·16GB)에서 8B Q4 추론은 판정 1건 5~15분 추정(실측 필요) — 스키마·일관성 검사용, 적대 검증 대체는 불가(INFERENCE). 무료 API: Groq(예: 70B 30 RPM·1,000/일), OpenRouter free(50~1,000/일, 프롬프트 학습 사용 모델 있음), HF Inference Providers(월 $0.10 크레딧 — 사실상 없음). Gemini는 정책상 배제(C-012, 사실만 기록).

## 11. 무역 통계
UN Comtrade 무료 키 500회/일·100,000행/회(CONFIRMED 패키지 README·INFERENCE 한도) · WITS 무인증 SDMX(연간만 — 관세청 월간 대체 불가). 관세청 data.go.kr은 무료·사용 중.

---

## 12. 즉시 실행 가능한 무료 편입(비용 0·승인 불요) — 9/30 전 착수 후보
1. **CFTC COT 커넥터**(P0) — 공공 도메인·API 명확. 2. **아르헨티나 공식 FOB + CEPEA 대두유** — basis 3각 근사의 일별 축(약관 조항 러너 재확인 후). 3. **세계은행 핑크 시트·IMF PCPS** 월간 유지류 — CE-015 장기 검증. 4. **ECMWF Open Data** 점 추출 — Open-Meteo 상용 조건 회피 경로(GRIB 처리 비용). 5. **CME DataMine 무료 정산 파일** — Databento 이탈 시 라이선스 정합 대안(로그인 필요).

## 13. 9/30 최종판까지 할 일
- Actions 러너에서 각 원천 약관 URL 재열람 → INFERENCE를 CONFIRMED로 전환(특히 야후·stooq·MPOB·MAGyP·CEPEA·ECB·Frankfurter·GDELT 한도).
- stooq `^bdi`·`zl.f` 실호출 판정, CME DataMine 계정 시험, ECMWF Open Data 1회 점 추출 시험(23산지).
- 온톨로지 `data_sources`·사전집 DataSource 엔티티·인과 지도 배지를 최종판과 동기.

관련: `paid_news_sources_pricing_2026_09_13.md`(뉴스 유료 가격) · `weathernext_compute_assessment_2026_09_13.md` · `g2_additional_data_requirements_2026_09_09.md` §3 · decision_queue DQ-1/2/24/25/26.
