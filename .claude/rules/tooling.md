# .claude/rules/tooling.md
> 승인자 지시(2026-09-28): 이후 작업은 아래 공개 도구 3종을 작업 유형별로 사용한다. 모든 세션에서 적용.

## 작업 유형 → 도구

| 작업 유형 | 도구 | 위치 | 사용 방식 |
|---|---|---|---|
| 코딩(작성·수정·리팩터·리뷰·의존성 선택) | **Ponytail** (MIT) | `.claude/skills/ponytail/` | 코드 작업 시작 시 `ponytail` 스킬 로드 — 기본 강도 `full` |
| 전체 아키텍처·워크플로우 도식 | **drawio-skill** (MIT) | `.claude/skills/drawio-skill/` | 편집 가능한 `.drawio` 산출 — 저장 위치 `docs/architecture/` |
| 비정형 자료 작업(GAIN·FAO PDF 요약, 일별 뉴스 다이제스트, 시맨틱 레이어) | **Graft** (NanoNets, MIT) | CLI `graft` + `.claude/skills/graft/` | 관련 코드 탐색·영향 범위 확인을 `graft ask/callers/skeleton`으로 먼저 수행 |

## 우선순위 (충돌 시)
1. CLAUDE.md §2 하드 제약·§6 휴먼 게이트·as-of 규칙이 도구 지침보다 우선한다.
2. **Ponytail**은 코드의 크기·형태만 다룬다. 보고 형식(korean_style.md, R-016 오류 보고 4항목)과
   테스트 규칙(testing.md — 시계열 누수 검증 필수)은 Ponytail의 "설명 최소화·검사 1개" 지침보다 우선한다.
   검증 가드·as-of 필드·오류 처리는 "단순화" 대상이 아니다(Ponytail 'When NOT to be lazy'와 동일).
3. **Graft**는 코드 저장소 지도(구조 그래프)다 — 비정형 원문 자체를 색인하지 않는다. 비정형 자료 판독은
   기존 절차(references.md: PDF→Markdown→요약)를 따르고, Graft는 그 처리 코드의 탐색에 쓴다.
4. **drawio-skill**의 PNG·SVG 내보내기는 draw.io 데스크톱 CLI가 필요하다(원격 실행 환경 미설치) —
   `.drawio` 원본 + 파이썬 전용 검증(`diagramctl.py test/review`)까지 수행하고, 이미지는 사내에서 draw.io로 연다.

## 보안·기밀
- Graft 사용 통계는 **끔**(`DO_NOT_TRACK=1` — `.claude/settings.json` env, `graft telemetry disable`).
- Graft `build --deep`(LLM 요약)은 코드 일부를 외부 LLM 제공사로 보낸다 — **승인 없이 실행 금지**.
  기본 `graft build`·`ask`·`callers`는 로컬 전용(키·네트워크 불요).
- 도식에는 인프라 상세(호스트·계정·네트워크 경로)를 넣지 않는다.
- 검토 후 미도입(2026-10-22, C-016): find-skills·design-taste-frontend·GSD. 신규 도구는 승인 후 반입(DQ-36).
- 반입 스킬은 원문 무수정(각 폴더 `SOURCE.md`에 출처·커밋 기록). 갱신 시 같은 방식으로 교체.

## 설치
- 세션 시작 훅이 `graft` 미설치 시 `@nanonets/graft@0.20.0`을 설치하고 로컬 그래프를 재생성한다(`graft/`는 gitignore).
- Ponytail·drawio-skill은 저장소에 포함되어 별도 설치가 없다.
