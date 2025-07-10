from fastapi import APIRouter, Depends, Query, Body
from sqlmodel import Session
from typing import Type, Dict, Any
from fastapi.responses import JSONResponse

from config.database import get_db
from services.base_crud import BaseCRUDService
from utils.responses import success, bad_request, not_found, paginated, server_error
from utils.types import PageParams

router = APIRouter(prefix="/basic", tags=["桥梁基础管理"])


# 桥分类管理
