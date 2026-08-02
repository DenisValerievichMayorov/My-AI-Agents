<#
.SYNOPSIS
    Загружает удобные алиасы и функции для работы с pi-агентами.

.DESCRIPTION
    Выполни в своей сессии (или в профиле PowerShell):

        . "C:\Users\anton\.grok\skills\herdr-pi-agents\scripts\load-pi-aliases.ps1"

    После этого agy / Grok / ты сможешь использовать короткие команды:
        pi-list
        pi-read phi-xxx
        pi-send phi-xxx "задача..."
        pi-wait phi-xxx

    Это делает использование идентичным для всех оркестраторов.
#>

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function pi-list {
    py "C:\Users\anton\agent_tools\herdr_helper.py" list
}

function pi-read {
    param(
        [Parameter(Mandatory=$true)][string]$Agent,
        [int]$Lines = 40
    )
    py "C:\Users\anton\agent_tools\herdr_helper.py" read $Agent -n $Lines
}

function pi-send {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$Task
    )
    & "$scriptDir\pi-send-task.ps1" -Name $Name -Task $Task
}

function pi-wait {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [int]$Timeout = 600
    )
    & "$scriptDir\pi-wait.ps1" -Name $Name -TimeoutSeconds $Timeout
}

function pi-launch {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$Model,
        [string]$Provider = "openrouter",
        [string]$Task = ""
    )
    # Cloud-only (local Ollama removed 2026-08-02)
    herdr agent start $Name -- pi -ne --provider $Provider --model $Model --tools read,bash,edit,write,grep,find,ls | Out-Null
    Start-Sleep -Milliseconds 800
    if ($Task) {
        & "$scriptDir\pi-send-task.ps1" -Name $Name -Task $Task
    } else {
        Write-Host "Агент $Name запущен ($Provider/$Model). Отправь задачу: pi-send $Name 'твоя задача'"
    }
}

Write-Host "Pi-agents aliases loaded. Доступны команды:" -ForegroundColor Green
Write-Host "  pi-list                 — список агентов" -ForegroundColor Gray
Write-Host "  pi-read <name> [lines]  — прочитать вывод" -ForegroundColor Gray
Write-Host "  pi-send <name> <task>   — отправить задачу (с Enter)" -ForegroundColor Gray
Write-Host "  pi-wait <name>          — ждать завершения" -ForegroundColor Gray
Write-Host "  pi-launch <name> <model> [task] — запустить pi и опционально сразу дать задачу" -ForegroundColor Gray
Write-Host ""
Write-Host "Пример для agy:" -ForegroundColor Cyan
Write-Host '  pi-launch pi-orfree tencent/hy3:free' -ForegroundColor DarkGray
Write-Host '  pi-send pi-orfree "Собери timeline и чек-лист из мастер индекса"' -ForegroundColor DarkGray
