import os
import re

SYNC_DIR = r"c:\Users\anton\Sync"
main_chat_path = os.path.join(SYNC_DIR, "ai_chat_room.txt")
conflict_chat_path = os.path.join(SYNC_DIR, "ai_chat_room.sync-conflict-20260517-130008-KFY2NMX.txt")

def parse_chat_file(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Разделяем сообщения по меткам времени или по пустым строкам
    # Так как формат у нас: \n[YYYY-MM-DD HH:MM:SS] [Sender]: Content\n
    # Мы можем разбить по регулярному выражению, которое находит начало сообщения
    raw_blocks = re.split(r'\n(?=\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\])', content)
    blocks = []
    for b in raw_blocks:
        b_clean = b.strip()
        if b_clean:
            blocks.append(b_clean)
    return blocks

def main():
    print("Чтение основного чата...")
    main_blocks = parse_chat_file(main_chat_path)
    
    print("Чтение конфликтного чата...")
    conflict_blocks = parse_chat_file(conflict_chat_path)
    
    # Объединяем блоки, удаляя дубликаты
    all_blocks = list(main_blocks)
    for cb in conflict_blocks:
        if cb not in all_blocks:
            all_blocks.append(cb)
            
    # Сортируем блоки по времени
    # Каждая строка начинается с [YYYY-MM-DD HH:MM:SS]
    def extract_time_key(block):
        match = re.match(r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', block)
        if match:
            return match.group(1)
        # Если метки времени нет, возвращаем пустую строку (она уйдет в начало)
        return ""
        
    all_blocks.sort(key=extract_time_key)
    
    # Записываем объединенный чат обратно в основной файл
    merged_content = "\n\n".join(all_blocks) + "\n"
    with open(main_chat_path, 'w', encoding='utf-8') as f:
        f.write(merged_content)
        
    print(f"Успешно объединено {len(all_blocks)} сообщений!")
    
    # Удаляем файл конфликта
    if os.path.exists(conflict_chat_path):
        os.remove(conflict_chat_path)
        print("Файл конфликта успешно удален!")

if __name__ == "__main__":
    main()
