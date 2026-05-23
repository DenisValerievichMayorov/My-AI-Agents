# resolve_syncthing_conflicts.ps1
# Очищает файлы конфликтов синхронизации Syncthing в указанной директории (по умолчанию ~/.gemini)

param (
    [string]$TargetDir = "$env:USERPROFILE\.gemini"
)

Write-Host "Поиск файлов конфликтов в $TargetDir..."
$conflictFiles = Get-ChildItem -Path $TargetDir -Filter "*.sync-conflict-*" -File

if ($conflictFiles.Count -eq 0) {
    Write-Host "Файлов-конфликтов не найдено. Все чисто!"
    exit 0
}

foreach ($file in $conflictFiles) {
    Write-Host "Удаление конфликта: $($file.Name)"
    Remove-Item $file.FullName -Force
}

Write-Host "Очистка завершена. Удалено файлов: $($conflictFiles.Count)"
