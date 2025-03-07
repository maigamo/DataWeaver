from fastapi import APIRouter, Depends, HTTPException, status, Query
from models import Database, UserRole
from .auth import get_current_user
from pydantic import BaseModel, constr

router = APIRouter(tags=["用户管理"])
db = Database()

class UserCreate(BaseModel):
    username: constr(min_length=2, max_length=256)  # 修改用户名长度限制
    password: constr(min_length=6, max_length=256)  # 密码长度限制
    role: constr(pattern='^(超级管理员|普通管理员|普通用户|操作员)$')  # 修改角色限制为中文
    status: constr(pattern='^(启用|禁用)$') = "启用"  # 状态限制，默认为启用

@router.get("/users")
async def list_users(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    search_term: str = Query("", description="搜索关键词"),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看用户列表"
        )
    
    try:
        users_data = db.get_all_users(page, page_size, search_term)
        return users_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users")
async def create_user(user_data: UserCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        # 记录权限不足操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="创建用户",
            operation_detail=f"尝试创建用户: {user_data.username}, 角色: {user_data.role}",
            operation_result="失败: 权限不足"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建新用户"
        )
    
    # 检查用户名是否已存在
    existing_user = db.get_user(user_data.username)
    if existing_user:
        # 记录用户名已存在操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="创建用户",
            operation_detail=f"尝试创建用户: {user_data.username}, 角色: {user_data.role}",
            operation_result="失败: 用户名已存在"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 创建新用户
    user_id = db.create_user(
        username=user_data.username,
        password=user_data.password,
        role=user_data.role,
        status=user_data.status
    )
    
    if user_id:
        # 记录创建用户成功操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="创建用户",
            operation_detail=f"创建用户: {user_data.username}, 角色: {user_data.role}, 状态: {user_data.status}",
            operation_result="成功"
        )
        return {"message": "用户创建成功", "user_id": user_id}
    else:
        # 记录创建用户失败操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="创建用户",
            operation_detail=f"尝试创建用户: {user_data.username}, 角色: {user_data.role}",
            operation_result="失败: 数据库错误"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="创建用户失败"
        )

@router.put("/users/{user_id}")
async def update_user(user_id: int, user_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        # 记录权限不足操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="更新用户",
            operation_detail=f"尝试更新用户ID: {user_id}",
            operation_result="失败: 权限不足"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以更新用户信息"
        )
    
    if user_id == 1 and current_user["id"] != 1:
        target_user = db.get_user_by_id(user_id)
        if target_user and target_user["username"] == "admin" and target_user["role"] == UserRole.SUPER_ADMIN.value:
            # 记录尝试修改超级管理员操作
            db.log_user_operation(
                user_id=current_user["id"],
                operation_type="更新用户",
                operation_detail=f"尝试更新超级管理员用户ID: {user_id}",
                operation_result="失败: 不能修改默认超级管理员账号"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能修改默认超级管理员账号"
            )
    
    # 记录更新前的用户信息
    old_user = db.get_user_by_id(user_id)
    if not old_user:
        # 记录用户不存在操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="更新用户",
            operation_detail=f"尝试更新不存在的用户ID: {user_id}",
            operation_result="失败: 用户不存在"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    success = db.update_user(
        user_id,
        username=user_data.get("username"),
        password=user_data.get("password"),
        role=user_data.get("role"),
        status=user_data.get("status")
    )
    
    if success:
        # 记录用户更新成功操作
        update_details = []
        if user_data.get("username"):
            update_details.append(f"用户名: {user_data.get('username')}")
        if user_data.get("password"):
            update_details.append("密码已更新")
        if user_data.get("role"):
            update_details.append(f"角色: {user_data.get('role')}")
        if user_data.get("status"):
            update_details.append(f"状态: {user_data.get('status')}")
        
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="更新用户",
            operation_detail=f"更新用户ID: {user_id}, 更新内容: {', '.join(update_details)}",
            operation_result="成功"
        )
        return {"message": "用户更新成功"}
    else:
        # 记录用户更新失败操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="更新用户",
            operation_detail=f"尝试更新用户ID: {user_id}",
            operation_result="失败: 可能用户不存在或用户名已被占用"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新用户失败，可能用户不存在或用户名已被占用"
        )

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        # 记录权限不足操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="删除用户",
            operation_detail=f"尝试删除用户ID: {user_id}",
            operation_result="失败: 权限不足"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以删除用户"
        )
    
    target_user = db.get_user_by_id(user_id)
    if not target_user:
        # 记录用户不存在操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="删除用户",
            operation_detail=f"尝试删除不存在的用户ID: {user_id}",
            operation_result="失败: 用户不存在"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if target_user["username"] == "admin" and target_user["role"] == UserRole.SUPER_ADMIN.value:
        # 记录尝试删除超级管理员操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="删除用户",
            operation_detail=f"尝试删除超级管理员用户ID: {user_id}, 用户名: {target_user['username']}",
            operation_result="失败: 不能删除默认超级管理员账号"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能删除默认超级管理员账号"
        )
    
    success = db.delete_user(user_id)
    
    if success:
        # 记录用户删除成功操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="删除用户",
            operation_detail=f"删除用户ID: {user_id}, 用户名: {target_user['username']}, 角色: {target_user['role']}",
            operation_result="成功"
        )
        return {"message": "用户删除成功"}
    else:
        # 记录用户删除失败操作
        db.log_user_operation(
            user_id=current_user["id"],
            operation_type="删除用户",
            operation_detail=f"尝试删除用户ID: {user_id}, 用户名: {target_user['username']}",
            operation_result="失败: 数据库错误"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="删除用户失败"
        )