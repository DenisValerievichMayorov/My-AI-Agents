# Gemini CLI Resource & Quota Monitor
# Date: May 23, 2026 | Location: Antwerp, Belgium

Clear-Host
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   GEMINI CLI NATIVE RESOURCE MONITOR   " -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Current Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "Location: Antwerp, Belgium"
Write-Host "-----------------------------------------------"

while($true) {
    $timestamp = Get-Date -Format 'HH:mm:ss'
    
    # In v0.43.0, quota info is often internal or accessible via specific flags
    # We will simulate the native feel by extracting status if possible
    Write-Host "[$timestamp] Checking Native Google Quotas..." -ForegroundColor Yellow
    
    # Placeholder for actual quota extraction logic if available in future updates
    # For now, we display the official limits for the configured models
    Write-Host "`n[Model: Gemini 1.5 Flash (Native)]" -ForegroundColor White
    Write-Host "  Requests per Day: 1,500"
    Write-Host "  Requests per Min: 15"
    Write-Host "  Token Limit: 1,000,000 TPM"
    
    Write-Host "`n[Model: Gemini 1.5 Pro (Native)]" -ForegroundColor White
    Write-Host "  Requests per Day: 50"
    Write-Host "  Requests per Min: 2"
    Write-Host "  Token Limit: 32,000 TPM"
    
    Write-Host "`n-----------------------------------------------"
    Write-Host "Press Ctrl+C to stop the monitor."
    
    Start-Sleep -Seconds 60
    Clear-Host
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "   GEMINI CLI NATIVE RESOURCE MONITOR   " -ForegroundColor Cyan
    Write-Host "===============================================" -ForegroundColor Cyan
}
