# 도입 라이브러리·프로그램 통합 가이드 (단계별 절차 포함)

**작성일**: 2026-08-12 · **작성**: C-01(총괄) · C-03(모델) · C-04(인프라·MLOps) · P1-06(시맨틱)
**근거**: `docs/research_desk/2026-08/model_strategy_2026_08_12/` (Champion–Challenger 전환)
**대체 관계**: `library_program_inventory_2026_08_11.md`의 **현행 재고 목록**은 유지하고,
본 문서는 **신규 도입 대상과 그 설치·연동 절차**를 담당한다.

> **읽는 법** — 3개 등급으로 나뉜다.
> **[A] 에이전트 자율**: GitHub Actions에서 `pip install`로 끝. 조정자 조치 불필요.
> **[B] 키/계정만 수동**: 조정자가 가입·키 발급 후 GitHub Secrets 등록. 이후 자동.
> **[C] 완전 수동**: 조정자가 콘솔·설치 작업 수행. 유료/무료를 명시.


> ## ⛔ 2026-08-12 개정 — Supabase·Neo4j 도입 **철회**, DW 보류 **해제**
>
> 조정자가 공유한 **회사 목표 아키텍처**(11월 Control Tower 클라우드 통합 · ETL 도구 ·
> PostgreSQL+중앙 저장소 → **통합 데이터 플랫폼 단일화**)가 본 문서의 전제를 바꿨다.
> 상세 판단: `docs/research_desk/2026-08/target_architecture_migration_2026_08_12.md`
>
> | 항목 | 본 문서 최초 판단(8/12 오전) | **개정 판단(8/12 확정)** |
> |---|---|---|
> | Supabase | [B] 도입 권고(무료 티어) | 🔴 **철회** — 회사가 걷어내는 PostgreSQL을, 사외 3rd-party에, 이관 3개월 전에 신설하는 3중 역행 |
> | Neo4j AuraDB | [B] 조건부 도입(4~6주 후) | 🔴 **무기한 보류** — 목표 아키텍처에 그래프 DB 카테고리 자체가 없음 |
> | DW | 보류(D-021로 목적 소멸) | 🟢 **보류 해제** — 전사 통합 데이터 플랫폼 단일화 목표로 전제 무효화. Nexus는 외부 데이터 전용 전용 스키마 |
> | DuckDB | 1순위 도입 | 🟢 **유지** — 파일 임베디드라 이식성 100%, 어디로 이관해도 동행 |
>
> **§2(Supabase 절차)·§3(Neo4j 절차)은 이력 보존용이며 현재 실행 대상이 아니다.**
> 조정자의 계정 생성 작업은 **불필요**하다.

---

## 0. 도입 우선순위 요약

| 순위 | 대상 | 등급 | 유·무료 | 도입 시점 | 목적 |
|---|---|---|---|---|---|
| 1 | LightGBM · statsmodels 확장 | **[A]** | 무료 | 즉시 | G1/G2 Champion 구성 |
| 2 | MAPIE (EnCQR) | **[A]** | 무료 | 즉시 | G2 구간 보정 |
| 3 | DuckDB | **[A]** | 무료 | 즉시 | as-of join·feature mart(추가 인프라 0) |
| 4 | great_expectations | **[A]** | 무료 | 1~2주 | 모델 진입 게이트 자동화 |
| ~~5~~ | ~~Supabase~~ | — | — | **철회** | 상단 개정 배너 참조 |
| ~~6~~ | ~~Neo4j AuraDB~~ | — | — | **무기한 보류** | 상단 개정 배너 참조 |
| 7 | 클라우드 학습 환경 Workspace | **[C]** | 유료 | G2 학습 착수 시 | 학습·모델 레지스트리 |
| 8 | Darts / NeuralForecast | **[A]** | 무료 | Challenger 단계 | N-BEATSx·N-HiTS·PatchTST |
| 9 | Chronos (foundation) | **[A]** | 무료 | Challenger 단계 | zero-shot baseline |
| 10 | Baltic Exchange BCAA | **[C]** | **유료(견적)** | 보류 | 운임 신호 고도화 |

