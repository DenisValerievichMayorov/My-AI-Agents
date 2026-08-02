<#
.SYNOPSIS
    Ждёт, пока указанный pi-агент перейдёт в состояние idle (или timeout).

.DESCRIPTION
    Полезно для оркестраторов (agy, Grok) после отправки тяжёлой задачи.
    Периодически проверяет статус и выводит прогресс.

.PARAMETER Name
    Имя агента

.PARAMETER TimeoutSeconds
    Максимальное время ожидания (по умолчанию 600 сек = 10 мин)

.PARAMETER PollInterval
    Интервал проверки в секундах (по умолчанию 5)
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$Name,

    [int]$TimeoutSeconds = 600,

    [int]$PollInterval = 5
)

$Herdr = if ($env:HERDR_BIN) { $env:HERDR_BIN } else { "$env:LOCALAPPDATA\Programs\Herdr\bin\herdr.exe" }

Write-Host "Ожидание завершения агента '$Name' (таймаут $TimeoutSeconds сек)..." -ForegroundColor Cyan

$start = Get-Date
$lastStatus = ""

while ($true) {
    $listJson = & $Herdr agent list 2>&1 | Out-String | ConvertFrom-Json -ErrorAction SilentlyContinue
    $agent = $listJson.result.agents | Where-Object { $_.name -eq $Name -or $_.agent -eq $Name } | Select-Object -Last 1

    if (-not $agent) {
        Write-Warning "Агент '$Name' исчез из списка."
        break
    }

    $status = $agent.agent_status
    if ($status -ne $lastStatus) {
        Write-Host "  [$((Get-Date).ToString('HH:mm:ss'))] Статус: $status" -ForegroundColor Yellow
        $lastStatus = $status
    }

    if ($status -eq "idle") {
        Write-Host "`nАгент '$Name' закончил работу (idle)." -ForegroundColor Green
        break
    }

    if ($status -eq "blocked") {
        Write-Host "`nАгент заблокирован!" -ForegroundColor Red
        break
    }

    $elapsed = (Get-Date) - $start
    if ($elapsed.TotalSeconds -gt $TimeoutSeconds) {
        Write-Warning "Таймаут ожидания ($TimeoutSeconds сек). Агент всё ещё в состоянии: $status"
        break
    }

    Start-Sleep -Seconds $PollInterval
}

# Показать последние строки
Write-Host "`nПоследние строки вывода:" -ForegroundColor Gray
& $Herdr agent read $Name --source recent --lines 20 2>&1 | Out-String | Select-Object -Last 25
