# 노트북이 꺼져도 도는 파이프라인 — 원인 진단과 요구사항 (2026-11-21)

## 1. 이번 오류의 원인

| 증상 | 원인 | 지금 상태 |
|---|---|---|
| `HTTP 500 … dockerDesktopLinuxEngine/v1.48/containers/2a03…/json` | 노트북 절전·종료 후 재개 직후 Docker Desktop 화면이 엔진(WSL2 가상머신)에 컨테이너 정보를 물었는데 엔진이 아직 응답 준비가 안 된 상태. 2a03…는 n8n 컨테이너 | 엔진 28.0.1 정상, n8n·runner 모두 실행 중(n8n 상태 확인 `ok`) — 일시 오류 |
| n8n 로그 `getaddrinfo ENOTFOUND api.n8n.io` | 재개 직후 네트워크(DNS) 미연결 | 일시 |
| 볼트 동기화 작업 11-21 14:07 실행 결과 0xC000013A | 노트북이 꺼져 07:00을 놓친 뒤 켜질 때 실행됐으나 도중 종료(로그오프·종료 신호) | 다음 실행 11-22 07:00, 수동 실행 가능 |
| 정체불명 runner 컨테이너 `optimistic_williamson` | 11-20 09:30 KST에 이름 없이 `docker run`으로 생성(작업 스케줄러 아님) — 외부 도구 실행 추정 | 동작에는 영향 없음, 확인 후 정리 권고 |

근본 문제: **스케줄·실행 주체(n8n·runner·작업 스케줄러)가 모두 노트북 위에 있다.** 노트북이 꺼지면 06:00 정기 실행·07:00 볼트 복사가 모두 멈춘다.

## 2. 지금 바로 할 수 있는 것 (노트북 유지, 오늘)

| # | 조치 | 효과 | 소요 |
|---|---|---|---|
| 1 | 500 오류가 보이면 Docker Desktop → Restart(안 되면 PowerShell `wsl --shutdown` 후 Docker Desktop 다시 열기). 컨테이너는 `restart: unless-stopped`라 자동 재기동 | 재개 직후 오류 해소 | 1분 |
| 2 | Docker Desktop 설정 'Start Docker Desktop when you sign in' 켜기 | 부팅 후 자동 기동 | 1분 |
| 3 | 전원 옵션: 전원 연결 시 절전 '안 함', 덮개 닫기 '아무것도 안 함'(실행이 예정된 날) | 06:00 실행 보장 | 2분 |
| 4 | **놓친 실행 따라잡기**: 로그온·재개 시 실행되는 작업 1개 — 엔진·n8n 상태 확인 → 오늘 통합 실행이 없으면 '04 통합'(또는 '00 시연') 실행 → 볼트 복사 | 꺼져 있던 동안 놓친 작업을 켜질 때 자동 보충 | 구현 30분(승인 필요 — 작업 스케줄러 추가) |
| 5 | n8n '04 통합' 스케줄 켜기 — 실행 위치가 정해진 뒤 | 정기 실행 재개 | 1분 |

한계: 노트북이 꺼져 있는 동안은 여전히 아무것도 돌지 않는다(놓친 것을 나중에 메울 뿐).

## 3. 상시 실행 구조 — 요구사항

**권장: 상시 켜진 작은 서버 1대(무료 또는 저가 클라우드)로 n8n + runner를 옮기고, 노트북은 개발·시연·열람용.**

