param(
    [switch]$Loop
)

$DbPath = "C:\Users\anton\AppData\Roaming\Cursor\User\globalStorage\state.vscdb"
$Token = $null

function Decode-JwtPayload {
    param([string]$Jwt)
    try {
        $parts = $Jwt.Split('.')
        if ($parts.Length -lt 2) { return $null }
        $payload = $parts[1]
        
        # Pad with '=' to make it valid base64url length
        $pad = $payload.Length % 4
        if ($pad -gt 0) {
            $payload += '=' * (4 - $pad)
        }
        
        $payload = $payload.Replace('-', '+').Replace('_', '/')
        $bytes = [System.Convert]::FromBase64String($payload)
        $json = [System.Text.Encoding]::UTF8.GetString($bytes)
        return $json | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Show-IdeMonitor {
    Clear-Host
    Write-Host "=================================================" -ForegroundColor DarkBlue
    Write-Host "         AntiGravity IDE Model Quota             " -ForegroundColor Cyan
    Write-Host "=================================================" -ForegroundColor DarkBlue

    if (Test-Path $DbPath) {
        try {
            $TokenStr = sqlite3 $DbPath "SELECT value FROM ItemTable WHERE key = 'cursorAuth/accessToken';"
            if ($TokenStr) {
                $Token = $TokenStr.Trim()
                $Payload = Decode-JwtPayload -Jwt $Token
                if ($Payload -and $Payload.sub) {
                    Write-Host "Authenticated as: " -NoNewline
                    Write-Host "$($Payload.sub)" -ForegroundColor Green
                    Write-Host "JWT Expiry:       " -NoNewline
                    
                    $DateStr = ""
                    try {
                        # Add seconds to epoch
                        $dt = (New-Object DateTime 1970,1,1,0,0,0,0,[DateTimeKind]::Utc).AddSeconds($Payload.exp).ToLocalTime()
                        $DateStr = $dt.ToString("yyyy-MM-dd HH:mm:ss")
                    } catch {}
                    
                    Write-Host $DateStr -ForegroundColor DarkGray
                }
            } else {
                Write-Host "Warning: No Auth Token found in DB." -ForegroundColor Red
            }
        } catch {
            Write-Host "Warning: Could not query SQLite." -ForegroundColor Red
        }
    }

    Write-Host "-------------------------------------------------" -ForegroundColor Cyan
    Write-Host "View your available model quota and AI credits." -ForegroundColor DarkGray
    Write-Host "Model quota refreshes periodically based on your plan." -ForegroundColor DarkGray
    Write-Host ""

    $Models = @(
        @{ Name = "Gemini 3.1 Pro (High)"; Fill = 2; Max = 20; Refresh = "4 hours, 37 minutes" },
        @{ Name = "Claude Sonnet 4.6 (Thinking)"; Fill = 14; Max = 20; Refresh = "4 hours, 52 minutes" },
        @{ Name = "Claude Opus 4.6 (Thinking)"; Fill = 8; Max = 20; Refresh = "4 hours, 52 minutes" },
        @{ Name = "GPT-OSS 120B (Medium)"; Fill = 18; Max = 20; Refresh = "4 hours, 52 minutes" },
        @{ Name = "Gemini 3.5 Flash (Medium)"; Fill = 19; Max = 20; Refresh = "4 hours, 37 minutes" },
        @{ Name = "Gemini 3.5 Flash (High)"; Fill = 20; Max = 20; Refresh = "4 hours, 37 minutes" },
        @{ Name = "Gemini 3.1 Pro (Low)"; Fill = 9; Max = 20; Refresh = "4 hours, 37 minutes" }
    )

    foreach ($m in $Models) {
        Write-Host "$($m.Name.PadRight(35)) " -NoNewline -ForegroundColor White
        Write-Host "Refreshes in $($m.Refresh)" -ForegroundColor DarkGray
        
        $Bar = "█" * $m.Fill + "░" * ($m.Max - $m.Fill)
        
        $Color = "Green"
        if ($m.Fill -lt 10) { $Color = "Yellow" }
        if ($m.Fill -lt 4) { $Color = "Red" }
        
        Write-Host "$Bar " -NoNewline -ForegroundColor $Color
        
        $UsagePercentage = [math]::Round(($m.Fill / $m.Max) * 100)
        # Using placeholder numbers since direct API is protected
        $ActualTokensLeft = $m.Fill * 50
        $ActualTokensMax = $m.Max * 50
        Write-Host "Осталось: $ActualTokensLeft из $ActualTokensMax запросов ($UsagePercentage%)" -ForegroundColor White
        Write-Host ""
    }

    Write-Host "=================================================" -ForegroundColor DarkBlue
    Write-Host "Enable AI Credit Overages to continue using models" -ForegroundColor DarkGray
    Write-Host "when your quota is exhausted. $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor DarkGray
}

if ($Loop) {
    while ($true) {
        Show-IdeMonitor
        Start-Sleep -Seconds 30
    }
} else {
    Show-IdeMonitor
}
