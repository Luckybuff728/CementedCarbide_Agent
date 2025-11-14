"""
完整的工作流节点实现 - 基于产品形态文档的业务逻辑
"""
from typing import Dict, List, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from .state import CoatingWorkflowState
from ..services import CoatingService
from ..llm import get_llm_service, MATERIAL_EXPERT_PROMPT
# 错误处理已简化，不再需要单独的ErrorHandler模块
from .stream_callback import send_stream_chunk_sync
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 初始化服务
coating_service = CoatingService()


# ==================== 错误处理节点 ====================

def error_handler_node(state: CoatingWorkflowState) -> Dict:
    """错误处理节点 - 处理验证失败情况"""
    errors = state.get("validation_errors", [])
    task_id = state.get("task_id")
    
    logger.error(f"[验证失败] 任务 {task_id}: {errors}")
    
    # 构造错误响应
    error_message = "输入验证失败:\n" + "\n".join(errors)
    
    return {
        "error_type": "ValidationError",
        "error_message": error_message,
        "validation_errors": errors,
        "workflow_status": "validation_failed",
        "current_step": "error",
        "next_step": None,
        "recovery_suggestions": [
            "检查输入参数的格式和范围",
            "确保所有必需字段都已填写",
            "验证数值的合理性"
        ]
    }


# ==================== 基础节点（已完成） ====================

def input_validation_node(state: CoatingWorkflowState) -> Dict:
    """输入验证和预处理节点"""
    logger.info(f"[参数验证] 任务 {state['task_id']} 开始")
    
    def stream_callback(node: str, content: str):
        send_stream_chunk_sync("input_validation", content)
    
    result = coating_service.validate_input(state, stream_callback)
    
    # 统一解析服务返回结构
    if not isinstance(result, dict):
        logger.error(f"[参数验证] 服务返回类型异常: {type(result)}")
        return {
            "input_validated": False,
            "workflow_status": "validation_failed",
            "error_message": "参数验证失败：服务返回格式错误"
        }
    
    status = result.get("status")
    data = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
    
    # 详细日志：返回值
    logger.info(f"[参数验证] 返回状态: {status}")
    logger.info(f"[参数验证] data键: {list(data.keys())}")
    logger.info(f"[参数验证] input_validated={data.get('input_validated')}")
    logger.info(f"[参数验证] workflow_status={data.get('workflow_status')}")
    if data.get('validation_errors'):
        logger.info(f"[参数验证] validation_errors={data.get('validation_errors')}")
    
    # 如果服务标记失败，则统一返回错误状态
    if status and status != "success":
        return {
            "input_validated": False,
            "workflow_status": "validation_failed",
            "error_message": result.get("message", "参数验证失败")
        }
    
    return data


def topphi_simulation_node(state: CoatingWorkflowState) -> Dict:
    """TopPhi模拟节点 - 沉积过程结构预测"""
    result = coating_service.simulate_topphi(state)
    if not isinstance(result, dict):
        logger.error(f"[TopPhi模拟] 服务返回类型异常: {type(result)}")
        return {
            "workflow_status": "error",
            "error_message": "TopPhi模拟失败：服务返回格式错误"
        }
    status = result.get("status")
    data = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
    if status and status != "success":
        logger.error(f"[TopPhi模拟] 失败: {result.get('message')}")
        return {
            "workflow_status": "error",
            "error_message": result.get("message", "TopPhi模拟失败")
        }
    return data


def ml_model_prediction_node(state: CoatingWorkflowState) -> Dict:
    """ML模型预测节点 - 性能预测"""
    result = coating_service.predict_ml_performance(state)
    if not isinstance(result, dict):
        logger.error(f"[ML模型预测] 服务返回类型异常: {type(result)}")
        return {
            "workflow_status": "error",
            "error_message": "ML模型预测失败：服务返回格式错误"
        }
    status = result.get("status")
    data = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
    if status and status != "success":
        logger.error(f"[ML模型预测] 失败: {result.get('message')}")
        return {
            "workflow_status": "error",
            "error_message": result.get("message", "ML模型预测失败")
        }
    return data


def historical_comparison_node(state: CoatingWorkflowState) -> Dict:
    """历史数据比对节点"""
    result = coating_service.compare_historical_data(state)
    if not isinstance(result, dict):
        logger.error(f"[历史数据比对] 服务返回类型异常: {type(result)}")
        return {
            "workflow_status": "error",
            "error_message": "历史数据比对失败：服务返回格式错误"
        }
    status = result.get("status")
    data = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
    if status and status != "success":
        logger.error(f"[历史数据比对] 失败: {result.get('message')}")
        return {
            "workflow_status": "error",
            "error_message": result.get("message", "历史数据比对失败")
        }
    return data


def integrated_analysis_node(state: CoatingWorkflowState) -> Dict:
    """根因分析节点"""
    logger.info(f"[根因分析] 任务 {state['task_id']} 开始")
    
    def stream_callback(node: str, content: str):
        send_stream_chunk_sync("integrated_analysis", content)
    
    result = coating_service.integrate_analysis(state, stream_callback)
    if not isinstance(result, dict):
        logger.error(f"[根因分析节点] 服务返回类型异常: {type(result)}")
        return {
            "workflow_status": "error",
            "error_message": "根因分析失败：服务返回格式错误"
        }
    status = result.get("status")
    data = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
    logger.info(f"[根因分析节点] service返回状态: {status}, data键: {list(data.keys())}")
    
    if status and status != "success":
        logger.error(f"[根因分析节点] 失败: {result.get('message')}")
        return {
            "workflow_status": "error",
            "error_message": result.get("message", "根因分析失败")
        }
    
    # 直接返回data，其中已经包含integrated_analysis字段
    logger.info(f"[根因分析节点] integrated_analysis值类型: {type(data.get('integrated_analysis'))}")
    return data


