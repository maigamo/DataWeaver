from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from pathlib import Path
from models import Database, UserRole
from .auth import get_current_user
from datetime import datetime

router = APIRouter(tags=["分支管理"])
db = Database()

# 获取分支列表接口
@router.get("/branches")
async def list_branches():
    try:
        # 获取templates目录下的所有目录作为分支
        templates_dir = Path("templates")
        if not templates_dir.exists():
            return {"branches": []}
        
        branches = []
        for item in templates_dir.iterdir():
            if item.is_dir():
                # 检查是否包含模板文件
                template_file = item.joinpath("j_initData.sql")
                if template_file.exists():
                    # 获取目录的创建时间
                    created_time = datetime.fromtimestamp(item.stat().st_ctime).strftime("%Y-%m-%d %H:%M:%S")
                    branches.append({
                        "name": item.name,
                        "created_at": created_time,
                        "description": "SQL模板分支"
                    })
        
        return {"branches": branches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 创建新分支并上传SQL模板文件
@router.post("/branches")
async def create_branch(
    branch_name: str = Form(..., min_length=2, max_length=256),
    sql_file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """创建新分支并上传SQL模板文件"""
    
    # 检查权限
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建分支"
        )
    
    # 验证分支名称
    if not branch_name or not branch_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分支名称不能为空"
        )
    
    # 检查分支名称是否包含非法字符
    import re
    if re.search(r'[\\/:*?"<>|]', branch_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分支名称包含非法字符"
        )
    
    # 检查SQL文件是否上传
    if not sql_file or sql_file.filename == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传SQL模板文件"
        )
    
    try:
        # 创建分支目录
        branch_dir = Path(f"templates/{branch_name}")
        branch_dir.mkdir(exist_ok=True, parents=True)
        
        # 保存SQL文件
        sql_file_path = branch_dir / "j_initData.sql"
        file_content = await sql_file.read()
        with open(sql_file_path, "wb") as f:
            f.write(file_content)
        
        # 记录分支信息到数据库
        branch_id = db.add_branch(branch_name, current_user["id"])
        if branch_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="分支名称已存在"
            )
        
        return {"id": branch_id, "message": f"分支 {branch_name} 创建成功"}
    except Exception as e:
        # 如果出错，清理已创建的目录
        import shutil
        if branch_dir.exists():
            shutil.rmtree(branch_dir)
        raise HTTPException(status_code=500, detail=str(e))

# 删除分支
@router.delete("/branches/{branch_name}")
async def delete_branch(branch_name: str, current_user: dict = Depends(get_current_user)):
    """删除指定分支"""
    # 检查权限
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以删除分支"
        )
    
    try:
        # 检查分支是否存在
        branch_dir = Path(f"templates/{branch_name}")
        if not branch_dir.exists() or not branch_dir.is_dir():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"分支 {branch_name} 不存在"
            )
        
        # 删除分支目录
        import shutil
        shutil.rmtree(branch_dir)
        
        return {"message": f"分支 {branch_name} 删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))