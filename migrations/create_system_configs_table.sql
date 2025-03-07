-- 创建系统配置表
CREATE TABLE IF NOT EXISTS system_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入一些基础配置
INSERT INTO system_configs (config_key, config_value, description) VALUES
('max_upload_size', '10485760', '最大上传文件大小（字节）'),
('allowed_file_types', '.pdf,.doc,.docx,.xls,.xlsx,.txt', '允许上传的文件类型'),
('resource_path', '/resource_center', '资源文件存储路径'),
('enable_user_registration', 'true', '是否允许用户注册'),
('enable_download_limit', 'false', '是否启用用户下载限制功能');