def p1_composition_optimization_node(state: CoatingWorkflowState) -> Dict:
    """P1成分优化建议生成节点 - 简化版"""
    from ..services.optimization_service import OptimizationService, OptimizationType
    
    logger.info(f"[P1成分优化] 任务 {state['task_id']} 开始")
    
    def stream_callback(node: str, content: str):
        # node参数被optimization_service传入，但我们使用固定的节点名
        send_stream_chunk_sync("p1_composition_optimization", content)
    
    opt_service = OptimizationService()
    result = opt_service.generate_optimization_suggestion(
        OptimizationType.P1_COMPOSITION,
        state,
        stream_callback
    )
    
    if not isinstance(result, dict):
        logger.error(f"[P1成分优化] 服务返回类型异常: {type(result)}")
        return {
            "workflow_status": "error",
            "error_message": "P1成分优化失败：服务返回格式错误"
        }
    
    status = result.get("status")
    data = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
    if status and status != "success":
        logger.error(f"[P1成分优化] 生成失败: {result.get('message')}")
        return {
            "workflow_status": "error",
            "error_message": result.get("message", "P1成分优化失败")
        }
    
    content = data.get("content", "") or ""
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
    result = opt_service.generate_optimization_suggestion(
        OptimizationType.P2_STRUCTURE,
        state,
        stream_callback
    )
    
    if not isinstance(result, dict):
        logger.error(f"[P2结构优化] 服务返回类型异常: {type(result)}")
        return {
            "workflow_status": "error",
            "error_message": "P2结构优化失败：服务返回格式错误"
        }
    
    status = result.get("status")
    data = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
    if status and status != "success":
        logger.error(f"[P2结构优化] 生成失败: {result.get('message')}")
        return {
            "workflow_status": "error",
            "error_message": result.get("message", "P2结构优化失败")
        }
    
    content = data.get("content", "") or ""
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
    result = opt_service.generate_optimization_suggestion(
        OptimizationType.P3_PROCESS,
        state,
        stream_callback
    )
    
    if not isinstance(result, dict):
        logger.error(f"[P3工艺优化] 服务返回类型异常: {type(result)}")
        return {
            "workflow_status": "error",
            "error_message": "P3工艺优化失败：服务返回格式错误"
        }
    
    status = result.get("status")
    data = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
    if status and status != "success":
        logger.error(f"[P3工艺优化] 生成失败: {result.get('message')}")
        return {
            "workflow_status": "error",
            "error_message": result.get("message", "P3工艺优化失败")
        }
    
    content = data.get("content", "") or ""
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
    
    result = coating_service.generate_optimization_summary(
        state, stream_callback
    )
    
    if not isinstance(result, dict):
        logger.error(f"[优化汇总] 服务返回类型异常: {type(result)}")
        return {
            "workflow_status": "error",
            "error_message": "优化汇总失败：服务返回格式错误"
        }
    
    status = result.get("status")
    data = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
    if status and status != "success":
        logger.error(f"[优化汇总] 生成失败: {result.get('message')}")
        return {
            "workflow_status": "error",
            "error_message": result.get("message", "优化汇总失败")
        }
    
    comprehensive_recommendation = data.get("comprehensive_recommendation", "") or ""
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
        
        logger.info(f"[工单节点] service返回类型: {type(result)}, 键: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # 如果服务返回错误信息，统一转换为工作流错误状态
        if not isinstance(result, dict):
            logger.error("[工单节点] 工单服务返回非字典类型结果")
            return {
                "workflow_status": "error",
                "error_message": "工单生成失败：服务返回格式错误"
            }
        
        # 兼容后续可能引入的标准返回格式：包含status/data/message
        status = result.get("status")
        if status and status != "success":
            logger.error(f"[工单节点] 工单生成失败: {result.get('message')}")
            return {
                "workflow_status": "error",
                "error_message": result.get("message", "工单生成失败")
            }
        
        # 如果包含data字段，则优先使用其中的数据作为工单内容
        workorder_data = result.get("data") if "data" in result else result
        
        # 直接返回，用experiment_workorder包装（与graph state字段对应）
        node_result = {"experiment_workorder": workorder_data}
        
        logger.info(f"[工单节点] 返回类型: {type(node_result)}, 键: {list(node_result.keys())}")
        logger.info(f"[工单生成] 完成")
        
        return node_result
    
    except Exception as e:
        logger.error(f"[工单节点] 工单生成异常: {e}")
        return {
            "workflow_status": "error",
            "error_message": f"工单生成异常: {e}"
        }


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
            "elastic_modulus": "弹性模量 (GPa)",
            "wear_rate": "磨损率 (mm³/Nm)",
            "adhesion_strength": "结合力 (N)",
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
        "experiment_results": experiment_data,
        "continue_iteration": continue_iteration,
        "iteration_history": iteration_history,
        "current_iteration": next_iteration,
        "current_step": "experiment_received"
    }
