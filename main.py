from fastapi import FastAPI, HTTPException, Depends, Query, Body, UploadFile, File
from sqlmodel import Session, select, func
from typing import List, Optional, Dict
from database import get_session, create_db_and_tables, init_demo_data
from models import *
from datetime import datetime

app = FastAPI(
    title="桥梁管理系统 - 简化版",
    description="基于完整路径表的桥梁管理系统，去掉中间关系表",
    version="2.0.0",
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    init_demo_data()


# =============================================================================
# 基础数据 CRUD 操作
# =============================================================================


@app.get("/bridge-types/", response_model=List[BridgeTypeResponse])
def get_bridge_types(
    is_active: Optional[bool] = Query(None), session: Session = Depends(get_session)
):
    """获取桥类型列表"""
    statement = select(BridgeType).order_by(BridgeType.sort_order)

    if is_active is not None:
        statement = statement.where(BridgeType.is_active == is_active)

    bridge_types = session.exec(statement).all()
    return [BridgeTypeResponse(**bt.dict()) for bt in bridge_types]


@app.post("/bridge-types/", response_model=BridgeTypeResponse)
def create_bridge_type(data: BridgeTypeCreate, session: Session = Depends(get_session)):
    """创建桥类型"""
    existing = session.exec(
        select(BridgeType).where(BridgeType.code == data.code)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"编码 '{data.code}' 已存在")

    bridge_type = BridgeType(**data.dict())
    session.add(bridge_type)
    session.commit()
    session.refresh(bridge_type)
    return BridgeTypeResponse(**bridge_type.dict())


@app.put("/bridge-types/{bridge_type_id}", response_model=BridgeTypeResponse)
def update_bridge_type(
    bridge_type_id: int, data: BridgeTypeUpdate, session: Session = Depends(get_session)
):
    """更新桥类型"""
    bridge_type = session.get(BridgeType, bridge_type_id)
    if not bridge_type:
        raise HTTPException(status_code=404, detail="桥类型不存在")

    update_data = data.dict(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.now()
        for key, value in update_data.items():
            setattr(bridge_type, key, value)
        session.add(bridge_type)
        session.commit()
        session.refresh(bridge_type)

    return BridgeTypeResponse(**bridge_type.dict())


@app.delete("/bridge-types/{bridge_type_id}")
def delete_bridge_type(bridge_type_id: int, session: Session = Depends(get_session)):
    """软删除桥类型"""
    bridge_type = session.get(BridgeType, bridge_type_id)
    if not bridge_type:
        raise HTTPException(status_code=404, detail="桥类型不存在")

    bridge_type.is_active = False
    bridge_type.updated_at = datetime.now()
    session.add(bridge_type)
    session.commit()

    return {"message": f"桥类型 '{bridge_type.name}' 已删除"}


@app.get("/parts/", response_model=List[PartResponse])
def get_parts(
    is_active: Optional[bool] = Query(None), session: Session = Depends(get_session)
):
    """获取部位列表"""
    statement = select(Part).order_by(Part.sort_order)

    if is_active is not None:
        statement = statement.where(Part.is_active == is_active)

    parts = session.exec(statement).all()
    return [PartResponse(**part.dict()) for part in parts]


@app.post("/parts/", response_model=PartResponse)
def create_part(data: PartCreate, session: Session = Depends(get_session)):
    """创建部位"""
    existing = session.exec(select(Part).where(Part.code == data.code)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"编码 '{data.code}' 已存在")

    part = Part(**data.dict())
    session.add(part)
    session.commit()
    session.refresh(part)
    return PartResponse(**part.dict())


@app.get("/structure-types/", response_model=List[StructureTypeResponse])
def get_structure_types(
    part_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    session: Session = Depends(get_session),
):
    """获取结构类型列表"""
    statement = (
        select(StructureType, Part).join(Part).order_by(StructureType.sort_order)
    )

    if part_id:
        statement = statement.where(StructureType.part_id == part_id)

    if is_active is not None:
        statement = statement.where(StructureType.is_active == is_active)

    results = session.exec(statement).all()

    return [
        StructureTypeResponse(
            id=st.id,
            code=st.code,
            name=st.name,
            description=st.description,
            part_id=st.part_id,
            part_name=part.name,
            is_active=st.is_active,
            sort_order=st.sort_order,
        )
        for st, part in results
    ]


@app.post("/structure-types/", response_model=StructureTypeResponse)
def create_structure_type(
    data: StructureTypeCreate, session: Session = Depends(get_session)
):
    """创建结构类型"""
    part = session.get(Part, data.part_id)
    if not part:
        raise HTTPException(status_code=400, detail="部位不存在")

    existing = session.exec(
        select(StructureType).where(StructureType.code == data.code)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"编码 '{data.code}' 已存在")

    structure_type = StructureType(**data.dict())
    session.add(structure_type)
    session.commit()
    session.refresh(structure_type)

    return StructureTypeResponse(
        id=structure_type.id,
        code=structure_type.code,
        name=structure_type.name,
        description=structure_type.description,
        part_id=structure_type.part_id,
        part_name=part.name,
        is_active=structure_type.is_active,
        sort_order=structure_type.sort_order,
    )


@app.get("/component-types/", response_model=List[ComponentTypeResponse])
def get_component_types(
    structure_type_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    session: Session = Depends(get_session),
):
    """获取部件类型列表"""
    statement = (
        select(ComponentType, StructureType)
        .join(StructureType)
        .order_by(ComponentType.sort_order)
    )

    if structure_type_id:
        statement = statement.where(
            ComponentType.structure_type_id == structure_type_id
        )

    if is_active is not None:
        statement = statement.where(ComponentType.is_active == is_active)

    results = session.exec(statement).all()

    return [
        ComponentTypeResponse(
            id=ct.id,
            code=ct.code,
            name=ct.name,
            description=ct.description,
            structure_type_id=ct.structure_type_id,
            structure_type_name=st.name,
            is_active=ct.is_active,
            sort_order=ct.sort_order,
        )
        for ct, st in results
    ]


@app.post("/component-types/", response_model=ComponentTypeResponse)
def create_component_type(
    data: ComponentTypeCreate, session: Session = Depends(get_session)
):
    """创建部件类型"""
    structure_type = session.get(StructureType, data.structure_type_id)
    if not structure_type:
        raise HTTPException(status_code=400, detail="结构类型不存在")

    existing = session.exec(
        select(ComponentType).where(ComponentType.code == data.code)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"编码 '{data.code}' 已存在")

    component_type = ComponentType(**data.dict())
    session.add(component_type)
    session.commit()
    session.refresh(component_type)

    return ComponentTypeResponse(
        id=component_type.id,
        code=component_type.code,
        name=component_type.name,
        description=component_type.description,
        structure_type_id=component_type.structure_type_id,
        structure_type_name=structure_type.name,
        is_active=component_type.is_active,
        sort_order=component_type.sort_order,
    )


@app.get("/damage-types/", response_model=List[DamageTypeResponse])
def get_damage_types(
    is_active: Optional[bool] = Query(None), session: Session = Depends(get_session)
):
    """获取病害类型列表"""
    statement = select(DamageType).order_by(DamageType.sort_order)

    if is_active is not None:
        statement = statement.where(DamageType.is_active == is_active)

    damage_types = session.exec(statement).all()
    return [DamageTypeResponse(**dt.dict()) for dt in damage_types]


@app.post("/damage-types/", response_model=DamageTypeResponse)
def create_damage_type(data: DamageTypeCreate, session: Session = Depends(get_session)):
    """创建病害类型"""
    existing = session.exec(
        select(DamageType).where(DamageType.code == data.code)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"编码 '{data.code}' 已存在")

    damage_type = DamageType(**data.dict())
    session.add(damage_type)
    session.commit()
    session.refresh(damage_type)
    return DamageTypeResponse(**damage_type.dict())


@app.get("/scales/", response_model=List[ScaleResponse])
def get_scales(
    is_active: Optional[bool] = Query(None), session: Session = Depends(get_session)
):
    """获取标度列表"""
    statement = select(Scale).order_by(Scale.sort_order)

    if is_active is not None:
        statement = statement.where(Scale.is_active == is_active)

    scales = session.exec(statement).all()
    return [ScaleResponse(**scale.dict()) for scale in scales]


@app.post("/scales/", response_model=ScaleResponse)
def create_scale(data: ScaleCreate, session: Session = Depends(get_session)):
    """创建标度"""
    existing = session.exec(select(Scale).where(Scale.code == data.code)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"编码 '{data.code}' 已存在")

    scale = Scale(**data.dict())
    session.add(scale)
    session.commit()
    session.refresh(scale)
    return ScaleResponse(**scale.dict())


# =============================================================================
# 核心路径管理
# =============================================================================


@app.post("/paths/")
def create_path(data: PathCreate, session: Session = Depends(get_session)):
    """创建完整路径"""
    # 验证路径中的每个组件都存在
    bridge_type = session.get(BridgeType, data.bridge_type_id)
    part = session.get(Part, data.part_id)
    structure_type = session.get(StructureType, data.structure_type_id)
    component_type = session.get(ComponentType, data.component_type_id)
    damage_type = session.get(DamageType, data.damage_type_id)

    if not all([bridge_type, part, structure_type, component_type, damage_type]):
        raise HTTPException(status_code=400, detail="路径中的某些组件不存在")

    # 验证标度存在
    scales = session.exec(select(Scale).where(Scale.id.in_(data.scale_ids))).all()
    if len(scales) != len(data.scale_ids):
        raise HTTPException(status_code=400, detail="部分标度不存在")

    # 创建路径记录
    created_paths = []
    for i, scale_id in enumerate(data.scale_ids):
        # 检查路径是否已存在
        existing = session.exec(
            select(BridgeDamageScalePath).where(
                BridgeDamageScalePath.bridge_type_id == data.bridge_type_id,
                BridgeDamageScalePath.part_id == data.part_id,
                BridgeDamageScalePath.structure_type_id == data.structure_type_id,
                BridgeDamageScalePath.component_type_id == data.component_type_id,
                BridgeDamageScalePath.damage_type_id == data.damage_type_id,
                BridgeDamageScalePath.scale_id == scale_id,
            )
        ).first()

        if not existing:
            path = BridgeDamageScalePath(
                bridge_type_id=data.bridge_type_id,
                part_id=data.part_id,
                structure_type_id=data.structure_type_id,
                component_type_id=data.component_type_id,
                damage_type_id=data.damage_type_id,
                scale_id=scale_id,
                sort_order=i,
            )
            session.add(path)
            created_paths.append(scale_id)
        elif not existing.is_active:
            existing.is_active = True
            existing.sort_order = i
            session.add(existing)
            created_paths.append(scale_id)

    session.commit()

    return {
        "message": f"路径 '{bridge_type.name}→{part.name}→{structure_type.name}→{component_type.name}→{damage_type.name}' 创建完成",
        "created_scales": created_paths,
    }


@app.get("/paths/", response_model=List[PathResponse])
def get_paths(
    bridge_type_id: Optional[int] = Query(None),
    part_id: Optional[int] = Query(None),
    structure_type_id: Optional[int] = Query(None),
    component_type_id: Optional[int] = Query(None),
    damage_type_id: Optional[int] = Query(None),
    scale_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    session: Session = Depends(get_session),
):
    """查询路径（支持多维度过滤）"""
    statement = (
        select(
            BridgeDamageScalePath,
            BridgeType.name.label("bridge_type_name"),
            Part.name.label("part_name"),
            StructureType.name.label("structure_type_name"),
            ComponentType.name.label("component_type_name"),
            DamageType.name.label("damage_type_name"),
            Scale.name.label("scale_name"),
            Scale.scale_value,
            Scale.qualitative_description,
            Scale.quantitative_description,
        )
        .join(BridgeType, BridgeDamageScalePath.bridge_type_id == BridgeType.id)
        .join(Part, BridgeDamageScalePath.part_id == Part.id)
        .join(
            StructureType, BridgeDamageScalePath.structure_type_id == StructureType.id
        )
        .join(
            ComponentType, BridgeDamageScalePath.component_type_id == ComponentType.id
        )
        .join(DamageType, BridgeDamageScalePath.damage_type_id == DamageType.id)
        .join(Scale, BridgeDamageScalePath.scale_id == Scale.id)
    )

    # 应用过滤条件
    if bridge_type_id:
        statement = statement.where(
            BridgeDamageScalePath.bridge_type_id == bridge_type_id
        )
    if part_id:
        statement = statement.where(BridgeDamageScalePath.part_id == part_id)
    if structure_type_id:
        statement = statement.where(
            BridgeDamageScalePath.structure_type_id == structure_type_id
        )
    if component_type_id:
        statement = statement.where(
            BridgeDamageScalePath.component_type_id == component_type_id
        )
    if damage_type_id:
        statement = statement.where(
            BridgeDamageScalePath.damage_type_id == damage_type_id
        )
    if scale_id:
        statement = statement.where(BridgeDamageScalePath.scale_id == scale_id)
    if is_active is not None:
        statement = statement.where(BridgeDamageScalePath.is_active == is_active)

    statement = statement.order_by(BridgeDamageScalePath.sort_order)
    results = session.exec(statement).all()

    paths = []
    for (
        path,
        bridge_type_name,
        part_name,
        structure_type_name,
        component_type_name,
        damage_type_name,
        scale_name,
        scale_value,
        qual_desc,
        quant_desc,
    ) in results:
        paths.append(
            PathResponse(
                id=path.id,
                bridge_type_name=bridge_type_name,
                part_name=part_name,
                structure_type_name=structure_type_name,
                component_type_name=component_type_name,
                damage_type_name=damage_type_name,
                scale_name=scale_name,
                scale_value=scale_value,
                qualitative_description=qual_desc,
                quantitative_description=quant_desc,
                sort_order=path.sort_order,
                is_active=path.is_active,
            )
        )

    return paths


@app.get("/paths/scales")
def get_scales_for_path(
    bridge_type_id: int,
    part_id: int,
    structure_type_id: int,
    component_type_id: int,
    damage_type_id: int,
    session: Session = Depends(get_session),
):
    """获取特定路径的可用标度"""
    # 验证路径存在
    bridge_type = session.get(BridgeType, bridge_type_id)
    part = session.get(Part, part_id)
    structure_type = session.get(StructureType, structure_type_id)
    component_type = session.get(ComponentType, component_type_id)
    damage_type = session.get(DamageType, damage_type_id)

    if not all([bridge_type, part, structure_type, component_type, damage_type]):
        raise HTTPException(status_code=400, detail="路径中的某些组件不存在")

    # 查询该路径的所有标度
    statement = (
        select(Scale, BridgeDamageScalePath.sort_order)
        .join(BridgeDamageScalePath, Scale.id == BridgeDamageScalePath.scale_id)
        .where(
            BridgeDamageScalePath.bridge_type_id == bridge_type_id,
            BridgeDamageScalePath.part_id == part_id,
            BridgeDamageScalePath.structure_type_id == structure_type_id,
            BridgeDamageScalePath.component_type_id == component_type_id,
            BridgeDamageScalePath.damage_type_id == damage_type_id,
            BridgeDamageScalePath.is_active == True,
        )
        .order_by(BridgeDamageScalePath.sort_order)
    )

    results = session.exec(statement).all()

    scales = []
    for scale, sort_order in results:
        scales.append(
            ScaleResponse(
                id=scale.id,
                code=scale.code,
                name=scale.name,
                scale_value=scale.scale_value,
                qualitative_description=scale.qualitative_description,
                quantitative_description=scale.quantitative_description,
                is_active=scale.is_active,
                sort_order=sort_order,
            )
        )

    return {
        "path": f"{bridge_type.name}→{part.name}→{structure_type.name}→{component_type.name}→{damage_type.name}",
        "scales": scales,
    }


@app.delete("/paths/{path_id}")
def delete_path(path_id: int, session: Session = Depends(get_session)):
    """删除路径"""
    path = session.get(BridgeDamageScalePath, path_id)
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")

    path.is_active = False
    path.updated_at = datetime.now()
    session.add(path)
    session.commit()

    return {"message": "路径已删除"}


# =============================================================================
# 演示和统计API
# =============================================================================


@app.get("/demo/scenarios")
def get_demo_scenarios(session: Session = Depends(get_session)):
    """获取演示场景验证"""
    scenarios = [
        {
            "description": "梁式桥 → 上部结构 → 钢结构A → 主梁A → 裂缝",
            "bridge_type_id": 1,
            "part_id": 1,
            "structure_type_id": 1,
            "component_type_id": 1,
            "damage_type_id": 1,
            "expected_scales": "1-3级",
        },
        {
            "description": "梁式桥 → 上部结构 → 钢结构B → 主梁B → 裂缝",
            "bridge_type_id": 1,
            "part_id": 1,
            "structure_type_id": 2,
            "component_type_id": 2,
            "damage_type_id": 1,
            "expected_scales": "1-4级",
        },
        {
            "description": "拱式桥 → 主拱圈 → 拱结构C → 拱圈C → 裂缝",
            "bridge_type_id": 2,
            "part_id": 4,
            "structure_type_id": 4,
            "component_type_id": 4,
            "damage_type_id": 1,
            "expected_scales": "1-5级",
        },
    ]

    for scenario in scenarios:
        # 获取实际的标度配置
        try:
            scales_response = get_scales_for_path(
                bridge_type_id=scenario["bridge_type_id"],
                part_id=scenario["part_id"],
                structure_type_id=scenario["structure_type_id"],
                component_type_id=scenario["component_type_id"],
                damage_type_id=scenario["damage_type_id"],
                session=session,
            )
            scenario["actual_scales"] = [s.name for s in scales_response["scales"]]
            scenario["status"] = "✅ 验证成功"
        except Exception as e:
            scenario["actual_scales"] = []
            scenario["status"] = f"❌ 验证失败: {str(e)}"

    return scenarios


@app.get("/demo/structure")
def get_demo_structure(session: Session = Depends(get_session)):
    """获取演示数据结构（原有的简单树形结构）"""
    # 获取完整的数据结构
    bridge_types = session.exec(
        select(BridgeType).where(BridgeType.is_active == True)
    ).all()

    structure = []
    for bridge_type in bridge_types:
        # 通过路径表获取该桥类型的所有部位
        parts_statement = (
            select(Part.id, Part.name, Part.code)
            .join(BridgeDamageScalePath, Part.id == BridgeDamageScalePath.part_id)
            .where(
                BridgeDamageScalePath.bridge_type_id == bridge_type.id,
                BridgeDamageScalePath.is_active == True,
            )
            .distinct()
        )
        parts = session.exec(parts_statement).all()

        bridge_data = {
            "id": bridge_type.id,
            "name": bridge_type.name,
            "code": bridge_type.code,
            "parts": [],
        }

        for part_id, part_name, part_code in parts:
            # 获取该桥类型-部位组合的所有路径
            path_statement = (
                select(
                    StructureType.name.label("structure_type_name"),
                    ComponentType.name.label("component_type_name"),
                    DamageType.name.label("damage_type_name"),
                    Scale.name.label("scale_name"),
                    Scale.scale_value,
                    Scale.qualitative_description,
                    Scale.quantitative_description,
                    BridgeDamageScalePath.sort_order,
                )
                .join(
                    StructureType,
                    BridgeDamageScalePath.structure_type_id == StructureType.id,
                )
                .join(
                    ComponentType,
                    BridgeDamageScalePath.component_type_id == ComponentType.id,
                )
                .join(DamageType, BridgeDamageScalePath.damage_type_id == DamageType.id)
                .join(Scale, BridgeDamageScalePath.scale_id == Scale.id)
                .where(
                    BridgeDamageScalePath.bridge_type_id == bridge_type.id,
                    BridgeDamageScalePath.part_id == part_id,
                    BridgeDamageScalePath.is_active == True,
                )
                .order_by(BridgeDamageScalePath.sort_order)
            )

            path_results = session.exec(path_statement).all()

            # 组织路径数据
            damage_types = {}
            for (
                structure_type_name,
                component_type_name,
                damage_type_name,
                scale_name,
                scale_value,
                qual_desc,
                quant_desc,
                sort_order,
            ) in path_results:

                path_key = f"{structure_type_name} → {component_type_name} → {damage_type_name}"

                if path_key not in damage_types:
                    damage_types[path_key] = {
                        "structure_type_name": structure_type_name,
                        "component_type_name": component_type_name,
                        "damage_type_name": damage_type_name,
                        "scales": [],
                    }

                damage_types[path_key]["scales"].append(
                    {
                        "name": scale_name,
                        "scale_value": scale_value,
                        "qualitative_description": qual_desc,
                        "quantitative_description": quant_desc,
                        "sort_order": sort_order,
                    }
                )

            bridge_data["parts"].append(
                {
                    "id": part_id,
                    "name": part_name,
                    "code": part_code,
                    "damage_types": list(damage_types.values()),
                }
            )

        structure.append(bridge_data)

    return {"structure": structure}


@app.get("/demo/statistics")
def get_demo_statistics(session: Session = Depends(get_session)):
    """获取系统统计信息"""
    # 获取基础数据统计
    basic_stats = {
        "bridge_types": len(
            session.exec(select(BridgeType).where(BridgeType.is_active == True)).all()
        ),
        "parts": len(session.exec(select(Part).where(Part.is_active == True)).all()),
        "structure_types": len(
            session.exec(
                select(StructureType).where(StructureType.is_active == True)
            ).all()
        ),
        "component_types": len(
            session.exec(
                select(ComponentType).where(ComponentType.is_active == True)
            ).all()
        ),
        "damage_types": len(
            session.exec(select(DamageType).where(DamageType.is_active == True)).all()
        ),
        "scales": len(session.exec(select(Scale).where(Scale.is_active == True)).all()),
        "total_paths": len(
            session.exec(
                select(BridgeDamageScalePath).where(
                    BridgeDamageScalePath.is_active == True
                )
            ).all()
        ),
    }

    # 关系统计
    bridge_part_relations = session.exec(
        select(BridgeDamageScalePath.bridge_type_id, BridgeDamageScalePath.part_id)
        .where(BridgeDamageScalePath.is_active == True)
        .distinct()
    ).all()

    component_damage_relations = session.exec(
        select(
            BridgeDamageScalePath.component_type_id,
            BridgeDamageScalePath.damage_type_id,
        )
        .where(BridgeDamageScalePath.is_active == True)
        .distinct()
    ).all()

    relation_stats = {
        "bridge_part_relations": len(bridge_part_relations),
        "component_damage_relations": len(component_damage_relations),
    }

    return {
        "basic_data": basic_stats,
        "relationships": relation_stats,
        "system_info": {
            "architecture": "完整路径表方案",
            "relationship_tables": 0,
            "core_table": "bridge_damage_scale_paths",
            "advantages": [
                "单一数据源，避免数据不一致",
                "支持复杂的多层嵌套关系",
                "维护简单，扩展性好",
                "删除了冗余的中间关系表",
            ],
        },
    }


# =============================================================================
# 批量导入API
# =============================================================================


@app.post("/import/batch", response_model=BatchImportResult)
def batch_import_data(
    request: BatchImportRequest, session: Session = Depends(get_session)
):
    """批量导入桥梁数据

    支持的JSON格式：
    {
        "data": [
            {
                "bridge_type": "梁式桥",
                "part": "上部结构",
                "structure_type": "钢结构A",  // 可选
                "component_type": "主梁A",    // 可选
                "damage_type": "裂缝",
                "scales": ["1级", "2级", "3级"],
                "bridge_type_desc": "以梁作为主要承重结构",  // 可选
                "damage_type_desc": "结构裂缝"  // 可选
            }
        ],
        "options": {
            "skip_existing": true,
            "create_missing": true,
            "validate_only": false
        }
    }
    """

    result = BatchImportResult(
        success=True,
        total_items=len(request.data),
        created_paths=0,
        created_base_data={
            "bridge_types": 0,
            "parts": 0,
            "structure_types": 0,
            "component_types": 0,
            "damage_types": 0,
            "scales": 0,
        },
        skipped_items=0,
        errors=[],
        warnings=[],
    )

    try:
        for idx, item in enumerate(request.data):
            try:
                # 处理单条数据
                item_result = process_import_item(item, request.options, session)

                # 累计结果
                if item_result["created"]:
                    result.created_paths += item_result["created_paths"]
                    for key, count in item_result["created_base_data"].items():
                        result.created_base_data[key] += count
                else:
                    result.skipped_items += 1

                # 收集警告
                result.warnings.extend(item_result.get("warnings", []))

            except Exception as e:
                result.errors.append(
                    {"item_index": idx, "item_data": item.dict(), "error": str(e)}
                )
                result.success = False

        # 如果不是只验证，则提交事务
        if not request.options.get("validate_only", False):
            session.commit()
        else:
            session.rollback()
            result.warnings.append("验证模式：未实际导入数据")

    except Exception as e:
        session.rollback()
        result.success = False
        result.errors.append({"error": f"批量导入失败: {str(e)}"})

    return result


def process_import_item(
    item: BatchImportItem, options: Dict[str, Any], session: Session
) -> Dict[str, Any]:
    """处理单条导入数据"""

    result = {
        "created": False,
        "created_paths": 0,
        "created_base_data": {
            "bridge_types": 0,
            "parts": 0,
            "structure_types": 0,
            "component_types": 0,
            "damage_types": 0,
            "scales": 0,
        },
        "warnings": [],
    }

    # 1. 获取或创建桥类型
    bridge_type = get_or_create_bridge_type(
        item.bridge_type, item.bridge_type_desc, options, session
    )
    if bridge_type and not session.get(BridgeType, bridge_type.id):
        result["created_base_data"]["bridge_types"] += 1

    # 2. 获取或创建部位
    part = get_or_create_part(item.part, item.part_desc, options, session)
    if part and not session.get(Part, part.id):
        result["created_base_data"]["parts"] += 1

    # 3. 处理结构类型（可空）
    structure_type = None
    if item.structure_type:
        structure_type = get_or_create_structure_type(
            item.structure_type, item.structure_type_desc, part.id, options, session
        )
        if structure_type and not session.get(StructureType, structure_type.id):
            result["created_base_data"]["structure_types"] += 1
    else:
        # 如果结构类型为空，创建一个默认的
        structure_type = get_or_create_structure_type(
            f"{item.part}_默认结构",
            f"{item.part}的默认结构类型",
            part.id,
            options,
            session,
        )
        result["warnings"].append(f"为部位 '{item.part}' 创建了默认结构类型")

    # 4. 处理部件类型（可空）
    component_type = None
    if item.component_type:
        component_type = get_or_create_component_type(
            item.component_type,
            item.component_type_desc,
            structure_type.id,
            options,
            session,
        )
        if component_type and not session.get(ComponentType, component_type.id):
            result["created_base_data"]["component_types"] += 1
    else:
        # 如果部件类型为空，创建一个默认的
        component_type = get_or_create_component_type(
            f"{structure_type.name}_默认部件",
            f"{structure_type.name}的默认部件类型",
            structure_type.id,
            options,
            session,
        )
        result["warnings"].append(
            f"为结构类型 '{structure_type.name}' 创建了默认部件类型"
        )

    # 5. 获取或创建病害类型
    damage_type = get_or_create_damage_type(
        item.damage_type, item.damage_type_desc, options, session
    )
    if damage_type and not session.get(DamageType, damage_type.id):
        result["created_base_data"]["damage_types"] += 1

    # 6. 获取或创建标度
    scale_ids = []
    for scale_name in item.scales:
        scale = get_or_create_scale(scale_name, options, session)
        if scale:
            scale_ids.append(scale.id)
            if not session.get(Scale, scale.id):
                result["created_base_data"]["scales"] += 1

    # 7. 创建路径
    if (
        all([bridge_type, part, structure_type, component_type, damage_type])
        and scale_ids
    ):
        created_count = create_paths_for_combination(
            session,
            bridge_type.id,
            part.id,
            structure_type.id,
            component_type.id,
            damage_type.id,
            scale_ids,
            options,
        )
        result["created_paths"] = created_count
        result["created"] = created_count > 0

    return result


# =============================================================================
# 辅助函数：获取或创建基础数据
# =============================================================================


def get_or_create_bridge_type(
    name: str, description: Optional[str], options: Dict[str, Any], session: Session
) -> Optional[BridgeType]:
    """获取或创建桥类型"""
    # 先查找现有的
    existing = session.exec(select(BridgeType).where(BridgeType.name == name)).first()
    if existing:
        return existing

    # 如果不允许创建缺失数据，返回None
    if not options.get("create_missing", True):
        return None

    # 创建新的
    code = name.lower().replace(" ", "_").replace("桥", "_bridge")
    bridge_type = BridgeType(
        code=code, name=name, description=description or f"{name}类型的桥梁"
    )
    session.add(bridge_type)
    session.flush()
    return bridge_type


def get_or_create_part(
    name: str, description: Optional[str], options: Dict[str, Any], session: Session
) -> Optional[Part]:
    """获取或创建部位"""
    existing = session.exec(select(Part).where(Part.name == name)).first()
    if existing:
        return existing

    if not options.get("create_missing", True):
        return None

    code = name.lower().replace(" ", "_")
    part = Part(code=code, name=name, description=description or f"{name}部位")
    session.add(part)
    session.flush()
    return part


def get_or_create_structure_type(
    name: str,
    description: Optional[str],
    part_id: int,
    options: Dict[str, Any],
    session: Session,
) -> Optional[StructureType]:
    """获取或创建结构类型"""
    existing = session.exec(
        select(StructureType).where(
            StructureType.name == name, StructureType.part_id == part_id
        )
    ).first()
    if existing:
        return existing

    if not options.get("create_missing", True):
        return None

    code = name.lower().replace(" ", "_")
    structure_type = StructureType(
        code=code,
        name=name,
        description=description or f"{name}结构类型",
        part_id=part_id,
    )
    session.add(structure_type)
    session.flush()
    return structure_type


def get_or_create_component_type(
    name: str,
    description: Optional[str],
    structure_type_id: int,
    options: Dict[str, Any],
    session: Session,
) -> Optional[ComponentType]:
    """获取或创建部件类型"""
    existing = session.exec(
        select(ComponentType).where(
            ComponentType.name == name,
            ComponentType.structure_type_id == structure_type_id,
        )
    ).first()
    if existing:
        return existing

    if not options.get("create_missing", True):
        return None

    code = name.lower().replace(" ", "_")
    component_type = ComponentType(
        code=code,
        name=name,
        description=description or f"{name}部件类型",
        structure_type_id=structure_type_id,
    )
    session.add(component_type)
    session.flush()
    return component_type


def get_or_create_damage_type(
    name: str, description: Optional[str], options: Dict[str, Any], session: Session
) -> Optional[DamageType]:
    """获取或创建病害类型"""
    existing = session.exec(select(DamageType).where(DamageType.name == name)).first()
    if existing:
        return existing

    if not options.get("create_missing", True):
        return None

    code = name.lower().replace(" ", "_")
    damage_type = DamageType(
        code=code, name=name, description=description or f"{name}病害"
    )
    session.add(damage_type)
    session.flush()
    return damage_type


def get_or_create_scale(
    name: str, options: Dict[str, Any], session: Session
) -> Optional[Scale]:
    """获取或创建标度"""
    existing = session.exec(select(Scale).where(Scale.name == name)).first()
    if existing:
        return existing

    if not options.get("create_missing", True):
        return None

    code = name.lower().replace(" ", "_")
    # 根据名称推断标度值
    scale_value = name
    if "级" in name:
        scale_value = name.replace("级", "")

    scale = Scale(
        code=code,
        name=name,
        scale_value=scale_value,
        qualitative_description=f"{name}程度的缺陷",
        quantitative_description=f"{name}的定量描述",
    )
    session.add(scale)
    session.flush()
    return scale


def create_paths_for_combination(
    session: Session,
    bridge_type_id: int,
    part_id: int,
    structure_type_id: int,
    component_type_id: int,
    damage_type_id: int,
    scale_ids: List[int],
    options: Dict[str, Any],
) -> int:
    """为组合创建路径"""
    created_count = 0

    for i, scale_id in enumerate(scale_ids):
        # 检查路径是否已存在
        existing = session.exec(
            select(BridgeDamageScalePath).where(
                BridgeDamageScalePath.bridge_type_id == bridge_type_id,
                BridgeDamageScalePath.part_id == part_id,
                BridgeDamageScalePath.structure_type_id == structure_type_id,
                BridgeDamageScalePath.component_type_id == component_type_id,
                BridgeDamageScalePath.damage_type_id == damage_type_id,
                BridgeDamageScalePath.scale_id == scale_id,
            )
        ).first()

        if existing:
            if options.get("skip_existing", True):
                continue
            elif not existing.is_active:
                existing.is_active = True
                existing.sort_order = i
                session.add(existing)
                created_count += 1
        else:
            path = BridgeDamageScalePath(
                bridge_type_id=bridge_type_id,
                part_id=part_id,
                structure_type_id=structure_type_id,
                component_type_id=component_type_id,
                damage_type_id=damage_type_id,
                scale_id=scale_id,
                sort_order=i,
            )
            session.add(path)
            created_count += 1

    return created_count


# =============================================================================
# Excel文件导入
# =============================================================================


@app.post("/import/excel", response_model=BatchImportResult)
async def import_excel_file(
    file: UploadFile = File(...),
    skip_existing: bool = True,
    create_missing: bool = True,
    validate_only: bool = False,
    session: Session = Depends(get_session),
):
    """从Excel文件导入数据

    Excel格式：
    桥类型 | 部位 | 结构类型 | 部件类型 | 病害类型 | 标度1 | 标度2 | 标度3 | ...
    """
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="只支持Excel文件")

    try:
        import pandas as pd
        from io import BytesIO

        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))

        # 转换Excel数据为BatchImportItem格式
        import_items = []

        for _, row in df.iterrows():
            # 获取标度列
            scale_columns = [col for col in df.columns if col.startswith("标度")]
            scales = []
            for col in scale_columns:
                if pd.notna(row[col]) and row[col] != "":
                    scales.append(str(row[col]))

            if not scales:
                continue  # 跳过没有标度的行

            item = BatchImportItem(
                bridge_type=str(row["桥类型"]),
                part=str(row["部位"]),
                structure_type=(
                    str(row["结构类型"]) if pd.notna(row.get("结构类型")) else None
                ),
                component_type=(
                    str(row["部件类型"]) if pd.notna(row.get("部件类型")) else None
                ),
                damage_type=str(row["病害类型"]),
                scales=scales,
            )
            import_items.append(item)

        # 执行批量导入
        request = BatchImportRequest(
            data=import_items,
            options={
                "skip_existing": skip_existing,
                "create_missing": create_missing,
                "validate_only": validate_only,
            },
        )

        return batch_import_data(request, session)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel文件处理失败: {str(e)}")


