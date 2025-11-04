"""
数据格式化工具 - 为参数添加单位信息
"""
from typing import Dict, Any, List


# 单位定义常量
UNITS = {
    # 成分单位
    "composition": {
        "al_content": "at.%",
        "ti_content": "at.%",
        "n_content": "at.%",
        "content": "at.%"
    },
    # 工艺参数单位
    "process": {
        "deposition_pressure": "Pa",
        "bias_voltage": "V",
        "deposition_temperature": "℃",
        "n2_flow": "sccm",
        "flow": "sccm",
        "target_power_al": "W",
        "target_power_ti": "W",
        "substrate_rotation": "rpm"
    },
    # 结构设计单位
    "structure": {
        "total_thickness": "μm",
        "thickness": "μm"
    },
    # 性能需求单位
    "requirements": {
        "hardness_requirement": "GPa",
        "adhesion_requirement": "N",
        "adhesion_strength": "N",
        "elastic_modulus": "GPa",
        "working_temperature": "℃",
        "cutting_speed": "m/min"
    }
}


def format_value_with_unit(value: Any, field_name: str, category: str) -> str:
    """
    格式化数值并添加单位
    
    Args:
        value: 原始数值
        field_name: 字段名
        category: 类别（composition/process/structure/requirements）
    
    Returns:
        带单位的字符串，如 "30.0 at.%"
    """
    if value is None:
        return "N/A"
    
    unit = UNITS.get(category, {}).get(field_name, "")
    
    # 根据类型格式化数值
    if isinstance(value, float):
        # 保留1位小数
        formatted_value = f"{value:.1f}"
    elif isinstance(value, int):
        formatted_value = str(value)
    else:
        formatted_value = str(value)
    
    return f"{formatted_value} {unit}" if unit else formatted_value


def format_composition_with_units(composition: Dict[str, Any]) -> Dict[str, Any]:
    """
    为涂层成分数据添加单位信息
    
    Args:
        composition: 原始成分数据
    
    Returns:
        带单位的成分数据
    """
    formatted = {
        "al_content": format_value_with_unit(composition.get("al_content"), "al_content", "composition"),
        "ti_content": format_value_with_unit(composition.get("ti_content"), "ti_content", "composition"),
        "n_content": format_value_with_unit(composition.get("n_content"), "n_content", "composition"),
    }
    
    # 处理其他元素
    if composition.get("other_elements"):
        formatted["other_elements"] = []
        for elem in composition["other_elements"]:
            formatted["other_elements"].append({
                "name": elem.get("name", "Unknown"),
                "content": format_value_with_unit(elem.get("content"), "content", "composition")
            })
    else:
        formatted["other_elements"] = "无"
    
    return formatted


def format_process_params_with_units(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    为工艺参数数据添加单位信息
    
    Args:
        params: 原始工艺参数数据
    
    Returns:
        带单位的工艺参数数据
    """
    formatted = {
        "process_type": params.get("process_type", "N/A"),
        "deposition_pressure": format_value_with_unit(params.get("deposition_pressure"), "deposition_pressure", "process"),
        "bias_voltage": format_value_with_unit(params.get("bias_voltage"), "bias_voltage", "process"),
        "deposition_temperature": format_value_with_unit(params.get("deposition_temperature"), "deposition_temperature", "process"),
        "n2_flow": format_value_with_unit(params.get("n2_flow"), "n2_flow", "process"),
    }
    
    # 处理其他气体
    if params.get("other_gases"):
        formatted["other_gases"] = []
        for gas in params["other_gases"]:
            formatted["other_gases"].append({
                "type": gas.get("type", "Unknown"),
                "flow": format_value_with_unit(gas.get("flow"), "flow", "process")
            })
    else:
        formatted["other_gases"] = "无"
    
    return formatted


def format_structure_with_units(structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    为结构设计数据添加单位信息
    
    Args:
        structure: 原始结构设计数据
    
    Returns:
        带单位的结构设计数据
    """
    formatted = {
        "structure_type": structure.get("structure_type", "single"),
        "total_thickness": format_value_with_unit(structure.get("total_thickness"), "total_thickness", "structure"),
    }
    
    # 处理多层结构
    if structure.get("layers"):
        formatted["layers"] = []
        for layer in structure["layers"]:
            formatted["layers"].append({
                "type": layer.get("type", "Unknown"),
                "thickness": format_value_with_unit(layer.get("thickness"), "thickness", "structure")
            })
    
    return formatted


def format_requirements_with_units(requirements: Dict[str, Any]) -> Dict[str, Any]:
    """
    为性能需求数据添加单位信息
    
    Args:
        requirements: 原始性能需求数据
    
    Returns:
        带单位的性能需求数据
    """
    formatted = {
        "substrate_material": requirements.get("substrate_material", "N/A"),
        "application_scenario": requirements.get("application_scenario", "N/A"),
    }
    
    # 添加可选的性能参数
    optional_fields = [
        "hardness_requirement", "adhesion_requirement", "adhesion_strength",
        "elastic_modulus", "working_temperature", "cutting_speed"
    ]
    
    for field in optional_fields:
        if field in requirements:
            formatted[field] = format_value_with_unit(requirements.get(field), field, "requirements")
    
    return formatted


def format_full_parameters_with_units(
    composition: Dict[str, Any],
    process_params: Dict[str, Any],
    structure: Dict[str, Any],
    requirements: Dict[str, Any]
) -> Dict[str, Any]:
    """
    格式化完整的参数数据，添加所有单位信息
    
    Args:
        composition: 涂层成分
        process_params: 工艺参数
        structure: 结构设计
        requirements: 性能需求
    
    Returns:
        完整的带单位参数数据
    """
    return {
        "coating_composition": format_composition_with_units(composition),
        "process_params": format_process_params_with_units(process_params),
        "structure_design": format_structure_with_units(structure),
        "target_requirements": format_requirements_with_units(requirements)
    }
