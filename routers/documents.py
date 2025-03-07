from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, File, UploadFile, responses
from pathlib import Path
from models import Database, UserRole
from .auth import get_current_user

router = APIRouter(tags=["文档管理"])
db = Database()

# 文档分类相关接口
from pydantic import BaseModel, constr
from typing import Optional

class DocumentCategoryCreate(BaseModel):
    name: constr(min_length=2, max_length=100, pattern=r'^[\w\-\s]+$')  # 分类名称格式验证
    description: Optional[constr(max_length=500)] = None  # 描述长度限制

@router.post("/document-categories")
async def create_document_category(
    category: DocumentCategoryCreate,
    current_user: dict = Depends(get_current_user)
):
    # 检查权限
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建文档分类"
        )
    
    category_id = db.add_document_category(
        name=category.name,
        description=category.description,
        created_by=current_user["id"]
    )
    
    if category_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分类名称已存在"
        )
    
    return {"id": category_id, "message": "文档分类创建成功"}

@router.get("/document-categories")
async def list_document_categories(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    search_term: str = Query("", description="搜索关键词"),
    current_user: dict = Depends(get_current_user)
):
    return db.get_document_categories(page, page_size, search_term)

# 文档管理相关接口
@router.post("/documents")
async def upload_document(
    title: str = Form(...),
    description: str = Form(None),
    category_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    # 检查权限
    if current_user["role"] not in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以上传文档"
        )
    
    try:
        # 创建文档目录
        docs_dir = Path("documents")
        docs_dir.mkdir(exist_ok=True)
        
        # 生成文件名和保存路径
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = Path(file.filename).suffix
        save_filename = f"{timestamp}_{file.filename}"
        file_path = docs_dir / save_filename
        
        # 保存文件
        file_content = await file.read()
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # 添加文档记录
        doc_id = db.add_document(
            title=title,
            description=description,
            category_id=category_id,
            file_path=str(file_path),
            file_size=len(file_content),
            file_type=file_ext.lstrip("."),
            uploaded_by=current_user["id"]
        )
        
        if doc_id is None:
            # 如果添加失败，删除已上传的文件
            file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文档添加失败"
            )
        
        return {"id": doc_id, "message": "文档上传成功"}
    except Exception as e:
        # 发生错误时，确保清理已上传的文件
        if "file_path" in locals():
            Path(file_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def list_documents(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    search_term: str = Query("", description="搜索关键词"),
    current_user: dict = Depends(get_current_user)
):
    return db.get_documents(page, page_size, category_id, search_term)

@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: dict = Depends(get_current_user)
):
    # 获取文档信息
    docs = db.get_documents(page_size=1, search_term=str(document_id))
    if not docs["documents"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    document = docs["documents"][0]
    file_path = Path(document["file_path"])
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    # 更新下载次数
    db.update_document_download_count(document_id)
    
    # 记录下载日志
    db.log_download(current_user["id"], file_path.name)
    
    return responses.FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream"
    )