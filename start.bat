@echo off
chcp 65001 >nul
title AI Resume Assistant - 本地服务
cd /d "%~dp0"

echo ╔═══════════════════════════════════════════════════╗
echo ║       AI Resume Assistant — 本地一键启动          ║
echo ╚═══════════════════════════════════════════════════╝
echo.

:: 检查 .venv 是否存在
if not exist ".venv\Scripts\python.exe" (
    echo ❌ 未找到虚拟环境 .venv
    echo    请先运行: python -m venv .venv
    echo    然后运行: .venv\Scripts\pip install -r backend\requirements.txt
    pause
    exit /b 1
)

:: 检查 .env 是否存在（DEEPSEEK_API_KEY）
if not exist ".env" (
    echo ⚠️  未找到 .env 文件，DeepSeek API Key 可能未配置
    echo    请复制 .env.example 为 .env 并填入 DEEPSEEK_API_KEY
    echo.
)

:: 检查是否已经有进程在跑
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    echo ⚠️  端口 8000 已被进程 PID=%%a 占用
    echo    如果是上一次的服务，将终止它...
    taskkill /PID %%a /F >nul 2>&1
    timeout /t 2 /nobreak >nul
)

echo ▶ 正在启动 FastAPI 服务...
echo.

start "AI Resume Assistant" /min cmd /c ".venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

:: 等待几秒让服务起来
timeout /t 4 /nobreak >nul

:: 打开浏览器
echo ✅ 服务已启动！正在打开浏览器...
echo.
start http://localhost:8000

echo ╔═══════════════════════════════════════════════════╗
echo ║  前端页面:  http://localhost:8000                  ║
echo ║  健康检查:  http://localhost:8000/api/health       ║
echo ║  线上 Demo: https://ai-resume-assistant-so11.onrender.com ║
echo ╚═══════════════════════════════════════════════════╝
echo.
echo 💡 提示：关闭本窗口不会停止服务。要停止请运行 stop.bat 或关闭 uvicorn 窗口。
pause
