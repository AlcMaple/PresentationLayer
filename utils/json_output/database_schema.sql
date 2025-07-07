
-- 桥梁数据库Schema建议
-- 生成时间: 2025-07-07T10:56:04.939621

-- 1. 桥梁类型表
CREATE TABLE bridge_types (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. 部位表
CREATE TABLE parts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    bridge_type_id INT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bridge_type_id) REFERENCES bridge_types(id) ON DELETE CASCADE,
    INDEX idx_bridge_type (bridge_type_id)
);

-- 3. 结构类型表
CREATE TABLE structure_types (
    id INT PRIMARY KEY AUTO_INCREMENT,
    part_id INT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (part_id) REFERENCES parts(id) ON DELETE CASCADE,
    INDEX idx_part (part_id)
);

-- 4. 部件类型表
CREATE TABLE component_types (
    id INT PRIMARY KEY AUTO_INCREMENT,
    structure_type_id INT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (structure_type_id) REFERENCES structure_types(id) ON DELETE CASCADE,
    INDEX idx_structure_type (structure_type_id)
);

-- 5. 构件形式表
CREATE TABLE component_forms (
    id INT PRIMARY KEY AUTO_INCREMENT,
    component_type_id INT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (component_type_id) REFERENCES component_types(id) ON DELETE CASCADE,
    INDEX idx_component_type (component_type_id)
);

-- 6. 病害类型表
CREATE TABLE damage_types (
    id INT PRIMARY KEY AUTO_INCREMENT,
    component_form_id INT,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (component_form_id) REFERENCES component_forms(id) ON DELETE CASCADE,
    INDEX idx_component_form (component_form_id)
);

-- 7. 评估标准表（标度、定性描述、定量描述）
CREATE TABLE evaluation_standards (
    id INT PRIMARY KEY AUTO_INCREMENT,
    damage_type_id INT,
    scale_value VARCHAR(50) NOT NULL,
    qualitative_description TEXT,
    quantitative_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (damage_type_id) REFERENCES damage_types(id) ON DELETE CASCADE,
    INDEX idx_damage_type (damage_type_id),
    INDEX idx_scale (scale_value)
);

-- 8. 数据导入日志表
CREATE TABLE import_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    source_file VARCHAR(255),
    sheet_name VARCHAR(100),
    records_imported INT,
    import_status ENUM('success', 'failed', 'partial'),
    error_message TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
