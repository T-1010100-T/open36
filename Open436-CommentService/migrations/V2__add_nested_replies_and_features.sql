-- M4 评论互动服务 - V2 扩展迁移
-- 功能：嵌套回复、评论点赞、分享记录、用户关注、话题标签

-- 1. 回复表添加 parent_id（嵌套回复）
ALTER TABLE replies ADD COLUMN IF NOT EXISTS parent_id INTEGER DEFAULT NULL;
COMMENT ON COLUMN replies.parent_id IS '父回复ID（NULL表示顶级回复）';
CREATE INDEX IF NOT EXISTS idx_replies_parent ON replies(parent_id);

-- 2. 评论点赞表
CREATE TABLE IF NOT EXISTS reply_likes (
    id SERIAL PRIMARY KEY,
    reply_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_reply_like UNIQUE (reply_id, user_id)
);
COMMENT ON TABLE reply_likes IS '评论点赞表';
CREATE INDEX IF NOT EXISTS idx_reply_likes_reply ON reply_likes(reply_id);
CREATE INDEX IF NOT EXISTS idx_reply_likes_user ON reply_likes(user_id);

-- 3. 分享记录表
CREATE TABLE IF NOT EXISTS share_records (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    user_id INTEGER,
    share_type VARCHAR(20) NOT NULL DEFAULT 'link',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE share_records IS '分享记录表';
COMMENT ON COLUMN share_records.share_type IS '分享类型：link/weibo/qq/wechat';
CREATE INDEX IF NOT EXISTS idx_share_records_post ON share_records(post_id);
CREATE INDEX IF NOT EXISTS idx_share_records_user ON share_records(user_id);

-- 4. 用户关注关系表
CREATE TABLE IF NOT EXISTS user_follows (
    id SERIAL PRIMARY KEY,
    follower_id INTEGER NOT NULL,
    following_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_follow UNIQUE (follower_id, following_id),
    CONSTRAINT chk_no_self_follow CHECK (follower_id != following_id)
);
COMMENT ON TABLE user_follows IS '用户关注关系表';
CREATE INDEX IF NOT EXISTS idx_user_follows_follower ON user_follows(follower_id);
CREATE INDEX IF NOT EXISTS idx_user_follows_following ON user_follows(following_id);

-- 5. 话题/标签表
CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200) DEFAULT '',
    posts_count INTEGER NOT NULL DEFAULT 0,
    followers_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE topics IS '话题/标签表';

-- 6. 帖子-话题关联表
CREATE TABLE IF NOT EXISTS post_topics (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,

    CONSTRAINT unique_post_topic UNIQUE (post_id, topic_id)
);
COMMENT ON TABLE post_topics IS '帖子-话题关联表';
CREATE INDEX IF NOT EXISTS idx_post_topics_post ON post_topics(post_id);
CREATE INDEX IF NOT EXISTS idx_post_topics_topic ON post_topics(topic_id);

-- 7. 话题关注表
CREATE TABLE IF NOT EXISTS topic_follows (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_topic_follow UNIQUE (user_id, topic_id)
);
COMMENT ON TABLE topic_follows IS '话题关注表';
CREATE INDEX IF NOT EXISTS idx_topic_follows_user ON topic_follows(user_id);
CREATE INDEX IF NOT EXISTS idx_topic_follows_topic ON topic_follows(topic_id);
