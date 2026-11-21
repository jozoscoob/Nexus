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
