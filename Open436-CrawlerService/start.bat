@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 启动 CrawlerService (端口 8009)...
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8009
