@echo off
chcp 65001 >nul
echo [GMC] Останавливаю старые копии agent_listener и heartbeat...
wmic process where "CommandLine like '%%agent_listener%%'" call terminate >nul 2>&1
wmic process where "CommandLine like '%%Sync\\Scripts\\heartbeat%%'" call terminate >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080" ^| findstr "LISTENING"') do taskkill /F /PID %%a >nul 2>&1
timeout /t 2 /nobreak >nul
del /f /q "%~dp0agent_listener.lock" 2>nul
set GMC_START_HEARTBEAT=0
set GMC_OPENROUTER_HEAVY=1
cd /d "%~dp0"
echo [GMC] Запуск единственного демона...
start "" /B python agent_listener.py
timeout /t 4 /nobreak >nul
echo [GMC] Панель: http://localhost:8080
start http://localhost:8080
