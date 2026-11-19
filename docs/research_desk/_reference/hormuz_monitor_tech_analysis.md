# Hormuz Monitor 기술 스택 분석 및 Nexus 적용 방안

**작성일**: 2026-05-26  
**참조**: https://github.com/rahoney/hormuz-monitor  
**패널**: C-01(PM) · C-03(Lead DS) · C-06(EDA) · C-08(DQOps) · P-02(지정학)  
**분류**: 내부 기술 참조 문서

---

> **HITL 게이트**: 이 문서는 기술 분석 목적. 도출된 구매 신호는 CLAUDE.md §6 HITL 프로세스 필요.

---

## 1. Hormuz Monitor 기술 스택 요약

### 1.1 핵심 구성요소

| 계층 | 기술 | Nexus 대응 |
|---|---|---|
| **실시간 선박 추적** | AISstream.io WebSocket | `ais_connector.py` (Phase A HTTP, Phase B WebSocket) |
| **상품 가격** | yfinance + EIA API | `commodity_connector.py` (동일 패턴) |
| **뉴스/이벤트** | RSS 피드 (BBC/Reuters/CNBC) | `gpr_connector.py` 확장 예정 |
| **AI 요약** | Google Gemini API | Perplexity sonar-pro (현행) |
| **데이터베이스** | Supabase PostgreSQL | DW (Phase B) |
| **프론트엔드** | Next.js + Recharts + MapLibre | 미구현 (GitHub Actions 아티팩트 방식) |
| **배포** | Vercel (FE) + Render (BE) | GitHub Actions + 클라우드 학습 환경 |

### 1.2 복합 위험 지수 공식

```
Hormuz Risk Score (0-100) =
  Vessel_Score  × 0.40  (탱커 통과 수 역비례)
  + Geo_Score   × 0.30  (지정학 긴장 지수)
  + Brent_Score × 0.20  (유가 수준 + 변동성)
  + VIX_Score   × 0.10  (금융시장 변동성)
```

**Nexus 대두유 적용 복합 지수**:
```
SBO Supply Risk Score (0-100) =
  AIS_HORMUZ_TANKER × 0.50  (호르무즈 탱커 통과 수 역비례)
  + AIS_MALACCA     × 0.30  (말라카 해협 탱커 통과 수)
  + AIS_PANAMA      × 0.20  (파나마 운하 탱커 통과 수)
```
→ `ais_connector.py`의 `_compute_risk_composite()` 구현 완료

---

## 2. MarineTraffic vs. AISstream.io 결정 (C-01 × P-02)

### 2.1 비교 분석

| 항목 | MarineTraffic API | AISstream.io |
|---|---|---|
| **가격** | $500+/월 (유료 전용) | 무료 tier 존재 (월 50만 메시지) |
| **데이터 지연** | ~5분 | 실시간 WebSocket |
| **선박 분류** | 정확한 선박 유형·목적지 | AIS 타입 코드 기반 (약간 부정확) |
| **역사 데이터** | 가능 (유료) | 없음 (실시간만) |
| **API 방식** | REST HTTP | WebSocket 스트리밍 |
| **커버리지** | 전 세계 (150K+ 선박) | 전 세계 (AIS 표준 기반) |

### 2.2 결정: AISstream.io Phase A / MarineTraffic Phase B

**C-01 PM 결론**: 현 Phase A에서는 **AISstream.io** 채택.
- 무료 tier로 주요 3개 해협(호르무즈·말라카·파나마) 탱커 수 파악 가능
- Hormuz Monitor 검증된 아키텍처 (신뢰성 확인)
- Phase B (운영 예산 확보 후): MarineTraffic v3 API로 전환, 선박별 화물 유형(대두유 전용 탱커 필터링) 가능

**P-02 지정학 결론**: 해협 봉쇄/교란 신호는 GPR 지수와 병렬 모니터링.
- 호르무즈: 이란-미국 긴장과 AWRP(전쟁 위험 보험료) 연동
- 말라카: 해적 활동, 남중국해 분쟁 신호
- 파나마: 가뭄 수위(운하 통과 제한), 미국 무역정책

**구현 상태**: `src/pipeline/connectors/ais_connector.py` 생성 완료 (Phase A)

---

## 3. Nexus에 적용할 핵심 패턴 (C-03 × C-06 × C-08 패널)

### 3.1 모듈형 ETL 패턴

**Hormuz Monitor 구조** → **Nexus 적용**:
```
collectors/     → src/pipeline/connectors/
jobs/           → .github/workflows/ (GitHub Actions cron)
services/       → src/forecasting/ (G1/G2/G3 분석)
db/             → DW (Phase B)
utils/          → src/utils/ (gemini_client 등)
```

