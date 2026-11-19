# 볼트 보기(data/vault_view/Nexus) → Google Drive 'Obsidian Vault\Nexus' 반영 (호스트 전용)
# 이유: Docker는 Google Drive for Desktop 가상 드라이브(G:)를 마운트하지 못함(2026-11-19 실측) —
#       컨테이너가 쓴 보기를 호스트가 복사한다. 대상은 볼트 안 'Nexus' 하위 폴더만(사용자 노트 보호).
# 사용: powershell -ExecutionPolicy Bypass -File scripts\sync_obsidian_vault.ps1 [-VaultDir "<볼트 경로>"]
param([string]$VaultDir = $env:OBSIDIAN_VAULT_DIR)

$ErrorActionPreference = "Stop"
$src = Join-Path $PSScriptRoot "..\data\vault_view\Nexus" | Resolve-Path -ErrorAction SilentlyContinue
if (-not $src -or -not (Test-Path (Join-Path $src ".nexus_managed"))) {
    Write-Error "[오류] 볼트 보기가 없음 — 먼저 runner의 vault_export 작업을 실행하세요"
}
if (-not $VaultDir) {
    # 공유 폴더 바로가기와 내 드라이브 양쪽에서 'Obsidian Vault' 폴더 자동 탐색
    $cands = @(Get-ChildItem "G:\.shortcut-targets-by-id\*\Obsidian Vault" -Directory -ErrorAction SilentlyContinue) +
             @(Get-ChildItem "G:\내 드라이브\*\Obsidian Vault", "G:\My Drive\*\Obsidian Vault" -Directory -ErrorAction SilentlyContinue)
    if ($cands.Count -ne 1) { Write-Error "[오류] 볼트 후보 $($cands.Count)개 — -VaultDir 또는 OBSIDIAN_VAULT_DIR로 지정하세요" }
    $VaultDir = $cands[0].FullName
}
$dst = Join-Path $VaultDir "Nexus"
if ((Test-Path $dst) -and (Get-ChildItem $dst -Force | Select-Object -First 1) -and -not (Test-Path (Join-Path $dst ".nexus_managed"))) {
    Write-Error "[오류] $dst 에 관리 표지가 없음 — 사용자 폴더일 수 있어 덮어쓰지 않음"
}
# /MIR: Nexus 하위만 원본과 동일하게(삭제 포함). 볼트의 다른 폴더는 건드리지 않음
robocopy $src $dst /MIR /NFL /NDL /NJH /NP /R:2 /W:2 | Out-Null
if ($LASTEXITCODE -ge 8) { Write-Error "[오류] 복사 실패(robocopy 코드 $LASTEXITCODE)" }
# 그래프 보기 색 그룹(태그별) — 볼트에 그래프 설정이 아직 없을 때만 넣음(사용자 설정 보호)
$gt = Join-Path $src ".obsidian-template\graph.json"; $gd = Join-Path $VaultDir ".obsidian\graph.json"
if ((Test-Path $gt) -and -not (Test-Path $gd)) { New-Item -ItemType Directory -Force (Join-Path $VaultDir ".obsidian") | Out-Null; Copy-Item $gt $gd; Write-Output "[정보] 그래프 색 그룹 설정 추가" }
$n = (Get-ChildItem $dst -Recurse -File -Filter *.md).Count
Write-Output "[완료] 볼트 반영: 노트 $($n)개"
