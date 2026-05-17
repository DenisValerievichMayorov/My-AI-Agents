# Инструкция по восстановлению Termux, Syncthing и Gemini CLI

Эта инструкция описывает полный процесс восстановления окружения после переустановки Termux, включая синхронизацию знаний (памяти) и настройку автоматизации.

## 1. Базовая установка в Termux
Откройте Termux и выполните следующие команды:
```bash
termux-setup-storage
pkg update && pkg upgrade -y
pkg install git nodejs python syncthing openssh rsync cronie -y
```

## 2. Настройка Syncthing (Синхронизация знаний)
1. Запустите Syncthing:
   ```bash
   syncthing
   ```
2. Откройте браузер на телефоне и перейдите по адресу: `http://127.0.0.1:8384`
3. В настройках **GUI** укажите ваш API-ключ: `ZG7QmDMDn5F2ii9v2jA9zuc3qSzDj7Lh`
4. Добавьте ваш ПК (Windows) как удаленное устройство (Add Remote Device). ID вашего ПК:
   `KFY2NMX-IU3IHRB-GBGTCWP-AHGR6DJ-Z6W6ID3-QLAGBUG-NOHT36L-2BXN2QP`
5. На ПК примите запрос от Termux.
6. На ПК расшарьте папки `.gemini`, `.hermes` и `Sync`.
7. В Termux примите эти папки со следующими путями:
   * **Gemini Memory (gemini):** `/data/data/com.termux/files/home/.gemini`
   * **Hermes Memory (hermes):** `/data/data/com.termux/files/home/.hermes`
   * **Work Sync (default):** `/data/data/com.termux/files/home/Sync`

## 3. Установка инструментов (CLI)
Установите Gemini CLI и (опционально) OpenClaw:
```bash
npm install -g @google/gemini-cli
npm install -g @openclaw/cli
```

## 4. Очистка лишнего места (по необходимости)
Если Termux занимает слишком много места (более 3-4 ГБ), выполните очистку кэша:
```bash
rm -rf ~/.npm
rm -rf ~/.cargo/registry
```
Также можно удалить старые логи сессий в папке `~/.gemini/tmp/home/chats/` (если они занимают много места).

## 5. Настройка SSH для удаленного доступа
Чтобы подключаться к Termux с компьютера:
1. Задайте пароль:
   ```bash
   passwd
   ```
2. Запустите SSH-сервер:
   ```bash
   sshd
   ```
Подключение к телефону:
* **С Windows (PowerShell/CMD):** `ssh -p 8022 IP_ТЕЛЕФОНА`
* **С Chromebook (Linux Terminal):** `ssh -p 8022 IP_ТЕЛЕФОНА`
(Устройства должны быть в одной Wi-Fi сети).

## 6. Автоматизация (Cron & Rclone для Google Drive)
Настройка фоновой синхронизации с Google Drive каждые 15 минут:
1. Скрипт синхронизации уже должен лежать в `~/Sync/auto-sync.sh`. Убедитесь, что он исполняемый:
   ```bash
   chmod +x ~/Sync/auto-sync.sh
   ```
2. Настройте расписание:
   ```bash
   crontab -e
   ```
   Добавьте строку:
   ```text
   */15 * * * * bash ~/Sync/auto-sync.sh > /dev/null 2>&1
   ```

## 7. Проверка связи (Global Mission Control)
После завершения синхронизации папок проверьте статус агентов:
```bash
gemini "Статус Агентов"
```
Ожидаемый ответ: «OpenClaw: Online, Antigravity: Online, Gemini CLI: Online».