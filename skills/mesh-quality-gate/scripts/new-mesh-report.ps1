#Requires -Version 5.1
param(
  [string]$Task = "task",
  [string]$Agent = $env:USERNAME,
  [string]$Scope = (Get-Location).Path,
  [string]$OutFile = ""
)

$report = @"
TASK: $Task
AGENT: $Agent
SCOPE: $Scope
DONE:
  - 
VERIFY:
  - 
RISK: none
NEXT: done
"@

if ($OutFile) {
  $dir = Split-Path -Parent $OutFile
  if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  Set-Content -Path $OutFile -Value $report -Encoding UTF8
  Write-Host "Wrote $OutFile"
} else {
  $report
  try {
    Set-Clipboard -Value $report
    Write-Host "(copied to clipboard)"
  } catch {
    Write-Host "(clipboard unavailable)"
  }
}
