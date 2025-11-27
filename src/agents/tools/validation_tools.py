"""
验证工具 - 参数验证相关的原子工具

功能：
1. 成分验证
2. 工艺参数验证
3. 成分归一化
"""
from typing import Dict, Any, List
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


# ==================== Pydantic Schema 定义 ====================

class CompositionInput(BaseModel):
    """成分验证输入参数"""
    al_content: float = Field(..., description="Al含量 (at.%)", ge=0, le=100)
    ti_content: float = Field(..., description="Ti含量 (at.%)", ge=0, le=100)
    n_content: float = Field(..., description="N含量 (at.%)", ge=0, le=100)
    other_elements: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="其他添加元素列表，格式：[{name: str, content: float}]"
    )


class ProcessParamsInput(BaseModel):
    """工艺参数验证输入"""
    process_type: str = Field(..., description="工艺类型")
    deposition_temperature: float = Field(..., description="沉积温度 (°C)", ge=0, le=1000)
    deposition_pressure: float = Field(default=0.5, description="沉积气压 (Pa)", ge=0)
    bias_voltage: float = Field(default=-100, description="偏压 (V)")
    n2_flow: float = Field(default=50, description="N₂流量 (sccm)", ge=0)


class NormalizeInput(BaseModel):
    """成分归一化输入"""
    composition: Dict[str, Any] = Field(..., description="原始成分数据")


# ==================== 工具定义 ====================

@tool(args_schema=CompositionInput)
def validate_composition_tool(
    al_content: float,
    ti_content: float,
    n_content: float,
    other_elements: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    验证涂层成分配比是否合理。
    
    检查内容：
    - 主要成分（Al/Ti/N）总量是否接近100%
    - 各成分是否在合理范围内
    - AlTiN 涂层的典型成分比例
    
    Returns:
        验证结果，包含 is_valid, errors, warnings
    """
    logger.info(f"[验证工具] 成分验证: Al={al_content}%, Ti={ti_content}%, N={n_content}%")
    
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
        "al_ti_ratio": al_content / metal_total if metal_total > 0 else 0
    }


@tool(args_schema=ProcessParamsInput)
def validate_process_params_tool(
    process_type: str,
    deposition_temperature: float,
    deposition_pressure: float = 0.5,
    bias_voltage: float = -100,
    n2_flow: float = 50
) -> Dict[str, Any]:
    """
    验证工艺参数是否合理。
    
    检查内容：
    - 沉积温度是否在工艺允许范围
    - 偏压是否合理
    - 气压和气体流量是否匹配
    
    Returns:
        验证结果，包含 is_valid, errors, warnings
    """
    logger.info(f"[验证工具] 工艺参数验证: {process_type}, {deposition_temperature}°C")
    
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


@tool(args_schema=NormalizeInput)
def normalize_composition_tool(composition: Dict[str, Any]) -> Dict[str, Any]:
    """
    将成分配比归一化到100%。
    
    当成分总和不等于100%时，按比例调整各成分含量。
    
    Returns:
        归一化后的成分数据
    """
    logger.info("[验证工具] 成分归一化")
    
    # 计算总量
    al = composition.get("al_content", 0) or 0
    ti = composition.get("ti_content", 0) or 0
    n = composition.get("n_content", 0) or 0
    
    other_total = 0
    other_elements = composition.get("other_elements", [])
    for elem in other_elements:
        other_total += elem.get("content", 0) or 0
    
    total = al + ti + n + other_total
    
    # 无需归一化
    if total == 0 or abs(total - 100) < 0.1:
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
