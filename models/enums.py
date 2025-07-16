from enum import Enum


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
    ASSESSMENTS_UNITS = "AU"
