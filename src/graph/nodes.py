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
    
    return coating_service.validate_input(state, stream_callback)


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


def await_user_selection_node(state: CoatingWorkflowState):
    """等待用户选择优化方案节点 - 简化版"""
    from langgraph.types import interrupt
    
    logger.info(f"等待用户选择优化方案")
    
    comprehensive_recommendation = state.get("comprehensive_recommendation", "")
    
    # 准备三个简单的选项（只包含方案名称）
    options = [
        {"id": "P1", "name": "P1 成分优化"},
        {"id": "P2", "name": "P2 结构优化"},
        {"id": "P3", "name": "P3 工艺优化"}
    ]
    
    # 使用interrupt()暂停工作流
    user_selection = interrupt({
        "type": "user_selection_required",
        "options": options,
        "message": "请选择一个优化方案进行实施",
        "comprehensive_recommendation": comprehensive_recommendation
    })
    
    # 当interrupt恢复时，user_selection会包含用户的选择
    logger.info(f"=" * 80)
    logger.info(f"[等待用户选择] interrupt恢复，接收到用户选择")
    logger.info(f"[等待用户选择] 用户选择: {user_selection}")
    logger.info(f"=" * 80)
    
    # 保存选择数据到状态中
    result = {
        "selected_optimization_type": user_selection,  # 应该是"P1", "P2", 或 "P3"
        "current_step": "user_selected"
    }
    logger.info(f"[等待用户选择] 返回数据: {result}")
    return result


def experiment_workorder_generation_node(state: CoatingWorkflowState) -> Dict:
    """
    实验工单生成节点 - 根据用户选择的优化方案，使用LLM生成实验工单
    """
    logger.info(f"[实验工单生成] 任务 {state['task_id']} 开始")
    
    try:
        # 获取用户选择的优化类型（P1/P2/P3）
        selected_type = state.get("selected_optimization_type", "")
        
        logger.info(f"[实验工单生成] 选择类型: {selected_type}")
        
        if not selected_type:
            logger.error("[实验工单生成] 缺少用户选择的优化方案")
            return {
                "error": "缺少用户选择的优化方案",
                "current_step": "workorder_failed"
            }
        
        # 获取对应的优化建议内容
        if selected_type == "P1":
            optimization_content = state.get("p1_content", "")
            optimization_name = "P1 成分优化"
        elif selected_type == "P2":
            optimization_content = state.get("p2_content", "")
            optimization_name = "P2 结构优化"
        elif selected_type == "P3":
            optimization_content = state.get("p3_content", "")
            optimization_name = "P3 工艺优化"
        else:
            return {
                "error": f"无效的优化类型: {selected_type}",
                "current_step": "workorder_failed"
            }
        
        logger.info(f"[实验工单生成] 优化建议内容长度: {len(optimization_content)}")
        
        # 使用LLM生成实验工单
        def stream_callback(node: str, content: str):
            send_stream_chunk_sync("experiment_workorder_generation", content)
        
        workorder_content = _generate_workorder_by_llm(
            optimization_name,
            optimization_content,
            state,
            stream_callback
        )
        
        logger.info(f"[实验工单生成] 完成，内容长度: {len(workorder_content)}")
        
        return {
            "experiment_workorder": workorder_content,
            "selected_optimization_name": optimization_name,
            "current_step": "workorder_generated",
            "workflow_status": "completed"
        }
        
    except Exception as e:
        return error_handler.handle_workflow_error(e, "experiment_workorder_generation", state)


# ==================== 辅助函数 ====================

def _generate_workorder_by_llm(
    optimization_name: str,
    optimization_content: str,
    state: Dict,
    stream_callback=None
) -> str:
    """使用LLM根据优化建议生成实验工单"""
    
    # 获取当前配方参数
    composition = state.get("coating_composition", {})
    process_params = state.get("process_params", {})
    structure_design = state.get("structure_design", {})
    target_requirements = state.get("target_requirements", "")
    
    # 构建提示词
    prompt = f"""
作为涂层工艺专家，请根据以下优化建议生成一份标准的实验工单：

## 选中的优化方案
**{optimization_name}**

## 优化建议详细内容
{optimization_content}

## 当前配方参数
- 成分配比: Al {composition.get('al_content', 0):.1f}%, Ti {composition.get('ti_content', 0):.1f}%, N {composition.get('n_content', 0):.1f}%
- 工艺参数: 温度{process_params.get('deposition_temperature', 0)}°C, 气压{process_params.get('deposition_pressure', 0)}Pa, 偏压{process_params.get('bias_voltage', 0)}V
- 结构设计: {structure_design.get('structure_type', '单层')}, 厚度{structure_design.get('total_thickness', 0)}μm
- 目标需求: {target_requirements}

---

**请生成包含以下内容的实验工单：**

### 1. 工单基本信息
- 工单编号（自动生成格式：WO-YYYYMMDD-XXX）
- 实验名称
- 优化类型
- 创建时间

### 2. 优化后的配方参数
根据优化建议，给出具体的调整后参数值：
- 成分配比（Al/Ti/N比例）
- 工艺参数（温度、气压、偏压、气体流量等）
- 结构设计（层数、厚度等）

### 3. 实验步骤
详细列出实验执行步骤，包括：
- 设备准备
- 参数设置
- 沉积过程
- 后处理

### 4. 关键控制点
列出需要重点关注的参数和注意事项

### 5. 预期性能提升
基于优化建议，预测性能改善情况

### 6. 质量检验要求
需要进行的测试项目和标准

**输出要求：**
- 使用Markdown格式
- 参数值要具体、准确，直接可用于实验
- 简洁专业，重点突出
- 使用中文输出
"""
    
    # 使用LLM流式生成
    llm = get_material_expert_llm()
    content = ""
    
    try:
        for chunk in llm.stream([
            SystemMessage(content=MATERIAL_EXPERT_PROMPT),
            HumanMessage(content=prompt)
        ]):
            if hasattr(chunk, 'content') and chunk.content:
                content += chunk.content
                if stream_callback:
                    stream_callback('experiment_workorder_generation', chunk.content)
        
        logger.info(f"[实验工单生成] LLM生成完成，长度: {len(content)}")
        return content
        
    except Exception as e:
        logger.error(f"[实验工单生成] LLM生成失败: {str(e)}")
        return f"实验工单生成失败: {str(e)}"


