import sys
import os
from sqlmodel import Session

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine
from models import (
    Categories,
    AssessmentUnit,
    BridgeTypes,
    BridgeStructures,
    BridgeParts,
    BridgeComponentTypes,
    BridgeComponentForms,
    BridgeDiseases,
    BridgeQualities,
    BridgeQuantities,
    BridgeScales,
)
from models.enums import ScalesType
from services.code_generator import get_code_generator


def add_default_data():
    """为所有基础表添加默认数据"""
    
    # 基础表配置
    base_tables = [
        {
            "model": Categories,
            "table_name": "categories",
            "description": "分类",
            "extra_fields": {"level": 0}
        },
        # {
        #     "model": AssessmentUnit,
        #     "table_name": "assessment_units", 
        #     "description": "评定单元",
        #     "extra_fields": {"level": 1}
        # },
        {
            "model": BridgeTypes,
            "table_name": "bridge_types",
            "description": "桥梁类型",
            "extra_fields": {"level": 2, "category_id": None}
        },
        {
            "model": BridgeStructures,
            "table_name": "bridge_structures",
            "description": "结构类型", 
            "extra_fields": {"level": 4}
        },
        {
            "model": BridgeParts,
            "table_name": "bridge_parts",
            "description": "部位",
            "extra_fields": {"level": 3}
        },
        {
            "model": BridgeComponentTypes,
            "table_name": "bridge_component_types",
            "description": "部件类型",
            "extra_fields": {"level": 5}
        },
        {
            "model": BridgeComponentForms,
            "table_name": "bridge_component_forms",
            "description": "构件形式",
            "extra_fields": {"level": 6}
        },
        {
            "model": BridgeDiseases,
            "table_name": "bridge_diseases",
            "description": "病害类型",
            "extra_fields": {"level": 7}
        },
        {
            "model": BridgeQualities,
            "table_name": "bridge_qualities",
            "description": "定性描述",
            "extra_fields": {"level": 9}
        },
        {
            "model": BridgeQuantities,
            "table_name": "bridge_quantities",
            "description": "定量描述",
            "extra_fields": {"level": 10}
        },
        {
            "model": BridgeScales,
            "table_name": "bridge_scales",
            "description": "标度",
            "extra_fields": {
                "level": 8,
                "scale_type": ScalesType.TEXT,
                "scale_value": None,
                "min_value": None,
                "max_value": None,
                "unit": None,
                "display_text": "-"
            }
        },
    ]
    
    success_count = 0
    error_count = 0
    errors = []
    
    with Session(engine) as session:
        code_generator = get_code_generator(session)
        
        for table_config in base_tables:
            try:
                model_class = table_config["model"]
                table_name = table_config["table_name"]
                description = table_config["description"]
                extra_fields = table_config["extra_fields"]
                
                print(f"处理表: {table_name} ({description})")
                
                # 生成编码
                code = code_generator.generate_code(table_name)
                
                # 构建基础数据
                data = {
                    "name": "-",
                    "code": code,
                    "description": f"默认{description}",
                    "sort_order": 999,  # 设置为最后排序
                    "is_active": True,
                }
                
                # 添加额外字段
                data.update(extra_fields)
                
                # 创建实例
                instance = model_class(**data)
                session.add(instance)
                session.commit()
                session.refresh(instance)
                
                print(f"  ✓ 成功添加记录: ID={instance.id}, Code={code}")
                success_count += 1
                
            except Exception as e:
                session.rollback()
                error_msg = f"表 {table_name} 添加数据失败: {str(e)}"
                print(f"  ✗ {error_msg}")
                errors.append(error_msg)
                error_count += 1
    
    # 输出统计信息
    print("\n" + "="*50)
    print("数据添加完成")
    print(f"成功: {success_count} 个表")
    print(f"失败: {error_count} 个表")
    
    if errors:
        print("\n错误详情:")
        for error in errors:
            print(f"  - {error}")
    
    print("="*50)


if __name__ == "__main__":
    print("开始为基础表添加默认数据...")
    add_default_data()
    print("脚本执行完成")