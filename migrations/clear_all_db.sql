-- 创建system_configs表
CREATE TABLE IF NOT EXISTS system_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 清空现有数据
DELETE FROM document_tags;
DELETE FROM tags;
DELETE FROM documents;
DELETE FROM document_categories;
DELETE FROM resource_download_logs;
DELETE FROM resources;
DELETE FROM user_operation_logs;
DELETE FROM download_logs;
DELETE FROM script_generation_logs;
DELETE FROM users;
DELETE FROM system_configs;

-- 重置自增ID
DELETE FROM sqlite_sequence;

-- 初始化用户数据
INSERT INTO users (username, password_hash, role, status, created_at)
VALUES (
    'dwadmin',
    '189ea6748354d8a1c3e418b3a9fd13af517ad7ce96f2ed8b0f0a89ac78c964fb',  -- 密码：Dw_10086
    '超级管理员',
    '启用',
    CURRENT_TIMESTAMP
);