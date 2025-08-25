from typing import Optional, Dict, Any, List
from sqlmodel import Session, select, and_

from models import BridgeScales, BridgeDiseases, Paths, AssessmentUnit
from models.enums import ScalesType, Rating


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


def get_damage_type_id_by_name(name: str, session: Session) -> Optional[int]:
    """通过病害类型名称获取ID"""
    try:
        stmt = select(BridgeDiseases.id).where(
            and_(BridgeDiseases.name == name, BridgeDiseases.is_active == True)
        )
        return session.exec(stmt).first()
    except:
        return None


def get_scale_id_by_value(value_str: str, session: Session) -> Optional[int]:
    """通过标度值获取ID"""
    match_result = match_scale_name_to_code(value_str, session)

    if match_result.get("matched"):
        # 通过编码获取ID
        scale_code = match_result["code"]
        return get_id_by_code(BridgeScales, scale_code, session)

    return None


def get_damage_code_by_id(damage_id: int, session: Session) -> Optional[str]:
    """通过病害ID获取编码"""
    try:
        stmt = select(BridgeDiseases.code).where(BridgeDiseases.id == damage_id)
        return session.exec(stmt).first()
    except:
        return None


def get_scale_code_by_id(scale_id: int, session: Session) -> Optional[str]:
    """通过标度ID获取编码"""
    try:
        stmt = select(BridgeScales.code).where(BridgeScales.id == scale_id)
        return session.exec(stmt).first()
    except:
        return None


def get_rating_by_score(score: float) -> Optional[Rating]:
    """通过分数获取评级"""
    if not 0 <= score <= 100:
        return None

    if score >= Rating.LEVEL_1.get_min_score:
        return Rating.LEVEL_1
    elif score >= Rating.LEVEL_2.get_min_score:
        return Rating.LEVEL_2
    elif score >= Rating.LEVEL_3.get_min_score:
        return Rating.LEVEL_3
    elif score >= Rating.LEVEL_4.get_min_score:
        return Rating.LEVEL_4
    else:
        return Rating.LEVEL_5


def get_assessment_units_by_category(
    category_id: int, session: Session
) -> List[Dict[str, Any]]:
    """
    获取指定类别下所有可用的评定单元列表

    Args:
        category_id: 桥梁类别ID
        session: 数据库会话

    Returns:
        评定单元列表，包含id和name
    """
    try:

        # 查询该类别下存在的评定单元ID
        existing_ids_stmt = (
            select(Paths.assessment_unit_id)
            .where(
                and_(
                    Paths.category_id == category_id,
                    Paths.assessment_unit_id.is_not(None),
                    Paths.is_active == True,
                )
            )
            .distinct()
        )
        existing_ids = session.exec(existing_ids_stmt).all()
        # print("existing_ids-p 评定单元:", existing_ids)

        if not existing_ids:
            return []

        # 查询评定单元详细信息
        stmt = (
            select(AssessmentUnit.id, AssessmentUnit.name)
            .where(
                and_(
                    AssessmentUnit.id.in_(existing_ids),
                    AssessmentUnit.is_active == True,
                )
            )
            .order_by(AssessmentUnit.name)
        )

        results = session.exec(stmt).all()
        # print("results-p 评定单元:", results)

        # 如果只有一个评定单元，且name 为“-”，则返回空列表
        if len(results) == 1 and results[0][1] == "-":
            return [{"id": results[0][0], "name": results[0][1]}]

        # 如果有多个评定单元，且name 为“-”，则过滤掉
        return [{"id": r[0], "name": r[1]} for r in results if r[1] != "-"]

    except Exception as e:
        print(f"获取评定单元列表时出错: {e}")
        return []
