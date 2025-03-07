from fastapi import APIRouter, Depends, HTTPException, status, Query
from models import Database, UserRole
from .auth import get_current_user
from datetime import datetime, timedelta

router = APIRouter(tags=["统计信息"])
db = Database()

# 统计信息接口
@router.get("/statistics")
async def get_statistics(
    start_date: str = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: str = Query(None, description="结束日期，格式：YYYY-MM-DD"),
    current_user: dict = Depends(get_current_user)
):
    # 检查权限
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看统计信息"
        )
    
    try:
        # 获取统计信息
        statistics = db.get_statistics(start_date, end_date)
        return statistics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 获取数据生成历史记录
@router.get("/generation-history")
async def get_generation_history(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    branch: str = Query(None, description="分支名称"),
    current_user: dict = Depends(get_current_user)
):
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        query = """SELECT 
            s.id, s.user_id, u.username, s.branch, s.file_name, s.created_at,
            s.user_start_index, s.user_max_index, s.department_index, s.users_per_department,
            s.device_start_index, s.device_max_index
            FROM script_generation_logs s
            LEFT JOIN users u ON s.user_id = u.id
        """
        
        params = []
        where_clauses = []
        
        # 如果指定了分支，添加过滤条件
        if branch:
            where_clauses.append("s.branch = ?")
            params.append(branch)
        
        # 添加WHERE子句
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        # 获取总记录数
        count_query = f"SELECT COUNT(*) FROM ({query})"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # 添加排序和分页
        query += " ORDER BY s.created_at DESC LIMIT ? OFFSET ?"
        offset = (page - 1) * page_size
        params.extend([page_size, offset])
        
        cursor.execute(query, params)
        records = [dict(row) for row in cursor.fetchall()]
        
        return {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
            "records": records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 获取生成趋势数据
@router.get("/statistics/trend")
async def get_trend_statistics(
    time_range: str = Query(..., description="时间范围，可选值：7/30/90/monthly"),
    current_user: dict = Depends(get_current_user)
):
    # 检查权限
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看统计信息"
        )
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        if time_range == "monthly":
            # 按月统计
            query = """
                SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count 
                FROM script_generation_logs 
                GROUP BY month 
                ORDER BY month DESC
                LIMIT 12
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return {"monthly": [dict(row) for row in results]}
        else:
            # 按天统计
            days = int(time_range)
            query = """
                SELECT date(created_at) as date, COUNT(*) as count 
                FROM script_generation_logs 
                WHERE date(created_at) >= date(?) 
                GROUP BY date 
                ORDER BY date DESC
            """
            cursor.execute(query, (datetime.now() - timedelta(days=days),))
            results = cursor.fetchall()
            return {"daily": [dict(row) for row in results]}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 获取下载趋势数据
@router.get("/statistics/download")
async def get_download_statistics(
    time_range: str = Query(..., description="时间范围，可选值：7/30/90/monthly"),
    current_user: dict = Depends(get_current_user)
):
    # 检查权限
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看统计信息"
        )
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        if time_range == "monthly":
            # 按月统计
            query = """
                SELECT month, SUM(count) as count FROM (
                    SELECT strftime('%Y-%m', downloaded_at) as month, COUNT(*) as count 
                    FROM download_logs 
                    GROUP BY month
                    UNION ALL
                    SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count 
                    FROM resource_download_logs 
                    GROUP BY month
                ) 
                GROUP BY month 
                ORDER BY month DESC
                LIMIT 12
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return {"monthly": [dict(row) for row in results]}
        else:
            # 按天统计
            days = int(time_range)
            query = """
                SELECT date, SUM(count) as count FROM (
                    SELECT date(downloaded_at) as date, COUNT(*) as count 
                    FROM download_logs 
                    WHERE date(downloaded_at) >= date(?)
                    GROUP BY date
                    UNION ALL
                    SELECT date(created_at) as date, COUNT(*) as count 
                    FROM resource_download_logs 
                    WHERE date(created_at) >= date(?)
                    GROUP BY date
                ) 
                GROUP BY date 
                ORDER BY date DESC
            """
            date_param = datetime.now() - timedelta(days=days)
            cursor.execute(query, (date_param, date_param))
            results = cursor.fetchall()
            return {"daily": [dict(row) for row in results]}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))