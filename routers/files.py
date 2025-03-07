from fastapi import APIRouter, HTTPException, status, Query, responses, Depends, Path
from pathlib import Path as PathLib
from datetime import datetime
from routers.auth import get_current_user
from models import Database

router = APIRouter(tags=["文件管理"])

# 数据库实例
db = Database()

# 获取生成的文件列表
@router.get("/files")
async def list_files(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search_term: str = Query("", max_length=100, description="搜索关键词"),
    current_user: dict = Depends(get_current_user)
):
    try:
        # 记录查询文件列表操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="查询文件列表",
            operation_detail=f"页码: {page}, 每页数量: {page_size}, 搜索关键词: {search_term}",
            operation_result="成功"
        )
        
        # 获取output目录下的所有zip文件
        output_dir = PathLib("output")
        files = [f for f in output_dir.glob("*.zip") if f.is_file()]
        
        # 如果有搜索关键词，进行过滤
        if search_term:
            files = [f for f in files if search_term.lower() in f.name.lower()]
        
        # 按修改时间倒序排序
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # 计算总页数和分页数据
        total = len(files)
        total_pages = (total + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # 获取当前页的文件
        current_page_files = files[start_idx:end_idx]
        
        # 构建文件信息列表
        file_list = [{
            "name": f.name,
            "size": f.stat().st_size,
            "created_at": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "download_url": f"/download/{f.name}"
        } for f in current_page_files]
        
        return {
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
            "files": file_list
        }
    except Exception as e:
        # 记录查询文件列表失败操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="查询文件列表",
            operation_detail=f"页码: {page}, 每页数量: {page_size}, 搜索关键词: {search_term}",
            operation_result=f"失败: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))

# 文件下载接口
@router.get("/download/{file_name:path}")
async def download_file(file_name: str = Path(max_length=255), current_user: dict = Depends(get_current_user)):
    try:
        # 获取文件的完整路径
        output_dir = PathLib("output")
        file_path = output_dir / file_name
        
        # 检查文件是否存在
        if not file_path.exists() or not file_path.is_file():
            # 记录文件下载失败操作
            db.log_user_operation(
                user_id=current_user["id"],
                operation_type="下载文件",
                operation_detail=f"文件名: {file_name}",
                operation_result="失败: 文件不存在"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 记录文件下载操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="下载文件",
            operation_detail=f"文件名: {file_name}, 文件大小: {file_path.stat().st_size} 字节",
            operation_result="成功"
        )
        
        # 记录下载日志
        db.log_download(current_user["id"], file_name)
        
        # 返回文件作为响应
        return responses.FileResponse(
            path=file_path,
            filename=file_name,
            media_type="application/zip"
        )
    except Exception as e:
        # 记录文件下载失败操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="下载文件",
            operation_detail=f"文件名: {file_name}",
            operation_result=f"失败: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))