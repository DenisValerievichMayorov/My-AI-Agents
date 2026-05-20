import sys
import os

def load_env_vars():
    paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '.hermes', '.env'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),
        os.path.expanduser("~/.hermes/.env"),
        "C:/Users/anton/.hermes/.env"
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, val = line.split('=', 1)
                            os.environ[key.strip()] = val.strip()
            except Exception:
                pass

load_env_vars()

# Добавляем путь к venv, чтобы видеть все библиотеки
venv_path = r"C:\Users\anton\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages"
if venv_path not in sys.path:
    sys.path.append(venv_path)

import time
import datetime
import socket
from sensors import get_all_events

# Настройки
ACTIVE_INTERVAL = 10
INACTIVE_INTERVAL = 45
IDLE_TIMEOUT = 1800
CHAT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_chat_room.txt')
DEVICE_NAME = socket.gethostname()
AUTO_CLEANUP_ENABLED = os.environ.get("GMC_AUTO_CLEANUP", "").lower() in ("1", "true", "yes", "on")
PROACTIVE_BRAIN_ENABLED = os.environ.get("GMC_PROACTIVE_BRAIN", "").lower() in ("1", "true", "yes", "on")
CLEANUP_INTERVAL = 3600

def post_proactive_thought(event):
    """Агент сам пишет в чат, когда видит событие или наступает время подумать."""
    msg = ""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if event['type'] == 'mail':
        msg = f"[{timestamp}] [System Event]: На ПК получено письмо: '{event['content']}'. Агенты, обсудите, нужно ли Денису на это реагировать?"
    elif event['type'] == 'photo':
        msg = f"[{timestamp}] [System Event]: На телефоне замечено новое фото: {os.path.basename(event['content'])}. Агент на телефоне, опиши, что там, и предложи задачу."
    elif event['type'] == 'whatsapp':
        msg = f"[{timestamp}] [System Event]: Новое сообщение в WhatsApp: '{event['content']}'. Агенты, проанализируйте и предложите Денису ответ."
    elif event['type'] == 'timer':
        is_pc = "desktop" in DEVICE_NAME.lower()
        if not is_pc:
            print("[heartbeat] Автономный цикл Proactive Brain пропускается на мобильном устройстве для исключения конфликтов синхронизации.")
            return
            
        if not PROACTIVE_BRAIN_ENABLED:
            print("[heartbeat] Proactive Brain отключен. Для включения установите GMC_PROACTIVE_BRAIN=1.")
            return

        print("[heartbeat] Запускаю автономный мыслительный цикл Proactive Brain...")
        try:
            import reasoning_engine
            report = reasoning_engine.run_proactive_analysis()
            if report:
                msg = f"[{timestamp}] [GMC Proactive Brain]:\n{report}"
            else:
                return
        except Exception as e:
            return
    
    if msg:
        # Проверяем на дубликаты в чате, чтобы избежать дублирования при работе на нескольких узлах
        if os.path.exists(CHAT_FILE):
            with open(CHAT_FILE, 'r', encoding='utf-8') as f:
                recent_chat = f.read()
            if msg.strip() in recent_chat:
                return
        with open(CHAT_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n{msg}\n")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 💡 Проактивная мысль отправлена.")

def main():
    last_active_time = time.time()
    last_thought_time = 0
    last_fast_thought_time = 0
    last_cleanup_time = time.time()
    last_proactive_hash = ""
    FAST_INTERVAL = 120 # каждые 120 секунд (был 20)
    IDLE_TIMEOUT = 1800 # 30 минут
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🫀 Сердцебиение запущено...")
    if not AUTO_CLEANUP_ENABLED:
        print("[heartbeat] Автоматический Cleaner отключен. Для включения установите GMC_AUTO_CLEANUP=1.")
    if not PROACTIVE_BRAIN_ENABLED:
        print("[heartbeat] Proactive Brain отключен. Для включения установите GMC_PROACTIVE_BRAIN=1.")

    while True:
        current_time = time.time()
        events = get_all_events()

        # Быстрый локальный цикл мониторинга через Gemma
        if current_time - last_fast_thought_time > FAST_INTERVAL:
            try:
                import reasoning_engine
                chat_txt = ""
                if os.path.exists(CHAT_FILE):
                    with open(CHAT_FILE, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        chat_txt = "".join(lines[-10:])
                fast_res = reasoning_engine.run_fast_local_analysis(chat_txt)
                if fast_res:
                    recent = [l for l in chat_txt.splitlines() if l.strip()][-5:]
                    gemma_spam = sum(1 for l in recent if "gemma triage" in l.lower())
                    if gemma_spam >= 4:
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚡ Gemma: пропуск (чат уже заполнен триажем).")
                    elif fast_res.strip() in chat_txt:
                        pass
                    else:
                        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        msg = f"[{timestamp}] [Gemma Triage Officer]:\n{fast_res}"
                        with open(CHAT_FILE, 'a', encoding='utf-8') as f:
                            f.write(f"\n{msg}\n")
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚡ Локальный Диспетчер Gemma выдал отчет.")
            except Exception as e:
                pass
            last_fast_thought_time = current_time

        try:
            if AUTO_CLEANUP_ENABLED and current_time - last_cleanup_time > CLEANUP_INTERVAL:
                import cleaner
                stats = cleaner.run_garbage_collector()
                if stats['deleted_files'] > 0 or stats['killed_chromes'] > 0:
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cleanup_msg = f"[{timestamp}] [System Alert]: 🧹 Выполнена автоматическая оптимизация: удалено {stats['deleted_files']} файлов конфликтов ({stats['bytes_saved_kb']:.2f} KB), уничтожено {stats['killed_chromes']} зависших процессов Chrome. Память и папки чисты!"
                    with open(CHAT_FILE, 'a', encoding='utf-8') as f:
                        f.write(f"\n{cleanup_msg}\n")
                last_cleanup_time = current_time
        except Exception as e:
            print(f"[heartbeat] Ошибка при очистке: {e}")
            last_cleanup_time = current_time
            
        # Фиксированный интервал мыслей: 120 секунд (тестовый режим)
        current_thought_interval = 120

        if current_time - last_thought_time > current_thought_interval:
            events.append({"type": "timer", "content": "auto"})
            last_thought_time = current_time

        if events:
            last_active_time = current_time
            for event in events:
                if event['type'] != 'chat':
                    post_proactive_thought(event)
            
        time_since_active = current_time - last_active_time
        sleep_time = ACTIVE_INTERVAL if time_since_active < IDLE_TIMEOUT else INACTIVE_INTERVAL
        time.sleep(sleep_time)

if __name__ == "__main__":
    main()
