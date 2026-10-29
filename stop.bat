@echo off
chcp 65001 >nul
title AI Resume Assistant - 停止服务

echo ▶ 正在停止 AI Resume Assistant...

:: 找到占用 8000 端口的进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    echo   终止进程 PID=%%a
    taskkill /PID %%a /F >nul 2>&1
)

echo ✅ 已停止
pause
