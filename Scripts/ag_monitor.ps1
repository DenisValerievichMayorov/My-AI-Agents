param(
    [switch]$Loop
)

$BatPath = "C:\Users\anton\Desktop\Launch_Antigravity_OpenRouter.bat"
$ApiKey = $null

if (Test-Path $BatPath) {
    $content = Get-Content $BatPath
    foreach ($line in $content) {
        if ($line -match "^set GEMINI_API_KEY=(.+)$") {
            $ApiKey = $matches[1]
            break
        }
    }
}

if (-not $ApiKey) {
    Write-Host "OpenRouter API Key not found in $BatPath!" -ForegroundColor Red
    exit 1
}

$Headers = @{
    "Authorization" = "Bearer $ApiKey"
}

function Show-Dashboard {
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "     AntiGravity Resource Monitor       " -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan

    try {
        $Response = Invoke-RestMethod -Uri "https://openrouter.ai/api/v1/auth/key" -Headers $Headers -ErrorAction Stop
        $Data = $Response.data
        
        $Limit = $Data.limit
        $Remaining = $Data.limit_remaining
        $Usage = $Data.usage

        if ($null -eq $Remaining -or $Remaining -lt 0) {
            $Remaining = 0
        }

        Write-Host "OpenRouter Credits: " -NoNewline
        Write-Host "`$$([math]::Round($Remaining, 4)) / `$$Limit" -ForegroundColor Green
        Write-Host "Usage: `$$([math]::Round($Usage, 4))" -ForegroundColor DarkGray
        Write-Host "----------------------------------------" -ForegroundColor Cyan

        # Prices per 1M tokens (Approximate avg of input/output)
        $Models = @(
            @{ Name = "DeepSeek V3 (Chat)"; CostPer1M = 0.60; Color = "Magenta" },
            @{ Name = "Gemini 2.0 Flash"; CostPer1M = 0.25; Color = "Cyan" },
            @{ Name = "Gemini 2.5 Pro"; CostPer1M = 1.12; Color = "Blue" },
            @{ Name = "Gemma 3 27b IT"; CostPer1M = 0.12; Color = "Yellow" }
        )

        Write-Host "Estimated Remaining Tokens:" -ForegroundColor White
        Write-Host ""
        
        foreach ($Model in $Models) {
            $TokensInMillions = $Remaining / $Model.CostPer1M
            $FormattedTokens = ""
            if ($TokensInMillions -gt 1) {
                $FormattedTokens = "$([math]::Round($TokensInMillions, 1))M tokens"
            } elseif ($TokensInMillions -gt 0) {
                $Tokens = [math]::Round($TokensInMillions * 1000000)
                $FormattedTokens = "$Tokens tokens"
            } else {
                $FormattedTokens = "0 tokens"
            }

            $BarSize = 20
            # Normalize bar size relative to max possible tokens in this list
            $MaxTokens = $Remaining / 0.12 # based on cheapest
            $Percentage = 0
            if ($MaxTokens -gt 0) {
                $Percentage = $TokensInMillions / $MaxTokens
            }
            $FilledLength = [math]::Round($Percentage * $BarSize)
            if ($FilledLength -gt $BarSize) { $FilledLength = $BarSize }
            if ($FilledLength -lt 1 -and $Remaining -gt 0) { $FilledLength = 1 }

            $Bar = "█" * $FilledLength + "░" * ($BarSize - $FilledLength)

            Write-Host "$($Model.Name.PadRight(20)) " -NoNewline
            Write-Host "$Bar " -ForegroundColor $Model.Color -NoNewline
            Write-Host $FormattedTokens -ForegroundColor White
        }

        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "Data fetched at $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor DarkGray
    }
    catch {
        Write-Host "Error fetching data from OpenRouter:" -ForegroundColor Red
        Write-Host $_.Exception.Message
    }
}

if ($Loop) {
    while ($true) {
        Show-Dashboard
        Start-Sleep -Seconds 60
    }
} else {
    Show-Dashboard
}
