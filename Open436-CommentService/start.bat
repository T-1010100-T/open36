@echo off
chcp 65001 > nul

echo ==========================================
echo   Open436 Comment Service (M4)
echo   Port: 8004
echo ==========================================

if exist venv\Scripts\activate.bat (
    echo [INFO] 激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo [WARN] 未找到虚拟环境，使用系统 Python
)

if not exist .env (
    echo [INFO] 复制环境变量模板...
    copy .env.example .env
)

set PYTHONPATH=%CD%;%PYTHONPATH%

echo [INFO] 启动评论互动服务...
python manage.py runserver 0.0.0.0:8004
