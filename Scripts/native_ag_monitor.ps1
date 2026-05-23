param(
    [switch]$Loop
)

# Current active conversation directory
$BrainPath = "C:\Users\anton\.gemini\antigravity\brain"

function Get-LatestConversation {
    $dirs = Get-ChildItem -Path $BrainPath -Directory -Force
    # Sort by LastWriteTime to get the most recent conversation
    $latest = $dirs | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    return $latest
}

function Show-NativeDashboard {
    Clear-Host
    Write-Host "=================================================" -ForegroundColor DarkBlue
    Write-Host "    [ AG-CORE ] Native Context & Resource Monitor    " -ForegroundColor Cyan
    Write-Host "=================================================" -ForegroundColor DarkBlue

    try {
        $LatestConv = Get-LatestConversation
        if (-not $LatestConv) {
            Write-Host "No active AntiGravity context found." -ForegroundColor Red
            return
        }

        $TranscriptPath = Join-Path $LatestConv.FullName ".system_generated\logs\transcript.jsonl"
        $FileSize = 0
        $TokensUsed = 0

        if (Test-Path $TranscriptPath) {
            $FileInfo = Get-Item $TranscriptPath
            $FileSize = $FileInfo.Length
            # Approximate calculation: 1 token ≈ 4 characters/bytes (for English-heavy JSON logs)
            $TokensUsed = [math]::Round($FileSize / 4)
        }

        # Max context for Gemini Pro models is usually 2,000,000 tokens.
        # We will use 2M as the limit.
        $ContextLimit = 2000000 
        $Remaining = $ContextLimit - $TokensUsed

        if ($Remaining -lt 0) {
            $Remaining = 0
        }

        Write-Host "Active Context ID: " -NoNewline
        Write-Host $LatestConv.Name -ForegroundColor DarkGray

        Write-Host "Context File Size: " -NoNewline
        Write-Host "$([math]::Round($FileSize / 1MB, 2)) MB" -ForegroundColor Yellow
        Write-Host "-------------------------------------------------" -ForegroundColor Cyan

        $Percentage = ($TokensUsed / $ContextLimit) * 100
        $BarSize = 30
        $FilledLength = [math]::Round(($TokensUsed / $ContextLimit) * $BarSize)
        if ($FilledLength -gt $BarSize) { $FilledLength = $BarSize }
        
        $Bar = "█" * $FilledLength + "░" * ($BarSize - $FilledLength)
        
        # Determine Color based on usage
        $BarColor = "Green"
        if ($Percentage -gt 50) { $BarColor = "Yellow" }
        if ($Percentage -gt 85) { $BarColor = "Red" }

        Write-Host "Gemini Native Context (2M tokens)" -ForegroundColor White
        Write-Host "$Bar " -ForegroundColor $BarColor -NoNewline
        Write-Host "$([math]::Round($Percentage, 2))%" -ForegroundColor White

        Write-Host ""
        Write-Host "Tokens Used: " -NoNewline
        Write-Host ("{0:N0}" -f $TokensUsed) -ForegroundColor Magenta -NoNewline
        Write-Host (" / {0:N0}" -f $ContextLimit) -ForegroundColor DarkGray

        Write-Host "Tokens Left: " -NoNewline
        Write-Host ("{0:N0}" -f $Remaining) -ForegroundColor Green
        
        Write-Host "-------------------------------------------------" -ForegroundColor Cyan

        # Also get physical RAM usage of Antigravity/Node/Gemini processes
        $Processes = Get-Process | Where-Object { $_.Name -match "AntiGravity|node|gemini|electron" }
        $TotalRAM = 0
        foreach ($p in $Processes) {
            $TotalRAM += $p.WorkingSet64
        }
        $RAM_MB = [math]::Round($TotalRAM / 1MB, 2)

        Write-Host "Host System Resource Footprint:" -ForegroundColor White
        Write-Host "Memory Usage: " -NoNewline
        Write-Host "$RAM_MB MB" -ForegroundColor Magenta

        Write-Host "=================================================" -ForegroundColor DarkBlue
        Write-Host "Status OK. AI Core optimal. $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor DarkGray
    }
    catch {
        Write-Host "Error fetching native context:" -ForegroundColor Red
        Write-Host $_.Exception.Message
    }
}

if ($Loop) {
    while ($true) {
        Show-NativeDashboard
        Start-Sleep -Seconds 10
    }
} else {
    Show-NativeDashboard
}
