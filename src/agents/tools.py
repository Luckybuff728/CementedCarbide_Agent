"""
Agent Tools - 将现有服务封装为 LangChain Tools
遵循 @tool 装饰器 + Pydantic Schema 的标准
"""
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import logging

from ..services.coating_service import CoatingService
from ..services.optimization_service import OptimizationService, OptimizationType

logger = logging.getLogger(__name__)

# 初始化服务
coating_service = CoatingService()
optimization_service = OptimizationService()


# ==================== Input Validation Tool ====================

class ValidateInputSchema(BaseModel):
    """输入验证工具的参数"""
    coating_composition: Dict[str, Any] = Field(..., description="涂层成分配比")
    process_params: Dict[str, Any] = Field(..., description="工艺参数")
    structure_design: Dict[str, Any] = Field(..., description="结构设计参数")
    target_requirements: Any = Field(..., description="目标性能需求描述")


@tool(args_schema=ValidateInputSchema)
def validate_input_tool(
    coating_composition: Dict[str, Any],
    process_params: Dict[str, Any],
    structure_design: Dict[str, Any],
    target_requirements: Any
) -> Dict[str, Any]:
    """
    验证涂层输入参数的有效性。
    
    检查成分配比、工艺参数、结构设计是否在合理范围内。
    返回验证结果和归一化后的参数。
    """
    state = {
        "task_id": "validation",
        "coating_composition": coating_composition,
        "process_params": process_params,
        "structure_design": structure_design,
        "target_requirements": target_requirements
    }
    
    result = coating_service.validate_input(state)
    
    if result.get("status") == "success":
        return result.get("data", {})
    else:
        return {"error": result.get("message", "验证失败")}


# ==================== Performance Prediction Tools ====================

class SimulateTopPhiSchema(BaseModel):
    """TopPhi模拟工具的参数"""
    coating_composition: Dict[str, Any] = Field(..., description="涂层成分配比")
    process_params: Dict[str, Any] = Field(..., description="工艺参数")


