# GMC Network Control (Global Mission Control)

Этот файл является единственным источником правды для управления вашей сетью из трех устройств: Windows (Главный узел), Chromebook и Телефон (Termux).

---

## 1. Актуальные IP-адреса (Tailscale)
Tailscale позволяет работать с устройствами по этим адресам из любой точки мира:

* **Главный узел (Windows/Desktop):** `100.72.214.118`
* **Chromebook (Penguin):** `100.106.187.105`
* **Телефон (Motorola/Termux):** `100.87.207.25`

---

## 2. SSH Подключения
Для входа на устройства используйте SSH. Ключи синхронизированы через папку `Sync`.

### Вход на Chromebook (с ПК или Телефона):
```bash
ssh -i ~/Sync/chromebook_ssh_key denisvalerievichmayorov1@100.106.187.105
```

### Вход на Телефон (с ПК или Хромбука):
```bash
ssh -p 8022 100.87.207.25
```
*(Обязательно: `passwd` и `sshd` должны быть выполнены в Termux заранее).*

---

## 3. Синхронизация данных (Syncthing)
Папки синхронизируются в реальном времени.

| Папка | Локальный путь (Termux/Linux) |
| :--- | :--- |
| **Gemini Memory** | `~/.gemini` |
| **Hermes Memory** | `~/.hermes` |
| **Work Sync** | `~/Sync` |

*API Key для Termux (Syncthing GUI):* `ZG7QmDMDn5F2ii9v2jA9zuc3qSzDj7Lh`

---

## 4. Автоматизация (Google Drive)
Скрипт `~/Sync/auto-sync.sh` управляет двусторонней синхронизацией с Google Drive.
Для автозапуска добавьте в `crontab -e`:
```text
*/15 * * * * bash ~/Sync/auto-sync.sh > /dev/null 2>&1
```

---
*Файл обновлен: 16 мая 2026 г.*
*Локация: папке Sync (синхронизируется автоматически)*
