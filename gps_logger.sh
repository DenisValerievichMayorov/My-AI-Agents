#!/data/data/com.termux/files/usr/bin/bash
# Скрипт для фиксации GPS координат с умным резервным IP-геолокатором
LOG_FILE="/data/data/com.termux/files/home/Sync/logs/gps_track.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Получаем локацию через наш Python скрипт (который имеет IP-резерв)
LOCATION=$(python3 /data/data/com.termux/files/home/Sync/get_loc_direct.py)

# Проверяем, есть ли ошибка
ERROR=$(echo $LOCATION | jq -r '.error // empty')

if [ -z "$ERROR" ]; then
    LAT=$(echo $LOCATION | jq -r '.latitude')
    LON=$(echo $LOCATION | jq -r '.longitude')
    PROVIDER=$(echo $LOCATION | jq -r '.provider // "gps"')
    echo "$DATE | $LAT | $LON | $PROVIDER" >> "$LOG_FILE"
else
    echo "$DATE | ERROR: $ERROR" >> "$LOG_FILE"
fi
