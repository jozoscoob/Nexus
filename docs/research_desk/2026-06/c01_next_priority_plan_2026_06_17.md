# C-01 PM 다음 우선순위 계획 — Session 25 이후

**작성일**: 2026-06-17  
**패널**: C-01(PM) · C-03(데이터) · C-05(QA/QC) · C-06(EDA) · C-08(DQSOps)  
**분류**: 내부 프로젝트 관리 문서  
**참조**: `MEMORY.md` PM-024 · `reports/wbs/wbs_full_project.md` v1.6  

---

> **HITL 게이트**: 이 계획은 데이터 파이프라인 운영 목적입니다. 조달 실행 결정은 CLAUDE.md §6 HITL 프로세스를 반드시 거쳐야 합니다.

---

## 1. C-01 현황 평가 — Session 25 완료 사항

| WBS | 작업 | 커밋 | 상태 |
|---|---|---|---|
| 1.1.40 (GATS 이동) | 2026 GATS 01~04월 파일 data/ → data/raw/USDA/FAS/GATS/ | be2e0f1 (main) | ✅ |
| 1.1.41b (FAO AMIS 파이프라인) | `scripts/ingest_fao_amis_pdf.py` + `historical_backfill.yml` fao-amis-ingest job | 93b625b (dev) | ✅ |
| D-014 문서화 | Feature Engineering/Selection 5단계 게이트 프레임워크 | 93b625b (dev) | ✅ |
| D-015 문서화 | Phase A 핵심 8개 피처 확정 + 30개 후보 목록 | 93b625b (dev) | ✅ |
| D-016/D-017 문서화 | FAO AMIS 관련성 분석 (C-03×P1-01~04 패널) | 93b625b (dev) | ✅ |
| MEMORY.md | D-014·D-015·D-016·D-017·A-041·PM-024 추가 | 93b625b (dev) | ✅ |

**총 Session 25 커밋**: main 1건(GATS 이동), dev 1건(804 lines)

---

## 2. 미완료 항목 — 이월 현황

### 2.1 장기 이월 (3+ 세션)

| 항목 | WBS | 이월 횟수 | 차단 이유 |
|---|---|---|---|
| GE 데이터 품질 검증 테스트 | 1.1.8 | 8회 | 항상 더 급한 버그 수정에 밀림 |
| feature→main PR 병합 후 스케줄 재활성화 | 1.1.0 | 4회 | dev 브랜치 작업 집중 |

### 2.2 신규 미완료 (이번 세션 생성)

| 항목 | 설명 | 우선도 |
|---|---|---|
| `commodity_connector.py` CPO 추가 | FCPOc1(Bursa 팜유 선물) → CPO_SBO_SPREAD 파생 | High |
| `scripts/ingest_wasde_xlsx.py` | WASDE 월별 Excel 파서 (10개 파일, 시트별) | High |
| `scripts/ingest_psd_data.py` | PS&D Oil/Oilseed Excel 파서 (D-012 기준 Local 제외) | High |
| `scripts/ingest_gats_data.py` | GATS 수출·재수출 Excel 통합 파서 | High |
| `src/pipeline/feature_quality_gate.py` | D-014 5단계 게이트 구현 | Medium |
| `data/schemas/feature_store.yaml` | 피처 스토어 스키마 정의 | Medium |
| `external_data_refresh.yml` FAO AMIS | 월별 자동 다운로드 단계 추가 (Phase B) | Low (Phase B) |

### 2.3 차단된 항목

| 항목 | 차단 이유 | 조치 |
|---|---|---|
| Request 4 추가 에이전트 | `aitmpl.com/featured/tinyfish` → HTTP 403, 접근 불가 | 사용자 직접 URL 재확인 필요 |
| Korea Customs DATA_GO_KR_SERVICE_KEY | 포털 키 만료 (A-025/A-036) | 수동 갱신 (data.go.kr 마이페이지) |
| AISSTREAM_API_KEY | 미등록 | aisstream.io 무료 가입 후 GitHub Secrets 등록 |

