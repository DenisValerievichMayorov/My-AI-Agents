# Единая инструкция по настройке узлов (Gemini Sync)

Этот файл является руководством для автономной настройки узлов (Termux, Chromebook). Выполняйте команды пошагово.

---

## 📱 Узел: Termux (Android)
**Выполнить в Termux:**

1. **Установка SSH:**
   ```bash
   pkg install openssh -y
   sshd
   ```

2. **Настройка ключа доступа (для управления с ПК):**
   ```bash
   mkdir -p ~/.ssh
   cat ~/Sync/chromebook_ssh_key.pub >> ~/.ssh/authorized_keys
   chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
   ```

3. **Автозапуск SSH (опционально):**
   ```bash
   echo "sshd" >> ~/.bashrc
   ```

---

## 💻 Узел: Chromebook (Penguin)
**Выполнить в Терминале Linux (Penguin):**

1. **Установка/Запуск SSH:**
   ```bash
   sudo apt update && sudo apt install openssh-server -y
   sudo systemctl enable ssh
   sudo systemctl start ssh
   ```

2. **Настройка ключа доступа:**
   ```bash
   mkdir -p ~/.ssh
   cat ~/Sync/chromebook_ssh_key.pub >> ~/.ssh/authorized_keys
   chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
   ```

---

## 4. Google Workspace / Photos API (Настройка для Gemini CLI)
Для доступа к API Google Фото (через навыки `google-workspace`):

1. **Google Cloud Console**: Создать проект -> Включить API (Photos Library, Gmail, Drive).
2. **OAuth 2.0**: Создать "Desktop app" клиент.
3. **Настройка в CLI (Termux)**:
   ```bash
   GSETUP="python ~/.gemini/skills/google-workspace/scripts/setup.py"
   # Укажите путь к JSON-файлу секретов
   $GSETUP --client-secret /path/to/client_secret.json
   # Получение URL для авторизации
   $GSETUP --auth-url --services all
   # Вставьте полученный URL из браузера:
   $GSETUP --auth-code "URL_ИЗ_БРАУЗЕРА"
   ```
4. **Проверка**: `$GSETUP --check`.

*Файл обновлен: 17 мая 2026 г. Синхронизируется автоматически через Syncthing/Google Drive.*
