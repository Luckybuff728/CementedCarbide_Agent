"""
完整的工作流节点实现 - 基于产品形态文档的业务逻辑
"""
from typing import Dict, List, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from .state import CoatingWorkflowState
from ..services import CoatingService
from ..llm.llm_config import get_material_expert_llm, MATERIAL_EXPERT_PROMPT
from ..utils import ErrorHandler
from .stream_callback import send_stream_chunk_sync
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 初始化服务
coating_service = CoatingService()
error_handler = ErrorHandler()


# ==================== 错误处理节点 ====================

def error_handler_node(state: CoatingWorkflowState) -> Dict:
    """错误处理节点"""
    errors = state.get("validation_errors", [])
    
    logger.error(f"工作流错误处理: {errors}")
    
    return error_handler.handle_validation_error(errors, {
        "task_id": state.get("task_id"),
        "current_step": state.get("current_step"),
        "workflow_status": state.get("workflow_status")
    })


# ==================== 基础节点（已完成） ====================

def input_validation_node(state: CoatingWorkflowState) -> Dict:
    """输入验证和预处理节点"""
    logger.info(f"[参数验证] 任务 {state['task_id']} 开始")
    
    def stream_callback(node: str, content: str):
        send_stream_chunk_sync("input_validation", content)
    
    result = coating_service.validate_input(state, stream_callback)
    
    # 详细日志：返回值
    logger.info(f"[参数验证] 返回数据类型: {type(result)}")
    logger.info(f"[参数验证] 返回数据键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
    logger.info(f"[参数验证] input_validated={result.get('input_validated')}")
    logger.info(f"[参数验证] workflow_status={result.get('workflow_status')}")
    if result.get('validation_errors'):
        logger.info(f"[参数验证] validation_errors={result.get('validation_errors')}")
    
    return result


def topphi_simulation_node(state: CoatingWorkflowState) -> Dict:
    """TopPhi模拟节点 - 沉积过程结构预测"""
    return coating_service.simulate_topphi(state)


def ml_model_prediction_node(state: CoatingWorkflowState) -> Dict:
    """ML模型预测节点 - 性能预测"""
    return coating_service.predict_ml_performance(state)


def historical_comparison_node(state: CoatingWorkflowState) -> Dict:
    """历史数据比对节点"""
    return coating_service.compare_historical_data(state)


def integrated_analysis_node(state: CoatingWorkflowState) -> Dict:
    """根因分析节点"""
    logger.info(f"[根因分析] 任务 {state['task_id']} 开始")
    
    def stream_callback(node: str, content: str):
        send_stream_chunk_sync("integrated_analysis", content)
    
    return coating_service.integrate_analysis(state, stream_callback)


def p1_composition_optimization_node(state: CoatingWorkflowState) -> Dict:
    """P1成分优化建议生成节点 - 简化版"""
    from ..services.optimization_service import OptimizationService, OptimizationType
    
    logger.info(f"[P1成分优化] 任务 {state['task_id']} 开始")
    
    def stream_callback(node: str, content: str):
        # node参数被optimization_service传入，但我们使用固定的节点名
        send_stream_chunk_sync("p1_composition_optimization", content)
    
    opt_service = OptimizationService()
    content = opt_service.generate_optimization_suggestion(
        OptimizationType.P1_COMPOSITION,
        state,
        stream_callback
    )
    
    logger.info(f"[P1成分优化] 完成，内容长度: {len(content)}")
    
    return {
        "p1_content": content
    }


def p2_structure_optimization_node(state: CoatingWorkflowState) -> Dict:
    """P2结构优化建议生成节点 - 简化版"""
    from ..services.optimization_service import OptimizationService, OptimizationType
    
    logger.info(f"[P2结构优化] 任务 {state['task_id']} 开始")
    
    def stream_callback(node: str, content: str):
        # node参数被optimization_service传入，但我们使用固定的节点名
        send_stream_chunk_sync("p2_structure_optimization", content)
    
    opt_service = OptimizationService()
    content = opt_service.generate_optimization_suggestion(
        OptimizationType.P2_STRUCTURE,
        state,
        stream_callback
    )
    
    logger.info(f"[P2结构优化] 完成，内容长度: {len(content)}")
    
    return {
        "p2_content": content
    }


def p3_process_optimization_node(state: CoatingWorkflowState) -> Dict:
    """P3工艺优化建议生成节点 - 简化版"""
    from ..services.optimization_service import OptimizationService, OptimizationType
    
    logger.info(f"[P3工艺优化] 任务 {state['task_id']} 开始")
    
    def stream_callback(node: str, content: str):
        # node参数被optimization_service传入，但我们使用固定的节点名
        send_stream_chunk_sync("p3_process_optimization", content)
    
    opt_service = OptimizationService()
    content = opt_service.generate_optimization_suggestion(
        OptimizationType.P3_PROCESS,
        state,
        stream_callback
    )
    
    logger.info(f"[P3工艺优化] 完成，内容长度: {len(content)}")
    
    return {
        "p3_content": content
    }


def optimization_summary_node(state: CoatingWorkflowState) -> Dict:
    """优化建议汇总节点 - 生成简短的综合建议"""
    logger.info(f"[优化汇总] 任务 {state['task_id']} 开始")
    
    # 获取P1/P2/P3原始内容
    p1_content = state.get("p1_content", "")
    p2_content = state.get("p2_content", "")
    p3_content = state.get("p3_content", "")
    
    # 使用LLM生成简短的综合建议（支持流式输出）
    def stream_callback(node: str, content: str):
        send_stream_chunk_sync("optimization_summary", content)
    
    comprehensive_recommendation = coating_service.generate_optimization_summary(
        state, stream_callback
    )
    
    logger.info(f"[优化汇总] 完成，综合建议长度: {len(comprehensive_recommendation)}")
    
    return {
        "comprehensive_recommendation": comprehensive_recommendation,
        "current_step": "optimization_complete",
        "workflow_status": "optimized"
    }



# ==================== 迭代优化节点（待实现） ====================
# 以下节点将在实施迭代优化功能时添加：
# - await_user_selection_node
# - experiment_workorder_node
# - await_experiment_results_node
# - convergence_check_node
