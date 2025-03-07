from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, File, UploadFile, responses, BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path
import os
import shutil
import zipfile
import time
from datetime import datetime, timezone, timedelta
import re
from typing import List, Optional
from pydantic import BaseModel, validator, Field
from models import Database, UserRole
from .auth import get_current_user

router = APIRouter(prefix="/resource-center", tags=["资源共享中心"])
db = Database()

# 创建资源目录
RESOURCE_DIR = Path("resource_center")
RESOURCE_DIR.mkdir(exist_ok=True)

# 定义资源上传请求模型
class ResourceUploadRequest(BaseModel):
    resource_name: str
    
    @validator('resource_name')
    def validate_resource_name(cls, v):
        # 验证资源名称长度（12-256个字符）
        if len(v) < 12 or len(v) > 256:
            raise ValueError('资源名称长度必须在12到256个字符之间')
        # 验证资源名称是否包含非法字符
        if re.search(r'[<>:"/\\|?*]', v):
            raise ValueError('资源名称包含非法字符')
        return v

# 定义资源信息响应模型
class ResourceInfo(BaseModel):
    id: int
    resource_name: str
    file_path: str
    file_size: int
    created_by: int
    created_at: str
    download_count: int = 0
    creator_name: str = ""

# 获取磁盘空间信息
def get_disk_space():
    total, used, free = shutil.disk_usage("/")
    return {
        "total": total,
        "used": used,
        "free": free,
        "total_gb": round(total / (1024**3), 2),
        "used_gb": round(used / (1024**3), 2),
        "free_gb": round(free / (1024**3), 2)
    }

# 检查用户是否有正在进行的下载
def is_user_downloading(user_id: int) -> bool:
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 检查是否有未完成的下载记录
    cursor.execute(
        "SELECT COUNT(*) FROM resource_download_logs WHERE user_id = ? AND status = 'downloading'",
        (user_id,)
    )
    count = cursor.fetchone()[0]
    return count > 0

# 更新下载状态
def update_download_status(log_id: int, status: str, error_message: str = None):
    conn = db.get_connection()
    cursor = conn.cursor()
    
    if error_message:
        cursor.execute(
            "UPDATE resource_download_logs SET status = ?, error_message = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, error_message, log_id)
        )
    else:
        cursor.execute(
            "UPDATE resource_download_logs SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, log_id)
        )
    
    conn.commit()

