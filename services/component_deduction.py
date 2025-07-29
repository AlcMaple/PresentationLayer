from typing import Optional


class ComponentDeductionService:
    """构件扣分服务"""

    _DEDUCTION_MAP = {
        3: {1: 0, 2: 20, 3: 35},
        4: {1: 25, 2: 0, 3: 40, 4: 50},
        5: {1: 0, 2: 35, 3: 45, 4: 60, 5: 100},
    }

    @staticmethod
    def get_deduction_value(max_scale: int, scale_value: int) -> Optional[int]:
        """获取构件扣分值"""
        deduction = ComponentDeductionService._DEDUCTION_MAP.get(max_scale)
        if deduction is None:
            return None

        return deduction.get(scale_value, None)