@tool(args_schema=SimulateTopPhiSchema)
def simulate_topphi_tool(
    coating_composition: Dict[str, Any],
    process_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    调用TopPhi第一性原理模拟引擎。
    
    预测涂层的微观结构：晶粒尺寸、择优取向、残余应力等。
    这是最准确但最耗时的预测方法。
    """
    state = {
        "task_id": "topphi",
        "coating_composition": coating_composition,
        "process_params": process_params
    }
    
    result = coating_service.simulate_topphi(state)
    
    if result.get("status") == "success":
        return result.get("data", {})
    else:
        return {"error": result.get("message", "TopPhi模拟失败")}


class PredictMLPerformanceSchema(BaseModel):
    """ML性能预测工具的参数"""
    coating_composition: Dict[str, Any] = Field(..., description="涂层成分配比")
    process_params: Dict[str, Any] = Field(..., description="工艺参数")
    structure_design: Dict[str, Any] = Field(..., description="结构设计参数")


@tool(args_schema=PredictMLPerformanceSchema)
def predict_ml_performance_tool(
    coating_composition: Dict[str, Any],
    process_params: Dict[str, Any],
    structure_design: Dict[str, Any]
) -> Dict[str, Any]:
    """
    使用机器学习模型预测涂层性能。
    
    预测硬度、弹性模量、磨损率、结合力等关键性能指标。
    速度快，适合快速评估。
    """
    state = {
        "task_id": "ml_prediction",
        "coating_composition": coating_composition,
        "process_params": process_params,
        "structure_design": structure_design
    }
    
    result = coating_service.predict_ml_performance(state)
    
    if result.get("status") == "success":
        return result.get("data", {})
    else:
        return {"error": result.get("message", "ML预测失败")}


class CompareHistoricalSchema(BaseModel):
    """历史数据对比工具的参数"""
    coating_composition: Dict[str, Any] = Field(..., description="涂层成分配比")
    process_params: Dict[str, Any] = Field(..., description="工艺参数")


@tool(args_schema=CompareHistoricalSchema)
def compare_historical_tool(
    coating_composition: Dict[str, Any],
    process_params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    检索并对比历史相似案例。
    
    从数据库中查找相似的涂层配方和参数，
    提供成功案例的性能数据作为参考。
    """
    state = {
        "task_id": "historical",
        "coating_composition": coating_composition,
        "process_params": process_params
    }
    
    result = coating_service.compare_historical_data(state)
    
    if result.get("status") == "success":
        return result.get("data", {})
    else:
        return {"error": result.get("message", "历史对比失败")}


class AnalyzeRootCauseSchema(BaseModel):
    """根因分析工具的参数"""
    topphi_result: Dict[str, Any] = Field(..., description="TopPhi模拟结果")
    ml_result: Dict[str, Any] = Field(..., description="ML预测结果")
    historical_result: Dict[str, Any] = Field(..., description="历史对比结果")
    target_requirements: Any = Field(..., description="目标性能需求")


@tool(args_schema=AnalyzeRootCauseSchema)
def analyze_root_cause_tool(
    topphi_result: Dict[str, Any],
    ml_result: Dict[str, Any],
    historical_result: Dict[str, Any],
    target_requirements: Any
) -> Dict[str, Any]:
    """
    综合分析性能预测结果，进行根因分析。
    
    基于TopPhi、ML、历史数据，使用LLM分析：
    - 成分与性能的关系
    - 工艺参数的影响
    - 与目标需求的差距
    - 主要改进方向
    """
    state = {
        "task_id": "analysis",
        "topphi_simulation": topphi_result,
        "ml_prediction": ml_result,
        "historical_comparison": historical_result,
        "target_requirements": target_requirements,
        "coating_composition": {},  # 从结果中提取
        "process_params": {},
        "structure_design": {}
    }
    
    result = coating_service.integrate_analysis(state)
    
    if result.get("status") == "success":
        return result.get("data", {})
    else:
        return {"error": result.get("message", "根因分析失败")}


# ==================== Optimization Tools ====================

class GenerateOptimizationSchema(BaseModel):
    """优化建议生成工具的参数"""
    analysis_result: Dict[str, Any] = Field(..., description="根因分析结果")
    optimization_type: str = Field(..., description="优化类型: P1(成分)/P2(结构)/P3(工艺)")
    coating_composition: Dict[str, Any] = Field(default_factory=dict, description="当前涂层成分配比")
    process_params: Dict[str, Any] = Field(default_factory=dict, description="当前工艺参数")
    structure_design: Dict[str, Any] = Field(default_factory=dict, description="当前结构设计")
    performance_prediction: Dict[str, Any] = Field(default_factory=dict, description="性能预测结果")
    target_requirements: Any = Field(default="", description="目标需求")


@tool(args_schema=GenerateOptimizationSchema)
def generate_p1_optimization_tool(
    analysis_result: Dict[str, Any],
    optimization_type: str = "P1",
    coating_composition: Dict[str, Any] = None,
    process_params: Dict[str, Any] = None,
    structure_design: Dict[str, Any] = None,
    performance_prediction: Dict[str, Any] = None,
    target_requirements: Any = ""
) -> Dict[str, Any]:
    """
    生成P1成分优化建议。
    
    基于根因分析，提供Al、Ti、N等元素的配比优化方案。
    包括多个可选方案和预期性能改进。
    """
    # 构建完整的state，包含所有必要信息
    state = {
        "task_id": "p1_opt",
        "integrated_analysis": analysis_result,
        "coating_composition": coating_composition or {},
        "process_params": process_params or {},
        "structure_design": structure_design or {},
        "performance_prediction": performance_prediction or {},
        "target_requirements": target_requirements
    }
    
    result = optimization_service.generate_optimization_suggestion(
        OptimizationType.P1_COMPOSITION,
        state,
        None
    )
    
    if result.get("status") == "success":
        return result.get("data", {})
    else:
        return {"error": result.get("message", "P1优化失败")}


@tool(args_schema=GenerateOptimizationSchema)
def generate_p2_optimization_tool(
    analysis_result: Dict[str, Any],
    optimization_type: str = "P2",
    coating_composition: Dict[str, Any] = None,
    process_params: Dict[str, Any] = None,
    structure_design: Dict[str, Any] = None,
    performance_prediction: Dict[str, Any] = None,
    target_requirements: Any = ""
) -> Dict[str, Any]:
    """
    生成P2结构优化建议。
    
    基于根因分析，提供涂层结构设计优化方案：
    单层/多层结构、梯度设计、界面设计等。
    """
    state = {
        "task_id": "p2_opt",
        "integrated_analysis": analysis_result,
        "coating_composition": coating_composition or {},
        "process_params": process_params or {},
        "structure_design": structure_design or {},
        "performance_prediction": performance_prediction or {},
        "target_requirements": target_requirements
    }
    
    result = optimization_service.generate_optimization_suggestion(
        OptimizationType.P2_STRUCTURE,
        state,
        None
    )
    
    if result.get("status") == "success":
        return result.get("data", {})
    else:
        return {"error": result.get("message", "P2优化失败")}


@tool(args_schema=GenerateOptimizationSchema)
def generate_p3_optimization_tool(
    analysis_result: Dict[str, Any],
    optimization_type: str = "P3",
    coating_composition: Dict[str, Any] = None,
    process_params: Dict[str, Any] = None,
    structure_design: Dict[str, Any] = None,
    performance_prediction: Dict[str, Any] = None,
    target_requirements: Any = ""
) -> Dict[str, Any]:
    """
    生成P3工艺优化建议。
    
    基于根因分析，提供工艺参数优化方案：
    温度、偏压、气体流量等关键参数的调整。
    """
    state = {
        "task_id": "p3_opt",
        "integrated_analysis": analysis_result,
        "coating_composition": coating_composition or {},
        "process_params": process_params or {},
        "structure_design": structure_design or {},
        "performance_prediction": performance_prediction or {},
        "target_requirements": target_requirements
    }
    
    result = optimization_service.generate_optimization_suggestion(
        OptimizationType.P3_PROCESS,
        state,
        None
    )
    
    if result.get("status") == "success":
        return result.get("data", {})
    else:
        return {"error": result.get("message", "P3优化失败")}


# ==================== Experiment Tools ====================

class GenerateWorkorderSchema(BaseModel):
    """实验工单生成工具的参数"""
    selected_optimization: str = Field(..., description="选择的优化方案: P1/P2/P3")
    optimization_content: str = Field(..., description="优化方案的详细内容")
    coating_composition: Dict[str, Any] = Field(default_factory=dict, description="当前涂层成分配比")
    process_params: Dict[str, Any] = Field(default_factory=dict, description="当前工艺参数")
    structure_design: Dict[str, Any] = Field(default_factory=dict, description="当前结构设计")
    target_requirements: Any = Field(default="", description="目标性能需求")


@tool(args_schema=GenerateWorkorderSchema)
def generate_workorder_tool(
    selected_optimization: str,
    optimization_content: str,
    coating_composition: Dict[str, Any] = None,
    process_params: Dict[str, Any] = None,
    structure_design: Dict[str, Any] = None,
    target_requirements: Any = ""
) -> Dict[str, Any]:
    """
    生成实验工单。
    
    基于用户选择的优化方案和当前配方参数，生成详细的实验指导工单：
    - 具体参数设置
    - 实验步骤
    - 预期结果
    - 注意事项
    """
    from ..services.workorder_service import generate_workorder
    
    # 构建完整的状态字典，包含当前配方参数
    state = {
        "task_id": "workorder",
        "selected_optimization_type": selected_optimization,
        f"{selected_optimization.lower()}_content": optimization_content,
        "coating_composition": coating_composition or {},
        "process_params": process_params or {},
        "structure_design": structure_design or {},
        "target_requirements": target_requirements or ""
    }
    
    result = generate_workorder(
        task_id=state["task_id"],
        selected_option=selected_optimization,
        task_state=state,
        stream_callback=None  # 已废弃，流式输出通过contextvars自动处理
    )
    
    if isinstance(result, dict) and not result.get("error"):
        return result
    else:
        return {"error": result.get("error", "工单生成失败")}


# ==================== 导出所有工具 ====================

ALL_TOOLS = [
    validate_input_tool,
    simulate_topphi_tool,
    predict_ml_performance_tool,
    compare_historical_tool,
    analyze_root_cause_tool,
    generate_p1_optimization_tool,
    generate_p2_optimization_tool,
    generate_p3_optimization_tool,
    generate_workorder_tool,
]

