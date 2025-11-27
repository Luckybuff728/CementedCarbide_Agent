"""
实验工具 - 实验结果可视化工具

功能：
- 显示性能对比图表（实验数据 vs ML预测 vs 历史最优）
"""
from typing import Dict, Any, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


# ==================== Pydantic Schema 定义 ====================

class PerformanceComparisonInput(BaseModel):
    """性能对比图输入"""
    experiment_data: Dict[str, Any] = Field(
        ..., 
        description="实验测量数据，包含 hardness(GPa), elastic_modulus(GPa), adhesion_strength(N), wear_rate(mm³/Nm)"
    )
    prediction_data: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="ML预测数据（可选），格式同实验数据"
    )
    historical_best: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="历史最优数据（可选），格式同实验数据"
    )
    target_requirements: Optional[Dict[str, Any]] = Field(
        default=None,
        description="目标需求，如 {hardness: '>=30', adhesion_strength: '>=60'}"
    )
    is_target_met: bool = Field(
        default=False, 
        description="是否达标（由你根据实验数据和目标需求判断）"
    )
    summary: str = Field(
        default="", 
        description="简要总结（一句话描述实验结果）"
    )


# ==================== 工具定义 ====================

@tool(args_schema=PerformanceComparisonInput)
def show_performance_comparison_tool(
    experiment_data: Dict[str, Any],
    prediction_data: Optional[Dict[str, Any]] = None,
    historical_best: Optional[Dict[str, Any]] = None,
    target_requirements: Optional[Dict[str, Any]] = None,
    is_target_met: bool = False,
    summary: str = ""
) -> Dict[str, Any]:
    """
    显示性能对比图表。
    
    当用户提交实验数据后，调用此工具将数据可视化。
    图表会对比展示：实验数据、ML预测值、历史最优值。
    
    使用场景：
    - 用户说"实验完成，硬度 28.5 GPa，结合力 55 N..."
    - 你解析数据后调用此工具
    - 前端会渲染 Plotly 对比图表
    
    注意：
    - experiment_data 是必填的
    - prediction_data 和 historical_best 从上下文获取（如果有）
    - is_target_met 由你根据目标需求判断
    
    Returns:
        结构化数据，前端自动渲染为对比图表
    """
    logger.info(f"[性能对比] 显示对比图表，达标={is_target_met}")
    
    # 验证实验数据
    valid_metrics = ["hardness", "elastic_modulus", "adhesion_strength", "wear_rate"]
    has_data = any(experiment_data.get(m) is not None for m in valid_metrics)
    
    if not has_data:
        logger.warning("[性能对比] 实验数据为空")
        return {"error": "实验数据为空，无法生成对比图"}
    
    # 清理数据：只保留有效的指标
    def clean_data(data):
        if not data:
            return None
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
        "experiment": clean_data(experiment_data),
        "prediction": clean_data(prediction_data),
        "historical": clean_data(historical_best),
        "target": target_requirements,
        "is_target_met": is_target_met,
        "summary": summary
    }
    
    logger.info(f"[性能对比] 数据准备完成: exp={bool(result['experiment'])}, pred={bool(result['prediction'])}, hist={bool(result['historical'])}")
    
    return result


# ==================== 请求实验数据输入 ====================

class ExperimentInputRequestInput(BaseModel):
    """请求实验数据输入"""
    iteration: int = Field(
        default=1, 
        description="当前迭代轮次（第几轮实验）"
    )
    workorder_id: Optional[str] = Field(
        default=None,
        description="关联的实验工单编号"
    )
    target_requirements: Optional[Dict[str, Any]] = Field(
        default=None,
        description="目标性能要求，如 {hardness: 30, adhesion_strength: 60}"
    )
    message: str = Field(
        default="请输入实验测试结果",
        description="提示用户的消息"
    )


@tool(args_schema=ExperimentInputRequestInput)
def request_experiment_input_tool(
    iteration: int = 1,
    workorder_id: Optional[str] = None,
    target_requirements: Optional[Dict[str, Any]] = None,
    message: str = "请输入实验测试结果"
) -> Dict[str, Any]:
    """
    请求用户输入实验数据。
    
    调用此工具后，前端会显示实验数据输入表单卡片，
    用户可以输入硬度、结合力、弹性模量等测试结果。
    
    使用场景：
    1. 实验工单生成后，提示用户完成实验并输入数据
    2. 用户说"我要输入实验数据"、"录入测试结果"
    3. 迭代优化时，收集新一轮实验结果
    
    注意：
    - 用户提交数据后，你会收到实验数据
    - 收到数据后调用 show_performance_comparison_tool 显示对比图表
    
    Returns:
        请求信息，前端会渲染输入卡片
    """
    logger.info(f"[实验输入] 请求用户输入第 {iteration} 轮实验数据")
    
    return {
        "type": "experiment_input_request",
        "iteration": iteration,
        "workorder_id": workorder_id,
        "target_requirements": target_requirements,
        "message": message
    }


# ==================== 工具列表 ====================

EXPERIMENT_TOOLS = [
    show_performance_comparison_tool,
    request_experiment_input_tool
]
