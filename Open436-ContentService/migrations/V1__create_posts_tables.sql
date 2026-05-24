-- M3 内容管理服务 - 初始数据库迁移

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 1. 帖子表
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    author_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    is_pinned BOOLEAN DEFAULT FALSE,
    pin_type VARCHAR(20) DEFAULT 'none',
    views_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'published',
    edit_count INTEGER NOT NULL DEFAULT 0,
    last_edited_at TIMESTAMP,
    last_edited_by INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_title_length CHECK (LENGTH(title) >= 5 AND LENGTH(title) <= 100),
    CONSTRAINT chk_content_length CHECK (LENGTH(content) >= 10 AND LENGTH(content) <= 50000),
    CONSTRAINT chk_status CHECK (status IN ('published', 'deleted')),
    CONSTRAINT chk_pin_type CHECK (pin_type IN ('none', 'global', 'section'))
);

COMMENT ON TABLE posts IS '帖子表';
COMMENT ON COLUMN posts.id IS '帖子ID';
COMMENT ON COLUMN posts.title IS '标题（5-100字符）';
COMMENT ON COLUMN posts.content IS '内容（支持富文本）';
COMMENT ON COLUMN posts.author_id IS '作者ID（关联M1）';
COMMENT ON COLUMN posts.section_id IS '板块ID（关联M5）';
COMMENT ON COLUMN posts.is_pinned IS '是否置顶';
COMMENT ON COLUMN posts.pin_type IS '置顶类型（none/global/section）';
COMMENT ON COLUMN posts.views_count IS '浏览量';
COMMENT ON COLUMN posts.status IS '状态（published/deleted）';
COMMENT ON COLUMN posts.edit_count IS '编辑次数';
COMMENT ON COLUMN posts.last_edited_at IS '最后编辑时间';
COMMENT ON COLUMN posts.last_edited_by IS '最后编辑者ID';

-- 2. 编辑历史表
CREATE TABLE IF NOT EXISTS post_edit_history (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    section_id INTEGER NOT NULL,
    edited_by INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_post_history FOREIGN KEY (post_id)
        REFERENCES posts(id) ON DELETE CASCADE
);

COMMENT ON TABLE post_edit_history IS '帖子编辑历史表';

-- 3. 索引
CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author_id);
CREATE INDEX IF NOT EXISTS idx_posts_section ON posts(section_id);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_pinned ON posts(is_pinned);
CREATE INDEX IF NOT EXISTS idx_posts_pin_type ON posts(pin_type);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at);
CREATE INDEX IF NOT EXISTS idx_posts_published_created ON posts(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_section_published ON posts(section_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_post_history_post ON post_edit_history(post_id);
CREATE INDEX IF NOT EXISTS idx_post_history_created ON post_edit_history(created_at);

-- 4. 触发器
DROP TRIGGER IF EXISTS update_posts_updated_at ON posts;
CREATE TRIGGER update_posts_updated_at
    BEFORE UPDATE ON posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