def predict_performance_improvement(opt_type: str, plan: Dict, current_perf: Dict, state: Dict) -> Dict:
    """预测性能提升"""
    current_hardness = current_perf.get("hardness", 28.5)
    
    # 基于优化类型的提升预测
    if "P1" in opt_type:  # 成分优化
        improvement_range = (2.0, 5.0)
    elif "P2" in opt_type:  # 结构优化  
        improvement_range = (1.5, 4.0)
    elif "P3" in opt_type:  # 工艺优化
        improvement_range = (1.0, 3.0)
    else:
        improvement_range = (1.0, 2.0)
    
    # 取中位数作为预测值
    predicted_improvement = sum(improvement_range) / 2
    predicted_hardness = current_hardness + predicted_improvement
    
    return {
        "current_hardness": current_hardness,
        "predicted_hardness": predicted_hardness,
        "improvement_value": predicted_improvement,
        "improvement_percentage": (predicted_improvement / current_hardness) * 100,
        "confidence": 0.75,
        "improvement_range": improvement_range,
        "risk_assessment": "中等风险",
        "key_factors": [
            f"{opt_type}方案实施效果",
            "工艺控制精度",
            "材料批次稳定性"
        ]
    }


def generate_optimized_parameters(plan: Dict, state: Dict) -> Dict:
    """生成优化后的参数"""
    logger.info(f"[generate_optimized_parameters] 输入plan: {plan}")
    logger.info(f"[generate_optimized_parameters] state中的coating_composition: {state.get('coating_composition')}")
    logger.info(f"[generate_optimized_parameters] state中的process_params: {state.get('process_params')}")
    
    current_composition = state.get("coating_composition", {})
    current_process = state.get("process_params", {})
    current_structure = state.get("structure_design", {})
    
    # 基于选择的方案类型调整参数
    optimized = {
        "composition": current_composition.copy() if current_composition else {},
        "process_params": current_process.copy() if current_process else {},
        "structure_design": current_structure.copy() if current_structure else {}
    }
    
    opt_type = plan.get("type", "")
    logger.info(f"[generate_optimized_parameters] 优化类型: {opt_type}")
    
    if "P1" in opt_type:
        # 成分优化示例
        optimized["composition"]["al_content"] = min(65, current_composition.get("al_content", 30) + 5)
        optimized["composition"]["ti_content"] = max(15, current_composition.get("ti_content", 25) - 3)
    
    elif "P2" in opt_type:
        # 结构优化示例
        optimized["structure_design"]["total_thickness"] = current_structure.get("total_thickness", 2.0) * 1.2
        optimized["structure_design"]["layer_type"] = "多层"
    
    elif "P3" in opt_type:
        # 工艺优化示例
        optimized["process_params"]["deposition_temperature"] = current_process.get("deposition_temperature", 550) + 30
        optimized["process_params"]["bias_voltage"] = current_process.get("bias_voltage", 90) + 15
    
    logger.info(f"[generate_optimized_parameters] 返回结果: {optimized}")
    return optimized


