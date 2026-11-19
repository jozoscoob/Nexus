# 매일 07:00 KST 작업 스케줄러 진입점 — ① runner에 볼트 내보내기 요청(검증 통과 시에만) ② Drive 볼트로 복사
# runner가 다른 작업 중(409)이면 1분 간격으로 최대 45분 기다린다(통합 파이프라인 06:00 실행과 겹칠 수 있음).
param([string]$VaultDir = $env:OBSIDIAN_VAULT_DIR)   # 작업 스케줄러 인수로 전달(Drive 바로가기 대상은 목록 조회가 불안정 — 2026-11-19 실측)
$ErrorActionPreference = "Stop"
$log = Join-Path $PSScriptRoot "..\docker\logs\vault_daily_sync.log"
function Write-Log($m) { $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m"; Add-Content -Path $log -Value $line -Encoding utf8; Write-Output $line }

$py = "import urllib.request,urllib.error,json,sys`n" +
      "try:`n r=urllib.request.urlopen(urllib.request.Request('http://localhost:8000/run/vault_export',method='POST'),timeout=1800)`n" +
      " d=json.loads(r.read()); print('FAILED' if d.get('failed') else 'OK')`n" +
      "except urllib.error.HTTPError as e:`n print('BUSY' if e.code==409 else f'HTTP{e.code}')"
$state = "BUSY"
for ($i = 0; $i -lt 45 -and $state -eq "BUSY"; $i++) {
    $state = (docker exec docker-runner-1 python -c $py 2>&1 | Select-Object -Last 1)
    if ($state -eq "BUSY") { Start-Sleep -Seconds 60 }
}
if ($state -ne "OK") { Write-Log "[오류] 볼트 내보내기 실패($state) — 이전 보기를 유지하고 복사하지 않음"; exit 1 }
Write-Log "[정보] 볼트 내보내기 완료"
$syncArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $PSScriptRoot "sync_obsidian_vault.ps1"))
if ($VaultDir) { $syncArgs += @("-VaultDir", $VaultDir) }
$out = & powershell @syncArgs 2>&1
Write-Log ($out | Out-String).Trim()
