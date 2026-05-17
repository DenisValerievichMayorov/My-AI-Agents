#!/data/data/com.termux/files/usr/bin/bash
# Скрипт для фиксации GPS координат
LOG_FILE="/data/data/com.termux/files/home/Sync/logs/gps_track.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Пытаемся получить локацию
LOCATION=$(termux-location -p network)

if [ $? -eq 0 ]; then
    # Парсим JSON через jq (если установлен)
    LAT=$(echo $LOCATION | jq -r '.latitude')
    LON=$(echo $LOCATION | jq -r '.longitude')
    echo "$DATE | $LAT | $LON" >> "$LOG_FILE"
else
    echo "$DATE | ERROR: Location not available" >> "$LOG_FILE"
fi
