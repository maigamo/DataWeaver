from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from typing import Optional
from datetime import datetime
import json
import zipfile
from pathlib import Path
from models import Database, UserRole
from .auth import get_current_user

router = APIRouter(tags=["操作管理"])
db = Database()

# 获取操作记录接口
@router.get("/api/operation-logs")
async def get_operation_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    start_date: Optional[str] = Query(None, regex=r'^\d{4}-\d{2}-\d{2}$', description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, regex=r'^\d{4}-\d{2}-\d{2}$', description="结束日期，格式：YYYY-MM-DD"),
    user_id: Optional[str] = Query(None, max_length=50, description="用户ID"),
    username: Optional[str] = Query(None, max_length=256, description="用户名"),
    operation_type: Optional[str] = Query(None, max_length=100, description="操作类型"),
    current_user: dict = Depends(get_current_user)
):
    print(f"[DEBUG] 接收到操作记录查询请求：page={page}, page_size={page_size}, start_date={start_date}, end_date={end_date}, user_id={user_id}")
    
    # 检查权限
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        print(f"[DEBUG] 用户权限不足：{current_user['role']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看操作记录"
        )
    
    try:
        print("[DEBUG] 开始查询操作记录...")
        # 获取操作记录
        logs = db.get_operation_logs(page, page_size, start_date, end_date, user_id, username, operation_type)
        print(f"[DEBUG] 查询成功，返回{len(logs.get('logs', []))}条记录")
        return logs
    except Exception as e:
        print(f"[ERROR] 查询操作记录失败：{str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 导出数据接口
@router.post("/api/operations/export")
async def export_data(
    start_date: Optional[str] = Form(None, regex=r'^\d{4}-\d{2}-\d{2}$'),
    end_date: Optional[str] = Form(None, regex=r'^\d{4}-\d{2}-\d{2}$'),
    export_type: str = Form(..., pattern=r'^(operation_logs|generation_history|statistics)$'),  # 导出类型：operation_logs, generation_history, statistics
    page_size: int = Form(1000, ge=100, le=10000, description="每页数据量"),
    compression_level: int = Form(9, ge=1, le=9, description="压缩级别，1-9，9为最高压缩率"),
    split_size: Optional[int] = Form(None, ge=1, le=1000, description="分卷大小（MB），不设置则不分卷"),
    current_user: dict = Depends(get_current_user)
):
    # 检查权限
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以导出数据"
        )
    
    try:
        # 根据导出类型获取数据
        all_data = []
        page = 1
        
        while True:
            data = None
            if export_type == "operation_logs":
                data = db.get_operation_logs(page=page, page_size=page_size, start_date=start_date, end_date=end_date)
                if not data.get('logs', []):
                    break
                all_data.extend(data['logs'])
            elif export_type == "generation_history":
                data = db.get_generation_history(start_date=start_date, end_date=end_date, page=page, page_size=page_size)
                if not data:
                    break
                all_data.extend(data)
            elif export_type == "statistics":
                data = db.get_statistics(start_date=start_date, end_date=end_date, page=page, page_size=page_size)
                if not data:
                    break
                all_data.extend(data)
            else:
                raise HTTPException(status_code=400, detail="不支持的导出类型")
            
            page += 1
        
        # 创建临时文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{export_type}_{timestamp}.zip"
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        temp_path = output_dir / filename
        
        # 准备数据分卷
        if split_size:
            split_size_bytes = split_size * 1024 * 1024  # 转换为字节
            total_data = len(all_data)
            items_per_volume = max(1, total_data // (total_data * 100 // split_size_bytes + 1))
            data_volumes = [all_data[i:i + items_per_volume] for i in range(0, total_data, items_per_volume)]
        else:
            data_volumes = [all_data]
        
        # 创建ZIP文件，使用指定压缩级别
        for vol_idx, volume_data in enumerate(data_volumes, 1):
            if split_size:
                volume_filename = f"{export_type}_{timestamp}_vol{vol_idx}.zip"
                volume_path = output_dir / volume_filename
            else:
                volume_path = temp_path
            
            with zipfile.ZipFile(volume_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zipf:
                # 将数据写入JSON文件并添加到ZIP
                json_filename = f"{export_type}_{timestamp}{f'_vol{vol_idx}' if split_size else ''}.json"
                with zipf.open(json_filename, 'w') as f:
                    f.write(json.dumps({"data": volume_data}, ensure_ascii=False, indent=2).encode('utf-8'))
        
        # 返回完整的数据和下载URL
        return {
            "data": data,
            "download_url": f"/download/{filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))