# =============================================================================
# JSON文件导入
# =============================================================================


@app.post("/import/json", response_model=BatchImportResult)
async def import_json_file(
    file: UploadFile = File(...), session: Session = Depends(get_session)
):
    """从JSON文件导入数据"""
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="只支持JSON文件")

    try:
        contents = await file.read()
        data = json.loads(contents)

        # 验证JSON格式
        if isinstance(data, dict) and "data" in data:
            request = BatchImportRequest(**data)
        elif isinstance(data, list):
            request = BatchImportRequest(data=data)
        else:
            raise HTTPException(status_code=400, detail="JSON格式不正确")

        return batch_import_data(request, session)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JSON文件处理失败: {str(e)}")


# =============================================================================
# 导入模板生成
# =============================================================================


@app.get("/import/template/json")
def generate_json_template():
    """生成JSON导入模板"""
    template = {
        "data": [
            {
                "bridge_type": "梁式桥",
                "part": "上部结构",
                "structure_type": "钢结构A",  # 可选，为null时会自动创建默认值
                "component_type": "主梁A",  # 可选，为null时会自动创建默认值
                "damage_type": "裂缝",
                "scales": ["1级", "2级", "3级"],
                "bridge_type_desc": "以梁作为主要承重结构的桥梁",  # 可选
                "part_desc": "桥梁上部结构",  # 可选
                "structure_type_desc": "钢结构类型A",  # 可选
                "component_type_desc": "主梁类型A",  # 可选
                "damage_type_desc": "结构裂缝",  # 可选
            },
            {
                "bridge_type": "梁式桥",
                "part": "上部结构",
                "structure_type": "钢结构B",
                "component_type": "主梁B",
                "damage_type": "裂缝",
                "scales": ["1级", "2级", "3级", "4级"],
            },
            {
                "bridge_type": "拱式桥",
                "part": "主拱圈",
                "structure_type": None,  # 结构类型为空，会自动创建默认值
                "component_type": None,  # 部件类型为空，会自动创建默认值
                "damage_type": "裂缝",
                "scales": ["1级", "2级", "3级", "4级", "5级"],
            },
        ],
        "options": {
            "skip_existing": True,  # 跳过已存在的路径
            "create_missing": True,  # 自动创建缺失的基础数据
            "validate_only": False,  # false=实际导入，true=只验证
        },
    }

    return {
        "template": template,
        "usage": {
            "description": "批量导入桥梁数据的JSON模板",
            "required_fields": ["bridge_type", "part", "damage_type", "scales"],
            "optional_fields": ["structure_type", "component_type", "*_desc"],
            "null_handling": "结构类型和部件类型可以为null，系统会自动创建默认值",
            "scales_format": "标度为字符串数组，系统会自动解析",
            "options": {
                "skip_existing": "是否跳过已存在的路径",
                "create_missing": "是否自动创建缺失的基础数据",
                "validate_only": "是否只验证不实际导入",
            },
        },
    }