# 获取资源列表
@router.get("/resources")
async def list_resources(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    search_term: str = Query("", description="搜索关键词"),
    current_user: dict = Depends(get_current_user)
):
    try:
        # 记录查询资源列表操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="查询资源列表",
            operation_detail=f"页码: {page}, 每页数量: {page_size}, 搜索关键词: {search_term}",
            operation_result="成功"
        )
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 构建查询条件
        query = """
        SELECT r.*, u.username as creator_name 
        FROM resources r
        LEFT JOIN users u ON r.created_by = u.id
        """
        params = []
        
        if search_term:
            query += " WHERE r.resource_name LIKE ? "
            params.append(f"%{search_term}%")
        
        # 获取总记录数
        count_query = f"SELECT COUNT(*) FROM ({query})"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # 获取分页数据
        query += " ORDER BY r.created_at DESC LIMIT ? OFFSET ?"
        offset = (page - 1) * page_size
        params.extend([page_size, offset])
        
        cursor.execute(query, params)
        resources = []
        for row in cursor.fetchall():
            resource = dict(row)
            # 转换时间为东八区时间
            created_at = datetime.fromisoformat(resource['created_at'].replace('Z', '+00:00'))
            beijing_time = created_at.astimezone(timezone(timedelta(hours=8)))
            resource['created_at'] = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
            resources.append(resource)
        
        return {
            "resources": resources,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    except Exception as e:
        # 记录查询资源列表失败操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="查询资源列表",
            operation_detail=f"页码: {page}, 每页数量: {page_size}, 搜索关键词: {search_term}",
            operation_result=f"失败: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))

# 上传资源文件
@router.post("/resources")
async def upload_resource(
    resource_name: str = Form(...),
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    # 检查权限
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以上传资源"
        )
    
    # 验证资源名称
    try:
        ResourceUploadRequest(resource_name=resource_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 检查文件数量
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="必须上传至少一个文件")
    
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="最多只能上传5个文件")
    
    # 获取磁盘空间信息
    disk_space = get_disk_space()
    
    # 检查文件大小总和
    total_size = 0
    file_contents = []
    file_names = set()
    
    for file in files:
        # 检查文件名是否重复
        if file.filename in file_names:
            raise HTTPException(status_code=400, detail=f"文件 {file.filename} 重复上传")
        
        file_names.add(file.filename)
        content = await file.read()
        file_contents.append((file.filename, content))
        total_size += len(content)
    
    # 检查总文件大小是否超过500MB
    if total_size > 500 * 1024 * 1024:  # 500MB
        raise HTTPException(status_code=400, detail="上传文件总大小不能超过500MB")
    
    try:
        # 生成唯一的资源文件名
        timestamp = int(time.time())
        resource_folder_name = f"{resource_name}_{timestamp}"
        resource_folder = RESOURCE_DIR / resource_folder_name
        resource_folder.mkdir(exist_ok=True)
        
        # 保存文件
        for filename, content in file_contents:
            file_path = resource_folder / filename
            with open(file_path, "wb") as f:
                f.write(content)
        
        # 创建压缩包
        zip_filename = f"{resource_folder_name}.zip"
        zip_path = RESOURCE_DIR / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for filename, _ in file_contents:
                file_path = resource_folder / filename
                zipf.write(file_path, arcname=filename)
        
        # 删除临时文件夹
        shutil.rmtree(resource_folder)
        
        # 记录资源信息到数据库
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO resources (resource_name, file_path, file_size, created_by)
            VALUES (?, ?, ?, ?)
            """,
            (resource_name, str(zip_path), total_size, current_user["id"])
        )
        
        resource_id = cursor.lastrowid
        conn.commit()
        
        # 记录上传操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="上传资源",
            operation_detail=f"资源名称: {resource_name}, 文件数量: {len(files)}, 总大小: {total_size} 字节",
            operation_result="成功"
        )
        
        return {
            "id": resource_id,
            "resource_name": resource_name,
            "file_size": total_size,
            "disk_space": disk_space,
            "message": "资源上传成功"
        }
    except Exception as e:
        # 记录上传失败操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="上传资源",
            operation_detail=f"资源名称: {resource_name}, 文件数量: {len(files)}",
            operation_result=f"失败: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))

# 下载资源文件
@router.get("/resources/{resource_id}/download")
async def download_resource(
    resource_id: int,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    try:
        # 检查是否启用下载限制
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT config_value FROM system_configs WHERE config_key = 'enable_download_limit'"
        )
        result = cursor.fetchone()
        enable_download_limit = True  # 默认启用限制
        if result and result['config_value'].lower() == 'false':
            enable_download_limit = False
            
        # 只有当启用下载限制时才检查用户是否有正在进行的下载
        if enable_download_limit and is_user_downloading(current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="您有正在进行的下载任务，请等待完成后再下载其他文件"
            )
        
        # 获取资源信息
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM resources WHERE id = ?", (resource_id,))
        resource = cursor.fetchone()
        
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="资源不存在"
            )
        
        resource = dict(resource)
        file_path = Path(resource["file_path"])
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="资源文件不存在"
            )
        
        # 记录下载开始
        cursor.execute(
            """
            INSERT INTO resource_download_logs (user_id, resource_id, status)
            VALUES (?, ?, ?)
            """,
            (current_user["id"], resource_id, "downloading")
        )
        log_id = cursor.lastrowid
        conn.commit()
        
        # 更新下载计数
        cursor.execute(
            "UPDATE resources SET download_count = download_count + 1 WHERE id = ?",
            (resource_id,)
        )
        conn.commit()
        
        # 记录下载操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="下载资源",
            operation_detail=f"资源ID: {resource_id}, 资源名称: {resource['resource_name']}",
            operation_result="成功"
        )
        
        # 设置后台任务在下载完成后更新状态
        def update_after_download():
            update_download_status(log_id, "completed")
        
        background_tasks.add_task(update_after_download)
        
        return responses.FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/zip"
        )
    except HTTPException as e:
        # 对于HTTP异常，直接抛出
        raise e
    except Exception as e:
        # 记录下载失败操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="下载资源",
            operation_detail=f"资源ID: {resource_id}",
            operation_result=f"失败: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))

# 获取全局下载状态
@router.get("/resources/download-status")
async def get_global_download_status(
    current_user: dict = Depends(get_current_user)
):
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 获取用户最近的下载记录
        cursor.execute(
            """
            SELECT * FROM resource_download_logs 
            WHERE user_id = ? AND status = 'downloading'
            ORDER BY created_at DESC LIMIT 1
            """,
            (current_user["id"],)
        )
        
        log = cursor.fetchone()
        
        if not log:
            return {"status": "no_record", "message": "没有正在进行的下载任务"}
        
        log = dict(log)
        
        # 返回下载中状态
        return {"status": "downloading", "message": "正在下载中", "resource_id": log["resource_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 重置用户下载状态（管理接口）
from fastapi import Request


@router.options("/resources/reset-download-status")
async def reset_download_status_options():
    logger.info("收到OPTIONS预检请求")
    return {"message": "OK"}

@router.post("/resources/reset-download-status")
async def reset_download_status(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"收到重置下载状态请求，请求方法：{request.method}，用户：{current_user['username']}")
    
    # 检查权限（只有管理员可以重置下载状态）
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        logger.warning(f"用户权限不足，当前角色：{current_user['role']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以重置下载状态"
        )
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 更新所有下载中状态为失败
        cursor.execute(
            """
            UPDATE resource_download_logs 
            SET status = 'failed', error_message = '管理员手动重置', completed_at = CURRENT_TIMESTAMP 
            WHERE status = 'downloading'
            """
        )
        
        affected_rows = cursor.rowcount
        conn.commit()
        
        # 记录操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="重置下载状态",
            operation_detail=f"影响记录数: {affected_rows}",
            operation_result="成功"
        )
        
        return {"message": f"成功重置 {affected_rows} 条下载记录", "affected_rows": affected_rows}
    except Exception as e:
        # 记录操作失败
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="重置下载状态",
            operation_detail="重置所有下载中状态",
            operation_result=f"失败: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))

# 获取特定资源的下载状态
@router.get("/resources/{resource_id}/download-status")
async def get_download_status(
    resource_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 获取最近的下载记录
        cursor.execute(
            """
            SELECT * FROM resource_download_logs 
            WHERE user_id = ? AND resource_id = ? 
            ORDER BY created_at DESC LIMIT 1
            """,
            (current_user["id"], resource_id)
        )
        
        log = cursor.fetchone()
        
        if not log:
            return {"status": "no_record", "message": "没有下载记录"}
        
        log = dict(log)
        
        # 如果下载失败，返回失败信息和重试选项
        if log["status"] == "failed":
            return {
                "status": "failed",
                "message": "下载失败",
                "error_message": log["error_message"],
                "can_retry": True
            }
        
        # 如果正在下载，返回下载中状态
        if log["status"] == "downloading":
            return {"status": "downloading", "message": "正在下载中"}
        
        # 如果已完成，返回完成状态
        return {"status": "completed", "message": "下载已完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 删除资源
@router.delete("/resources/{resource_id}")
async def delete_resource(
    resource_id: int,
    current_user: dict = Depends(get_current_user)
):
    # 检查权限（只有超级管理员可以删除资源）
    if current_user["role"] != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以删除资源"
        )
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 获取资源信息
        cursor.execute("SELECT * FROM resources WHERE id = ?", (resource_id,))
        resource = cursor.fetchone()
        
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="资源不存在"
            )
        
        resource = dict(resource)
        file_path = Path(resource["file_path"])
        
        try:
            # 删除文件
            if file_path.exists():
                try:
                    file_path.unlink()
                except PermissionError:
                    logger.error(f"删除文件失败：权限不足 - {file_path}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="删除文件失败：权限不足"
                    )
                except OSError as e:
                    logger.error(f"删除文件失败：{str(e)} - {file_path}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"删除文件失败：{str(e)}"
                    )
            else:
                logger.warning(f"文件不存在，仅删除数据库记录 - {file_path}")
            
            # 先删除资源下载日志
            cursor.execute("DELETE FROM resource_download_logs WHERE resource_id = ?", (resource_id,))
            
            # 删除资源记录
            cursor.execute("DELETE FROM resources WHERE id = ?", (resource_id,))
            conn.commit()
            
            # 记录删除操作
            db.log_user_operation(
                user_id=current_user["id"],
                operation_type="删除资源",
                operation_detail=f"资源ID: {resource_id}, 资源名称: {resource['resource_name']}",
                operation_result="成功"
            )
            
            return {"message": "资源删除成功"}
        except Exception as e:
            # 发生错误时回滚数据库操作
            conn.rollback()
            raise e
            
    except HTTPException as e:
        raise e
    except Exception as e:
        # 记录删除失败操作
        error_msg = str(e)
        logger.error(f"删除资源失败：{error_msg}")
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="删除资源",
            operation_detail=f"资源ID: {resource_id}",
            operation_result=f"失败: {error_msg}"
        )
        raise HTTPException(status_code=500, detail=error_msg)

# 获取磁盘空间信息接口
@router.get("/disk-space")
async def get_disk_space_info(
    current_user: dict = Depends(get_current_user)
):
    try:
        # 记录查询磁盘空间信息操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="查询磁盘空间信息",
            operation_detail="获取磁盘空间使用情况",
            operation_result="成功"
        )
        
        return get_disk_space()
    except Exception as e:
        # 记录查询失败操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="查询磁盘空间信息",
            operation_detail="获取磁盘空间使用情况",
            operation_result=f"失败: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))