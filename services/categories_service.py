from sqlmodel import Session, select
from typing import Optional, List

from models import Categories
from services.base_crud import BaseCRUDService
from api.schemas.categories import CategoriesCreate, CategoriesUpdate


class CategoriesService(
    BaseCRUDService[Categories, CategoriesCreate, CategoriesUpdate]
):
    """分类服务类"""

    def __init__(self, session: Session):
        super().__init__(Categories, session)

    def get_by_name(self, name: str) -> Optional[Categories]:
        """根据名称查询分类"""

        statement = select(Categories).where(Categories.name == name)
        return self.session.exec(statement).first()

    def get_active_list(self) -> List[Categories]:
        """获取所有启用的分类"""

        statement = (
            select(Categories)
            .where(Categories.is_active == True)
            .order_by(Categories.sort_order)
        )
        return self.session.exec(statement).all()


def get_categories_service(session: Session) -> CategoriesService:
    """获取分类服务实例"""
    return CategoriesService(session)
