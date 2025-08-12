from enum import Enum
from typing import Optional


class ScalesType(str, Enum):
    """标度类型枚举"""

    NUMERIC = "NUMERIC"  # 数值型：1,2,3,4,5
    # PERCENTAGE = "PERCENTAGE"  # 百分比型：10%-20%，20%-50%
    RANGE = "RANGE"  # 范围型：≤10mm，＞10mm 且≤20mm
    TEXT = "TEXT"  # 文本型


class CodePrefix(str, Enum):
    """编码前缀枚举"""

    CATEGORIES = "CAT"
    BRIDGE_TYPES = "BT"
    BRIDGE_PARTS = "BP"
    BRIDGE_STRUCTURES = "BS"
    BRIDGE_COMPONENT_TYPES = "BCT"
    BRIDGE_COMPONENT_FORMS = "BCF"
    BRIDGE_DISEASES = "BD"
    BRIDGE_SCALES = "SC"
    BRIDGE_QUALITIES = "BQL"
    BRIDGE_QUANTITIES = "BQT"
    PATHS = "P"
    ASSESSMENT_UNITS = "AU"
    SCORES = "SCR"
    WEIGHT_REFERENCES = "WR"


class Rating(Enum):
    """评定等级枚举"""

    LEVEL_1 = ("1类", 95, 100)  # (评定等级, 最低分, 最高分)
    LEVEL_2 = ("2类", 80, 95)
    LEVEL_3 = ("3类", 60, 80)
    LEVEL_4 = ("4类", 40, 60)
    LEVEL_5 = ("5类", 0, 40)

    @property
    def get_name(self) -> str:
        return self.value[0]

    @property
    def get_min_score(self) -> int:
        return self.value[1]

    @property
    def get_max_score(self) -> int:
        return self.value[2]


class CalculationMode(str, Enum):
    """权重分配计算方式"""

    DEFAULT = "default"  # 使用默认构件数量
    CUSTOM = "custom"  # 使用自定义构件数量


class BridgeMainComponents(str, Enum):
    """桥梁主要部件枚举"""

    UPPER_COMPONENT = "上部承重构件"
    PIER = "桥墩"
    ABUTMENT = "桥台"
    FOUNDATION = "基础"
    BEARING = "支座"
    MAIN_ARCH = "主拱圈"
    ARCH_SUPERSTRUCTURE = "拱上结构"
    DECK_SLAB = "桥面板"
    RIGID_FRAME_ARCH = "刚架拱片"
    TRUSS_ARCH = "桁架拱片"
    H_CONN_SYS = "横向联结系"
    ARCH_RIBS = "拱肋"
    COLUMN = "立柱"
    HANGERS = "吊杆"
    TIE_RODS = "系杆"
    ROADWAY_SLABS = "行车道板(梁)"
    MAIN_CABLES = "主缆"
    SLINGS = "吊索"
    STIFFEN_BEAMS = "加劲梁"
    TOWERS = "索塔"
    ANCHORS = "锚碇"
    CABLE_SYS = "斜拉索系统（斜拉索、锚具、斜拉索护套、减震装置等）"
    MAIN_BEAMS = "主粱"


class BridgePartWeight(Enum):
    """桥梁部位权重枚举"""

    SUPERSTRUCTURE = ("上部结构", 0.40)
    SUBSTRUCTURE = ("下部结构", 0.40)
    DECK_SYSTEM = ("桥面系", 0.20)

    @property
    def part_name(self) -> str:
        """获取部位名称"""
        return self.value[0]

    @property
    def weight(self) -> float:
        """获取权重值"""
        return self.value[1]

    @classmethod
    def get_weight_by_name(cls, part_name: str) -> Optional[float]:
        """根据部位名称获取权重"""
        for item in cls:
            if item.part_name == part_name:
                return item.weight
        return None

    @classmethod
    def get_all_weights(cls) -> dict:
        """获取所有部位权重字典"""
        return {item.part_name: item.weight for item in cls}
