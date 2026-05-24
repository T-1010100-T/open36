#!/bin/bash

# Open436 用户管理服务启动脚本 (Linux/Mac)

echo "=========================================="
echo "   Open436 User Service (M2)"
echo "   Port: 8002"
echo "=========================================="

# 激活虚拟环境
if [ -d "venv" ]; then
    echo "[INFO] 激活虚拟环境..."
    source venv/bin/activate
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "[INFO] 复制环境变量模板..."
    cp .env.example .env
fi

# 设置 PYTHONPATH
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "[INFO] 启动用户管理服务..."
python manage.py runserver 0.0.0.0:8002
