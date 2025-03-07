from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .documents import router as documents_router
from .operations import router as operations_router
from .templates import router as templates_router
from .branches import router as branches_router
from .files import router as files_router
from .statistics import router as statistics_router
from .resource_center import router as resource_center_router
from .system_config import router as system_config_router

routers = [
    auth_router,
    users_router,
    documents_router,
    operations_router,
    templates_router,
    branches_router,
    files_router,
    statistics_router,
    resource_center_router,
    system_config_router
]