@echo off
chcp 65001 >nul
echo ========================================
echo   Open436 CrawlerService 一键安装
echo ========================================
echo.

cd /d "%~dp0"

REM 1. 创建虚拟环境
echo [1/4] 创建虚拟环境...
if not exist ".venv" (
    python -m venv .venv
    echo     虚拟环境创建完成
) else (
    echo     虚拟环境已存在，跳过
)

REM 2. 安装依赖（阿里云镜像）
echo.
echo [2/4] 安装依赖（阿里云镜像）...
call .venv\Scripts\pip.exe install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
if errorlevel 1 (
    echo     依赖安装失败！
    pause
    exit /b 1
)
echo     依赖安装完成

REM 3. 安装 Crawl4AI 浏览器
echo.
echo [3/4] 安装 Crawl4AI 浏览器（Playwright Chromium）...
call .venv\Scripts\crawl4ai-setup.exe
if errorlevel 1 (
    echo     Crawl4AI 浏览器安装失败！尝试手动运行: .venv\Scripts\crawl4ai-setup.exe
    pause
    exit /b 1
)
echo     Crawl4AI 浏览器安装完成

REM 4. 创建数据目录
echo.
echo [4/4] 创建数据目录...
if not exist "data" mkdir data

echo.
echo ========================================
echo   安装完成！启动命令：
echo   .venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8009
echo ========================================
echo.
pause
