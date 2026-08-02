param(
  [Parameter(Mandatory = $true)]
  [string]$Prompt,
  [int]$TimeoutSec = 300
)

$ErrorActionPreference = "Stop"
$Agy = "$env:LOCALAPPDATA\agy\bin\agy.exe"
if (-not (Test-Path $Agy)) {
  $Agy = (Get-Command agy -ErrorAction SilentlyContinue).Source
}
if (-not $Agy) {
  Write-Error "agy not found. Install Antigravity CLI first."
}

Write-Host "=== agy delegate ===" -ForegroundColor Cyan
& $Agy --print --dangerously-skip-permissions -p $Prompt
exit $LASTEXITCODE