@app.get("/import/template/excel")
def generate_excel_template():
    """生成Excel导入模板"""
    template_data = [
        {
            "桥类型": "梁式桥",
            "部位": "上部结构",
            "结构类型": "钢结构A",
            "部件类型": "主梁A",
            "病害类型": "裂缝",
            "标度1": "1级",
            "标度2": "2级",
            "标度3": "3级",
            "标度4": "",
            "标度5": "",
        },
        {
            "桥类型": "梁式桥",
            "部位": "上部结构",
            "结构类型": "钢结构B",
            "部件类型": "主梁B",
            "病害类型": "裂缝",
            "标度1": "1级",
            "标度2": "2级",
            "标度3": "3级",
            "标度4": "4级",
            "标度5": "",
        },
        {
            "桥类型": "拱式桥",
            "部位": "主拱圈",
            "结构类型": "",  # 空值示例
            "部件类型": "",  # 空值示例
            "病害类型": "裂缝",
            "标度1": "1级",
            "标度2": "2级",
            "标度3": "3级",
            "标度4": "4级",
            "标度5": "5级",
        },
    ]

    return {
        "template_data": template_data,
        "usage": {
            "description": "Excel批量导入模板",
            "required_columns": ["桥类型", "部位", "病害类型", "标度1"],
            "optional_columns": ["结构类型", "部件类型", "标度2-标度5"],
            "null_handling": "结构类型和部件类型可以留空，系统会自动创建默认值",
            "scales_handling": "标度列按需填写，空列会被忽略",
            "file_format": "支持.xlsx和.xls格式",
        },
    }


# =============================================================================
# 验证和预览功能
# =============================================================================


@app.post("/import/validate")
def validate_import_data(
    request: BatchImportRequest, session: Session = Depends(get_session)
):
    """验证导入数据（不实际导入）"""
    request.options["validate_only"] = True
    return batch_import_data(request, session)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
