"""
验证工具 - 参数验证相关的原子工具

功能：
1. 成分验证
2. 工艺参数验证
3. 成分归一化

更新说明 (v2.1)：
- 使用 ToolRuntime 从状态自动获取参数
- 工具无需 LLM 传递复杂参数，减少错误
"""
from typing import Dict, Any, List, Optional
from langchain.tools import tool, ToolRuntime
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


# ==================== 内部验证函数 ====================
# 将验证逻辑抽取为独立函数，供工具调用

def _validate_composition_logic(
    al_content: float,
    ti_content: float,
    n_content: float,
    other_elements: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    验证涂层成分配比的核心逻辑
    
    Args:
        al_content: Al含量 (at.%)
        ti_content: Ti含量 (at.%)
        n_content: N含量 (at.%)
        other_elements: 其他添加元素列表
    
    Returns:
        验证结果，包含 is_valid, errors, warnings
    """
    errors = []
    warnings = []
    
    # 计算总成分
    total = al_content + ti_content + n_content
    if other_elements:
        for elem in other_elements:
            total += elem.get("content", 0)
    
    # 检查总量
    if total < 50:
        errors.append(f"成分总量过低 ({total:.1f}%)，无法形成有效涂层")
    elif abs(total - 100) > 5:
        warnings.append(f"成分总量为 {total:.1f}%，建议调整至接近 100%")
    
    # 检查 N 含量（AlTiN 涂层通常 N 含量在 45-55%）
    if n_content < 40:
        warnings.append(f"N含量偏低 ({n_content}%)，可能影响氮化物相的形成")
    elif n_content > 60:
        warnings.append(f"N含量偏高 ({n_content}%)，可能导致 N 过饱和")
    
    # 检查 Al/(Al+Ti) 比例
    metal_total = al_content + ti_content
    al_ratio = 0
    if metal_total > 0:
        al_ratio = al_content / metal_total
        if al_ratio > 0.7:
            warnings.append(f"Al/(Al+Ti)比例 ({al_ratio:.2f}) 偏高，硬度可能受限")
        elif al_ratio < 0.3:
            warnings.append(f"Al/(Al+Ti)比例 ({al_ratio:.2f}) 偏低，抗氧化性可能不足")
    
    is_valid = len(errors) == 0
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "total_content": total,
        "al_ti_ratio": al_ratio
    }


def _validate_process_params_logic(
    process_type: str,
    deposition_temperature: float,
    deposition_pressure: float = 0.5,
    bias_voltage: float = -100,
    n2_flow: float = 50
) -> Dict[str, Any]:
    """
    验证工艺参数的核心逻辑
    
    Args:
        process_type: 工艺类型
        deposition_temperature: 沉积温度 (°C)
        deposition_pressure: 沉积气压 (Pa)
        bias_voltage: 偏压 (V)
        n2_flow: N₂流量 (sccm)
    
    Returns:
        验证结果，包含 is_valid, errors, warnings
    """
    errors = []
    warnings = []
    
    # 温度范围检查
    valid_temp_ranges = {
        "magnetron_sputtering": (200, 600),
        "arc_ion_plating": (200, 550),
        "cvd": (400, 1000),
        "pecvd": (150, 500),
    }
    
    temp_range = valid_temp_ranges.get(process_type, (200, 600))
    if deposition_temperature < temp_range[0]:
        warnings.append(f"温度 ({deposition_temperature}°C) 低于推荐范围 {temp_range[0]}°C")
    elif deposition_temperature > temp_range[1]:
        errors.append(f"温度 ({deposition_temperature}°C) 超过工艺上限 {temp_range[1]}°C")
    
    # 偏压检查（PVD 工艺）
    if process_type in ["magnetron_sputtering", "arc_ion_plating"]:
        if abs(bias_voltage) < 50:
            warnings.append(f"偏压 ({bias_voltage}V) 偏低，可能影响涂层致密度")
        elif abs(bias_voltage) > 300:
            warnings.append(f"偏压 ({bias_voltage}V) 偏高，可能导致过大残余应力")
    
    # 气压检查
    if deposition_pressure < 0.1:
        warnings.append(f"气压 ({deposition_pressure}Pa) 偏低")
    elif deposition_pressure > 5:
        warnings.append(f"气压 ({deposition_pressure}Pa) 偏高，可能降低沉积速率")
    
    is_valid = len(errors) == 0
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "process_type": process_type,
        "recommended_temp_range": temp_range
    }


# ==================== 工具定义（使用 ToolRuntime） ====================

@tool
def validate_composition_tool(runtime: ToolRuntime) -> Dict[str, Any]:
    """
    验证涂层成分配比是否合理。
    
    自动从当前状态获取成分数据进行验证，无需手动传递参数。
    
    检查内容：
    - 主要成分（Al/Ti/N）总量是否接近100%
    - 各成分是否在合理范围内
    - AlTiN 涂层的典型成分比例
    
    Returns:
        验证结果，包含 is_valid, errors, warnings
    """
    # 从状态自动获取成分数据
    state = runtime.state
    composition = state.get("coating_composition", {})
    
    al_content = composition.get("al_content", 0) or 0
    ti_content = composition.get("ti_content", 0) or 0
    n_content = composition.get("n_content", 0) or 0
    other_elements = composition.get("other_elements", [])
    
    logger.info(f"[验证工具] 成分验证: Al={al_content}%, Ti={ti_content}%, N={n_content}%")
    
    # 检查是否有成分数据
    if al_content == 0 and ti_content == 0 and n_content == 0:
        return {
            "is_valid": False,
            "errors": ["未提供涂层成分数据，请先输入成分配比"],
            "warnings": [],
            "total_content": 0,
            "al_ti_ratio": 0
        }
    
    # 调用验证逻辑
    return _validate_composition_logic(al_content, ti_content, n_content, other_elements)


@tool
def validate_process_params_tool(runtime: ToolRuntime) -> Dict[str, Any]:
    """
    验证工艺参数是否合理。
    
    自动从当前状态获取工艺参数进行验证，无需手动传递参数。
    
    检查内容：
    - 沉积温度是否在工艺允许范围
    - 偏压是否合理
    - 气压和气体流量是否匹配
    
    Returns:
        验证结果，包含 is_valid, errors, warnings
    """
    # 从状态自动获取工艺参数
    state = runtime.state
    process_params = state.get("process_params", {})
    
    process_type = process_params.get("process_type", "magnetron_sputtering")
    deposition_temperature = process_params.get("deposition_temperature", 0) or 0
    deposition_pressure = process_params.get("deposition_pressure", 0.5) or 0.5
    bias_voltage = process_params.get("bias_voltage", -100) or -100
    n2_flow = process_params.get("n2_flow", 50) or 50
    
    logger.info(f"[验证工具] 工艺参数验证: {process_type}, {deposition_temperature}°C")
    
    # 检查是否有工艺参数
    if deposition_temperature == 0:
        return {
            "is_valid": False,
            "errors": ["未提供工艺参数，请先输入沉积温度等参数"],
            "warnings": [],
            "process_type": process_type,
            "recommended_temp_range": (200, 600)
        }
    
    # 调用验证逻辑
    return _validate_process_params_logic(
        process_type, deposition_temperature, deposition_pressure, bias_voltage, n2_flow
    )


@tool
def normalize_composition_tool(runtime: ToolRuntime) -> Dict[str, Any]:
    """
    将成分配比归一化到100%。
    
    自动从当前状态获取成分数据，当成分总和不等于100%时，按比例调整各成分含量。
    
    Returns:
        归一化后的成分数据
    """
    logger.info("[验证工具] 成分归一化")
    
    # 从状态获取成分数据
    state = runtime.state
    composition = state.get("coating_composition", {})
    
    # 计算总量
    al = composition.get("al_content", 0) or 0
    ti = composition.get("ti_content", 0) or 0
    n = composition.get("n_content", 0) or 0
    
    other_total = 0
    other_elements = composition.get("other_elements", [])
    for elem in other_elements:
        other_total += elem.get("content", 0) or 0
    
    total = al + ti + n + other_total
    
    # 检查是否有数据
    if total == 0:
        return {
            "normalized": {},
            "original_total": 0,
            "scaling_factor": 1.0,
            "message": "未提供成分数据"
        }
    
    # 无需归一化
    if abs(total - 100) < 0.1:
        return {
            "normalized": composition.copy(),
            "original_total": total,
            "scaling_factor": 1.0
        }
    
    # 归一化
    factor = 100.0 / total
    normalized = {
        "al_content": al * factor,
        "ti_content": ti * factor,
        "n_content": n * factor,
    }
    
    # 归一化其他元素
    if other_elements:
        normalized["other_elements"] = [
            {
                "name": elem.get("name", ""),
                "content": (elem.get("content", 0) or 0) * factor
            }
            for elem in other_elements
        ]
    
    logger.info(f"[验证工具] 归一化完成: {total:.1f}% → 100%")
    
    return {
        "normalized": normalized,
        "original_total": total,
        "scaling_factor": factor
    }
