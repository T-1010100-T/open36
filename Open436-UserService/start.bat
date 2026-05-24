@echo off
chcp 65001 > nul

REM Open436 用户管理服务启动脚本 (Windows)

echo ==========================================
echo   Open436 User Service (M2)
echo   Port: 8002
echo ==========================================

REM 检查虚拟环境
if exist venv\Scripts\activate.bat (
    echo [INFO] 激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo [WARN] 未找到虚拟环境，使用系统 Python
)

REM 设置环境变量
if not exist .env (
    echo [INFO] 复制环境变量模板...
    copy .env.example .env
)

REM 设置 PYTHONPATH
set PYTHONPATH=%CD%;%PYTHONPATH%

echo [INFO] 启动用户管理服务...
python manage.py runserver 0.0.0.0:8002
