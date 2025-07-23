from typing import Optional, Dict, Any
from sqlmodel import Session, select, and_

from models import BridgeScales
from models.enums import ScalesType


def get_reference_data(all_options: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """
    获取用于匹配的参考数据，用于通过 name 去查找 code

    Returns:
        {
            'bridge_type': {'钢筋混凝土T梁桥': 'RC_T', ...},
            'part': {'桥面系': 'P01', ...}
        }
    """
    try:
        # 构建name到code的映射
        reference_data = {}

        # 从 all_options['categories'] 中获取数据，存入 reference_data['category']
        mappings = [
            ("categories", "category"),
            ("assessment_units", "assessment_unit"),
            ("bridge_types", "bridge_type"),
            ("bridge_parts", "part"),
            ("bridge_structures", "structure"),
            ("bridge_component_types", "component_type"),
            ("bridge_component_forms", "component_form"),
            ("bridge_diseases", "disease"),
            ("bridge_scales", "scale"),
            ("bridge_qualities", "quality"),
            ("bridge_quantities", "quantity"),
        ]

        for option_key, ref_key in mappings:
            if option_key in all_options:
                reference_data[ref_key] = {}
                for item in all_options[option_key]:
                    name = item.get("name", "").strip()
                    code = item.get("code", "").strip()
                    if name and code:
                        # name作为key，code作为value
                        reference_data[ref_key][name] = code

        return reference_data

    except Exception as e:
        print(f"获取参考数据时出错: {e}")
        return {}


def match_name_to_code(
    input_name: str,
    ref_key: str,
    reference_data: Dict[str, Dict[str, str]],
    session: Session = None,
) -> Dict[str, Any]:
    """
    匹配名称到编码

    Args:
        input_name: 输入的名称
        ref_key: 参考数据键
        reference_data: 参考数据
        session: 数据库会话
    """
    if ref_key not in reference_data:
        return {"matched": False}

    # 处理标度
    if ref_key == "scale" and session:
        return match_scale_name_to_code(input_name, session)

    ref_dict = reference_data[ref_key]

    if input_name in ref_dict:
        return {
            "matched": True,
            "code": ref_dict[input_name],
            "matched_name": input_name,
        }

    return {"matched": False}


def match_scale_name_to_code(input_value: str, session: Session) -> Dict[str, Any]:
    """
    匹配标度值到编码

    Args:
        input_value: 输入的标度值
        session: 数据库会话
    """
    try:
        input_value = str(input_value).strip()

        # 数值型
        try:
            numeric_value = float(input_value)
            if numeric_value.is_integer():
                numeric_value = int(numeric_value)

            stmt = select(BridgeScales.code).where(
                and_(
                    BridgeScales.scale_type == ScalesType.NUMERIC,
                    BridgeScales.scale_value == numeric_value,
                    BridgeScales.is_active == True,
                )
            )
            result = session.exec(stmt).first()
            if result:
                return {
                    "matched": True,
                    "code": result,
                    "matched_name": str(numeric_value),
                }
        except (ValueError, TypeError):
            pass

        # 范围型
        range_match = parse_range_value(input_value)
        if range_match:
            stmt = select(BridgeScales.code).where(
                and_(
                    BridgeScales.scale_type == ScalesType.RANGE,
                    BridgeScales.min_value == range_match["min_value"],
                    BridgeScales.max_value == range_match["max_value"],
                    BridgeScales.unit == range_match["unit"],
                    BridgeScales.is_active == True,
                )
            )
            result = session.exec(stmt).first()
            if result:
                return {
                    "matched": True,
                    "code": result,
                    "matched_name": input_value,
                }

        # 文本型
        stmt = select(BridgeScales.code).where(
            and_(
                BridgeScales.scale_type == ScalesType.TEXT,
                BridgeScales.display_text == input_value,
                BridgeScales.is_active == True,
            )
        )
        result = session.exec(stmt).first()
        if result:
            return {
                "matched": True,
                "code": result,
                "matched_name": input_value,
            }

        return {"matched": False}

    except Exception as e:
        print(f"匹配标度时出错: {e}")
        return {"matched": False}


def parse_range_value(input_value: str) -> Optional[Dict[str, Any]]:
    """
    解析范围值

    Args:
        input_value: 输入值，如 "10-20mm"

    Returns:
        解析结果 {"min_value": 10, "max_value": 20, "unit": "mm"}
    """
    try:
        import re

        # 匹配格式：数字-数字单位
        pattern = r"^(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)([a-zA-Z%]+)$"
        match = re.match(pattern, input_value.strip())

        if match:
            min_val = float(match.group(1))
            max_val = float(match.group(2))
            unit = match.group(3)

            if min_val.is_integer():
                min_val = int(min_val)
            if max_val.is_integer():
                max_val = int(max_val)

            return {"min_value": min_val, "max_value": max_val, "unit": unit}

        return None

    except Exception as e:
        print(f"解析范围值时出错: {e}")
        return None


def get_id_by_code(model_class, code: str, session: Session) -> Optional[int]:
    """
    通过code获取ID
    """
    try:
        stmt = select(model_class.id).where(
            and_(model_class.code == code, model_class.is_active == True)
        )
        return session.exec(stmt).first()
    except:
        return None
