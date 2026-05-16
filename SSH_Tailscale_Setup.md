# Настройка SSH между Windows, Chromebook и Termux через Tailscale

Tailscale объединяет все устройства в одну сеть с постоянными IP. SSH теперь работает напрямую, без настройки портов в роутере.

## 📍 Ваши постоянные Tailscale IP:
- **Windows (PC):** `100.72.214.118`
- **Chromebook (Penguin):** `100.106.187.105`
- **Android (Motorola/Termux):** `100.87.207.25`

---

## 1. Настройка Android (Termux)
Termux использует **порт 8022**.

1. **Установка:** `pkg install openssh -y`
2. **Запуск:** `sshd` (запускайте в Termux перед каждой сессией).
3. **Авторизация (выполнить на ПК):**
   ```powershell
   type $env:USERPROFILE\.ssh\id_rsa.pub | ssh -p 8022 логин_termux@100.87.207.25 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
   ```

---

## 2. Настройка Chromebook (Penguin)
Chromebook использует **стандартный порт 22**.

1. **Установка:** `sudo apt update && sudo apt install openssh-server -y`
2. **Запуск:** `sudo systemctl enable --now ssh`
3. **Авторизация (выполнить на ПК):**
   ```powershell
   type $env:USERPROFILE\.ssh\id_rsa.pub | ssh логин_linux@100.106.187.105 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
   ```

---

## 3. Команды для быстрого подключения

* **Вход на Termux:**
  ```powershell
  ssh -p 8022 логин_termux@100.87.207.25
  ```

* **Вход на Chromebook:**
  ```powershell
  ssh логин_linux@100.106.187.105
  ```

*(Если `id_rsa.pub` не существует, создайте его командой `ssh-keygen` в PowerShell).*

