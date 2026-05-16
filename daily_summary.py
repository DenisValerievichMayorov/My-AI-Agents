import os
import datetime
import google_tool

SYNC_DIR = os.path.dirname(os.path.abspath(__file__))
CHAT_FILE = os.path.join(SYNC_DIR, 'ai_chat_room.txt')
WA_FILE = os.path.join(SYNC_DIR, 'whatsapp_messages.txt')

def get_last_day_context():
    context = "--- АНАЛИЗ ДНЯ ---\n"
    
    # 1. Чат агентов
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, 'r', encoding='utf-8') as f:
            context += "Последние события в чате:\n" + "".join(f.readlines()[-20:]) + "\n"
            
    # 2. WhatsApp
    if os.path.exists(WA_FILE):
        with open(WA_FILE, 'r', encoding='utf-8') as f:
            context += "Сообщения WhatsApp за сегодня:\n" + "".join(f.readlines()[-10:]) + "\n"
            
    # 3. Google Workspace
    context += "\nДанные из Google:\n"
    context += google_tool.list_calendar() + "\n"
    context += google_tool.list_drive() + "\n"
    context += google_tool.search_gmail("after:" + (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y/%m/%d"))
    
    return context

if __name__ == '__main__':
    print(get_last_day_context())