### 3.2 RSS 뉴스 피드 수집 (Priority 2 — 비정형 데이터)

Hormuz Monitor가 사용하는 RSS 패턴을 Nexus에 적용:
```python
# 대두유 관련 RSS 키워드 필터
SOYBEAN_OIL_KEYWORDS_EN = ["soybean oil", "soybean", "soy oil", "vegetable oil", 
                             "argentina export", "india import duty", "biodiesel", "USDA WASDE"]
SOYBEAN_OIL_KEYWORDS_KO = ["대두유", "콩기름", "식용유", "USDA", "바이오디젤"]

# 소스: Reuters (식품/원자재), Bloomberg Agriculture, USDA News, AGWeb
```
→ `news_sentiment_connector.py` Phase B 구현 예정 (MEMORY D-005)

### 3.3 다중 주기 캐싱 전략

| 데이터 유형 | Hormuz Monitor TTL | Nexus 적용 |
|---|---|---|
| 상품 가격 (CBOT, 환율) | 93-103초 | GitHub Actions 일별 + yfinance 즉시 조회 |
| 선박/해협 데이터 | 425-513초 | AIS 6시간 간격 |
| 뉴스/이벤트 | 1,636-7,269초 | Perplexity 일별 갱신 |
| USDA WASDE | 월별 | WASDE 발표일 트리거 |

### 3.4 오류 격리 패턴 (C-08 DQOps 관련)

Hormuz Monitor의 `error_repo.py` 패턴:
- 자격증명 마스킹: API 키 앞 8자리만 로그에 표시 (이미 `customs_connector.py`에 적용)
- 소스별 실패 추적: `source_runs` 테이블 → GitHub Actions 아티팩트로 대체
- 오류 격리: 단일 커넥터 실패가 파이프라인 전체를 차단하지 않음

### 3.5 조건부 실행 패턴 (USDA 보고서 날짜 기반)

Hormuz Monitor의 exchange-hour 기반 조건부 실행을 USDA 발표 스케줄에 적용:
```yaml
# USDA WASDE 발표월 두 번째 금요일 집중 수집
- cron: "30 20 8-14 1,2,3,4,5,6,7,8,9,10,11,12 5"  # 매월 8-14일 금요일
```
→ 향후 `wasde_connector.py`에 "WASDE 발표일 전후 집중 수집" 로직 추가 예정

---

## 4. 신규 변수 제안 (G1 변수 풀 확장)

C-03 검토 결과, Hormuz Monitor 분석을 통해 다음 변수 추가를 권고:

| 변수 코드 | 설명 | 출처 | 우선순위 |
|---|---|---|---|
| `AIS_HORMUZ_TANKER_COUNT` | 호르무즈 해협 일별 탱커 통과 수 | AISstream.io | **P1** |
| `AIS_MALACCA_TANKER_COUNT` | 말라카 해협 일별 탱커 통과 수 | AISstream.io | P1 |
| `AIS_PANAMA_TANKER_COUNT` | 파나마 운하 일별 탱커 통과 수 | AISstream.io | P2 |
| `SBO_STRAIT_RISK_COMPOSITE` | 3개 해협 복합 위험 지수 (0-100) | AIS 연산 | **P1** |
| `SBO_NEWS_SENTIMENT` | 대두유 관련 뉴스 감성 점수 (-1~+1) | RSS + FinBERT | P2 (Phase B) |
| `AWRP_MULTIPLIER` | 전쟁 위험 보험료 배수 (vs. 기준) | Perplexity/Lloyd's | P2 |

---

## 5. 즉시 적용 조치 요약

| 조치 | 파일 | 상태 |
|---|---|---|
| AIS 커넥터 생성 (Phase A) | `src/pipeline/connectors/ais_connector.py` | ✅ 완료 |
| SBO 복합 위험 지수 산출 | `ais_connector.py` → `_compute_risk_composite()` | ✅ 완료 |
| MarineTraffic Phase B 결정 문서화 | 이 문서 §2.2 | ✅ 완료 |
| RSS 뉴스 수집 설계 | MEMORY D-005 참조 → Phase B | 📋 예정 |
| AIS 커넥터 WBS 등록 | `reports/WBS 초안 ver.xlsm` | 📋 진행 중 |

---

## 6. 참조 파일 (hormuz-monitor)

- **위험 점수 계산**: `backend/services/risk_score_service.py`
- **AIS 수집**: `backend/collectors/shipping/aisstream_collector.py`
- **시장 데이터**: `backend/collectors/market/yfinance_collector.py`
- **AI 요약**: `backend/utils/gemini_client.py`
- **프론트 캐싱**: `frontend/src/lib/api/dashboard-cache.ts`

---

*Project Nexus · 기술 참조 문서 · C-01/C-03/C-06/C-08/P-02 패널*
