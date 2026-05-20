#!/bin/bash

# ==============================================================================
# 🤖 AUTOPILOT SETUP: SYNC PI AGENT FOR TERMUX (ANDROID) & CHROMEBOOK (LINUX)
# ==============================================================================
# This script automates symlinking and configuration for the Pi coding agent
# so it operates in absolute sync with Windows and other active mesh devices.
# ==============================================================================

# Harmonious colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${GREEN}🔄 Инициализация синхронизации Pi Агента...${NC}"
echo -e "${BLUE}====================================================${NC}"

# 1. Determine Home and Sync directory
HOME_DIR=$HOME
SYNC_DIR="$HOME_DIR/Sync"

if [ ! -d "$SYNC_DIR" ]; then
    echo -e "${RED}❌ Ошибка: Папка Sync не найдена в $HOME_DIR!${NC}"
    echo -e "${YELLOW}Пожалуйста, настройте Syncthing или создайте папку Sync вручную.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Папка Sync обнаружена по адресу: $SYNC_DIR${NC}"

# 2. Backup existing configurations if they exist
echo -e "${BLUE}[1/5] Резервное копирование локальных конфигов...${NC}"
if [ -d "$HOME_DIR/.pi" ] && [ ! -L "$HOME_DIR/.pi" ]; then
    echo -e "${YELLOW}Предупреждение: Обнаружена локальная папка ~/.pi. Создаем бэкап...${NC}"
    mv "$HOME_DIR/.pi" "$HOME_DIR/.pi.bak_$(date +%F_%T)"
fi

# 3. Create symlinks for .pi settings directory
echo -e "${BLUE}[2/5] Связывание директории настроек Pi...${NC}"
if [ -d "$SYNC_DIR/.pi" ]; then
    ln -sf "$SYNC_DIR/.pi" "$HOME_DIR/.pi"
    echo -e "${GREEN}✅ Junction-ссылка успешно создана: ~/.pi -> ~/Sync/.pi${NC}"
else
    echo -e "${RED}❌ Ошибка: ~/Sync/.pi не существует. Дождитесь окончания синхронизации Syncthing!${NC}"
    exit 1
fi

# 4. Create symlinks for Clinerules and Cursorrules (System Persona Instructions)
echo -e "${BLUE}[3/5] Связывание правил поведения (.clinerules и .cursorrules)...${NC}"
if [ -f "$SYNC_DIR/.clinerules" ]; then
    ln -sf "$SYNC_DIR/.clinerules" "$HOME_DIR/.clinerules"
    echo -e "${GREEN}✅ Ссылка для .clinerules создана в $HOME_DIR/.clinerules${NC}"
fi
if [ -f "$SYNC_DIR/.cursorrules" ]; then
    ln -sf "$SYNC_DIR/.cursorrules" "$HOME_DIR/.cursorrules"
    echo -e "${GREEN}✅ Ссылка для .cursorrules создана в $HOME_DIR/.cursorrules${NC}"
fi

# 5. Add custom aliases to Shell Profile for easy execution
echo -e "${BLUE}[4/5] Настройка переменных среды и алиасов...${NC}"
SHELL_PROFILE=""
if [ -f "$HOME_DIR/.zshrc" ]; then
    SHELL_PROFILE="$HOME_DIR/.zshrc"
elif [ -f "$HOME_DIR/.bashrc" ]; then
    SHELL_PROFILE="$HOME_DIR/.bashrc"
fi

if [ -n "$SHELL_PROFILE" ]; then
    # Add loopback environment check for local Ollama in Termux
    if ! grep -q "OLLAMA_HOST" "$SHELL_PROFILE"; then
        echo -e "\n# GMC Ollama config" >> "$SHELL_PROFILE"
        echo "export OLLAMA_HOST=127.0.0.1:11434" >> "$SHELL_PROFILE"
    fi
    # Add fast git-sync alias
    if ! grep -q "alias pi-sync" "$SHELL_PROFILE"; then
        echo "alias pi-sync='sh $SYNC_DIR/Scripts/setup_pi_termux_chromebook.sh'" >> "$SHELL_PROFILE"
    fi
    echo -e "${GREEN}✅ Настройки профиля успешно обновлены в $SHELL_PROFILE!${NC}"
else
    echo -e "${YELLOW}Предупреждение: Файл профиля оболочки (.bashrc или .zshrc) не найден. Алиасы не настроены.${NC}"
fi

# 6. Verify local Ollama server status
echo -e "${BLUE}[5/5] Проверка локального сервера моделей Ollama...${NC}"
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✅ Ollama установлена!${NC}"
    if pgrep -x "ollama" > /dev/null; then
        echo -e "${GREEN}🟢 Сервер Ollama запущен и работает в фоне.${NC}"
    else
        echo -e "${YELLOW}⚠️ Сервер Ollama не запущен. Вы можете запустить его командой: ollama serve &${NC}"
    fi
else
    echo -e "${YELLOW}ℹ️ Подсказка: Вы можете установить локальный сервер моделей Ollama в Termux с помощью: pkg install ollama${NC}"
fi

echo -e "${BLUE}====================================================${NC}"
echo -e "${GREEN}🎉 СИНХРОНИЗАЦИЯ УСПЕШНО ЗАВЕРШЕНА!${NC}"
echo -e "${YELLOW}Pi Агент теперь полностью интегрирован в сеть GMC и обменивается сессиями с Windows и Chromebook.${NC}"
echo -e "${BLUE}====================================================${NC}"
