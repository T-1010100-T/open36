# Open436 评论互动服务 (M4)

回复、点赞、收藏等互动功能。

## 服务信息

- **服务名称**: comment-service
- **服务端口**: 8004
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
Get-Content migrations\V1__create_comments_tables.sql | docker exec -i open436-postgres-dev psql -U open436 -d open436

# 启动服务
.\start.bat
```

## API 接口

### 回复接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/replies/?post_id={id} | 回复列表 |
| POST | /api/replies/ | 发布回复 |
| PUT | /api/replies/{id}/ | 编辑回复 |
| DELETE | /api/replies/{id}/ | 删除回复 |

### 点赞/收藏接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/posts/{id}/like/ | 点赞/取消点赞 |
| POST | /api/posts/{id}/favorite/ | 收藏/取消收藏 |
| GET | /api/favorites/ | 我的收藏 |

### 内部接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /internal/posts/{id}/replies/count/ | 回复数 |
| GET | /internal/posts/{id}/likes/count/ | 点赞数 |
| GET | /internal/posts/{id}/favorites/count/ | 收藏数 |
| GET | /internal/users/{id}/replies/ | 用户回复历史 |

## 数据库表

- **replies** - 回复表
- **post_likes** - 帖子点赞表
- **post_favorites** - 帖子收藏表
