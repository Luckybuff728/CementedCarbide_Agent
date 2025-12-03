"""
实验工具 - 实验结果可视化工具

功能：
- 显示性能对比图表（实验数据 vs ML预测 vs 历史最优）

更新说明 (v2.1)：
- 使用 ToolRuntime 从状态自动获取 ML预测、目标需求等数据
- 实验数据仍由 LLM 从用户消息中解析并传递
"""
from typing import Dict, Any, Optional
from langchain.tools import tool, ToolRuntime
from pydantic import BaseModel, Field
from loguru import logger


# ==================== Pydantic Schema 定义 ====================

class ExperimentDataInput(BaseModel):
    """实验数据输入（由 LLM 从用户消息解析）"""
    # 实验数据（必须从用户消息解析）
    hardness: Optional[float] = Field(default=None, description="实验测得的硬度 (GPa)")
    elastic_modulus: Optional[float] = Field(default=None, description="实验测得的弹性模量 (GPa)")
    adhesion_strength: Optional[float] = Field(default=None, description="实验测得的结合力 (N)")
    wear_rate: Optional[float] = Field(default=None, description="实验测得的磨损率 (mm³/Nm)")
    
    # 预测数据（可选，从对话上下文中提取之前 ML 预测工具的结果）
    pred_hardness: Optional[float] = Field(default=None, description="ML预测的硬度 (GPa)，从之前的预测结果中提取")
    pred_elastic_modulus: Optional[float] = Field(default=None, description="ML预测的弹性模量 (GPa)")
    pred_adhesion_strength: Optional[float] = Field(default=None, description="ML预测的结合力 (N)")
    pred_wear_rate: Optional[float] = Field(default=None, description="ML预测的磨损率 (mm³/Nm)")
    
    # 历史数据（可选，从对话上下文中提取之前历史对比工具的结果）
    hist_hardness: Optional[float] = Field(default=None, description="历史最优硬度 (GPa)，从之前的历史对比结果中提取")
    hist_elastic_modulus: Optional[float] = Field(default=None, description="历史最优弹性模量 (GPa)")
    hist_adhesion_strength: Optional[float] = Field(default=None, description="历史最优结合力 (N)")
    hist_wear_rate: Optional[float] = Field(default=None, description="历史最优磨损率 (mm³/Nm)")
    
    # 判断和总结
    is_target_met: bool = Field(default=False, description="是否达标（由你根据实验数据和目标需求判断）")
    summary: str = Field(default="", description="简要总结（一句话描述实验结果）")


# ==================== 工具定义（使用 ToolRuntime + 部分参数） ====================

