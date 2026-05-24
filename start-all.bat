@echo off
chcp 65001 >nul 2>nul
title Open436 全方位启动器
color 0A

echo.
echo  ═══════════════════════════════════════════════
echo       Open436 全方位项目启动器 v1.0
echo       精准即虔诚，编造即渎神
echo  ═══════════════════════════════════════════════
echo.

set "ROOT=%~dp0"
set "DEPLOY=%ROOT%deploy\dev"
set "VENV_PY=%ROOT%.venv\Scripts\python.exe"

REM ═══════════════════════════════════════════════
REM Phase 0: 前置检查
REM ═══════════════════════════════════════════════
echo [Phase 0] 前置环境检查...
set "MISSING=0"

where docker >nul 2>nul || (echo   [X] Docker 未安装 & set "MISSING=1")
where java >nul 2>nul  || (echo   [X] Java 未安装 & set "MISSING=1")
where mvn >nul 2>nul   || (echo   [X] Maven 未安装 & set "MISSING=1")
where node >nul 2>nul  || (echo   [X] Node.js 未安装 & set "MISSING=1")

if not exist "%VENV_PY%" (
    echo   [!] Python venv 不存在，尝试创建...
    cd /d "%ROOT%" && python -m venv .venv && .venv\Scripts\pip install -r Open436-UserService\requirements.txt
)

if "%MISSING%"=="1" (
    echo.
    echo   [!] 缺少必要工具，部分服务可能无法启动
    echo.
)

echo   [OK] 前置检查完成
echo.

REM ═══════════════════════════════════════════════
REM Phase 1: Docker 基础设施
REM ═══════════════════════════════════════════════
echo [Phase 1] 启动 Docker 基础设施...

cd /d "%DEPLOY%"
docker-compose -f docker-compose.yml up -d postgres redis consul minio kong-database 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo   [!] Docker 基础设施启动失败，尝试启动已有容器...
    docker start open436-postgres-dev open436-redis-dev open436-consul-dev open436-minio-dev kong-database-dev 2>nul
)

echo   等待数据库就绪 (10s)...
timeout /t 10 /nobreak >nul

docker-compose -f docker-compose.yml up -d kong 2>nul || docker start open436-kong-dev 2>nul
echo   等待 Kong 就绪 (8s)...
timeout /t 8 /nobreak >nul

echo   启动 HOJ MySQL...
docker start open436-hoj-mysql 2>nul || echo   [!] HOJ MySQL 容器不可用

echo   等待 MySQL 就绪 (5s)...
timeout /t 5 /nobreak >nul

echo   配置 Kong 路由...
cd /d "%DEPLOY%"
powershell -ExecutionPolicy Bypass -File kong-config.ps1 2>nul || echo   [!] Kong 配置需手动执行

echo   [OK] 基础设施已启动
echo.

REM ═══════════════════════════════════════════════
REM Phase 2: Java 后端服务
REM ═══════════════════════════════════════════════
echo [Phase 2] 启动 Java 后端服务...

echo   启动 M1 认证服务 (8081)...
start "M1-Auth-8081" /min cmd /k "cd /d %ROOT%Open436-Auth && title M1-Auth-8081 && mvn spring-boot:run -Dspring-boot.run.profiles=dev"

echo   启动 Enrollment 报名服务 (8084)...
start "Enrollment-8084" /min cmd /k "cd /d %ROOT%Open436-Enrollment && title Enrollment-8084 && mvn spring-boot:run -Dspring-boot.run.profiles=dev"

echo   启动 HOJ 后端 (6688)...
start "HOJ-Backend-6688" /min cmd /k "cd /d %ROOT%Open436-hoj\hoj-springboot\DataBackup && title HOJ-Backend-6688 && mvn spring-boot:run -Dspring-boot.run.profiles=dev"

echo   启动 HOJ 判题 (8088)...
start "HOJ-Judge-8088" /min cmd /k "cd /d %ROOT%Open436-hoj\hoj-springboot\JudgeServer && title HOJ-Judge-8088 && mvn spring-boot:run -Dspring-boot.run.profiles=dev"

echo   [OK] Java 服务启动中
echo.

REM ═══════════════════════════════════════════════
REM Phase 3: Python 后端服务
REM ═══════════════════════════════════════════════
echo [Phase 3] 启动 Python 后端服务...

echo   启动 M2 用户服务 (8002)...
start "M2-User-8002" /min cmd /k "cd /d %ROOT%Open436-UserService && title M2-User-8002 && ..\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8002"

echo   启动 M3 内容服务 (8003)...
start "M3-Content-8003" /min cmd /k "cd /d %ROOT%Open436-ContentService && title M3-Content-8003 && ..\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8003"

echo   启动 M4 评论服务 (8004)...
start "M4-Comment-8004" /min cmd /k "cd /d %ROOT%Open436-CommentService && title M4-Comment-8004 && ..\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8004"

echo   启动 M5 板块服务 (8005)...
start "M5-Section-8005" /min cmd /k "cd /d %ROOT%Open436-SectionService && title M5-Section-8005 && ..\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8005"

echo   [OK] Python 服务启动中
echo.

REM ═══════════════════════════════════════════════
REM Phase 4: 前端服务
REM ═══════════════════════════════════════════════
echo [Phase 4] 启动前端服务...

echo   启动 Frontend (3000)...
start "Frontend-3000" /min cmd /k "cd /d %ROOT%Open436-Frontend && title Frontend-3000 && npm run dev"

echo   启动 Admin (3001)...
start "Admin-3001" /min cmd /k "cd /d %ROOT%Open436-Admin && title Admin-3001 && npm run dev"

echo   启动 HOJ-Vue (8066)...
start "HOJ-Vue-8066" /min cmd /k "cd /d %ROOT%Open436-hoj\hoj-vue && title HOJ-Vue-8066 && npm run serve"

echo   [OK] 前端服务启动中
echo.

REM ═══════════════════════════════════════════════
REM Summary
REM ═══════════════════════════════════════════════
echo  ═══════════════════════════════════════════════
echo       全部服务已分发启动
echo  ═══════════════════════════════════════════════
echo.
echo  基础设施 ^(Docker^):
echo    PostgreSQL : localhost:55432  (open436/open436)
echo    Redis      : localhost:6379
echo    Consul     : http://localhost:8500
echo    Minio      : http://localhost:9001  (minioadmin/minioadmin)
echo    Kong Proxy : http://localhost:8000
echo    Kong Admin : http://localhost:8001
echo    HOJ MySQL  : localhost:3307   (root/hoj123456)
echo.
echo  后端服务:
echo    M1 Auth      : http://localhost:8081/actuator/health
echo    M2 User      : http://localhost:8002
echo    M3 Content   : http://localhost:8003
echo    M4 Comment   : http://localhost:8004
echo    M5 Section   : http://localhost:8005/health/
echo    M7 File      : [跳过] Cargo/Rust 未安装
echo    Enrollment   : http://localhost:8084/actuator/health
echo    HOJ Backend  : http://localhost:6688
echo    HOJ Judge    : http://localhost:8088
echo.
echo  前端:
echo    Frontend : http://localhost:3000
echo    Admin    : http://localhost:3001
echo    HOJ-Vue  : http://localhost:8066
echo.
echo  [!] Java 服务首次启动需下载依赖，请耐心等待
echo  [!] 所有后端服务窗口已最小化，可在任务栏查看
echo.
pause
