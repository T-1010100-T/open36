-- M4 评论互动服务 - 初始数据库迁移

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 1. 回复表
CREATE TABLE IF NOT EXISTS replies (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    floor_number INTEGER NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    edit_count INTEGER NOT NULL DEFAULT 0,
    last_edited_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_reply_content_length CHECK (LENGTH(content) >= 2 AND LENGTH(content) <= 10000)
);

COMMENT ON TABLE replies IS '回复表';
COMMENT ON COLUMN replies.post_id IS '帖子ID（关联M3 posts.id）';
COMMENT ON COLUMN replies.author_id IS '作者ID（关联M1 users_auth.id）';
COMMENT ON COLUMN replies.floor_number IS '楼层号';
COMMENT ON COLUMN replies.is_deleted IS '是否已删除';

-- 2. 帖子点赞表
CREATE TABLE IF NOT EXISTS post_likes (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_post_like UNIQUE (post_id, user_id)
);

COMMENT ON TABLE post_likes IS '帖子点赞表';

-- 3. 帖子收藏表
CREATE TABLE IF NOT EXISTS post_favorites (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_post_favorite UNIQUE (post_id, user_id)
);

COMMENT ON TABLE post_favorites IS '帖子收藏表';

-- 4. 索引
CREATE INDEX IF NOT EXISTS idx_replies_post ON replies(post_id);
CREATE INDEX IF NOT EXISTS idx_replies_author ON replies(author_id);
CREATE INDEX IF NOT EXISTS idx_replies_deleted ON replies(is_deleted);
CREATE INDEX IF NOT EXISTS idx_replies_floor ON replies(post_id, floor_number);
CREATE INDEX IF NOT EXISTS idx_replies_created ON replies(created_at);

CREATE INDEX IF NOT EXISTS idx_post_likes_post ON post_likes(post_id);
CREATE INDEX IF NOT EXISTS idx_post_likes_user ON post_likes(user_id);

CREATE INDEX IF NOT EXISTS idx_post_favorites_post ON post_favorites(post_id);
CREATE INDEX IF NOT EXISTS idx_post_favorites_user ON post_favorites(user_id);

-- 5. 触发器
DROP TRIGGER IF EXISTS update_replies_updated_at ON replies;
CREATE TRIGGER update_replies_updated_at
    BEFORE UPDATE ON replies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
