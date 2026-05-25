#!/bin/bash
# ══════════════════════════════════════════════════
#  Open436 Kong 路由初始化脚本
#  在 Kong 容器启动后执行，注册所有后端服务路由
# ══════════════════════════════════════════════════
set -euo pipefail

KONG_ADMIN="http://localhost:${KONG_ADMIN:-8001}"

echo "========================================="
echo "  Open436 Kong 路由初始化"
echo "========================================="

# 等待 Kong 就绪
echo "[1/3] 等待 Kong 就绪..."
retry=0
until curl -sf "$KONG_ADMIN/status" > /dev/null 2>&1; do
    retry=$((retry + 1))
    if [ $retry -ge 30 ]; then
        echo "[FAIL] Kong 未就绪，超时退出"
        exit 1
    fi
    sleep 2
done
echo "  Kong 已就绪"

# 清理旧配置
echo "[2/3] 清理旧路由..."
for svc in auth-service enrollment-service file-service user-service content-service comment-service section-service; do
    curl -sf -X DELETE "$KONG_ADMIN/services/$svc" 2>/dev/null || true
done
sleep 1

# 注册服务路由
echo "[3/3] 注册服务路由..."

register_service() {
    local name=$1 url=$2 shift 2
    echo "  → $name ($url)"
    curl -sf -X POST "$KONG_ADMIN/services" \
        --data "name=$name" \
        --data "url=$url" > /dev/null
    for path in "$@"; do
        curl -sf -X POST "$KONG_ADMIN/services/$name/routes" \
            --data "paths[]=$path" \
            --data "strip_path=false" > /dev/null
    done
}

register_service "auth-service"       "http://auth:8081"          "/api/auth"
register_service "enrollment-service" "http://enrollment:8084"    "/api/enrollment" "/api/interview"
register_service "file-service"       "http://file-service:8007"  "/api/files"
register_service "user-service"       "http://user-service:8002"  "/api/users"
register_service "content-service"    "http://content-service:8003" "/api/posts" "/api/contents"
register_service "comment-service"    "http://comment-service:8004" "/api/comments"
register_service "section-service"    "http://section-service:8005" "/api/sections"

# 文件服务启用 satoken 鉴权
curl -sf -X POST "$KONG_ADMIN/services/file-service/plugins" \
    --data "name=satoken-auth" \
    --data "config.auth_service_url=http://auth:8081" > /dev/null

echo ""
echo "========================================="
echo "  Kong 路由配置完成!"
echo "========================================="
echo ""
echo "已注册路由:"
echo "  /api/auth       → auth:8081"
echo "  /api/enrollment → enrollment:8084"
echo "  /api/interview  → enrollment:8084"
echo "  /api/files      → file-service:8007 (鉴权)"
echo "  /api/users      → user-service:8002"
echo "  /api/posts      → content-service:8003"
echo "  /api/comments   → comment-service:8004"
echo "  /api/sections   → section-service:8005"
echo ""
