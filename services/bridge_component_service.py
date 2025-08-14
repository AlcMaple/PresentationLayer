from typing import Optional, Set, Dict
from sqlmodel import Session, select

from models import BridgeTypes, BridgeParts, BridgeMainComponents, BridgeComponentTypes
from exceptions import NotFoundException


class BridgeComponentService:
    """桥梁部件服务类"""

    def __init__(self, session: Session):
        self.session = session

        # 桥梁类型与主要部件的映射关系
        self.BRIDGE_TYPE_MAIN_COMPONENTS = {
            "梁式桥": {
                BridgeMainComponents.UPPER_COMPONENT,
                BridgeMainComponents.PIER,
                BridgeMainComponents.ABUTMENT,
                BridgeMainComponents.FOUNDATION,
                BridgeMainComponents.BEARING,
            },
            "拱式桥": {
                BridgeMainComponents.MAIN_ARCH,
                BridgeMainComponents.ARCH_SUPERSTRUCTURE,
                BridgeMainComponents.DECK_SLAB,
                BridgeMainComponents.PIER,
                BridgeMainComponents.ABUTMENT,
                BridgeMainComponents.FOUNDATION,
                BridgeMainComponents.RIGID_FRAME_ARCH,
                BridgeMainComponents.TRUSS_ARCH,
                BridgeMainComponents.H_CONN_SYS,
            },
            "钢-混凝土组合拱桥": {
                BridgeMainComponents.ARCH_RIBS,
                BridgeMainComponents.H_CONN_SYS,
                BridgeMainComponents.COLUMN,
                BridgeMainComponents.HANGERS,
                BridgeMainComponents.TIE_RODS,
                BridgeMainComponents.ROADWAY_SLABS,
                BridgeMainComponents.BEARING,
            },
            "悬索桥": {
                BridgeMainComponents.ARCH_RIBS,
                BridgeMainComponents.SLINGS,
                BridgeMainComponents.STIFFEN_BEAMS,
                BridgeMainComponents.TOWERS,
                BridgeMainComponents.ANCHORS,
                BridgeMainComponents.PIER,
                BridgeMainComponents.ABUTMENT,
                BridgeMainComponents.FOUNDATION,
                BridgeMainComponents.BEARING,
            },
            "斜拉桥": {
                BridgeMainComponents.CABLE_SYS,
                BridgeMainComponents.MAIN_BEAMS,
                BridgeMainComponents.TOWERS,
                BridgeMainComponents.PIER,
                BridgeMainComponents.ABUTMENT,
                BridgeMainComponents.FOUNDATION,
                BridgeMainComponents.BEARING,
            },
        }

    def is_main_component(self, bridge_type_name: str, component_name: str) -> bool:
        """
        判断指定部件是否为特定桥梁类型的主要部件

        Args:
            bridge_type_name (str): 桥梁类型名称
            component_name (str): 部件名称

        Returns:
            bool: True表示是主要部件，False表示不是主要部件
        """
        if bridge_type_name not in self.BRIDGE_TYPE_MAIN_COMPONENTS:
            return False

        main_components = self.BRIDGE_TYPE_MAIN_COMPONENTS[bridge_type_name]
        return component_name in main_components

    def is_main_component_by_id(
        self, bridge_type_id: int, component_type_id: int
    ) -> bool:
        """
        通过ID判断指定部件是否为特定桥梁类型的主要部件

        Args:
            bridge_type_id (int): 桥梁类型ID
            component_type_id (int): 部件ID

        Returns:
            bool: True表示是主要部件，False表示不是主要部件

        Raises:
            NotFoundException: 当桥梁类型或部位不存在时抛出
        """
        # 查询桥梁类型名称
        bridge_type = self.session.get(BridgeTypes, bridge_type_id)
        if not bridge_type:
            raise NotFoundException("BridgeType", str(bridge_type_id))

        # 查询部位名称
        part = self.session.get(BridgeComponentTypes, component_type_id)
        if not part:
            raise NotFoundException("BridgeComponentTypes", str(component_type_id))

        return self.is_main_component(bridge_type.name, part.name)

    def get_main_components_for_bridge_type(self, bridge_type_name: str) -> Set[str]:
        """
        获取指定桥梁类型的所有主要部件

        Args:
            bridge_type_name (str): 桥梁类型名称

        Returns:
            Set[str]: 主要部件名称集合
        """
        return self.BRIDGE_TYPE_MAIN_COMPONENTS.get(bridge_type_name, set())


def get_bridge_component_service(session: Session) -> BridgeComponentService:
    """获取桥梁部件服务实例"""
    return BridgeComponentService(session)
