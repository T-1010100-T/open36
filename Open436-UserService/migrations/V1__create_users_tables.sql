-- M2 用户管理服务 - 初始数据库迁移
-- 创建用户资料表和用户统计表

-- 创建触发器函数（如果不存在）
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 1. 用户资料表
CREATE TABLE IF NOT EXISTS users_profile (
    user_id INTEGER PRIMARY KEY,
    nickname VARCHAR(20) NOT NULL,
    avatar_url VARCHAR(500),
    bio TEXT,
    nickname_updated_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_nickname_length CHECK (LENGTH(nickname) >= 2 AND LENGTH(nickname) <= 20),
    CONSTRAINT chk_bio_length CHECK (bio IS NULL OR LENGTH(bio) <= 200)
);

-- 添加注释
COMMENT ON TABLE users_profile IS '用户资料表';
COMMENT ON COLUMN users_profile.user_id IS '用户ID（主键，关联 M1 的 users_auth.id）';
COMMENT ON COLUMN users_profile.nickname IS '昵称（2-20字符）';
COMMENT ON COLUMN users_profile.avatar_url IS '头像URL（存储在 M7 文件服务）';
COMMENT ON COLUMN users_profile.bio IS '个人简介（最大200字符）';
COMMENT ON COLUMN users_profile.nickname_updated_at IS '昵称最后修改时间（用于30天限制）';
COMMENT ON COLUMN users_profile.created_at IS '创建时间';
COMMENT ON COLUMN users_profile.updated_at IS '更新时间';

-- 2. 用户统计表
CREATE TABLE IF NOT EXISTS user_statistics (
    user_id INTEGER PRIMARY KEY,
    posts_count INTEGER NOT NULL DEFAULT 0,
    replies_count INTEGER NOT NULL DEFAULT 0,
    likes_received INTEGER NOT NULL DEFAULT 0,
    favorites_received INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user FOREIGN KEY (user_id)
        REFERENCES users_profile(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_posts_count CHECK (posts_count >= 0),
    CONSTRAINT chk_replies_count CHECK (replies_count >= 0),
    CONSTRAINT chk_likes_received CHECK (likes_received >= 0),
    CONSTRAINT chk_favorites_received CHECK (favorites_received >= 0)
);

-- 添加注释
COMMENT ON TABLE user_statistics IS '用户统计表';
COMMENT ON COLUMN user_statistics.user_id IS '用户ID（主键，外键）';
COMMENT ON COLUMN user_statistics.posts_count IS '发帖数';
COMMENT ON COLUMN user_statistics.replies_count IS '回复数';
COMMENT ON COLUMN user_statistics.likes_received IS '获赞总数';
COMMENT ON COLUMN user_statistics.favorites_received IS '获收藏总数';
COMMENT ON COLUMN user_statistics.updated_at IS '更新时间';

-- 3. 索引
CREATE INDEX IF NOT EXISTS idx_users_profile_nickname ON users_profile(nickname);
CREATE INDEX IF NOT EXISTS idx_users_profile_created_at ON users_profile(created_at);
CREATE INDEX IF NOT EXISTS idx_users_profile_updated_at ON users_profile(updated_at);

CREATE INDEX IF NOT EXISTS idx_user_statistics_posts_count ON user_statistics(posts_count DESC);
CREATE INDEX IF NOT EXISTS idx_user_statistics_likes_received ON user_statistics(likes_received DESC);

-- 4. 触发器（自动更新 updated_at）
DROP TRIGGER IF EXISTS update_users_profile_updated_at ON users_profile;
CREATE TRIGGER update_users_profile_updated_at
    BEFORE UPDATE ON users_profile
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_statistics_updated_at ON user_statistics;
CREATE TRIGGER update_user_statistics_updated_at
    BEFORE UPDATE ON user_statistics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
