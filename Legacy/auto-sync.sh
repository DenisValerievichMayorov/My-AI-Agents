#!/bin/bash
# Auto-sync script for Denis
# Uses rclone bisync from crontab

rclone bisync /home/denisvalerievichmayorov1/Sync gdrive:Sync
