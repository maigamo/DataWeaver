from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, constr
from typing import Optional

from models import Database

# JWT相关配置
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8小时过期

# 数据库实例
db = Database()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 用户认证相关模型
class Token(BaseModel):
    access_token: str  # JWT token
    token_type: str  # token类型

class TokenData(BaseModel):
    username: Optional[constr(max_length=256)] = None  # 用户名长度限制

class User(BaseModel):
    username: constr(min_length=2, max_length=256)  # 修改用户名长度限制和格式验证
    role: constr(pattern='^(超级管理员|普通管理员|普通用户|操作员)$')  # 修改角色限制为中文
    status: constr(pattern='^(启用|禁用)$')  # 状态限制

class UserInDB(User):
    password: str  # 用户密码

class LoginData(BaseModel):
    username: str  # 用户名
    password: str  # 密码

router = APIRouter(tags=["认证"])

# 用户认证相关函数
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = db.get_user(token_data.username)
    if user is None:
        raise credentials_exception
    return user

# 登录接口
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # 验证输入长度
    if len(form_data.username) > 256 or len(form_data.password) > 256:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或密码长度超过限制"
        )
    
    user = db.authenticate_user(form_data.username, form_data.password)
    if not user:
        # 登录失败，但不记录日志（因为没有有效的user_id）
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 记录登录成功日志
    db.log_user_operation(
        user_id=user["id"],
        operation_type="登录成功",
        operation_detail=f"用户名: {user['username']}, 角色: {user['role']}",
        operation_result="登录成功"
    )
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "Bearer"}

# 获取当前用户信息
@router.get("/users/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user