@tool(args_schema=ExperimentDataInput)
def show_performance_comparison_tool(
    runtime: ToolRuntime,
    # 实验数据
    hardness: Optional[float] = None,
    elastic_modulus: Optional[float] = None,
    adhesion_strength: Optional[float] = None,
    wear_rate: Optional[float] = None,
    # 预测数据（Agent 从对话上下文提取）
    pred_hardness: Optional[float] = None,
    pred_elastic_modulus: Optional[float] = None,
    pred_adhesion_strength: Optional[float] = None,
    pred_wear_rate: Optional[float] = None,
    # 历史数据（Agent 从对话上下文提取）
    hist_hardness: Optional[float] = None,
    hist_elastic_modulus: Optional[float] = None,
    hist_adhesion_strength: Optional[float] = None,
    hist_wear_rate: Optional[float] = None,
    # 判断和总结
    is_target_met: bool = False,
    summary: str = ""
) -> Dict[str, Any]:
    """
    显示性能对比图表（实验 vs ML预测 vs 历史最优）。
    
    使用场景：用户说"实验完成，硬度 28.5 GPa，结合力 55 N..."
    
    你需要：
    1. 从用户消息解析实验数据（hardness, elastic_modulus 等）
    2. 从对话上下文中提取之前的 ML 预测结果（pred_hardness 等）
    3. 从对话上下文中提取之前的历史对比结果（hist_hardness 等）
    
    前端会渲染 Plotly 对比图表。
    
    Args:
        hardness: 实验测得的硬度 (GPa)
        pred_hardness: ML预测的硬度，从之前 predict_ml_performance_tool 的结果中提取
        hist_hardness: 历史最优硬度，从之前 compare_historical_tool 的结果中提取
        （其他参数同理）
    
    Returns:
        结构化数据，前端自动渲染为对比图表
    """
    logger.info(f"[性能对比] 显示对比图表，达标={is_target_met}")
    
    # 构建实验数据
    experiment_data = {}
    if hardness is not None:
        experiment_data["hardness"] = hardness
    if elastic_modulus is not None:
        experiment_data["elastic_modulus"] = elastic_modulus
    if adhesion_strength is not None:
        experiment_data["adhesion_strength"] = adhesion_strength
    if wear_rate is not None:
        experiment_data["wear_rate"] = wear_rate
    
    if not experiment_data:
        logger.warning("[性能对比] 实验数据为空")
        return {"error": "实验数据为空，无法生成对比图"}
    
    # 优先使用 Agent 传入的数据，否则从状态获取
    state = runtime.state
    
    # 构建预测数据：优先使用传入参数
    prediction_data = {}
    if pred_hardness is not None:
        prediction_data["hardness"] = pred_hardness
    if pred_elastic_modulus is not None:
        prediction_data["elastic_modulus"] = pred_elastic_modulus
    if pred_adhesion_strength is not None:
        prediction_data["adhesion_strength"] = pred_adhesion_strength
    if pred_wear_rate is not None:
        prediction_data["wear_rate"] = pred_wear_rate
    
    # 如果 Agent 没传入，尝试从状态获取
    if not prediction_data:
        prediction_data = state.get("ml_prediction", {})
    
    # 构建历史数据：优先使用传入参数
    historical_best = {}
    if hist_hardness is not None:
        historical_best["hardness"] = hist_hardness
    if hist_elastic_modulus is not None:
        historical_best["elastic_modulus"] = hist_elastic_modulus
    if hist_adhesion_strength is not None:
        historical_best["adhesion_strength"] = hist_adhesion_strength
    if hist_wear_rate is not None:
        historical_best["wear_rate"] = hist_wear_rate
    
    # 目标需求从状态获取
    target_requirements = state.get("target_requirements", {})
    
    logger.info(f"[性能对比] 数据来源: prediction={bool(prediction_data)}, historical={bool(historical_best)}, target={bool(target_requirements)}")
    
    # 清理数据函数
    def clean_data(data):
        if not data:
            return None
        valid_metrics = ["hardness", "elastic_modulus", "adhesion_strength", "wear_rate"]
        cleaned = {}
        for metric in valid_metrics:
            val = data.get(metric)
            if val is not None:
                try:
                    cleaned[metric] = float(val)
                except (ValueError, TypeError):
                    pass
        return cleaned if cleaned else None
    
    result = {
        "type": "performance_comparison",
        "experiment": experiment_data,
        "prediction": clean_data(prediction_data),
        "historical": clean_data(historical_best),
        "target": target_requirements if isinstance(target_requirements, dict) else {},
        "is_target_met": is_target_met,
        "summary": summary
    }
    
    logger.info(f"[性能对比] 数据准备完成: exp={bool(result['experiment'])}, pred={bool(result['prediction'])}, hist={bool(result['historical'])}")
    
    return result


# ==================== 请求实验数据输入 ====================

class ExperimentInputRequestInput(BaseModel):
    """请求实验数据输入（可选参数）"""
    message: str = Field(
        default="请输入实验测试结果",
        description="提示用户的消息"
    )


@tool(args_schema=ExperimentInputRequestInput)
def request_experiment_input_tool(
    runtime: ToolRuntime,
    message: str = "请输入实验测试结果"
) -> Dict[str, Any]:
    """
    请求用户输入实验数据。
    
    自动从状态获取迭代次数、工单ID、目标需求等信息。
    调用此工具后，前端会显示实验数据输入表单卡片。
    
    使用场景：
    1. 实验工单生成后，提示用户完成实验并输入数据
    2. 用户说"我要输入实验数据"、"录入测试结果"
    3. 迭代优化时，收集新一轮实验结果
    
    Args:
        message: 提示用户的消息
    
    Returns:
        请求信息，前端会渲染输入卡片
    """
    # 从状态获取相关信息
    state = runtime.state
    iteration = state.get("current_iteration", 1)
    workorder = state.get("experiment_workorder", {})
    workorder_id = workorder.get("id") if workorder else None
    target_requirements = state.get("target_requirements", {})
    
    logger.info(f"[实验输入] 请求用户输入第 {iteration} 轮实验数据")
    
    return {
        "type": "experiment_input_request",
        "iteration": iteration,
        "workorder_id": workorder_id,
        "target_requirements": target_requirements if isinstance(target_requirements, dict) else {},
        "message": message
    }


# ==================== 工具列表 ====================

EXPERIMENT_TOOLS = [
    show_performance_comparison_tool,
    request_experiment_input_tool
]
