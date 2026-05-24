#!/bin/bash

echo "=========================================="
echo "   Open436 Comment Service (M4)"
echo "   Port: 8004"
echo "=========================================="

if [ -d "venv" ]; then
    echo "[INFO] 激活虚拟环境..."
    source venv/bin/activate
fi

if [ ! -f ".env" ]; then
    echo "[INFO] 复制环境变量模板..."
    cp .env.example .env
fi

export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "[INFO] 启动评论互动服务..."
python manage.py runserver 0.0.0.0:8004