---

## 3. WSJF 우선순위 — Sprint 4 계획 (2026-06-17 ~ )

> WSJF = (사업가치 + 시간가치 + 리스크감소) / 작업규모  
> G2 학습 준비도 기준: 모든 수동 업로드 데이터가 Parquet 변환 완료되어야 Historical Backfill 실행 가능

### Sprint 4-A: 수동 업로드 데이터 Parquet 변환 (WSJF 최고)

G1/G2/G3 학습을 위한 데이터 기반 확보. WASDE·PS&D·GATS 파서 3종이 이 스프린트의 핵심.

| 순서 | 작업 | 파일 | 예상 규모 | WSJF |
|---|---|---|---|---|
| ① | WASDE 월별 Excel 파서 | `scripts/ingest_wasde_xlsx.py` | 중 (~120줄) | 9.2 |
| ② | PS&D Oil/Oilseed 파서 | `scripts/ingest_psd_data.py` | 소 (~80줄) | 8.7 |
| ③ | GATS 수출·재수출 파서 | `scripts/ingest_gats_data.py` | 소 (~90줄) | 8.4 |
| ④ | FAO AMIS PDF 실제 실행 테스트 | `ingest_fao_amis_pdf.py` 검증 | 소 (테스트만) | 7.9 |
| ⑤ | historical_backfill.yml에 WASDE/PSD/GATS 잡 추가 | `.github/workflows/historical_backfill.yml` | 소 (~40줄) | 7.8 |

**Sprint 4-A 완료 기준**: `data/raw/` 아래 5개 parquet 파일 생성 확인  
- `wasde_historical.parquet` (CBOT SBO 공급/수요/재고)  
- `psd_soybeanoil_historical.parquet` (PSD Oil, Local 제외)  
- `psd_soybean_historical.parquet` (PSD Oilseed)  
- `gats_export_historical.parquet` + `gats_reexport_historical.parquet`  
- `fao_amis_historical.parquet` (인제스트 스크립트 기존 구현)

### Sprint 4-B: CPO 외생 변수 완성 (WSJF 높음)

D-015 Phase A 핵심 8개 피처 중 `CPO_SBO_SPREAD`가 현재 미구현.

| 순서 | 작업 | 파일 | 비고 |
|---|---|---|---|
| ① | FCPOc1 Bursa 팜유 선물 추가 | `commodity_connector.py` | yfinance `FCPO.KL` 또는 TE API |
| ② | CPO_SBO_SPREAD 파생 지표 계산 | `commodity_connector.py` | `CPO_price - CBOT_SBO_FUTURES` |
| ③ | commodity_data.yaml 스키마 업데이트 | `data/schemas/commodity_data.yaml` | 새 컬럼 2개 추가 |

### Sprint 4-C: WBS 1.1.8 GE 데이터 품질 테스트 (WSJF 중-높음)

8+ 세션 이월된 핵심 게이트. G2/G3 학습 전 C-08 DQSOps PASS 필수.

| 순서 | 작업 | 파일 |
|---|---|---|
| ① | 파이프라인 parquet 스키마 검증 | `tests/test_pipeline_quality.py` |
| ② | DQSOps 5차원 자동 점수 | `src/pipeline/validators/c08_dq_validator.py` 통합 테스트 |
| ③ | pytest CI job 추가 | `.github/workflows/external_data_refresh.yml` |

### Sprint 4-D: 피처 스토어 스키마·게이트 (WSJF 중)

D-014 5단계 게이트를 코드로 구현. G1 LASSO 분석의 공식 입력 경로 확립.

| 작업 | 파일 |
|---|---|
| 피처 스토어 YAML 스키마 | `data/schemas/feature_store.yaml` |
| 5단계 게이트 Python 모듈 | `src/pipeline/feature_quality_gate.py` |

---

## 4. PR 병합 및 스케줄 재활성화 계획