| 영역 | 요구사항 | 구체안 |
|---|---|---|
| 실행 호스트 | 24시간 켜진 Linux + Docker | ①Oracle Cloud Always Free(Ampere ARM, 무료 한도 내 4 OCPU·24 GB급 — 장기 유휴 회수 정책은 가입 시 확인) ②저가 ARM VPS(월 수천 원대) ③집 미니 PC(일회성 구입). 1순위 ① |
| 이미지 호환 | ARM64에서 runner 이미지 빌드 | python:3.11-slim·node:22-slim은 다중 아키텍처, lightgbm·pyarrow·duckdb ARM 휠 존재 → `docker buildx --platform linux/arm64` 시험 빌드로 확인 |
| 코드 | 서버에서 저장소 받기 | GitHub 배포 키(읽기 전용) + `git pull` |
| 데이터 | 라이선스·수동 업로드 원자료(Databento·TE·관세청 GW·references 등 약 2 GB)는 GitHub에 없음 | 최초 1회 rsync(SSH) 또는 rclone(Drive 경유)로 복사, 이후 서버가 원본 |
| 비밀값 | API 키 | 서버 `docker/.env`(권한 600), 저장소·로그에 출력 금지 |
| Codex | 데스크톱 로그인 파일을 서버에 두면 토큰 순환으로 노트북 앱이 로그아웃될 수 있음 | 서버는 `OPENAI_API_KEY`(사용량 과금)로 전환하거나, 서버에서는 Codex 단계 건너뜀(비치명 설계 그대로) |
| 스케줄 | 06:00 통합·주간 정비·07:00 볼트 | n8n 스케줄 켜기(서버) · 볼트 복사는 작업 스케줄러 대신 **rclone → Google Drive 'Obsidian Vault/Nexus'**(서버 작업으로 편입) |
| 알림 | 지금 실패 알림은 runner 로그 파일에만 기록 → 꺼진 노트북에서는 아무도 모름 | n8n 실패 알림 워크플로우에 이메일(Gmail SMTP) 또는 텔레그램 노드 추가 + 외부 생존 신호(healthchecks.io 무료 — 정해진 시각에 신호가 안 오면 메일) |
| 접근·보안 | n8n 화면 외부 공개 금지 | 방화벽은 SSH만, n8n·runner는 127.0.0.1 바인딩 유지 → SSH 터널 또는 Tailscale로 접속 |
| 산출물 열람 | 터미널·G2 화면을 노트북·휴대폰에서 | 실행 끝에 `reports/`를 rclone으로 Drive 폴더에 복사(비공개) |
| 백업 | 서버 장애 대비 | 매일 parquet·n8n DB 볼륨을 압축해 Drive로(7일 보관) — 코드는 GitHub |
| 시간대 | 컨테이너 TZ=Asia/Seoul | API 요청 날짜는 UTC(11-20 기후 커넥터 수정 완료) — 나머지 커넥터도 같은 점검 후속 |
| 비용 | — | ①은 무료(한도 내), Drive는 기존 계정, 알림 무료 |

## 4. 진행 순서(승인 시)

1. 오늘: 2절 1~3(직접 1분 작업) + 4번 따라잡기 작업 구현(승인 시).
2. 1~2일: ARM 시험 빌드 → Oracle 계정·VM 생성(계정 생성은 최종 결정자가 직접) → Docker·저장소·데이터·.env 이전 → n8n 워크플로우 가져오기·게시 → 시연 워크플로우 1회 실행 확인.
3. 이어서: 알림(메일/텔레그램)·생존 신호·rclone(볼트·산출물·백업) 연결 → 06:00 스케줄 켜기 → 노트북 작업 스케줄러 볼트 작업 해제.

## 5. 결정 필요
1. 상시 호스트: Oracle Always Free / 저가 VPS / 미니 PC 중 선택(권장 Oracle — 계정 생성은 직접).
2. 서버의 Codex 단계: API 키(과금) 사용 / 서버에서는 건너뜀.
3. 알림 채널: 이메일 / 텔레그램.
4. 노트북 '놓친 실행 따라잡기' 작업 추가 승인.

## 6. 2026-11-21 Docker 기동 실패 복구 기록

