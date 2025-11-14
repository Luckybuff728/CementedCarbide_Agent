"""
涂层参数数据模型定义
"""
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class CoatingComposition(BaseModel):
    """涂层成分模型"""
    # 主要元素成分 (Al、Ti、N)
    al_content: float = Field(..., ge=0, le=100, description="铝含量(at.%)")
    ti_content: float = Field(..., ge=0, le=100, description="钛含量(at.%)")
    n_content: float = Field(..., ge=0, le=100, description="氮含量(at.%)")
    
    # 其他元素配置
    other_elements: List[Dict[str, float]] = Field(
        default_factory=list,
        description="其他元素列表，格式：[{'name': 'Cr', 'content': 2.5}]"
    )
    
    @validator('al_content', 'ti_content', 'n_content')
    def validate_individual_content(cls, v):
        """验证单个元素含量范围"""
        if not 0 <= v <= 100:
            raise ValueError(f"元素含量必须在0-100%之间，当前值: {v}%")
        return v


class ProcessParameters(BaseModel):
    """工艺参数模型"""
    # 工艺选择 - 放在最前面
    process_type: Literal["magnetron_sputtering", "cvd"] = Field(
        "magnetron_sputtering", 
        description="工艺选择：磁控溅射或CVD"
    )
    
    # 基础工艺参数
    deposition_pressure: float = Field(0.6, description="沉积气压(Pa)")
    bias_voltage: float = Field(90, description="偏压(V)")
    deposition_temperature: float = Field(550, description="沉积温度(℃)")
    
    # 气体流量配置
    n2_flow: float = Field(210, description="N2流量(sccm)")
    
    # 其他气体配置（包括Ar、Kr等）
    other_gases: List[Dict[str, float]] = Field(
        default_factory=list,
        description="其他气体配置，格式：[{'type': 'Ar', 'flow': 280}]"
    )
    
    # PVD特有参数
    target_power_al: Optional[float] = Field(None, description="Al靶材功率(W)")
    target_power_ti: Optional[float] = Field(None, description="Ti靶材功率(W)")
    substrate_rotation: Optional[float] = Field(None, description="基体旋转速度(rpm)")
    

class LayerConfig(BaseModel):
    """单层配置模型"""
    layer_name: str = Field(..., description="层名称")
    layer_type: Literal["AlTiN", "TiN", "AlN", "TiAlN", "CrN", "custom"] = Field(
        "AlTiN", description="层类型"
    )
    thickness: float = Field(..., gt=0, description="厚度(μm)")
    composition: Optional[Dict[str, float]] = Field(
        None, description="该层的元素组成(如果是custom类型)"
    )
    

class StructureDesign(BaseModel):
    """涂层结构设计模型"""
    total_thickness: float = Field(..., gt=0, description="总厚度(μm)")
    structure_type: Literal["single_layer", "multi_layer", "gradient"] = Field(
        "single_layer", description="结构类型：单层/多层/梯度"
    )
    
    # 多层结构配置
    layers: List[LayerConfig] = Field(
        default_factory=list,
        description="各层配置（当选择多层时）"
    )
    
    # 梯度结构参数
    gradient_profile: Optional[Dict[str, Any]] = Field(
        None, description="梯度分布参数（当选择梯度时）"
    )
    

class TargetRequirements(BaseModel):
    """目标性能需求模型"""
    # 基体选择 - 放在最前面
    substrate_material: str = Field(..., description="基体材料选择")
    
    # 核心性能指标
    hardness_requirement: Optional[float] = Field(None, description="硬度要求(GPa)")
    adhesion_requirement: Optional[float] = Field(None, description="结合力要求(N)")
    elastic_modulus: Optional[float] = Field(None, description="弹性模量(GPa)")
    
    # 应用场景描述（带提示词）
    application_scenario: str = Field(
        ..., 
        description="应用场景（温度、切削材料、切削速度等）"
    )
    
    # 工作环境参数
    working_temperature: Optional[float] = Field(None, description="工作温度(℃)")
    cutting_material: Optional[str] = Field(None, description="切削材料")
    cutting_speed: Optional[float] = Field(None, description="切削速度(m/min)")
    
    # 其他性能要求
    wear_resistance: Optional[str] = Field(None, description="耐磨性要求")
    oxidation_resistance: Optional[str] = Field(None, description="抗氧化性要求")
    other_requirements: Optional[str] = Field(None, description="其他要求")


class CoatingInput(BaseModel):
    """涂层输入参数汇总模型"""
    # 按照涂层成分.md的顺序排列
    composition: CoatingComposition          # 1. 涂层成分
    process_params: ProcessParameters       # 2. 工艺参数  
    structure_design: StructureDesign       # 3. 结构设计
    target_requirements: TargetRequirements # 4. 性能需求
    
    # 额外信息
    additional_info: Optional[Dict] = Field(default_factory=dict)
    
    @validator('composition')
    def validate_composition_sum(cls, v):
        """验证成分总和"""
        total = v.al_content + v.ti_content + v.n_content
        for element in v.other_elements:
            total += element.get('content', 0)
        
        if total > 100.1:  # 允许小的数值误差
            raise ValueError(f"成分总和不能超过100%，当前总和: {total:.1f}%")
        return v
    
    @validator('structure_design')
    def validate_layer_structure(cls, v):
        """验证层结构配置"""
        if v.structure_type == "multi_layer" and not v.layers:
            raise ValueError("多层结构必须配置至少一层")
        
        # 验证总厚度与各层厚度的一致性
        if v.layers:
            total_layer_thickness = sum(layer.thickness for layer in v.layers)
            if abs(total_layer_thickness - v.total_thickness) > 0.1:
                raise ValueError(
                    f"各层厚度之和({total_layer_thickness:.1f}μm)与总厚度({v.total_thickness:.1f}μm)不一致"
                )
        
        return v
