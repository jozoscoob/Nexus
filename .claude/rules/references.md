# .claude/rules/references.md
> `docs/research_desk/references/`(승인자 공유 PDF·논문)를 다룰 때 로드. 승인자 지시(2026-09-09): **향후 PDF는 전부
> Markdown으로 변환한 뒤 .md 요약을 생성해 처리**한다(토큰 절감·판독 재현성). 세션은 PDF를 직접 판독하지 않는다.

## 반입 절차 (순서 고정)
1. **해시 중복 검사** — `sha256sum`으로 기보관본과 대조(D-038: 중복은 재보관 금지, README에 '중복 차단'만 기록).
2. **변환** — `python scripts/pdf_to_markdown.py <pdf>` → `references/markdown/{stem}.md`(본문·목차·표) +
   `references/summaries/{stem}.md`(요약 골격: 서지·메타·키워드·수치 후보 자동).
   승인자가 웹으로 PDF를 올리면 `reference_pdf_to_md.yml`이 push 시 자동 변환·커밋한다.
3. **요약 작성** — 세션은 `markdown/*.md`만 읽고 골격의 '핵심 주장·방법·Nexus 관련성·정직 분류·인용 문장·온톨로지 후보'를 채운다.
   분류 어휘: 채용 / Challenger 검토 대기 / 배경 / 인용 주의 / 반면교사. 수치는 locator(쪽·표) 없이는 인용하지 않는다.
4. **색인** — `references/README.md` 표에 1행 추가(파일 | 출처 | 공유일 | 연결 문서). 4-라벨(CONFIRMED/INFERENCE/DATA GAP/NOT COMPARABLE) 준수.
5. **온톨로지 반영** — 인과 근거는 `src/semantic/ontology.yaml` evidence, 방법론 선례는 `src/semantic/methods.yaml`(MP-xx),
   엔티티는 `entities.yaml` → `python scripts/validate_semantic_layer.py --strict` 통과 후 커밋.
6. **MEMORY** — 당월 아카이브에 통합 결과(반영 위치·정직 분류) 기록.

## 규율
- 스캔본(텍스트 층 부족)은 변환기가 표시 — 이때만 이미지 판독을 예외 허용하고 요약에 '스캔본 판독' 명시.
- 원문 PDF는 보관·출처 추적용이며 요약·markdown이 작업 입력이다. markdown은 재생성 가능 산출물이므로 원문 변경 시 `--force`로 재생성.
- 기밀·거취·인프라 상세는 요약에 기록하지 않는다.

## 판독 도구 표준 (2026-11-19 승인 — R-046, 모든 프로젝트 참조 문서에 적용)
| 문서 유형 | 1차 도구 | 비고 |
|---|---|---|
| 텍스트 층이 있는 PDF(영문·포르투갈어 등 논문·보고서) | **MinerU 4.x basic**(ONNX·CPU·오프라인) | 무경계 학술 표 복원 최우수. 쪽 표지 `<!-- page N of M -->`로 locator 확보 |
| 스캔본·한국어 이미지 PDF | **opendataloader-pdf hybrid**(docling + EasyOCR ko/en) | 느림(약 30초/쪽) — 스캔본에만 |
| 대량 1차 분류·빠른 텍스트 | opendataloader-pdf 표준 모드 | 표 구조는 평탄화됨 |
| 폴백 | `scripts/pdf_to_markdown.py`(PyMuPDF·pdfplumber) | 괘선 표 추출 가능 |
- 실행은 저장소 밖 Docker 이미지·캐시(`_pdfparse_cache`)에서만 — 호스트 전역 설치 금지. 텔레메트리 끔, MinerU `--remote`(외부 업로드) **사용 금지**.
- 저널 PDF 원문과 전문 변환본은 저장소에 올리지 않는다(저작권) — 요약·쪽 locator 인용(≤25단어)만 반입.

### 판독 품질 규칙 3종 (필수)
1. **쪽수 검사** — 변환 직후 출력의 쪽 표지 수와 PDF 쪽수를 대조한다. 불일치(부분 결과 반환)면 `--force`로 강제 재변환한다(2026-11-19 실측: 33건 중 2건이 1쪽만 출력하고 성공 코드 반환).
2. **수치 교차 확인** — 인용할 수치는 두 번째 도구(opendataloader 표준 모드 또는 PDF 텍스트 층 `pdftotext -layout`)로 대조한다. 표 머리글·국가 열 순서는 특히 확인(국가 제목 오배치로 공급자 수가 뒤바뀐 선례).
3. **그래픽 속 숫자** — 인포그래픽·차트 위 숫자는 원문 쪽 이미지로 수동 확인하기 전에는 반입하지 않는다(변환기가 누락·순서 혼동).