- 증상: Docker Desktop 기동 시 `Wsl/Service/RegisterDistro/CreateVm/HCS/ERROR_NO_SYSTEM_RESOURCES` — docker-desktop 시스템 배포판이 사라져 다시 만들다가 가상머신 메모리 할당 실패.
- 원인: 물리 메모리 부족(15.4 GB 중 여유 0.8 GB — 브라우저·데스크톱 앱 다수 + Penpot 컨테이너 약 1.7 GB). `.wslconfig`가 없어 WSL 가상머신 메모리 상한도 없었음.
- 조치: `%USERPROFILE%\.wslconfig` 생성(memory=6GB · processors=4 · swap=4GB) → `wsl --shutdown` → Docker Desktop 재기동(16초 만에 엔진 정상, 배포판 재생성). 데이터 디스크(docker_data.vhdx 34 GB, n8n 볼륨 포함)는 그대로 — n8n 워크플로우 8개·runner 작업 20개·Codex 정상 확인. 출처 미상 runner 사본 컨테이너 삭제, Penpot은 정지(필요할 때 `docker compose -f docker/penpot/docker-compose.yaml start`).
- 재발 방지: 상한(6 GB) 유지 · 쓰지 않는 Penpot 정지 · 노트북 메모리가 빠듯하면 브라우저 탭·메신저를 줄인 뒤 Docker 기동.

## 7. Oracle Cloud Always Free 준비 — 최종 결정자가 직접 할 일

1. oracle.com/cloud/free 에서 가입(카드 인증은 본인 확인용 — Always Free 한도 안에서는 과금 없음). 홈 리전은 **서울 또는 춘천**(바꿀 수 없음).
2. 콘솔 → Compute → Instances → Create: 이미지 **Ubuntu 22.04/24.04**, Shape **VM.Standard.A1.Flex(Ampere)** — OCPU 2~4 · 메모리 12~24 GB, 부트 볼륨 100 GB 이상.
3. SSH 키: '공개 키 붙여넣기'에 노트북에서 만든 공개 키(`ssh-keygen -t ed25519`) 등록. 개인 키는 노트북에만.
4. 네트워크(보안 목록): 인바운드는 **22번(SSH)만**. n8n 5678은 열지 않음(SSH 터널로 접속).
5. 만들어지면 공인 IP를 알려 주시면 됨 — 이후 Docker 설치·저장소·데이터·비밀값 이전·n8n 게시·시연 실행 확인은 제가 SSH로 진행(비밀값은 화면에 출력하지 않음).
   - 참고: ARM 서버라 runner 이미지는 서버에서 다시 빌드. 첫 단계에서 ARM 빌드 시험부터 함.
   - 남은 결정: 서버 Codex(API 키 과금 / 건너뜀) · 알림 채널(이메일 / 텔레그램).

## 8. 2026-11-23 Oracle 무료 등급 축소·E2.1.Micro 적합성 평가

- **확인된 사실**: Oracle은 2026년에 Always Free Ampere A1 한도를 4 OCPU·24 GB → **2 OCPU·12 GB**로 절반 축소(시행일은 6/15·8/18로 보도 엇갈림). 용량 부족(Out of capacity) 오류는 무료 ARM 수요 쏠림으로 흔한 현상이며 AD를 바꿔도 지속될 수 있음.
- **실측(노트북, 2026-11-23)**: runner의 마트·게이트 작업 컨테이너 최대 메모리 **3,368 MB**(cgroup memory.peak, 4코어에서 276초) · n8n 최대 **1,081 MB**(유휴 약 420~620 MB). 둘을 함께 돌리면 최소 약 4.5 GB 필요.
- **VM.Standard.E2.1.Micro**(AMD x86, 1/8 OCPU 기준·순간 확장, **메모리 1 GB**): **부적합.**
  1. 메모리: n8n 하나(0.4~1.1 GB)만으로 1 GB가 차고, 마트 작업(3.4 GB)은 스왑을 써도 메모리 부족 종료 또는 극심한 스왑으로 사실상 멈춤.
  2. CPU: 기준 1/8 OCPU는 노트북 4코어의 수십 분의 일 — 노트북 4.6분 마트가 수 시간, 20분 수집이 반나절 이상 걸려 06:00 실행이 다음 날과 겹침.
  3. 부수: x86이라 이미지 호환은 문제없으나, 위 두 이유로 runner·n8n 어느 쪽도 올릴 수 없음. 생존 신호 같은 아주 작은 역할에만 쓸 수 있음.
