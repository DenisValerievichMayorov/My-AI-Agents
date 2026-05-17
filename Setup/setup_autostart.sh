#!/bin/bash
# GMC Unified Autostart Setup Script

DEVICE_TYPE="unknown"
if [ -d "/data/data/com.termux" ]; then
    DEVICE_TYPE="termux"
elif [ -f "/etc/debian_version" ]; then
    DEVICE_TYPE="chromebook"
fi

echo "--- GMC AUTOSTART SETUP FOR DEVICE TYPE: $DEVICE_TYPE ---"

if [ "$DEVICE_TYPE" = "termux" ]; then
    # 1. Настройка автозапуска в Termux (~/.bashrc)
    echo "Configuring ~/.bashrc for Termux..."
    
    # Резервная копия существующего .bashrc
    if [ -f "$HOME/.bashrc" ]; then
        cp "$HOME/.bashrc" "$HOME/.bashrc.bak"
    fi

    # Пишем чистое автозапуск-окружение
    cat << 'EOF' > "$HOME/.bashrc"
# Start SSH daemon on shell open
if ! pgrep -x "sshd" > /dev/null; then
    sshd
fi

# Auto-start GMC Agent and Heartbeat in background if not running
if ! pgrep -f "agent_listener.py" > /dev/null; then
    nohup python3 -u "$HOME/Sync/agent_listener.py" > "$HOME/Sync/agent.log" 2>&1 &
    echo "GMC Agent started in background."
fi
if ! pgrep -f "heartbeat.py" > /dev/null; then
    nohup python3 -u "$HOME/Sync/heartbeat.py" > "$HOME/Sync/heartbeat.log" 2>&1 &
    echo "GMC Heartbeat started in background."
fi
EOF

    echo "Source .bashrc to run the background processes immediately..."
    source "$HOME/.bashrc"
    
    echo "✅ Termux Autostart Setup completed successfully!"
    pgrep -lf "python3"

elif [ "$DEVICE_TYPE" = "chromebook" ]; then
    echo "Configuring systemd services for Chromebook..."
    
    mkdir -p "$HOME/.config/systemd/user"

    cat << 'EOF' > $HOME/.config/systemd/user/gmc-listener.service
[Unit]
Description=GMC AI Agent Listener
After=network.target

[Service]
Type=simple
WorkingDirectory=%h/Sync
ExecStart=/usr/bin/python3 -u agent_listener.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

    cat << 'EOF' > $HOME/.config/systemd/user/gmc-heartbeat.service
[Unit]
Description=GMC Heartbeat Monitor
After=network.target

[Service]
Type=simple
WorkingDirectory=%h/Sync
ExecStart=/usr/bin/python3 -u heartbeat.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

    # Включаем lingering и запускаем сервисы
    loginctl enable-linger
    systemctl --user daemon-reload
    systemctl --user enable gmc-listener.service gmc-heartbeat.service
    systemctl --user restart gmc-listener.service gmc-heartbeat.service
    
    echo "✅ Chromebook systemd Autostart completed successfully!"
    systemctl --user status gmc-listener.service gmc-heartbeat.service --no-pager
else
    echo "❌ Unknown device type. Setup skipped."
fi