> **판단**: 지금 당장 필요한 것은 5·6번이 아니라 1~4번이다. 조사 패키지 결론대로
> **feature mart와 기준선 재현이 선행**이며, Neo4j는 "검증된 엣지가 충분히 쌓인 뒤"가
> 도입 시점이다(§5 참조). 무리한 조기 도입은 운영 부담만 늘린다.

---

## 1. [A] 즉시 도입 — Actions `pip install`만으로 완료

조정자 조치 **불필요**. 에이전트가 워크플로우에 반영한다.

```bash
# G1/G2 Champion 스택
pip install lightgbm>=4.0 scikit-learn>=1.4 statsmodels>=0.14 arch>=6.0 mapie>=0.8 shap>=0.44
# feature mart / 품질 게이트
pip install duckdb>=1.0 great-expectations>=0.18
# Challenger (해당 단계에서만)
pip install darts>=0.30           # N-BEATSx · N-HiTS · TFT 통합 인터페이스
pip install neuralforecast>=1.7   # Nixtla 계열 (PatchTST 포함)
```

| 라이브러리 | 라이선스 | 역할 | 비고 |
|---|---|---|---|
| lightgbm | MIT | Quantile GBM(G2 분위수), G1 중요도 | 이미 승인됨(libraries.md) |
| arch | NCSA | EGARCH-X 변동성 | 승인됨 |
| mapie | BSD-3 | **EnCQR** 구간 보정 | 승인됨(용도만 CQR→EnCQR로 갱신) |
| duckdb | MIT | as-of join·parquet 직접 질의 | **신규** — 서버 불필요, 파일 기반 |
| great-expectations | Apache-2.0 | 모델 진입 게이트 자동 검증 | 승인됨(미사용 상태) |
| darts / neuralforecast | Apache-2.0 | Challenger 딥러닝 | **신규** — Challenger 단계에서만 |

### 1.1 DuckDB를 먼저 쓰는 이유 (Supabase·Neo4j보다 앞선 이유)

as-of join(`available_at ≤ t`인 최근값)은 **SQL의 ASOF JOIN 한 줄**로 끝난다.
DuckDB는 서버·계정·비용이 전부 없고 parquet을 직접 읽는다.

```sql
-- gold feature view: 발표일 기준 as-of 정렬 (미래 정보 누수 차단)
SELECT p.price_date, p.value AS sbo_close, w.value AS wasde_stu
FROM read_parquet('data/raw/databento_bo_historical.parquet') p
ASOF LEFT JOIN read_parquet('data/raw/wasde_historical.parquet') w
  ON w.available_at <= p.price_date;
```

**절차**: ① 워크플로우 `pip install duckdb` ② `src/features/build_feature_mart.py` 작성
③ 산출 `data/gold/feature_mart.parquet` — 별도 인프라 0.

---

## 2. [B] Supabase — 사건·근거 테이블과 대시보드 백엔드

**등급**: 키/계정만 수동 · **무료 티어**(Free: 프로젝트 2개, DB 500MB, 대역 5GB/월)
**용도**: `event_schema.json`의 사건·인과·근거를 관계형으로 적재하고, G2 대시보드(9/10 목표)의
읽기 백엔드로 사용. PostgreSQL 관리형이라 별도 서버 운영이 없다.

> **왜 Supabase인가**: ERD가 요구하는 것은 그래프가 아니라 **관계형 + provenance**다
> (조사 패키지: "운영 데이터는 관계형 DB에 저장하고, **검증된 관계만** 그래프로 투영").
> 즉 Supabase가 1차 저장소, Neo4j가 2차 투영이라는 순서가 설계상 맞다.

### 2.1 조정자 수행 절차 (약 15분)

