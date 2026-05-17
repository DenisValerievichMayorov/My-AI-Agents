import time
import os
import datetime
import socket
from sensors import get_all_events

# Настройки
ACTIVE_INTERVAL = 10
INACTIVE_INTERVAL = 900
IDLE_TIMEOUT = 1800
CHAT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_chat_room.txt')
DEVICE_NAME = socket.gethostname()

def post_proactive_thought(event):
    """Агент сам пишет в чат, когда видит событие или наступает время подумать."""
    msg = ""
    if event['type'] == 'mail':
        msg = f"[System Event]: На ПК получено письмо: '{event['content']}'. Агенты, обсудите, нужно ли Денису на это реагировать?"
    elif event['type'] == 'photo':
        msg = f"[System Event]: На телефоне замечено новое фото: {os.path.basename(event['content'])}. Агент на телефоне, опиши, что там, и предложи задачу."
    elif event['type'] == 'whatsapp':
        msg = f"[System Event]: Новое сообщение в WhatsApp: '{event['content']}'. Агенты, проанализируйте и предложите Денису ответ."
    elif event['type'] == 'timer':
        # Проверяем, не пора ли сделать ночной отчет (в час ночи)
        now = datetime.datetime.now()
        if now.hour == 1 and now.minute < 5:
            msg = f"[System Event]: Время ночной рефлексии. Агенты, запустите !run daily_summary.py, проанализируйте весь прошедший день и составьте для Дениса план на завтра."
        else:
            msg = f"[System Event]: Регулярная проверка. Агенты, посмотрите календарь и почту Дениса (!google). Есть ли что-то важное на завтра?"
    
    if msg:
        with open(CHAT_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n{msg}\n")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 💡 Проактивная мысль отправлена.")

def main():
    last_active_time = time.time()
    last_thought_time = time.time()
    THOUGHT_INTERVAL = 1800 # 30 минут
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🫀 Сердцебиение запущено...")
    
    while True:
        current_time = time.time()
        events = get_all_events()
        
        # Регулярная мысль раз в 30 минут
        if current_time - last_thought_time > THOUGHT_INTERVAL:
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
