from enum import Enum


class ScalesType(str, Enum):
    """标度类型枚举"""

    NUMERIC = "NUMERIC"  # 数值型：1,2,3,4,5
    PERCENTAGE = "PERCENTAGE"  # 百分比型：10%-20%，20%-50%
    RANGE = "RANGE"  # 范围型：≤10mm，＞10mm 且≤20mm
    TEXT = "TEXT"  # 文本型
