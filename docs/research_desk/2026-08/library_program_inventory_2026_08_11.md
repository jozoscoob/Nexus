# 라이브러리·프로그램 인벤토리 — GitHub 통합 가능 vs 수동 설정 (유료/무료 구분)

**작성일**: 2026-08-11 · **작성**: C-01(총괄) · C-04(인프라 검증)
**목적(조정자 Req)**: Nexus가 사용하는 전체 라이브러리·프로그램·서비스를
① **GitHub(Actions) 통합 가능 — 에이전트가 자율 처리**와 ② **수동 설정 필요 — 조정자 개입**으로
구분하고, 수동 항목은 **유료/무료**를 명시함.

---

## 1. GitHub Actions 통합 가능 — 에이전트 자율 처리 (전부 무료 OSS)

워크플로우 `pip install`로 즉시 설치되며 별도 조치가 필요 없음. 실사용 기준(2026-08-11 워크플로우 전수 조사).

| 분류 | 라이브러리 | 용도 | 비고 |
|---|---|---|---|
| 데이터 | `pandas` `numpy` `pyarrow` | 전 파이프라인 공통 | libraries.md 승인 |
| HTTP | `httpx` | 전 커넥터 REST 호출 | IPv4 강제 트랜스포트(A-085) |
| HTTP 우회 | `curl_cffi` | yfinance 429 완화(브라우저 임퍼소네이션) | A-071 |
| 시장 데이터 | `yfinance` | CBOT BO=F 폴백 | 레이트리밋 위험 — Databento가 1순위 |
| 시장 데이터 | `databento` | CBOT ZL 15개년(공식 SDK) | SDK 무료 · **데이터는 종량제(§2)** |
| 무역 통계 | `comtradeapicall` | UN Comtrade 폴백 | 무료 500건/일 |
| PDF | `pdfplumber` `pypdf` | GAIN·FAO 판독 | DRM 문서는 판독 불가(§3) |
| Excel | `openpyxl` | 수동 업로드 xlsx 파싱·열람 사본 | `scripts/` 한정 — 프로덕션 금지(C-011) |
| ML/통계 | `scikit-learn` `statsmodels` `scipy` | G1 ElasticNet·Granger | libraries.md 승인 |
| 리포트 | `weasyprint` `markdown2` | KO/EN HTML+PDF 생성 | fonts-noto-cjk(apt) 동반 |
| 테스트 | `pytest` | WBS 1.1.8 품질 검증 | |
| 설정 | `pyyaml` | 시맨틱 레이어 YAML | |
| LLM SDK | `openai` `anthropic` | 교차검증·헬스체크 | SDK 무료 · **API는 종량제(§2)** |
| WebSocket | `websocket-client` | AISstream 해협 추적 | |

> `google-genai`는 헬스체크 워크플로우에 잔존하나 **Gemini 전면 배제(조정자 지시)** — 제거 예정.

---

## 2. API 서비스 — 키 등록만 수동(1회), 이후 Actions 자동

### 2.1 무료 (키 발급만 필요)

| 서비스 | 데이터 | 키 상태 |
|---|---|---|
| FRED | FX·금리·CPI·VIX·CPO 프록시 | ✅ 등록 |
| BOK ECOS | 한국 금리·환율 | ✅ 등록 |
| KOSIS | 한국 CPI | ✅ 등록 |
| data.go.kr (관세청 GW) | HS별 수출입 실적 | ✅ 등록 (Actions 전용 — 샌드박스 차단) |
| USDA NASS·FAS(PSD/ESR)·ARMS | 작황·수급·수출 | ✅ 등록 |
| NOAA CPC | ENSO ONI | 키 불요 |
| Open-Meteo ERA5-Land | 12개 산지 기후 | 키 불요 |
| NASA POWER · FIRMS | 농업기상·산불 | ✅ 등록(FIRMS 선택) |
| USGS · GDELT | 지진·이벤트 | 키 불요 |
| UN Comtrade | 무역 통계 폴백 | ✅ 등록 (무료 500건/일) |
| AISstream.io | 해협 탱커 추적 | ✅ 등록 (무료 tier) |
| stooq | BDI 폴백 CSV | 키 불요 |

### 2.2 유료 (과금 발생 — 조정자 결제 관리)

| 서비스 | 데이터 | 과금 형태 | 상태 |
|---|---|---|---|
| Trading Economics | BDI·CPO 히스토리 | 구독 $65~200/월 | ✅ 사용 중 |
| Databento | CBOT ZL 15개년 | 종량제(1회 ~$1 미만) | ✅ 사용 중 — 재실행 시 소액 재과금 |
| Perplexity API | 실시간 프록시(BCAA·GPR·정책 뉴스) | 크레딧 종량제 | ✅ 사용 중 |
| OpenAI API | gpt-5.6-sol/luna 교차검증(Reasoning Pro) | 종량제 | ✅ 사용 중 (Req 4) |
| Anthropic API | 헬스체크·모델 모니터 | 종량제 | ✅ 사용 중 |

---

## 3. 수동 설치·설정 필요 — 조정자(사용자) 직접 처리

| 항목 | 유료/무료 | 사유·조치 |
|---|---|---|
| **사내 DRM 클라이언트(Document SAFER)** | 사내 라이선스 | GAIN PDF 130건 DRM 차단 — **DRM 해제 후 재업로드 필요** (`reports/market/drm_blocked_documents.md`) |
| 클라우드 학습 환경 워크스페이스 | 유료(클라우드 구독) | G2 학습 환경 — 구독·리소스그룹·오브젝트 스토리지 연결은 포털에서 수동 구성 |
| 키 보관소 | 유료(클라우드 구독) | 프로덕션 시크릿 이중화 — Phase B |
| DW 계정·웨어하우스 | 유료 | Phase B 데이터 웨어하우스 — 계정 개설·권한은 수동 |
| GitHub Secrets 등록 | 무료 | 신규 API 키 등록·로테이션은 Settings에서 수동(보안상 에이전트 불가) |
| data.go.kr 활용신청 갱신 | 무료 | 관세청 GW 키 만료 시 포털에서 재승인(A-036 3단계 절차) |
| Excel + XLGantt 매크로 | 유료(MS Office) | WBS xlsm 열람·VBA Gantt 갱신은 로컬 Excel 필요 |
| Claude Code CLI 플러그인(`/plugin`) | 무료 | 대화형 CLI 전용 — 원격 환경 설치 불가 → `korean_style.md` 규칙 파일로 대체(A-047) |

---

## 4. 운영 원칙 재확인

- **API 우선(조정자 표준)**: 수동 작업은 최후 수단. 위 §3 항목만 수동 유지, 나머지는 전부 Actions 자동화.
- **키 관리**: 모든 키는 GitHub Secrets + `os.environ` — 코드·문서 하드코딩 금지(CLAUDE.md §2).
- **신규 라이브러리 도입 절차**: `.claude/rules/libraries.md` 갱신 후 사용(무단 의존성 추가 금지).
- **자율/승인 경계**: §1(무료 OSS)은 에이전트 자율 · §2.2(유료)·§3은 조정자 승인 후 진행.
