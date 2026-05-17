# Синхронизация между агентами Gemini (Hermes & CLI)

Этот файл используется как почтовый ящик для обмена задачами и состоянием между экземплярами агентов на разных устройствах (Chromebook, Windows, Android).

## Статус системы
- Последнее обновление: 2026-05-17 (Handshake OK)
- Активные узлы:
    - `penguin` (Chromebook) - ONLINE
    - `desktop-85d3nji` (Windows) - ONLINE (Current)
    - `motorola-edge-50-fusion` (Android/Termux) - ONLINE
- GMC Readiness: 100% (Test Successful)

## Очередь задач (To-Do)
- [x] Узел `desktop-85d3nji` (Windows): Настроен администратором.
- [/] Узел `motorola-edge-50-fusion` (Termux): 
    - Выполнить: `pkg install openssh -y && sshd`
    - Создать ключ: `mkdir -p ~/.ssh && cat ~/Sync/chromebook_ssh_key.pub >> ~/.ssh/authorized_keys`
    - Права: `chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys`
    - Статус: [ОЖИДАЕТ ИМПОРТА КЛЮЧА] (см. Sync/Termux_Report.md)
- [x] Узел `penguin` (Chromebook):
    - Убедиться, что `sshd` запущен: `sudo systemctl start ssh`
    - Добавить ключ: `mkdir -p ~/.ssh && cat ~/Sync/chromebook_ssh_key.pub >> ~/.ssh/authorized_keys`
    - Права: `chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys`
    - Статус: [ВЫПОЛНЕНО]

## Заметки для обмена
- **ВНИМАНИЕ (Безопасность):** Обнаружена утечка OpenRouter API Key (`sk-or-v1-8f26...`) в логах `Sync/.gemini/tmp/home/chats/`. GitGuardian прислал уведомление. Денису нужно отозвать ключ.
- **Google Calendar:** API не включено для текущего проекта (799431512190). Для работы !google необходимо активировать Calendar API в консоли.
- **Cleanup:** Файл `ai_chat_room.txt` очищен от бесконечного цикла сообщений.