### 현재 상태
- Dev 브랜치 `claude/setup-nexus-llm-tools-RX4aS`: Session 25 커밋까지 push 완료 (93b625b)
- Main 브랜치: GATS 파일 이동 완료, dev 브랜치 변경사항 미반영

### 권고 순서
1. **Sprint 4-A 완료 후** dev → main PR 생성 (Sessions 23~25 누적 변경 포함)
2. PR 병합 후 `external_data_refresh.yml` cron 주석 해제 → 스케줄 재활성화
3. 재활성화 전 C-08 DQSOps 수동 1회 실행 → 8개 커넥터 상태 점검

---

## 5. G2/G3 착수 전제 조건 체크리스트

C-01의 판단: G2 클라우드 학습 환경 착수는 아래 조건이 모두 충족된 후 진행.

| 조건 | 현재 상태 | 담당 |
|---|---|---|
| 8개 외부 커넥터 C-08 DQSOps PASS ≥ 0.70 | ⚠️ 미검증 | C-08 |
| WASDE/PS&D/GATS/FAO AMIS parquet 생성 | ❌ 미구현 | C-04 |
| CPO_SBO_SPREAD 지표 수집 | ❌ 미구현 | C-03 |
| WBS 1.1.8 GE 테스트 PASS | ❌ 미구현 | C-05/C-08 |
| Phase A 30개 피처 후보 수집 완료 | ⚠️ 8개 확정, 22개 진행 중 | C-03/C-06 |
| feature→main PR 병합 | ⚠️ 병합 대기 중 | C-01 |

**현재 G2 착수 가능 시점 추정**: Sprint 4-A~C 완료 후 (약 3~4 세션 소요 예상)

---

## 6. 에이전트별 다음 액션 요약

| 에이전트 | 담당 다음 작업 | 긴급도 |
|---|---|---|
| **C-01** (PM) | Sprint 4-A 착수 조율 · dev→main PR 준비 | HIGH |
| **C-03** (데이터) | WASDE/PS&D/GATS 파서 3종 구현 · CPO FCPOc1 추가 | HIGH |
| **C-04** (문서인텔) | FAO AMIS ingest_fao_amis_pdf.py 실제 PDF 테스트 확인 | MEDIUM |
| **C-05** (QA/QC) | 파서 3종 코드 리뷰 · Red Flag 점검 | HIGH |
| **C-06** (EDA) | Sprint 4-A parquet 생성 후 기술통계 EDA 실행 | AFTER 4-A |
| **C-08** (DQSOps) | 수동 업로드 parquet 5종 DQSOps 검증 · WBS 1.1.8 착수 | MEDIUM |
| **P1-01** (상품) | CPO_SBO_SPREAD 임계값 설정 ($50·$175/MT) 검토 | MEDIUM |
| **P1-02** (거시) | ARGENTINA_SOY_CRUSH_VOLUME 수집 방법 결정 | LOW |
| **P1-03** (지정학) | INDIA_PALM_IMPORT_QUOTA GAIN PDF 수령 후 파싱 | LOW |
| **P1-04** (공급망) | GATS 데이터 수집 완료 후 한국 SBO 수입 경로 재분석 | AFTER 4-A |

---

## 7. 미결 참조 요청 (차단된 외부 의존성)

| 항목 | 상태 | 사용자 조치 필요 |
|---|---|---|
| 추가 에이전트 참조 URL (`aitmpl.com/featured/tinyfish`) | HTTP 403 — 접근 불가 | URL 재확인 또는 직접 에이전트 사양 제공 |
| Korea Customs API 키 | 만료 (A-025/A-036) | data.go.kr 마이페이지 재신청 |
| AISSTREAM_API_KEY | 미등록 | aisstream.io 무료 가입 → GitHub Secrets |

---

*→ Sprint 4-A 착수: `scripts/ingest_wasde_xlsx.py` 구현 시작*  
*→ 다음 MEMORY.md 업데이트 예정: PM-025 (Sprint 4-A 완료 시)*
