#!/bin/bash
# ══════════════════════════════════════════════════
#  Open436 一键启动脚本 (Linux/Mac)
#  使用: chmod +x docker-start.sh && ./docker-start.sh
# ══════════════════════════════════════════════════
set -e

cd "$(dirname "$0")"

# 颜色
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; C='\033[0;36m'; NC='\033[0m'

echo ""
echo -e "${C}═════════════════════════════════════════════════════"
echo -e "  Open436 Docker 一键启动器"
echo -e "═════════════════════════════════════════════════════${NC}"
echo ""

# 1. 检查 Docker
echo -e "${Y}[1/5]${NC} 检查 Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${R}  [X] Docker 未安装，请先安装 Docker Desktop${NC}"
    exit 1
fi
if ! docker info &> /dev/null; then
    echo -e "${R}  [X] Docker 未启动，请先启动 Docker Desktop${NC}"
    exit 1
fi
echo -e "${G}  [OK] Docker 就绪${NC}"

# 2. 环境配置
echo -e "${Y}[2/5]${NC} 检查环境配置..."
if [ ! -f .env ]; then
    cp .env.docker .env
    echo -e "${G}  [OK] 已从 .env.docker 创建 .env${NC}"
else
    echo -e "${G}  [OK] .env 已存在${NC}"
fi

# 3. 构建并启动
echo -e "${Y}[3/5]${NC} 构建并启动所有服务..."
PROFILE=""
if [ "${1:-}" = "--with-hoj" ] || [ "${1:-}" = "--hoj" ]; then
    PROFILE="--profile hoj"
    echo -e "${C}  包含 HOJ 在线判题系统${NC}"
fi

docker compose $PROFILE up -d --build 2>&1 | tail -5

# 4. 等待服务就绪
echo -e "${Y}[4/5]${NC} 等待核心服务就绪 (30s)..."
sleep 15
echo -n "  ."
sleep 15
echo " done"

# 5. 配置 Kong 路由
echo -e "${Y}[5/5]${NC} 配置 Kong 路由..."
bash docker/init-kong.sh 2>/dev/null || echo -e "${Y}  [!] Kong 配置失败，可手动执行: bash docker/init-kong.sh${NC}"

# 输出访问信息
echo ""
echo -e "${C}═════════════════════════════════════════════════════"
echo -e "  所有服务已启动!"
echo -e "═════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${G}前端:${NC}"
echo "    用户端:    http://localhost:3000"
echo "    管理后台:  http://localhost:3001"
echo ""
echo -e "  ${G}基础设施:${NC}"
echo "    PostgreSQL: localhost:55436  (open436/open436)"
echo "    Redis:      localhost:6379"
echo "    Consul:     http://localhost:8500"
echo "    Minio:      http://localhost:9001  (minioadmin/minioadmin)"
echo "    Kong Proxy: http://localhost:8000"
echo "    Kong Admin: http://localhost:8001"
echo ""
echo -e "  ${G}后端服务 (通过 Kong 访问):${NC}"
echo "    Auth:       http://localhost:8000/api/auth"
echo "    Enrollment: http://localhost:8000/api/enrollment"
echo "    Interview:  http://localhost:8000/api/interview"
echo ""
echo -e "  ${Y}提示:${NC}"
echo "    查看日志: docker compose logs -f [服务名]"
echo "    停止服务: docker compose down"
echo "    含HOJ启动: ./docker-start.sh --with-hoj"
echo ""
