import hashlib
import sqlite3

# 测试密码
password = 'Dw_10086'

# 使用models.py中的哈希方法
def hash_password(password):
    # 添加盐值处理，与models.py中的实现保持一致
    salt = "DataWeaver_salt"
    salted_password = password + salt
    return hashlib.sha256(salted_password.encode()).hexdigest()

# 生成哈希值
generated_hash = hash_password(password)
expected_hash = 'c6ad3ef7c89f434789f0c523bc8d221ed2f04d0f6a133147c12b0e94721b869b'

print(f'密码: {password}')
print(f'生成的哈希值: {generated_hash}')
print(f'预期的哈希值: {expected_hash}')
print(f'匹配结果: {generated_hash == expected_hash}')

# 连接数据库检查用户
try:
    conn = sqlite3.connect('sqlweaver.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, password_hash FROM users WHERE username = 'dwadmin'")
    result = cursor.fetchone()
    if result:
        print(f'\n数据库中的用户信息:')
        print(f'用户名: {result[0]}')
        print(f'密码哈希: {result[1]}')
        print(f'哈希匹配: {result[1] == generated_hash}')
    else:
        print('\n数据库中未找到用户')
    conn.close()
except Exception as e:
    print(f'\n连接数据库时出错: {e}')