- **같은 날 재발한 Docker 500의 원인**: 메모리 상한 6 GB 안에 runner(3.4 GB)+n8n(1.1 GB)+Penpot(약 1.7 GB, 엔진 재시작 때 다시 켜짐)이 겹쳐 가상머신 메모리가 소진 → 상한을 **8 GB(스왑 8 GB)**로 올리고 Penpot 자동 재시작을 끔. 이후 마트 작업 정상 완료.
- **권고 순서**: ①A1을 **2 OCPU·12 GB 이하**(예: 2/12 또는 1/6)로 계속 시도 + 계정을 Pay As You Go로 전환(무료 한도는 그대로, 용량 배정 우선) ②보장이 필요하면 저가 ARM VPS(8 GB급) ③장기적으로 미니 PC. E2.1.Micro는 쓰지 않음.

## 9. 2026-11-24 상시 서버 배포(Oracle Cloud, ARM 4 OCPU·24 GB)

> 서버 주소·키는 저장소에 적지 않는다. 노트북의 `~/.ssh/config` 별칭 `nexus-oracle`과 `~/.ssh/nexus_oracle`(새 키)로만 접속.

| 단계 | 내용 |
|---|---|
| 접속 키 | 대화로 공유된 최초 키는 **폐기** — 노트북에서 새 ed25519 키를 만들어 서버에 등록하고, 서버 `authorized_keys`에서 최초 키를 삭제. 노트북의 최초 키 사본(업로드 파일 포함)도 삭제 |
| 서버 준비 | Ubuntu 24.04 aarch64 · 시간대 Asia/Seoul · 스왑 8 GB · Docker 29.x + Compose 플러그인(공식 ARM 저장소) · 인바운드는 SSH(22)만(이미지 기본 iptables 규칙 확인) |
| 코드 | `/opt/nexus` ← 커밋된 HEAD를 `git archive`로 전송(다른 작업 세션의 미커밋 변경은 보내지 않음, 원문 PDF 제외) |
| 데이터 | `data/`(PDF 제외, 1.8 GB) + `data/raw/References` 전송 — parquet 42/42 일치. GAIN·FAO 원본 PDF는 요약으로 대체해 보내지 않음 |
| 비밀값 | 루트 `.env`를 열지 않고 파일째 복사(권한 600). `docker/.env`에는 Codex 로그인 자리표시자 경로만 |
| Codex | 서버에는 로그인 파일이 없어 교차검증 단계는 **건너뜀**(비치명). `codex_bridge.py`가 로그인 없으면 건너뛰도록 수정 |
| n8n | 노트북 n8n 데이터 볼륨(워크플로우 8개·소유자 계정·게시 상태)을 그대로 이전. n8n은 서버 127.0.0.1:5678에만 바인딩 — 노트북에서 `ssh -N -L 5678:localhost:5678 nexus-oracle` 후 http://localhost:5678 |
| runner | ARM에서 이미지 빌드 성공(공식 다중 아키텍처 베이스) |

### 운영 메모
- 코드 갱신(11-26부터): 노트북에서 커밋·push → 서버 `sudo sh /opt/nexus/docker/deploy.sh`(§10). 이전의 `git archive` 전송 방식은 폐기.
- 노트북 n8n·runner는 중복 실행을 막기 위해 정지(서버가 스케줄 담당). 노트북은 개발·시연·열람용.
- 남은 일: 실패 알림(이메일/텔레그램) · 생존 신호(healthchecks.io) · rclone(Google Drive — 볼트·산출물·백업) · 서버 Codex(API 키 여부 결정).

## 10. 2026-11-24 SPEC 1순위 구축(단일 파이프라인·Codex 검증·메일·운영 보강)

> 합의 사양: 저장소 루트 `SPEC.md`. 서버 주소·키·메일 주소·비밀번호는 저장소에 적지 않는다.

