# Open436 用户管理服务 (M2)

用户业务信息管理、个人资料、用户统计数据、活动历史。

## 服务信息

- **服务名称**: user-service
- **服务端口**: 8002
- **技术栈**: Python 3.11 + Django 4.2 + DRF
- **数据库**: PostgreSQL
- **认证方式**: Kong Gateway Headers

## 快速开始

### 1. 安装依赖

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
copy .env.example .env
# 编辑 .env 文件
```

### 3. 执行数据库迁移

```bash
# 使用 Docker 提供的 PostgreSQL
Get-Content migrations\V1__create_users_tables.sql | docker exec -i open436-postgres-dev psql -U open436 -d open436
```

### 4. 启动服务

```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

### 5. 验证服务

- 健康检查: http://localhost:8002/health/
- API文档: http://localhost:8002/api/docs/
- 管理后台: http://localhost:8002/admin/

## API 接口

### 公开接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/users/{user_id}/ | 获取用户信息 |
| PUT | /api/users/{user_id}/profile/ | 更新用户资料 |
| POST | /api/users/{user_id}/avatar/ | 上传头像 |
| GET | /api/users/{user_id}/statistics/ | 获取统计数据 |
| GET | /api/users/{user_id}/posts/ | 发帖历史（预留M3） |
| GET | /api/users/{user_id}/replies/ | 回复历史（预留M4） |

### 管理员接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/admin/users/ | 用户列表 |
| POST | /api/admin/users/ | 创建用户 |

### 内部接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /internal/users/batch/ | 批量获取用户信息 |
| POST | /internal/users/{user_id}/statistics/increment/ | 更新统计数据 |

## 数据库表

- **users_profile** - 用户资料表
- **user_statistics** - 用户统计表

## 文档

- [PRD - M2 用户管理模块](../docs/PRD/M2-用户管理模块.md)
- [TDD - M2 用户管理服务](../docs/TDD/M2-用户管理服务/)
