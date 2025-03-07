from fastapi import APIRouter, Depends, HTTPException, status, Query
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
from models import Database, UserRole
from .auth import get_current_user
from datetime import datetime
import zipfile

router = APIRouter(tags=["模板管理"])
db = Database()

# 数据模板查询接口
class TemplateQueryParams(BaseModel):
    branch: str
    keyword: Optional[str] = None
    page: int = 1
    page_size: int = 20

@router.post("/query/templates")
async def query_templates(params: TemplateQueryParams, current_user: dict = Depends(get_current_user)):
    try:
        # 获取指定分支的模板目录
        template_dir = Path(f"templates/{params.branch}")
        if not template_dir.exists() or not template_dir.is_dir():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"分支 {params.branch} 不存在"
            )
        
        # 读取SQL模板文件
        template_file = template_dir / "j_initData.sql"
        if not template_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"分支 {params.branch} 的模板文件不存在"
            )
        
        with open(template_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 如果有关键词，进行过滤
        lines = content.split('\n')
        filtered_lines = []
        if params.keyword:
            keyword = params.keyword.lower()
            filtered_lines = [line for line in lines if keyword in line.lower()]
        else:
            filtered_lines = lines
        
        # 分页处理
        total = len(filtered_lines)
        total_pages = (total + params.page_size - 1) // params.page_size
        start_idx = (params.page - 1) * params.page_size
        end_idx = min(start_idx + params.page_size, total)
        
        # 获取当前页的数据
        current_page_lines = filtered_lines[start_idx:end_idx]
        
        return {
            "total": total,
            "total_pages": total_pages,
            "current_page": params.page,
            "page_size": params.page_size,
            "lines": current_page_lines
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 定义请求模型
class ScriptGenerateRequest(BaseModel):
    branch: str
    user_start_index: int = 2
    user_max_index: int = 8000
    current_department_index: int = 0
    users_per_department: int = 2500
    device_start_index: int = 1
    device_max_index: int = 1

# 创建输出目录
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

def generate_sql_script(params: ScriptGenerateRequest) -> str:
    """根据参数生成SQL脚本内容"""
    # 根据分支选择对应的SQL模板
    template_path = Path(f"templates/{params.branch}/j_initData.sql")
    
    # 如果分支对应的模板不存在，则使用默认模板
    if not template_path.exists():
        template_path = Path("templates/master/j_initData.sql")
    
    # 读取SQL模板
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    
    # 替换参数
    script = template.replace(
        "    DECLARE i INT DEFAULT 2;  -- 用户初始化序号",
        f"    DECLARE i INT DEFAULT {params.user_start_index};  -- 用户初始化序号"
    ).replace(
        "    DECLARE max_i INT DEFAULT 250002;  -- 用户最大序号",
        f"    DECLARE max_i INT DEFAULT {params.user_max_index};  -- 用户最大序号"
    ).replace(
        "    DECLARE org_cur INT DEFAULT 0;    --部门的初始化id",
        f"    DECLARE org_cur INT DEFAULT {params.current_department_index};    --部门的初始化id"
    ).replace(
        "    DECLARE org_add INT DEFAULT 5000;  --每个部门设置多少个用户",
        f"    DECLARE org_add INT DEFAULT {params.users_per_department};  --每个部门设置多少个用户"
    ).replace(
        "    DECLARE device_index INT DEFAULT 1; -- 定义每个用户的初始化设备序号",
        f"    DECLARE device_index INT DEFAULT {params.device_start_index}; -- 定义每个用户的初始化设备序号"
    ).replace(
        "    DECLARE device_count INT DEFAULT 2;  -- 定义每个用户添加几个设备",
        f"    DECLARE device_count INT DEFAULT {params.device_max_index};  -- 定义每个用户添加几个设备"
    )
    
    return script

def create_zip_file(sql_content: str, params: ScriptGenerateRequest) -> str:
    """创建ZIP文件并返回文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"{timestamp}_{params.branch}_u{params.user_start_index}-{params.user_max_index}_d{params.current_department_index}-{params.users_per_department}_dev{params.device_start_index}-{params.device_max_index}.zip"
    zip_path = output_dir / zip_filename
    
    sql_filename = "generated_script.sql"
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(sql_filename, sql_content)
    
    return zip_filename

@router.post("/generate-script")
async def generate_script(params: ScriptGenerateRequest, current_user: dict = Depends(get_current_user)):
    try:
        # 生成SQL脚本
        sql_content = generate_sql_script(params)
        
        # 创建ZIP文件
        zip_filename = create_zip_file(sql_content, params)
        
        # 记录SQL生成操作
        db.log_script_generation(
            user_id=current_user["id"],
            branch=params.branch,
            user_start_index=params.user_start_index,
            user_max_index=params.user_max_index,
            department_index=params.current_department_index,
            users_per_department=params.users_per_department,
            device_start_index=params.device_start_index,
            device_max_index=params.device_max_index,
            file_name=zip_filename
        )
        
        # 记录用户操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="生成SQL脚本",
            operation_detail=f"分支: {params.branch}, 用户范围: {params.user_start_index}-{params.user_max_index}, 部门索引: {params.current_department_index}, 每部门用户数: {params.users_per_department}",
            operation_result="成功"
        )
        
        # 构建下载URL
        download_url = f"/download/{zip_filename}"
        
        return {
            "status": "success",
            "download_url": download_url
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))