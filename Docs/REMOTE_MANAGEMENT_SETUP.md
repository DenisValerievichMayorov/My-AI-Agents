# Инструкция: Настройка SSH-сервера для управления (Windows & Android)

Для того чтобы я (Chromebook) мог подключаться к вашим устройствам и выполнять на них команды (например, для синхронизации, проверки статуса или автоматизации), на каждом из них нужно настроить SSH-сервер.

---

## 1. Windows: Настройка OpenSSH Server

1. **Установка:**
   - Откройте **Параметры** -> **Приложения** -> **Дополнительные компоненты**.
   - Нажмите "Просмотреть компоненты", найдите **OpenSSH Server** и установите его.

2. **Запуск сервера:**
   - Откройте PowerShell от имени администратора.
   - Выполните команды:
     ```powershell
     Start-Service sshd
     Set-Service -Name sshd -StartupType 'Automatic'
     ```

3. **Настройка доступа:**
   - Чтобы я мог заходить без пароля, скопируйте свой публичный ключ (из `Sync/chromebook_ssh_key.pub`) в файл `C:\Users\ВАШ_ПОЛЬЗОВАТЕЛЬ\.ssh\authorized_keys`.
   - Если файла или папки `.ssh` нет — создайте их.

---

## 2. Android (Termux): Настройка SSH

1. **Установка:**
   - Откройте Termux и выполните:
     ```bash
     pkg update && pkg install openssh
     ```

2. **Запуск сервера:**
   - Запустите сервер командой:
     ```bash
     sshd
     ```
   - (Чтобы он запускался сам, можно добавить `sshd` в файл `~/.bashrc`).

3. **Настройка доступа:**
   - Скопируйте публичный ключ (`chromebook_ssh_key.pub`) в файл `~/.ssh/authorized_keys` на телефоне:
     ```bash
     mkdir -p ~/.ssh
     cat ~/storage/shared/Sync/chromebook_ssh_key.pub >> ~/.ssh/authorized_keys
     chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
     ```

---

## 3. Проверка (Выполнить на Chromebook)

После настройки на устройствах вы сможете проверить связь с Chromebook:

```bash
# Подключение к Windows (IP из Tailscale)
ssh denisvalerievichmayorov1@100.72.214.118

# Подключение к Android
ssh denisvalerievichmayorov1@100.87.207.25
```

Как только вы всё настроите, дайте мне знать — я проверю связь!
