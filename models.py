import sqlite3
import os
import hashlib
import time
from datetime import datetime
from pathlib import Path
from enum import Enum, auto
from threading import local

# 数据库文件路径
DB_PATH = "sqlweaver.db"

# 用户角色枚举
class UserRole(Enum):
    OPERATOR = "操作员"         # 可点击生成sql与下载sql
    NORMAL_USER = "普通用户"    # 只能下载文件
    ADMIN = "普通管理员"        # 可点击生成sql与下载sql与查询统计信息
    SUPER_ADMIN = "超级管理员"  # 拥有所有权限

# 用户状态枚举
class UserStatus(Enum):
    ACTIVE = "启用"
    DISABLED = "禁用"

class Database:
    _thread_local = local()
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        if not hasattr(self._thread_local, 'conn') or self._thread_local.conn is None:
            self._thread_local.conn = sqlite3.connect(self.db_path)
            # 启用外键约束
            self._thread_local.conn.execute("PRAGMA foreign_keys = ON")
            # 设置行工厂，返回字典而不是元组
            self._thread_local.conn.row_factory = sqlite3.Row
        return self._thread_local.conn
    
    def close(self):
        if hasattr(self._thread_local, 'conn') and self._thread_local.conn:
            self._thread_local.conn.close()
            self._thread_local.conn = None
    
    def init_db(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        ''')
        
        # 创建生成脚本日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS script_generation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            branch TEXT NOT NULL,
            user_start_index INTEGER NOT NULL,
            user_max_index INTEGER NOT NULL,
            department_index INTEGER NOT NULL,
            users_per_department INTEGER NOT NULL,
            device_start_index INTEGER NOT NULL,
            device_max_index INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # 创建下载日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS download_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            downloaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # 创建用户操作日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            operation_type TEXT NOT NULL,
            operation_detail TEXT,
            operation_result TEXT,
            ip_address TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # 创建资源表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            created_by INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            download_count INTEGER DEFAULT 0,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
        ''')
        
        # 创建资源下载日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS resource_download_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            resource_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (resource_id) REFERENCES resources (id)
        )
        ''')
        
        # 创建分支管理表
        # 创建文档分类表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_by INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
        ''')
        
        # 创建文档表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            file_type TEXT NOT NULL,
            uploaded_by INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            download_count INTEGER DEFAULT 0,
            expiration_date DATETIME,
            FOREIGN KEY (category_id) REFERENCES document_categories (id),
            FOREIGN KEY (uploaded_by) REFERENCES users (id)
        )
        ''')
        
        # 创建标签表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建文档标签关联表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_tags (
            document_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (document_id, tag_id),
            FOREIGN KEY (document_id) REFERENCES documents (id),
            FOREIGN KEY (tag_id) REFERENCES tags (id)
        )
        ''')
        
        # 创建存储空间统计表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS storage_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_space INTEGER NOT NULL,
            used_space INTEGER NOT NULL,
            warning_threshold INTEGER NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('DROP TABLE IF EXISTS branches')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_by INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 检查是否需要创建默认超级管理员账户
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = ?", (UserRole.SUPER_ADMIN.value,))
        if cursor.fetchone()[0] == 0:
            # 创建默认超级管理员账户 (用户名: admin, 密码: admin123)
            self.create_user("admin", "admin123", UserRole.SUPER_ADMIN.value)
        
        conn.commit()
    
    def _hash_password(self, password):
        """对密码进行哈希处理"""
        # 使用简单的SHA-256哈希，添加盐值增强安全性
        salt = "DataWeaver_salt"
        salted_password = password + salt
        return hashlib.sha256(salted_password.encode()).hexdigest()
    
    def create_user(self, username, password, role, status=UserStatus.ACTIVE.value):
        """创建新用户"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 密码哈希
        password_hash = self._hash_password(password)
        
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, status) VALUES (?, ?, ?, ?)",
                (username, password_hash, role, status)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            conn.rollback()
            return None
    
    def update_user(self, user_id, username=None, password=None, role=None, status=None):
        """更新用户信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 获取当前用户信息
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return False
        
        # 准备更新数据
        update_data = {}
        if username is not None:
            update_data['username'] = username
        if password is not None:
            update_data['password_hash'] = self._hash_password(password)
        if role is not None:
            update_data['role'] = role
        if status is not None:
            update_data['status'] = status
        
        if not update_data:
            return True  # 没有需要更新的数据
        
        # 构建更新SQL
        set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
        values = list(update_data.values())
        values.append(user_id)
        
        try:
            cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return True
        except sqlite3.Error:
            conn.rollback()
            return False
    
    def delete_user(self, user_id):
        """删除用户及其相关数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 首先删除用户相关的操作日志
            cursor.execute("DELETE FROM user_operation_logs WHERE user_id = ?", (user_id,))
            
            # 删除用户的脚本生成记录
            cursor.execute("DELETE FROM script_generation_logs WHERE user_id = ?", (user_id,))
            
            # 删除用户的下载记录
            cursor.execute("DELETE FROM download_logs WHERE user_id = ?", (user_id,))
            
            # 删除用户的资源下载记录
            cursor.execute("DELETE FROM resource_download_logs WHERE user_id = ?", (user_id,))
            
            # 删除用户创建的资源
            cursor.execute("DELETE FROM resources WHERE created_by = ?", (user_id,))
            
            # 删除用户创建的文档
            cursor.execute("DELETE FROM documents WHERE uploaded_by = ?", (user_id,))
            
            # 删除用户创建的文档分类
            cursor.execute("DELETE FROM document_categories WHERE created_by = ?", (user_id,))
            
            # 最后删除用户本身
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Error deleting user: {e}")
            return False
    
    def get_user(self, username):
        """根据用户名获取用户信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user:
            return dict(user)
        return None
    
    def get_user_by_id(self, user_id):
        """根据ID获取用户信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if user:
            return dict(user)
        return None
    
    def get_all_users(self, page=1, page_size=10, search_term=None):
        """获取所有用户（分页）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        offset = (page - 1) * page_size
        
        query = "SELECT * FROM users"
        params = []
        
        if search_term:
            query += " WHERE username LIKE ?"
            params.append(f"%{search_term}%")
        
        # 获取总记录数
        count_query = f"SELECT COUNT(*) FROM ({query})"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # 获取分页数据
        query += " ORDER BY id LIMIT ? OFFSET ?"
        params.extend([page_size, offset])
        
        cursor.execute(query, params)
        users = [dict(row) for row in cursor.fetchall()]
        
        return {
            "users": users,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    
    def verify_password(self, username, password):
        """验证用户密码"""
        user = self.get_user(username)
        if not user:
            return False
        
        # 检查用户状态
        if user['status'] != UserStatus.ACTIVE.value:
            return False
        
        # 验证密码
        password_hash = self._hash_password(password)
        if user['password_hash'] == password_hash:
            # 更新最后登录时间
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user['id'],)
            )
            conn.commit()
            return True
        
        return False
        
    def authenticate_user(self, username, password):
        """验证用户凭据并返回用户信息"""
        # 获取用户信息
        user = self.get_user(username)
        if not user:
            return None
            
        # 验证密码
        if self.verify_password(username, password):
            return user
        
        return None
    
    def log_script_generation(self, user_id, branch, user_start_index, user_max_index, 
                             department_index, users_per_department, 
                             device_start_index, device_max_index, file_name):
        """记录脚本生成日志"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """INSERT INTO script_generation_logs 
                (user_id, branch, user_start_index, user_max_index, department_index, 
                users_per_department, device_start_index, device_max_index, file_name) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, branch, user_start_index, user_max_index, department_index, 
                users_per_department, device_start_index, device_max_index, file_name)
            )
            conn.commit()
            return True
        except sqlite3.Error:
            conn.rollback()
            return False
    
    def log_download(self, user_id, file_name):
        """记录文件下载日志"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO download_logs (user_id, file_name) VALUES (?, ?)",
                (user_id, file_name)
            )
            conn.commit()
            return True
        except sqlite3.Error:
            conn.rollback()
            return False
    
    def log_user_operation(self, user_id, operation_type, operation_detail=None, operation_result=None, ip_address=None):
        """记录用户操作日志"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """INSERT INTO user_operation_logs 
                (user_id, operation_type, operation_detail, operation_result, ip_address) 
                VALUES (?, ?, ?, ?, ?)""",
                (user_id, operation_type, operation_detail, operation_result, ip_address)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            conn.rollback()
            print(f"[ERROR] 记录用户操作失败 - user_id: {user_id}, operation_type: {operation_type}")
            print(f"[ERROR] 错误详情: {str(e)}")
            return False
    
    def add_branch(self, name, description, created_by):
        """添加新分支"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO branches (name, description, created_by) VALUES (?, ?, ?)",
                (name, description, created_by)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            conn.rollback()
            return None
    
    def get_statistics(self, start_date=None, end_date=None):
        """获取统计信息"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 设置默认日期范围为所有历史记录
        if not start_date:
            start_date = "1970-01-01"
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d 23:59:59")
        
        # 脚本生成次数
        cursor.execute(
            "SELECT COUNT(*) FROM script_generation_logs WHERE created_at BETWEEN ? AND ?",
            (start_date, end_date)
        )
        generation_count = cursor.fetchone()[0]
        
        # 下载次数（包括SQL脚本下载和资源中心文件下载）
        cursor.execute(
            """SELECT COUNT(*) FROM (
                SELECT downloaded_at FROM download_logs WHERE downloaded_at BETWEEN ? AND ?
                UNION ALL
                SELECT created_at as downloaded_at FROM resource_download_logs WHERE created_at BETWEEN ? AND ?
            )""",
            (start_date, end_date, start_date, end_date)
        )
        download_count = cursor.fetchone()[0]
        
        # 服务用户数
        cursor.execute(
            """SELECT COUNT(DISTINCT user_id) FROM (
                SELECT user_id FROM script_generation_logs WHERE created_at BETWEEN ? AND ?
                UNION
                SELECT user_id FROM download_logs WHERE downloaded_at BETWEEN ? AND ?
            )""",
            (start_date, end_date, start_date, end_date)
        )
        user_count = cursor.fetchone()[0]
        
        # 分支使用情况
        cursor.execute(
            """SELECT branch, COUNT(*) as count FROM script_generation_logs 
            WHERE created_at BETWEEN ? AND ? GROUP BY branch ORDER BY count DESC""",
            (start_date, end_date)
        )
        branch_usage = [dict(row) for row in cursor.fetchall()]
        
        # 按月统计生成和下载次数（用于图表展示）
        cursor.execute(
            """SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count 
            FROM script_generation_logs WHERE created_at BETWEEN ? AND ? 
            GROUP BY month ORDER BY month""",
            (start_date, end_date)
        )
        monthly_generations = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute(
            """SELECT month, SUM(count) as count FROM (
                SELECT strftime('%Y-%m', downloaded_at) as month, COUNT(*) as count 
                FROM download_logs WHERE downloaded_at BETWEEN ? AND ? 
                GROUP BY month
                UNION ALL
                SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count 
                FROM resource_download_logs WHERE created_at BETWEEN ? AND ? 
                GROUP BY month
            ) GROUP BY month ORDER BY month""",
            (start_date, end_date, start_date, end_date)
        )
        monthly_downloads = [dict(row) for row in cursor.fetchall()]
        
        return {
            "generation_count": generation_count,
            "download_count": download_count,
            "user_count": user_count,
            "branch_usage": branch_usage,
            "monthly_statistics": {
                "generations": monthly_generations,
                "downloads": monthly_downloads
            }
        }
    
    # 第二个log_user_operation函数已删除，使用上面定义的函数

    def get_operation_logs(self, page=1, page_size=10, start_date=None, end_date=None, user_id=None, username=None, operation_type=None):
        """获取所有操作记录（分页）
        包括用户操作日志、脚本生成记录和文件下载记录
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 设置默认日期范围
        if not start_date:
            start_date = "1970-01-01"
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d 23:59:59")
        
        # 构建查询条件
        where_conditions = ["s.created_at BETWEEN ? AND ?"]
        params = [start_date, end_date]
        
        if user_id:
            where_conditions.append("s.user_id = ?")
            params.append(user_id)
            
        if username:
            where_conditions.append("u.username = ?")
            params.append(username)
            
        if operation_type:
            where_conditions.append("operation_type = ?")
            params.append(operation_type)
        
        where_clause = " AND ".join(where_conditions)
        
        # 构建用户操作日志查询 - 排除已在专用表中记录的下载和脚本生成操作
        user_op_query = f"""
            SELECT 
                operation_type,
                s.id,
                s.user_id,
                u.username,
                NULL as branch,
                operation_detail as file_name,
                s.created_at as operation_time,
                NULL as user_start_index,
                NULL as user_max_index,
                NULL as department_index,
                NULL as users_per_department,
                NULL as device_start_index,
                NULL as device_max_index,
                NULL as downloaded_at
            FROM user_operation_logs s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE {where_clause} AND operation_type NOT IN ('download', 'script_generation')
        """
        
        # 构建脚本生成记录查询
        gen_query = f"""
            SELECT 
                'script_generation' as operation_type,
                s.id,
                s.user_id,
                u.username,
                s.branch,
                s.file_name,
                s.created_at as operation_time,
                s.user_start_index,
                s.user_max_index,
                s.department_index,
                s.users_per_department,
                s.device_start_index,
                s.device_max_index,
                NULL as downloaded_at
            FROM script_generation_logs s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE {where_clause}
        """
        
        # 构建文件下载记录查询
        download_where_conditions = ["downloaded_at BETWEEN ? AND ?"]
        download_params = [start_date, end_date]
        
        if user_id:
            download_where_conditions.append("d.user_id = ?")
            download_params.append(user_id)
            
        if username:
            download_where_conditions.append("u.username = ?")
            download_params.append(username)
            
        if operation_type and operation_type == 'download':
            # 如果指定了操作类型为download，这里不需要额外条件，因为这个查询本身就是download类型
            pass
        elif operation_type:
            # 如果指定了其他操作类型，则这个查询不应返回任何结果
            download_where_conditions.append("1=0")
        
        download_where_clause = " AND ".join(download_where_conditions)
        
        download_query = f"""
            SELECT 
                'download' as operation_type,
                d.id,
                d.user_id,
                u.username,
                NULL as branch,
                d.file_name,
                d.downloaded_at as operation_time,
                NULL as user_start_index,
                NULL as user_max_index,
                NULL as department_index,
                NULL as users_per_department,
                NULL as device_start_index,
                NULL as device_max_index,
                d.downloaded_at
            FROM download_logs d
            LEFT JOIN users u ON d.user_id = u.id
            WHERE {download_where_clause}
        """
        
        # 合并查询并按时间排序
        union_query = f"""
            SELECT * FROM (
                {user_op_query}
                UNION ALL
                {gen_query}
                UNION ALL
                {download_query}
            ) ORDER BY operation_time DESC
        """
        
        # 获取总记录数
        count_query = f"SELECT COUNT(*) FROM ({union_query})"
        cursor.execute(count_query, params + params + download_params)
        total_count = cursor.fetchone()[0]
        
        # 添加分页
        offset = (page - 1) * page_size
        paginated_query = f"{union_query} LIMIT ? OFFSET ?"
        cursor.execute(paginated_query, params + params + download_params + [page_size, offset])
        
        logs = [dict(row) for row in cursor.fetchall()]
        
        return {
            "logs": logs,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    
    def add_document_category(self, name, description, created_by):
        """添加文档分类"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO document_categories (name, description, created_by) VALUES (?, ?, ?)",
                (name, description, created_by)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            conn.rollback()
            return None
    
    def get_document_categories(self, page=1, page_size=10, search_term=None):
        """获取文档分类列表（分页）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        offset = (page - 1) * page_size
        query = "SELECT c.*, u.username as creator_name FROM document_categories c LEFT JOIN users u ON c.created_by = u.id"
        params = []
        
        if search_term:
            query += " WHERE c.name LIKE ? OR c.description LIKE ?"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        # 获取总记录数
        count_query = f"SELECT COUNT(*) FROM ({query})"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # 获取分页数据
        query += " ORDER BY c.created_at DESC LIMIT ? OFFSET ?"
        params.extend([page_size, offset])
        
        cursor.execute(query, params)
        categories = [dict(row) for row in cursor.fetchall()]
        
        return {
            "categories": categories,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    
    def add_document(self, title, description, category_id, file_path, file_size, file_type, uploaded_by):
        """添加文档"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """INSERT INTO documents 
                (title, description, category_id, file_path, file_size, file_type, uploaded_by) 
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (title, description, category_id, file_path, file_size, file_type, uploaded_by)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error:
            conn.rollback()
            return None
    
    def get_documents(self, page=1, page_size=10, category_id=None, search_term=None):
        """获取文档列表（分页）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        offset = (page - 1) * page_size
        query = """SELECT d.*, c.name as category_name, u.username as uploader_name 
                   FROM documents d 
                   LEFT JOIN document_categories c ON d.category_id = c.id 
                   LEFT JOIN users u ON d.uploaded_by = u.id"""
        params = []
        
        conditions = []
        if category_id:
            conditions.append("d.category_id = ?")
            params.append(category_id)
        if search_term:
            conditions.append("(d.title LIKE ? OR d.description LIKE ?)")
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # 获取总记录数
        count_query = f"SELECT COUNT(*) FROM ({query})"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # 获取分页数据
        query += " ORDER BY d.created_at DESC LIMIT ? OFFSET ?"
        params.extend([page_size, offset])
        
        cursor.execute(query, params)
        documents = [dict(row) for row in cursor.fetchall()]
        
        return {
            "documents": documents,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    
    def update_document_download_count(self, document_id):
        """更新文档下载次数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE documents SET download_count = download_count + 1 WHERE id = ?",
                (document_id,)
            )
            conn.commit()
            return True
        except sqlite3.Error:
            conn.rollback()
            return False

def check_expired_files(self):
    """检查并删除过期文件"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    current_time = datetime.now()
    cursor.execute(
        "SELECT id, file_path FROM documents WHERE expiration_date <= ?",
        (current_time,)
    )
    expired_files = cursor.fetchall()
    
    for file in expired_files:
        file_path = file['file_path']
        if os.path.exists(file_path):
            os.remove(file_path)
        
        cursor.execute("DELETE FROM documents WHERE id = ?", (file['id'],))
        cursor.execute("DELETE FROM document_tags WHERE document_id = ?", (file['id'],))
    
    conn.commit()

def add_tag(self, tag_name):
    """添加新标签"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.rollback()
        return None

def add_tag_to_document(self, document_id, tag_id):
    """为文档添加标签"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO document_tags (document_id, tag_id) VALUES (?, ?)",
            (document_id, tag_id)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        conn.rollback()
        return False

def update_storage_statistics(self, total_space, used_space, warning_threshold):
    """更新存储空间统计信息"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """INSERT OR REPLACE INTO storage_statistics 
        (id, total_space, used_space, warning_threshold, updated_at) 
        VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)""",
        (total_space, used_space, warning_threshold)
    )
    conn.commit()

def get_storage_statistics(self):
    """获取存储空间统计信息"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM storage_statistics WHERE id = 1")
    stats = cursor.fetchone()
    
    if stats:
        return dict(stats)
    return None