| 항목 | 내용 |
|---|---|
| 단일 워크플로우 | n8n **Nexus Pipeline**(화~토 06:00) — 색 구역 4개(① 수집 ② 정제 ③ 품질 점검 ④ 분석·평가)를 순서대로 실행, 구역마다 '▶ 여기부터 실행' 수동 시작, 끝에 요약 메일 1통. 기존 01~04는 게시 해제(되돌리기용 보관), 시연·Databento·실패 알림은 별도 유지 |
| Codex 검증 | 서버 자체 로그인(기기 코드 방식) → 영구 볼륨 `codex_home`(재빌드·재시작에도 유지). 정형 데이터는 **파일별 요약 통계와 코드만** 전달(라이선스 원값 금지 — `codex_verify_data`), 비정형·시맨틱·온톨로지는 원문 전체 열람 허용(`codex_verify_semantic` — 제안만, 적용은 승인 후). 로그인이 없으면 해당 단계는 '미실행'으로 건너뛰고 메일에 표시 |
| 메일 | n8n 메일 노드(SMTP, Gmail 앱 비밀번호는 최종 결정자가 n8n 화면에서 직접 입력). 제목은 항상 `[Nexus]` → Gmail 필터가 'Nexus' 라벨로 이동. 실패한 실행마다 1통, 정상이면 3줄 일일 요약, 매주 주간 요약. 메일 발송 실패는 파이프라인 성패와 분리 |
| 작업 API 인증 | runner `POST /run/<job>`에 공유 토큰 헤더(`X-Runner-Token`) 필수 — 값은 서버 `docker/.env`에만, n8n은 환경 변수 식으로 참조(워크플로우 JSON에 값 없음). 토큰 없으면 401 |
| 실행 이력 정리 | n8n `EXECUTIONS_DATA_PRUNE` — 14일·최대 1만 건(SQLite 무한 증가 방지) |
| SSH 보강 | 비밀번호 로그인 끔(이미지 기본) + 루트 로그인 끔 + 인증 시도 3회 + fail2ban(10분 내 5회 실패 시 1시간 차단). 변경 후 새 연결로 키 로그인 확인 |
| 보고서 Google Drive 저장(11-27) | 승인자 승인. rclone(범위 drive.file — 앱이 만든 폴더·파일만), 토큰은 runner 전용 볼륨 `rclone_config`(검증 컨테이너 없음). 원격 루트는 앱이 만든 'Nexus Reports' 폴더 ID로 고정 → 승인자가 원하는 폴더로 옮겨도 동작. 파이프라인 ④ 끝(`drive_upload`)에서 `YYYY-MM/YYYY-MM-DD/`로 G1 보고서(원본·요약 미포함)·경보·브리프·실행 보고·Codex 보고서 저장, 폴더 링크는 메일용 `reports/ops/drive_links_<날짜>.json`. 11월 백필 6일·56파일. 로그인은 서버 `rclone config create … scope=drive.file`(호스트 망) + 노트북 SSH 터널 53682 — 대기 중 다른 요청이 들어가면 실패하므로 터널 점검 금지 |
| Codex 검증 컨테이너(11-26) | 별도 컨테이너 + 내부 전용 망 + 허용 목록 프록시(OpenAI·ChatGPT만). 공개 데이터는 사본 전체·라이선스는 통계만, 쓰기는 스테이징·출력 폴더만. 제안은 게이트 → 승인 → 작업자 적용(백업 14일). 서버에서만 켬(`COMPOSE_PROFILES=verifier`) — SPEC §3.8 |
| 배포 키 | ✅ 11-26 등록·전환 완료 — `/opt/nexus`는 git 작업 사본(원문 PDF 제외 sparse checkout·blob 지연 받기, 브랜치 `claude/codex-obsidian-g2-framework`). 갱신은 `sudo sh /opt/nexus/docker/deploy.sh` 한 줄: fast-forward만, 서버가 갱신하는 추적 데이터 9개(TE xlsx 5·신호 아카이브·경보 원장 등)는 유지하고 겹치면 아무것도 바꾸지 않고 중단, 이미지·compose 변경 시에만 재빌드·재기동 |
| 노트북 볼트 복사 | 07:00 작업이 서버 runner를 토큰 헤더와 함께 호출하도록 갱신 |

### 다음 단계(SPEC 2순위 — 승인 후)
- 마트: 과거 일별 스냅샷 병합(최신 스냅샷만 남기는 현행 방식의 이력 손실 해소).
- runner: 작업 대기열 + 단계별 재개(현재는 한 번에 1작업, 바쁘면 409).
- 원천별 호출 속도 제한 공용 도우미(429 재발 방지).
