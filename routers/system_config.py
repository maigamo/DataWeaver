from fastapi import APIRouter, Depends, HTTPException, status, Body
from models import Database, UserRole
from .auth import get_current_user

router = APIRouter(prefix="/system-config", tags=["系统配置"])
db = Database()

@router.get("/configs")
async def get_system_configs(current_user: dict = Depends(get_current_user)):
    """获取系统配置列表"""
    # 检查权限
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以查看系统配置"
        )
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM system_configs")
        configs = [dict(row) for row in cursor.fetchall()]
        
        return {"configs": configs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/configs/{config_key}")
async def update_system_config(
    config_key: str,
    config_value: dict = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """更新系统配置"""
    if "config_value" not in config_value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="config_value参数是必需的"
        )
    # 检查权限
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以更新系统配置"
        )
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 检查配置是否存在
        cursor.execute(
            "SELECT * FROM system_configs WHERE config_key = ?",
            (config_key,)
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置项不存在"
            )
        
        # 更新配置值
        cursor.execute(
            "UPDATE system_configs SET config_value = ?, updated_at = CURRENT_TIMESTAMP WHERE config_key = ?",
            (config_value["config_value"], config_key)
        )
        conn.commit()
        
        return {"message": "配置更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configs/{config_key}")
async def get_system_config(config_key: str):
    """获取指定的系统配置值"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT config_value FROM system_configs WHERE config_key = ?",
            (config_key,)
        )
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置项不存在"
            )
        
        return {"config_value": result["config_value"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))