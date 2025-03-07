-- 初始化用户数据
INSERT INTO users (username, password_hash, role, status, created_at)
VALUES (
    'dwadmin',
    'c6ad3ef7c89f434789f0c523bc8d221ed2f04d0f6a133147c12b0e94721b869b',  -- 密码：Dw_10086
    'SUPER_ADMIN',
    'ACTIVE',
    CURRENT_TIMESTAMP
);

-- 添加系统配置，禁止编辑和删除dwadmin用户
INSERT INTO system_configs (config_key, config_value, description)
VALUES ('protected_users', 'dwadmin', '受保护的用户，不允许编辑和删除');