def generate_experiment_workorder(plan: Dict, params: Dict, improvement: Dict, state: Dict) -> Dict:
    """生成实验工单"""
    workorder_id = f"WO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 提取优化类型和描述
    optimization_type = plan.get("type", "未知优化类型") if plan else "未指定"
    plan_description = plan.get("description", "无描述") if plan else "无描述"
    
    # 提取预测性能或设置默认值
    target_hardness = improvement.get("predicted_hardness", 0) if improvement else 0
    expected_improvements = []
    
    if improvement:
        if improvement.get("improvement_value", 0) > 0:
            expected_improvements.append(f"硬度提升 {improvement.get('improvement_value', 0):.1f} GPa")
        if improvement.get("improvement_percentage", 0) > 0:
            expected_improvements.append(f"性能提升 {improvement.get('improvement_percentage', 0):.1f}%")
    
    if not expected_improvements:
        expected_improvements = ["性能优化验证"]
    
    return {
        "workorder_id": workorder_id,
        "created_at": datetime.now().isoformat(),
        "optimization_type": optimization_type,
        "plan_description": plan_description,
        "selected_option": plan.get("id", "unknown") if plan else "unknown",
        "target_hardness": target_hardness,
        "optimized_parameters": params or {},
        "expected_improvements": expected_improvements,
        "characterization_plan": [
            "硬度测试（纳米压痕）",
            "SEM形貌观察",
            "厚度测量（台阶仪）",
            "结合力测试（划痕法）",
            "XRD相结构分析"
        ],
        "expected_timeline": "5-7个工作日",
        "priority": "normal",
        "notes": f"基于{optimization_type}的优化方案实验验证：{plan_description}"
    }


def analyze_experiment_results(results: Dict, predicted: Dict, baseline: Dict) -> Dict:
    """分析实验结果"""
    actual_hardness = results.get("hardness_test", {}).get("value", 0)
    predicted_hardness = predicted.get("predicted_hardness", 0)
    baseline_hardness = baseline.get("hardness", 0)
    
    # 计算性能差距
    prediction_error = abs(actual_hardness - predicted_hardness)
    actual_improvement = actual_hardness - baseline_hardness
    
    # 成功评估
    success_rate = min(100, max(0, (actual_improvement / predicted.get("improvement_value", 1)) * 100))
    
    return {
        "actual_hardness": actual_hardness,
        "predicted_hardness": predicted_hardness,
        "baseline_hardness": baseline_hardness,
        "actual_improvement": actual_improvement,
        "predicted_improvement": predicted.get("improvement_value", 0),
        "prediction_accuracy": max(0, 100 - (prediction_error / predicted_hardness * 100)),
        "performance_gap": {
            "hardness_gap": prediction_error,
            "relative_error": prediction_error / predicted_hardness * 100
        },
        "success_evaluation": {
            "success_rate": success_rate,
            "achievement_level": "优秀" if success_rate > 80 else "良好" if success_rate > 60 else "需改进"
        }
    }


def make_iteration_decision(success_eval: Dict, current_iter: int, max_iter: int, state: Dict) -> Dict:
    """迭代决策逻辑"""
    success_rate = success_eval.get("success_rate", 0)
    
    if success_rate > 80:
        # 成功，结束迭代
        return {
            "next_action": "complete",
            "next_step": "result_summary",
            "reason": f"优化效果良好，成功率{success_rate:.1f}%",
            "workflow_status": "completed"
        }
    
    elif current_iter >= max_iter:
        # 达到最大迭代次数
        return {
            "next_action": "complete",
            "next_step": "result_summary", 
            "reason": f"达到最大迭代次数{max_iter}",
            "workflow_status": "completed"
        }
    
    elif success_rate > 40:
        # 继续当前优化路径
        return {
            "next_action": "continue_current",
            "next_step": "performance_improvement_prediction",
            "reason": f"当前方案有效果但仍有提升空间，成功率{success_rate:.1f}%",
            "workflow_status": "iterating"
        }
    
    else:
        # 尝试其他优化路径
        return {
            "next_action": "try_other",
            "next_step": "p1_composition_optimization",
            "reason": f"当前方案效果不佳，成功率{success_rate:.1f}%，尝试其他优化路径",
            "suggested_optimization": suggest_alternative_optimization(state),
            "workflow_status": "iterating"
        }


def suggest_alternative_optimization(state: Dict) -> Dict:
    """建议替代的优化方案"""
    tried_optimizations = state.get("optimization_history", [])
    
    # 简化的替代方案建议逻辑
    all_types = ["P1_成分优化", "P2_结构优化", "P3_工艺优化"]
    tried_types = [opt.get("type") for opt in tried_optimizations]
    
    for opt_type in all_types:
        if opt_type not in tried_types:
            return {"type": opt_type, "reason": f"尝试{opt_type}路径"}
    
    return {"type": "P1_成分优化", "reason": "重新评估成分配比"}


def generate_final_summary(state: Dict) -> Dict:
    """生成最终结果汇总"""
    return {
        "task_id": state["task_id"],
        "completion_time": datetime.now().isoformat(),
        "initial_performance": state.get("performance_prediction", {}),
        "final_performance": state.get("experiment_results", {}),
        "optimization_history": state.get("optimization_history", []),
        "total_iterations": state.get("current_iteration", 0),
        "success_metrics": state.get("experiment_analysis", {}).get("success_evaluation", {}),
        "key_achievements": [
            "完成涂层性能预测",
            "生成多维度优化建议",
            "实施闭环实验验证"
        ],
        "recommendations": "基于实验结果，建议进一步优化工艺参数以获得更稳定的性能表现"
    }


