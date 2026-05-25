@echo off
chcp 65001 >nul 2>nul
title Open436 Docker 一键启动器
color 0A

echo.
echo  ═══════════════════════════════════════════════════
echo       Open436 Docker 一键启动器
echo  ═══════════════════════════════════════════════════
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%"

REM [1/5] 检查 Docker
echo [1/5] 检查 Docker...
where docker >nul 2>nul || (
    echo   [X] Docker 未安装，请先安装 Docker Desktop
    pause & exit /b 1
)
docker info >nul 2>nul || (
    echo   [X] Docker 未启动，请先启动 Docker Desktop
    pause & exit /b 1
)
echo   [OK] Docker 就绪

REM [2/5] 环境配置
echo [2/5] 检查环境配置...
if not exist .env (
    copy .env.docker .env >nul
    echo   [OK] 已从 .env.docker 创建 .env
) else (
    echo   [OK] .env 已存在
)

REM [3/5] 构建并启动
echo [3/5] 构建并启动所有服务 (首次较慢, 请耐心等待)...
if "%1"=="--with-hoj" (
    echo   包含 HOJ 在线判题系统
    docker compose --profile hoj up -d --build
) else (
    docker compose up -d --build
)

REM [4/5] 等待就绪
echo [4/5] 等待核心服务就绪 (30s)...
timeout /t 30 /nobreak >nul

REM [5/5] 配置 Kong
echo [5/5] 配置 Kong 路由...
bash docker\init-kong.sh 2>nul || echo   [!] Kong 配置需手动执行

echo.
echo  ═══════════════════════════════════════════════════
echo       所有服务已启动!
echo  ═══════════════════════════════════════════════════
echo.
echo   前端:
echo     用户端:    http://localhost:3000
echo     管理后台:  http://localhost:3001
echo.
echo   基础设施:
echo     PostgreSQL: localhost:55432  (open436/open436)
echo     Redis:      localhost:6379
echo     Consul:     http://localhost:8500
echo     Minio:      http://localhost:9001  (minioadmin/minioadmin)
echo     Kong Proxy: http://localhost:8000
echo     Kong Admin: http://localhost:8001
echo.
echo   后端服务 (通过 Kong 访问):
echo     Auth:       http://localhost:8000/api/auth
echo     Enrollment: http://localhost:8000/api/enrollment
echo     Interview:  http://localhost:8000/api/interview
echo.
echo   常用命令:
echo     查看日志: docker compose logs -f [服务名]
echo     停止服务: docker compose down
echo     含HOJ启动: docker-start.bat --with-hoj
echo.
pause
