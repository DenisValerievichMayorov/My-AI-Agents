@echo off
title AntiGravity Live IDE Quota Monitor
mode con: cols=65 lines=32
color 0f
python C:\Users\anton\agent_tools\ag_monitor.py --quota --loop
pause