1. **가입**: <https://supabase.com> → GitHub 계정으로 로그인
2. **프로젝트 생성**: `New project` → 이름 `nexus-prod` → **Region: Northeast Asia (Seoul)**
   → DB 비밀번호 설정(비밀번호 관리자에 보관, 재확인 불가)
3. **연결 정보 복사**: `Project Settings → Database → Connection string(URI)`
4. **API 키 복사**: `Project Settings → API` → `Project URL`, `service_role` 키
   ⚠️ `service_role`은 RLS를 우회하는 관리자 키다. **절대 클라이언트·프런트에 노출 금지**,
   GitHub Secrets에만 저장한다.
5. **GitHub Secrets 등록**: 저장소 `Settings → Secrets and variables → Actions → New secret`
   | Secret 이름 | 값 |
   |---|---|
   | `SUPABASE_URL` | Project URL |
   | `SUPABASE_SERVICE_KEY` | service_role 키 |
   | `SUPABASE_DB_URL` | Connection string(URI) |
6. **조정자 완료** — 이후 스키마 생성·적재는 에이전트가 처리한다.

### 2.2 에이전트 수행 (조정자 조치 후 자동)

- `pip install supabase psycopg2-binary`
- `sql/supabase_schema.sql` 작성 — ERD 매핑:
  `source_document` · `evidence_span` · `canonical_entity` · `market_event` ·
  `causal_claim` · `trade_flow` · `forecast` (모두 `provenance.yaml` 계약 준수)
- 적재 스크립트 `scripts/load_events_to_supabase.py`
- Unstructured Analysis Pipeline에 적재 잡 추가

### 2.3 무료 티어 한계와 대응

| 항목 | Free | 초과 시 |
|---|---|---|
| DB 용량 | 500MB | 사건 테이블만 적재(원문 PDF·요약 md는 Git 유지) → 초과 가능성 낮음 |
| 일시정지 | 7일 무활동 시 | 파이프라인이 주기 실행되므로 해당 없음 |
| 백업 | 미제공 | parquet·Git이 원본 — DB는 파생물이라 재생성 가능 |

---

## 3. [B] Neo4j AuraDB — 지식그래프 (도입 시점: 4~6주 후)

**등급**: 키/계정만 수동 · **무료 티어**(AuraDB Free: 노드 20만·관계 40만, 1인스턴스)
**용도**: 검증된 `Cause → Market Mechanism → Price Outcome` 엣지의 다단 전파 탐색.

> **도입 시점 판단(C-01)**: 지금은 **이르다**. 조사 패키지가 "KG 먼저, GNN 나중"이라 했고
> 그 KG조차 **검증된 엣지**를 전제한다. 현재 `review_status: validated` 엣지는 아직 축적되지
> 않았다(P1-01~04 도메인 검증 대기). 빈 그래프를 먼저 세우면 운영 대상만 늘어난다.
> **선행 조건**: ① Supabase 사건 테이블 가동 ② validated 인과 엣지 100건 이상.

### 3.1 조정자 수행 절차 (선행 조건 충족 후, 약 10분)

