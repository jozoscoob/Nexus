# 매일 07:00 KST 작업 스케줄러 진입점 — ① 상시 서버에 볼트 내보내기 요청 ② 결과를 내려받아 ③ Drive 볼트로 복사
# 2026-11-24: 실행 주체가 상시 서버로 이동(노트북 runner 정지). 서버 접속은 ~/.ssh/config 별칭 nexus-oracle(주소·키는 저장소에 없음).
# 서버 runner가 다른 작업 중(409)이면 1분 간격으로 최대 45분 기다린다(06:00 통합 실행과 겹칠 수 있음).
param([string]$VaultDir = $env:OBSIDIAN_VAULT_DIR, [string]$ServerAlias = "nexus-oracle")
$ErrorActionPreference = "Stop"
$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
$log = Join-Path $repo "docker\logs\vault_daily_sync.log"
function Write-Log($m) { $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m"; Add-Content -Path $log -Value $line -Encoding utf8; Write-Output $line }

$py = "import urllib.request,urllib.error,json`ntry:`n r=urllib.request.urlopen(urllib.request.Request('http://localhost:8000/run/vault_export',method='POST'),timeout=1800)`n d=json.loads(r.read()); print('FAILED' if d.get('failed') else 'OK')`nexcept urllib.error.HTTPError as e:`n print('BUSY' if e.code==409 else f'HTTP{e.code}')"
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($py))
$state = "BUSY"
for ($i = 0; $i -lt 45 -and $state -eq "BUSY"; $i++) {
    $state = (& ssh -o ConnectTimeout=20 $ServerAlias "echo $b64 | base64 -d > /tmp/vx.py && docker cp /tmp/vx.py docker-runner-1:/tmp/vx.py && docker exec docker-runner-1 python /tmp/vx.py" 2>&1 | Select-Object -Last 1)
    if ($state -eq "BUSY") { Start-Sleep -Seconds 60 }
}
if ($state -ne "OK") { Write-Log "[오류] 서버 볼트 내보내기 실패($state) — 이전 보기를 유지하고 복사하지 않음"; exit 1 }

# 서버 → 노트북: 압축 파일로 받아 풂(PowerShell 파이프는 바이너리를 깨므로 파일 경유)
$tmp = Join-Path $env:TEMP "nexus_vault_view.tgz"
& ssh $ServerAlias "tar czf /tmp/nexus_vault_view.tgz -C /opt/nexus/data/vault_view Nexus" | Out-Null
& scp -q "${ServerAlias}:/tmp/nexus_vault_view.tgz" $tmp
if (-not (Test-Path $tmp)) { Write-Log "[오류] 볼트 보기 내려받기 실패"; exit 1 }
$view = Join-Path $repo "data\vault_view"
if (Test-Path (Join-Path $view "Nexus")) { Remove-Item -Recurse -Force (Join-Path $view "Nexus") }
New-Item -ItemType Directory -Force $view | Out-Null
& tar -xzf $tmp -C $view
Remove-Item -Force $tmp
Write-Log "[정보] 서버 볼트 보기 수신"

$syncArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $PSScriptRoot "sync_obsidian_vault.ps1"))
if ($VaultDir) { $syncArgs += @("-VaultDir", $VaultDir) }
$out = & powershell @syncArgs 2>&1
Write-Log ($out | Out-String).Trim()
