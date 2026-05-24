# Open436 内容管理服务 (M3)

帖子生命周期管理：发布、浏览、编辑、删除、置顶。

## 服务信息

- **服务名称**: content-service
- **服务端口**: 8003
- **技术栈**: Python 3.11 + Django 4.2 + DRF
- **数据库**: PostgreSQL

## 快速开始

```bash
# 安装依赖
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env

# 执行数据库迁移
Get-Content migrations\V1__create_posts_tables.sql | docker exec -i open436-postgres-dev psql -U open436 -d open436

# 启动服务
.\start.bat
```

## API 接口

### 公开接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/posts/ | 帖子列表（支持板块筛选） |
| POST | /api/posts/ | 发布帖子 |
| GET | /api/posts/{id}/ | 帖子详情 |
| PUT | /api/posts/{id}/ | 编辑帖子 |
| DELETE | /api/posts/{id}/ | 删除帖子（软删除） |

### 管理员接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/posts/{id}/restore/ | 恢复帖子 |
| POST | /api/posts/{id}/pin/ | 置顶 |
| POST | /api/posts/{id}/unpin/ | 取消置顶 |
| GET | /api/posts/{id}/history/ | 编辑历史 |

### 内部接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /internal/posts/{id}/increment-views/ | 浏览量+1 |
| GET | /internal/posts/{id}/validate/ | 验证帖子 |
| GET | /internal/posts/by-user/{user_id}/ | 用户帖子列表 |

## 数据库表

- **posts** - 帖子表
- **post_edit_history** - 编辑历史表