1. **가입**: <https://neo4j.com/cloud/aura-free/> → 이메일 또는 Google 계정
2. **인스턴스 생성**: `New Instance → AuraDB Free` → Region 서울/도쿄
3. **자격증명 다운로드**: 생성 시 표시되는 `.txt`를 저장 —
   `NEO4J_URI`(neo4j+s://xxxx.databases.neo4j.io) · `NEO4J_USERNAME`(neo4j) ·
   `NEO4J_PASSWORD`. **이 화면을 닫으면 비밀번호를 다시 볼 수 없다.**
4. **GitHub Secrets 등록**: `NEO4J_URI` · `NEO4J_USERNAME` · `NEO4J_PASSWORD`
5. **조정자 완료** — 스키마·투영은 에이전트가 처리한다.

### 3.2 에이전트 수행

- `pip install neo4j>=5.0`
- 제약 조건 생성(중복 방지):
  ```cypher
  CREATE CONSTRAINT entity_id IF NOT EXISTS
  FOR (e:CanonicalEntity) REQUIRE e.term_id IS UNIQUE;
  ```
- **투영 규칙**: Supabase에서 `review_status = 'validated'`인 `causal_claim`만 적재.
  `extracted`·`rejected`는 투영하지 않는다(S1 결정).
- DAG 강제: `Cause → Price` 직접 엣지 생성 금지 — 반드시 `MarketMechanism` 경유.

### 3.3 무료 티어 한계

노드 20만·관계 40만. 현재 예상 규모(엔티티 152 + 사건 수천)로는 **충분**하다.
초과 시 AuraDB Professional(약 $65/월~)이나 자체 호스팅 Neo4j Community(무료)로 전환한다.

---

## 4. [C] 완전 수동 — 조정자 콘솔 작업

| 항목 | 유·무료 | 절차 요약 |
|---|---|---|
| **클라우드 학습 환경 Workspace** | **유료**(구독 종량제) | ① portal.azure.com → 리소스 그룹 생성 ② `Machine Learning` 작업 영역 생성(Region: Korea Central) ③ 연결된 스토리지 계정 확인 ④ `Access control(IAM)`에서 서비스 주체 생성 → `AZURE_ML_*` Secrets 등록. G2 학습 착수 시점에만 필요 |
| **사내 DRM 클라이언트** | 사내 라이선스 | ✅ **해소 완료**(2026-08-11, 130건 재업로드) — 신규 문서 업로드 시 동일 절차 유지 |
| **Excel + XLGantt** | **유료**(MS Office) | WBS xlsm의 VBA Gantt 갱신용. 로컬 Excel 필요 |
| **Baltic Exchange BCAA** | **유료(견적 필요)** | 빈도·재배포 범위·과거기간을 명시해 공식 견적 요청. 현재는 Perplexity 프록시로 대체 중이라 **보류 권고** |
| **DBpia 논문 3건** | **유료(구독 확인)** | 소속기관 로그인 우선 → 불가 시 KCI·RISS 공개본 확인 → 그래도 없고 구현 세부가 필요할 때만 구매 |
| GitHub Secrets 등록 | 무료 | 보안상 에이전트가 수행 불가 — 조정자 직접 |

---

## 5. 도입하지 **않기로** 한 것 (근거 포함)

| 후보 | 판단 | 근거 |
|---|---|---|
| ~~DW~~ | **보류 해제(2026-08-12)** | 구 근거(내부 웨어하우스 목적 소멸)가 회사 목표 아키텍처로 무효화됨 — 통합 데이터 플랫폼는 내부 전용이 아니라 **전사 단일 저장 계층**이다. Nexus의 정착지 |
| GNN (PyG 등) | **보류** | 조사 패키지: "KG 먼저, GNN 나중". 검증된 엣지가 부족한 상태의 GNN은 노이즈 학습 |
| vmdpy | **제외** | 전체 시계열 일괄 분해 → 미래 정보 누수(2026-08-12 결정) |
| google-genai | **제거 완료** | Gemini 전면 배제(C-012·C-013) |
| Airflow·Dagster | **불필요** | GitHub Actions가 현 규모의 스케줄링을 충족. 오케스트레이터 도입은 운영 부담만 증가 |

---

## 6. 조정자 액션 체크리스트

**지금 필요한 것 (2건)**
- [ ] Supabase 가입 → 프로젝트 생성 → Secrets 3종 등록 (§2.1) — **무료**
- [ ] (G2 학습 착수 시) 클라우드 학습 환경 Workspace 생성 → Secrets 등록 (§4) — **유료**

**나중에 (선행 조건 충족 후)**
- [ ] Neo4j AuraDB — validated 인과 엣지 100건 이상 축적 후 (§3.1) — **무료 티어**
- [ ] Baltic Exchange 견적 — 필요성 재검토 후 (§4) — **유료**

**에이전트가 처리 (조치 불필요)**
- 라이브러리 설치·워크플로우 반영·스키마 생성·적재 스크립트·검증 게이트 전부
