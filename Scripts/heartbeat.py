import time
import os
import datetime
import socket
from sensors import get_all_events

# Настройки
ACTIVE_INTERVAL = 10
INACTIVE_INTERVAL = 45
IDLE_TIMEOUT = 1800
CHAT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_chat_room.txt')
DEVICE_NAME = socket.gethostname()

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
            
        print("[heartbeat] Запускаю автономный мыслительный цикл Proactive Brain...")
        try:
            import reasoning_engine
            report = reasoning_engine.run_proactive_analysis()
            if report:
                msg = f"[{timestamp}] [GMC Proactive Brain]:\n{report}"
            else:
                msg = f"[{timestamp}] [System Event]: Регулярная проверка. Агенты, проанализируйте текущую переписку, почту и календарь Дениса (!google). Чем мы можем помочь ему прямо сейчас, в данный момент, не забывая о планах на будущее?"
        except Exception as e:
            msg = f"[{timestamp}] [System Event]: Регулярная проверка. Ошибка Proactive Brain: {e}"
    
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
    last_thought_time = 0 # Запуск мысли сразу при старте
    last_cleanup_time = 0 # Запуск очистки сразу при старте
    CLEANUP_INTERVAL = 3600 # 1 час
    IDLE_TIMEOUT = 1800 # 30 минут
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🫀 Сердцебиение запущено...")
    
    while True:
        current_time = time.time()
        events = get_all_events()
        
        # Автоматическая очистка мусора и памяти раз в час
        if current_time - last_cleanup_time > CLEANUP_INTERVAL:
            print("[heartbeat] Запуск автоматической очистки системы и памяти...")
            try:
                import cleaner
                stats = cleaner.run_garbage_collector()
                if stats['deleted_files'] > 0 or stats['killed_chromes'] > 0:
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cleanup_msg = f"[{timestamp}] [System Alert]: 🧹 Выполнена автоматическая оптимизация: удалено {stats['deleted_files']} файлов конфликтов ({stats['bytes_saved_kb']:.2f} KB), уничтожено {stats['killed_chromes']} зависших процессов Chrome. Память и папки чисты!"
                    with open(CHAT_FILE, 'a', encoding='utf-8') as f:
                        f.write(f"\n{cleanup_msg}\n")
            except Exception as e:
                print(f"[heartbeat] Ошибка при очистке: {e}")
            last_cleanup_time = current_time
            
        # Динамический интервал мыслей: 120 секунд при активности (тестирование), 1800 секунд при простое
        is_active = (current_time - last_active_time) < IDLE_TIMEOUT
        current_thought_interval = 120 if is_active else 1800
        
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
