# DataWeaver 数据库初始化说明

本文档详细说明了如何从零开始初始化 DataWeaver 的数据库。

## 数据库初始化步骤

1. 确保已安装 SQLite3
   ```bash
   # 检查 SQLite3 是否已安装
   sqlite3 --version
   ```

2. 创建数据库文件
   ```bash
   # 在项目根目录下创建 data 目录（如果不存在）
   mkdir -p data
   
   # 创建数据库文件
   sqlite3 data/dataweaver.db
   ```

3. 执行初始化脚本
   ```bash
   # 在 SQLite 命令行中执行
   sqlite3 data/dataweaver.db < migrations/init.sql
   ```

## 数据库表结构说明

### users 表
- 用户信息表，存储系统用户数据
- 包含用户名、密码哈希、角色、状态等信息
- 主键：id（自增）

### documents 表
- 文档信息表，存储系统中的文档
- 包含标题、内容、分类、状态等信息
- 外键关联：category_id -> document_categories(id)
- 外键关联：created_by -> users(id)

### document_categories 表
- 文档分类表，支持多级分类
- 包含分类名称、描述、父级分类等信息
- 外键关联：parent_id -> document_categories(id)（自关联）

### tags 表
- 标签表，存储文档标签
- 包含标签名称、描述等信息

### document_tags 表
- 文档标签关联表，实现文档和标签的多对多关系
- 外键关联：document_id -> documents(id)
- 外键关联：tag_id -> tags(id)

### resources 表
- 资源文件表，存储上传的文件信息
- 包含文件名、路径、大小、类型等信息
- 外键关联：created_by -> users(id)

### resource_download_logs 表
- 资源下载日志表，记录资源下载历史
- 外键关联：resource_id -> resources(id)
- 外键关联：user_id -> users(id)

### user_operation_logs 表
- 用户操作日志表，记录用户的操作历史
- 外键关联：user_id -> users(id)

### download_logs 表
- 下载日志表，记录系统中的下载操作
- 外键关联：user_id -> users(id)

### script_generation_logs 表
- 脚本生成日志表，记录脚本生成历史
- 外键关联：user_id -> users(id)

### system_configs 表
- 系统配置表，存储系统级配置信息
- 包含配置键值对和描述信息

## 初始用户信息

系统初始化时会创建一个超级管理员用户：
- 用户名：dwadmin
- 密码：Dw_10086
- 角色：超级管理员
- 状态：启用

## 注意事项

1. 初始化数据库前请确保：
   - SQLite3 已正确安装
   - 有足够的磁盘空间
   - 对目标目录有写入权限

2. 安全建议：
   - 首次登录后请立即修改超级管理员密码
   - 定期备份数据库文件
   - 妥善保管数据库文件，避免未授权访问

3. 维护建议：
   - 定期清理日志表数据
   - 监控数据库文件大小
   - 保持数据库文件的定期备份