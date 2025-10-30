"""
涂层参数数据模型定义
"""
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class CoatingComposition(BaseModel):
    """涂层成分模型"""
    al_content: float = Field(..., ge=0, le=100, description="铝含量(%)")
    ti_content: float = Field(..., ge=0, le=100, description="钛含量(%)")
    n_content: float = Field(..., ge=0, le=100, description="氮含量(%)")
    x_element: Optional[str] = Field(None, description="X元素类型")
    x_content: Optional[float] = Field(0, ge=0, le=100, description="X元素含量(%)")
    
    @validator('al_content', 'ti_content', 'n_content', 'x_content')
    def validate_sum(cls, v, values):
        """验证成分总和不超过100%"""
        total = sum([
            values.get('al_content', 0),
            values.get('ti_content', 0),
            values.get('n_content', 0),
            values.get('x_content', 0)
        ])
        if total > 100:
            raise ValueError(f"成分总和不能超过100%，当前总和: {total}%")
        return v


class ProcessParameters(BaseModel):
    """工艺参数模型"""
    deposition_pressure: float = Field(0.6, description="沉积气压(Pa)")
    n2_flow: float = Field(210, description="N2流量(sccm)")
    ar_flow: float = Field(280, description="Ar流量(sccm)")
    kr_flow: float = Field(200, description="Kr流量(sccm)")
    bias_voltage: float = Field(90, description="偏压(V)")
    deposition_temperature: float = Field(550, description="沉积温度(℃)")
    

class StructureDesign(BaseModel):
    """涂层结构设计模型"""
    total_thickness: float = Field(..., gt=0, description="总厚度(μm)")
    layers: List[Dict[str, float]] = Field(
        default_factory=list,
        description="各层结构和占比"
    )
    

class TargetRequirements(BaseModel):
    """目标性能需求模型"""
    application_scenario: str = Field(..., description="应用场景")
    hardness_requirement: Optional[float] = Field(None, description="硬度要求(GPa)")
    adhesion_requirement: Optional[str] = Field(None, description="结合力要求")
    wear_resistance: Optional[str] = Field(None, description="耐磨性要求")
    oxidation_resistance: Optional[str] = Field(None, description="抗氧化性要求")
    other_requirements: Optional[str] = Field(None, description="其他要求")


class CoatingInput(BaseModel):
    """涂层输入参数汇总模型"""
    composition: CoatingComposition
    process_params: ProcessParameters
    structure_design: StructureDesign
    target_requirements: TargetRequirements
    additional_info: Optional[Dict] = Field(default_factory=dict)


class PerformancePrediction(BaseModel):
    """性能预测结果模型"""
    hardness: Optional[float] = Field(None, description="预测硬度(GPa)")
    adhesion_level: Optional[str] = Field(None, description="预测结合力等级")
    wear_rate: Optional[float] = Field(None, description="磨损率")
    oxidation_temperature: Optional[float] = Field(None, description="抗氧化温度(℃)")
    deposition_structure: Optional[Dict] = Field(None, description="沉积结构预测")
    confidence_score: float = Field(0.0, description="预测置信度(0-1)")


class OptimizationSuggestion(BaseModel):
    """优化建议模型"""
    optimization_type: Literal["P1", "P2", "P3"] = Field(..., description="优化类型")
    category_name: str = Field(..., description="类别名称")
    suggestions: List[Dict[str, Any]] = Field(..., description="具体建议列表")
    expected_improvement: Dict[str, float] = Field(
        default_factory=dict,
        description="预期改进"
    )
    priority: int = Field(1, ge=1, le=5, description="优先级(1-5)")
    rationale: str = Field(..., description="建议理由")


class ExperimentResult(BaseModel):
    """实验结果模型"""
    experiment_id: str = Field(..., description="实验ID")
    actual_hardness: Optional[float] = Field(None, description="实际硬度(GPa)")
    sem_images: Optional[List[str]] = Field(None, description="SEM图像路径")
    actual_performance: Dict[str, Any] = Field(default_factory=dict)
    deviation_analysis: Optional[str] = Field(None, description="偏差分析")
    timestamp: datetime = Field(default_factory=datetime.now)


class IterationState(BaseModel):
    """迭代状态模型"""
    iteration_number: int = Field(0, description="迭代次数")
    current_performance: Dict[str, float] = Field(default_factory=dict)
    optimization_history: List[OptimizationSuggestion] = Field(default_factory=list)
    experiment_history: List[ExperimentResult] = Field(default_factory=list)
    convergence_status: str = Field("ongoing", description="收敛状态")


class CoatingTask(BaseModel):
    """涂层任务完整模型"""
    task_id: str = Field(..., description="任务ID")
    input_params: CoatingInput
    prediction_results: Optional[PerformancePrediction] = None
    optimization_suggestions: List[OptimizationSuggestion] = Field(default_factory=list)
    selected_optimization: Optional[str] = None
    iteration_state: IterationState = Field(default_factory=IterationState)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: Literal["created", "predicting", "optimizing", "iterating", "completed"] = "created"
