import os
import sys
import socket
import subprocess
import webbrowser
import time

def check_tailscale_windows():
    try:
        out = subprocess.check_output("powershell \"Get-Service Tailscale -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Status\"", shell=True).decode('utf-8').strip()
        return out.lower() == "running"
    except Exception:
        return False

def check_tailscale_linux():
    try:
        subprocess.check_output(["pgrep", "tailscaled"])
        return True
    except Exception:
        return False

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex(('127.0.0.1', port)) == 0

def get_tailscale_ip():
    try:
        return subprocess.check_output(["tailscale", "ip", "-4"]).decode('utf-8').strip()
    except Exception:
        return None

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def main():
    port = int(os.environ.get("GMC_DASHBOARD_PORT", "8080"))
    
    print("\n" + "="*50)
    print("🚀  GLOBAL MISSION CONTROL - DASHBOARD LAUNCHER  🚀")
    print("="*50 + "\n")
    
    # 1. Проверяем Tailscale
    print("🔍 Проверка статуса Tailscale...")
    ts_running = False
    if sys.platform == "win32":
        ts_running = check_tailscale_windows()
    else:
        ts_running = check_tailscale_linux()
        
    if ts_running:
        print("🟢 Tailscale запущен и работает в штатном режиме.")
    else:
        print("⚠️ Tailscale НЕ ЗАПУЩЕН! Попытка запустить службу...")
        if sys.platform == "win32":
            try:
                subprocess.run("powershell \"Start-Service Tailscale -ErrorAction SilentlyContinue\"", shell=True)
                time.sleep(2)
                if check_tailscale_windows():
                    print("🟢 Служба Tailscale успешно запущена!")
                    ts_running = True
                else:
                    print("❌ Не удалось запустить Tailscale. Пожалуйста, запустите приложение вручную.")
            except Exception as e:
                print(f"❌ Ошибка автозапуска Tailscale: {e}")
        else:
            print("👉 Пожалуйста, запустите Tailscale на вашем устройстве.")

    # 2. Получаем IP адреса
    ts_ip = get_tailscale_ip() if ts_running else None
    local_ip = get_local_ip()
    
    # 3. Проверяем GMC Демон
    print("\n🔍 Проверка фонового демона GMC на порту {}...".format(port))
    if is_port_open(port):
        print("🟢 Демон GMC уже активен и обрабатывает запросы.")
    else:
        print("⚠️ Демон GMC не отвечает на порту {}. Запускаем в фоновом режиме...".format(port))
        
        # Находим путь к скрипту
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        # Если запущено из .agents/skills/gmc-dashboard-launcher/scripts
        listener_path = os.path.join(r"C:\Users\anton\sync\scripts", "agent_listener.py")
        if not os.path.exists(listener_path):
            # Пробуем относительный путь
            listener_path = os.path.join(base_dir, "sync", "scripts", "agent_listener.py")
            
        if os.path.exists(listener_path):
            try:
                if sys.platform == "win32":
                    subprocess.Popen(
                        ["python", listener_path],
                        creationflags=0x08000000 | 0x00000008, # CREATE_NO_WINDOW | DETACHED_PROCESS
                        close_fds=True
                    )
                else:
                    subprocess.Popen(
                        ["python", listener_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        preexec_fn=os.setpgrp
                    )
                print("⏳ Демон GMC успешно запущен. Ожидание инициализации...")
                time.sleep(3)
            except Exception as e:
                print(f"❌ Ошибка запуска демона GMC: {e}")
        else:
            print(f"❌ Скрипт agent_listener.py не найден по пути: {listener_path}")

    # 4. Открываем браузер и выводим информацию
    target_url = f"http://localhost:{port}"
    print("\n" + "="*50)
    print("🌐  АДРЕСА ДЛЯ ПОДКЛЮЧЕНИЯ К ПАНЕЛИ:")
    print("="*50)
    print(f"🖥️  На этом ПК:       {target_url}")
    print(f"🏠  В домашней Wi-Fi:  http://{local_ip}:{port}")
    if ts_ip:
        print(f"🌍  Из любой точки:    http://{ts_ip}:{port}  (Через Tailscale)")
    print("="*50 + "\n")
    
    print("🌐 Открываем панель управления в браузере по умолчанию...")
    try:
        webbrowser.open(target_url)
        print("🎉 Успешно открыто! Приятной работы!")
    except Exception as e:
        print(f"⚠️ Не удалось автоматически открыть браузер: {e}")
        print("👉 Скопируйте одну из ссылок выше вручную.")

if __name__ == "__main__":
    main()
