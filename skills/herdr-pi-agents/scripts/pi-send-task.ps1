<#
.SYNOPSIS
    Надёжная отправка задачи pi-агенту в Herdr с гарантированным нажатием Enter.

.DESCRIPTION
    Используется оркестраторами (Grok, agy и др.) для делегирования работы локальным pi-агентам.
    Решает главную проблему: после herdr agent send нужно обязательно нажать Enter.

.PARAMETER Name
    Имя pi-агента (например: phi-compile-granite, phi-docs-qwen и т.д.)

.PARAMETER Task
    Полный текст задачи. Будет отправлен как "TASK: <текст>"

.PARAMETER Prefix
    Префикс перед задачей (по умолчанию "TASK:"). Можно изменить на "INSTRUCTION:" или убрать.

.EXAMPLE
    .\pi-send-task.ps1 -Name "phi-compile-granite" -Task "Прочитай 00_MASTER_INDEX.md и сделай timeline + evidence list"

.NOTES
    Требует herdr в PATH или указанный в переменной окружения.
    Работает как из PowerShell, так и может быть вызван из других агентов.
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Name,

    [Parameter(Mandatory=$true)]
    [string]$Task,

    [string]$Prefix = "TASK:"
)

$Herdr = if ($env:HERDR_BIN) { $env:HERDR_BIN } else { "$env:LOCALAPPDATA\Programs\Herdr\bin\herdr.exe" }

if (-not (Test-Path $Herdr)) {
    Write-Error "Herdr не найден: $Herdr"
    exit 1
}

Write-Host "Отправка задачи агенту '$Name'..." -ForegroundColor Cyan

# 1. Получаем список агентов, чтобы найти pane_id
$listJson = & $Herdr agent list 2>&1 | Out-String | ConvertFrom-Json
$agentInfo = $listJson.result.agents | Where-Object { $_.name -eq $Name -or $_.agent -eq $Name } | Select-Object -Last 1

if (-not $agentInfo) {
    Write-Error "Агент '$Name' не найден в Herdr. Запусти herdr agent list для проверки."
    exit 1
}

$paneId = $agentInfo.pane_id
Write-Host "  Найден pane: $paneId (статус: $($agentInfo.agent_status))" -ForegroundColor DarkGray

# 2. Формируем сообщение
$fullMessage = if ($Prefix) { "$Prefix $Task" } else { $Task }

# 3. Отправляем текст
& $Herdr agent send $Name $fullMessage 2>&1 | Out-Null
Write-Host "  Текст отправлен." -ForegroundColor Green

# 4. Критически важно: нажимаем Enter
& $Herdr pane send-keys $paneId enter 2>&1 | Out-Null
Write-Host "  Enter нажат — задача передана pi." -ForegroundColor Green

Write-Host "`nГотово. Можешь мониторить:" -ForegroundColor Yellow
Write-Host "  herdr agent read $Name --source recent --lines 30" -ForegroundColor Gray
Write-Host "  или: py C:\Users\anton\agent_tools\herdr_helper.py read $Name -n 40" -ForegroundColor Gray
