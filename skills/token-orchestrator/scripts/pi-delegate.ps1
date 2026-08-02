param(
  [Parameter(Mandatory = $true)]
  [string]$Prompt,
  [string]$Model = ""
)

$ErrorActionPreference = "Stop"
if (-not (Get-Command pi -ErrorAction SilentlyContinue)) {
  Write-Error "pi not found. Run: powershell -File Sync/Scripts/install_pi_agent.ps1"
}

$args = @("-p", $Prompt, "--no-session")
if ($Model) { $args += @("--model", $Model) }

Write-Host "=== pi delegate ===" -ForegroundColor Cyan
& pi @args
exit $LASTEXITCODE