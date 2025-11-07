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



# ==================== 迭代优化节点 ====================

def await_user_selection_node(state: CoatingWorkflowState) -> Dict:
    """等待用户选择优化方案节点 - 使用interrupt暂停工作流"""
    from langgraph.types import interrupt
    
    logger.info(f"[等待用户选择] 任务 {state['task_id']}, 迭代 {state.get('current_iteration', 1)}")
    
    # 使用interrupt暂停工作流，等待用户选择
    user_selection = interrupt({
        "type": "await_user_selection",
        "iteration": state.get("current_iteration", 1),
        "options": ["P1", "P2", "P3"],
        "p1_summary": state.get("p1_content", "")[:200] if state.get("p1_content") else "",
        "p2_summary": state.get("p2_content", "")[:200] if state.get("p2_content") else "",
        "p3_summary": state.get("p3_content", "")[:200] if state.get("p3_content") else "",
        "comprehensive_recommendation": state.get("comprehensive_recommendation", "")
    })
    
    logger.info(f"[等待用户选择] 用户选择: {user_selection}")
    
    # ✅ 修复：interrupt返回的是整个resume对象，需要提取字段
    if isinstance(user_selection, dict):
        selected_type = user_selection.get("selected_optimization_type")
        selected_name = user_selection.get("selected_optimization_name")
    else:
        # 兼容直接传入字符串的情况
        selected_type = user_selection
        selected_name = None
    
    return {
        "selected_optimization_type": selected_type,  # "P1" / "P2" / "P3"
        "selected_optimization_name": selected_name,
        "current_step": "user_selected"
    }


def experiment_workorder_node(state: CoatingWorkflowState) -> Dict:
    """生成实验工单节点 - 集成现有workorder_service"""
    from ..services.workorder_service import generate_workorder
    
    logger.info(f"[工单生成] 任务 {state['task_id']}, 迭代 {state.get('current_iteration', 1)}")
    
    selected_type = state.get("selected_optimization_type")
    if not selected_type:
        logger.error("[工单生成] 缺少用户选择的优化方案")
        return {
            "error_message": "缺少用户选择的优化方案",
            "workflow_status": "error"
        }
    
    # 流式输出回调
    def stream_callback(node: str, content: str):
        send_stream_chunk_sync("experiment_workorder", content)
    
    try:
        # 调用现有的工单生成服务
        result = generate_workorder(
            task_id=state['task_id'],
            selected_option=selected_type,
            task_state=state,
            stream_callback=stream_callback
        )
        
        if not result.get("success"):
            logger.error(f"[工单生成] 失败: {result.get('error')}")
            return {
                "error_message": result.get("error"),
                "workflow_status": "error"
            }
        
        logger.info(f"[工单生成] 完成")
        
        return {
            "experiment_workorder": result.get("experiment_workorder"),
            "selected_optimization_name": result.get("selected_optimization_name"),
            "current_step": "workorder_generated"
        }
    
    except Exception as e:
        return error_handler.handle_workflow_error(e, "experiment_workorder", state)


def await_experiment_results_node(state: CoatingWorkflowState) -> Dict:
    """等待实验结果节点 - 包含用户继续迭代的决策"""
    from langgraph.types import interrupt
    from datetime import datetime
    
    logger.info(f"[等待实验] 任务 {state['task_id']}, 迭代 {state.get('current_iteration', 1)}")
    
    # 使用interrupt暂停，等待实验数据 + 用户决策
    result = interrupt({
        "type": "await_experiment_results",
        "iteration": state.get("current_iteration", 1),
        "workorder": state.get("experiment_workorder", ""),
        "expected_fields": {
            "hardness": "硬度 (GPa)",
            "adhesion_strength": "结合力 (N)",
            "oxidation_temperature": "抗氧化温度 (℃)",
            "wear_rate": "磨损率 (mm³/Nm)",
            "surface_roughness": "表面粗糙度 (μm)",
            "notes": "备注",
            "continue_iteration": "是否继续迭代 (boolean)"
        }
    })
    
    # 从result中提取数据
    experiment_data = result.get("experiment_data", {})
    continue_iteration = result.get("continue_iteration", False)
    
    logger.info(f"[等待实验] 实验数据: {experiment_data}")
    logger.info(f"[等待实验] 继续迭代: {continue_iteration}")
    
    # 记录当前迭代到历史
    iteration_record = {
        "iteration": state.get("current_iteration", 1),
        "selected_optimization": state.get("selected_optimization_type"),
        "selected_optimization_name": state.get("selected_optimization_name"),
        "experiment_results": experiment_data,
        "timestamp": datetime.now().isoformat()
    }
    
    iteration_history = state.get("iteration_history", [])
    iteration_history.append(iteration_record)
    
    logger.info(f"[等待实验] 已记录第 {iteration_record['iteration']} 轮迭代到历史")
    
    # ✅ 只有继续迭代时才递增迭代次数
    next_iteration = state.get("current_iteration", 1) + 1 if continue_iteration else state.get("current_iteration", 1)
    
    return {
        "experimental_results": experiment_data,
        "continue_iteration": continue_iteration,
        "iteration_history": iteration_history,
        "current_iteration": next_iteration,
        "current_step": "experiment_received"
    }
