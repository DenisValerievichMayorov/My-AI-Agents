#!/bin/bash
# Универсальный скрипт для мгновенного запуска и открытия веб-интерфейса GMC на любом Linux, macOS или Android (через Termux)

GMC_IP="100.72.214.118"
PORT="8080"
URL="http://$GMC_IP:$PORT"

echo "🌀 Проверяю статус Tailscale..."
if command -v tailscale &> /dev/null; then
    if ! tailscale status &> /dev/null; then
        echo "⚠️ Tailscale отключен! Пробую запустить..."
        sudo tailscale up
    else
        echo "✅ Tailscale подключен и активен."
    fi
else
    echo "ℹ️ Tailscale CLI не найден (возможно, используется графический клиент). Убедись, что VPN Tailscale включен."
fi

echo "🚀 Открываю панель управления GMC в браузере: $URL"
if command -v termux-open &> /dev/null; then
    termux-open "$URL"
elif command -v xdg-open &> /dev/null; then
    xdg-open "$URL"
elif command -v open &> /dev/null; then
    open "$URL"
else
    echo "⚠️ Не удалось определить утилиту авто-открытия браузера."
    echo "Пожалуйста, открой ссылку вручную: $URL"
fi
