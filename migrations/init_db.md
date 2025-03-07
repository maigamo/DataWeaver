# 数据库初始化脚本说明

## 功能概述

`clear_all_db.sql` 脚本用于初始化数据库，主要执行以下操作：

1. 清空所有现有数据表
2. 重置所有表的自增ID
3. 创建超级管理员账户

## 密码加密方式

系统使用 SHA-256 哈希算法对用户密码进行加密存储。这是一种单向加密算法，具有以下特点：

- 不可逆性：无法从哈希值反推出原始密码
- 确定性：相同的输入永远产生相同的哈希值
- 抗碰撞性：不同的输入产生相同哈希值的概率极低

### 示例

初始化脚本中的超级管理员账户设置如下：
- 用户名：dwadmin
- 明文密码：Dw_10086
- 密码哈希值：c6ad3ef7c89f434789f0c523bc8d221ed2f04d0f6a133147c12b0e94721b869b

### 如何生成密码哈希

如果需要为新用户生成密码哈希，可以使用以下方法：

1. Python示例：
```python
import hashlib

def generate_password_hash(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()
```

2. Node.js示例：
```javascript
const crypto = require('crypto');

function generatePasswordHash(password) {
    return crypto.createHash('sha256').update(password).digest('hex');
}
```

## 注意事项

1. 执行此脚本将清空所有现有数据，请在执行前确保数据已备份
2. 初始超级管理员账户创建后，建议立即修改默认密码
3. 在生产环境中，建议使用更强的密码策略，如加盐哈希等