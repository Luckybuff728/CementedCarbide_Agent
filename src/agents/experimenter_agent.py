"""
Experimenter Agent - 实验工单和迭代管理专家

核心职责：
1. 生成实验工单
2. 等待用户输入实验结果
3. 分析实验结果（对比预测、对比目标）
4. 管理迭代流程（更新参数、准备下一轮）

迭代逻辑（关键）：
- 用户输入实验数据后，进行对比分析
- 如果继续迭代，从优化建议中提取新参数
- 用新参数重新分析，而不是用原始参数
"""
from typing import Dict, Any
from langchain_core.messages import AIMessage
from langgraph.types import interrupt
from langgraph.errors import GraphInterrupt
from ..graph.agent_state import CoatingAgentState
from .tools import generate_workorder_tool
from ..services.experiment_analysis_service import get_experiment_analysis_service
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def experimenter_agent_node(state: CoatingAgentState) -> Dict[str, Any]:
    """
    Experimenter Agent 节点
    
    处理流程：
    1. 检查用户是否已选择优化方案
    2. 生成实验工单
    3. 等待用户输入实验结果（interrupt）
    4. 分析实验结果（对比预测、对比目标）
    5. 如果继续迭代，更新参数为优化建议中的值
    
    Returns:
        更新实验相关状态
    """
    logger.info(f"[Experimenter] 任务 {state.get('task_id')} 开始")
    
    messages = []
    results = {}
    
    try:
        # ========== 阶段1: 检查用户选择 ==========
        selected_type = state.get("selected_optimization_type")
        selected_name = state.get("selected_optimization_name")
        
        if not selected_type:
            logger.warning("[Experimenter] 用户尚未选择方案")
            return {
                "current_agent": "experimenter",
                "messages": [AIMessage(content="⏳ 等待您在右侧面板选择优化方案...")],
                "last_completed_agent": None
            }
        
        logger.info(f"[Experimenter] 用户已选择方案: {selected_type}")
        
        # 获取对应的优化内容
        content_key = f"{selected_type.lower()}_content"
        optimization_content = state.get(content_key, "")
        
        # ========== 阶段2: 生成实验工单 ==========
        if not state.get("experiment_workorder"):
            logger.info(f"[Experimenter] 生成 {selected_type} 实验工单")
            
            if not optimization_content:
                raise Exception(f"未找到 {selected_type} 优化方案内容")
            
            workorder_result = generate_workorder_tool.invoke({
                "selected_optimization": selected_type,
                "optimization_content": optimization_content,
                "coating_composition": state.get("coating_composition", {}),
                "process_params": state.get("process_params", {}),
                "structure_design": state.get("structure_design", {}),
                "target_requirements": state.get("target_requirements", "")
            })
            
            if workorder_result.get("error"):
                raise Exception(f"工单生成失败: {workorder_result['error']}")
            
            results["experiment_workorder"] = workorder_result
            logger.info("[Experimenter] 工单生成完成")
            
            # 工单生成后返回，等待下一次调用进入interrupt
            return {
                **results,
                "current_agent": "experimenter",
                "messages": messages,
                "last_completed_agent": None
            }
        
        # ========== 阶段3: 等待实验结果 ==========
        if state.get("experiment_workorder") and not state.get("experiment_results"):
            logger.info("[Experimenter] 等待实验结果")
            
            experiment_feedback = interrupt({
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
            
            # ====== interrupt 后继续执行（用户已输入数据）======
            logger.info(f"[Experimenter] 收到实验反馈")
            
            experiment_data = experiment_feedback.get("experiment_data", {})
            # 注意：continue_iteration将在分析完成后询问用户，而不是提交时决定
            
            results["experiment_results"] = experiment_data
            
            # ========== 阶段4: 分析实验结果（关键！）==========
            logger.info("[Experimenter] 开始分析实验结果...")
            
            analysis_service = get_experiment_analysis_service()
            
            # 获取预测数据
            prediction_data = state.get("performance_prediction", {})
            if isinstance(prediction_data, dict):
                prediction_data = prediction_data.get("predicted_performance", prediction_data)
            
            # 获取目标需求
            target_requirements = state.get("target_requirements", {})
            if isinstance(target_requirements, str):
                target_requirements = {}
            
            # 获取历史最优
            historical_best = None
            historical_comparison = state.get("historical_comparison", {})
            if historical_comparison and historical_comparison.get("similar_cases"):
                similar_cases = historical_comparison.get("similar_cases", [])
                if similar_cases:
                    best_case = similar_cases[0]
                    historical_best = {
                        "hardness": best_case.get("hardness", 0),
                        "elastic_modulus": best_case.get("elastic_modulus", 0),
                        "wear_rate": best_case.get("wear_rate", 0),
                        "adhesion_strength": best_case.get("adhesion_strength", 0)
                    }
            
            # 执行综合分析
            analysis_result = analysis_service.analyze_experiment_results(
                experiment_data=experiment_data,
                prediction_data=prediction_data,
                target_requirements=target_requirements,
                historical_best=historical_best
            )
            
            results["experiment_analysis"] = analysis_result
            
            # 性能对比数据（用于前端可视化）
            results["performance_comparison"] = {
                "experiment_data": experiment_data,
                "prediction_data": prediction_data,
                "historical_best": historical_best,
                "target_comparison": analysis_result.get("target_comparison"),
                "prediction_comparison": analysis_result.get("prediction_comparison")
            }
            
            # 生成分析消息
            is_target_met = analysis_result.get("is_target_met", False)
            analysis_report = analysis_result.get("analysis_report", "")
            
            if is_target_met:
                messages.append(AIMessage(content=f"✅ **实验结果达标！**\n\n{analysis_report}"))
            else:
                unmet = analysis_result.get("unmet_metrics", [])
                metric_names = {
                    "hardness": "硬度",
                    "elastic_modulus": "弹性模量", 
                    "wear_rate": "磨损率",
                    "adhesion_strength": "结合力"
                }
                unmet_names = [metric_names.get(m, m) for m in unmet]
                messages.append(AIMessage(
                    content=f"⚠️ **实验结果分析**\n\n"
                           f"未达标指标：{', '.join(unmet_names)}\n\n"
                           f"{analysis_report}"
                ))
            
            # 记录迭代历史
            iteration_record = {
                "iteration": state.get("current_iteration", 1),
                "selected_optimization": selected_type,
                "selected_optimization_name": selected_name,
                "experiment_results": experiment_data,
                "analysis_result": {
                    "is_target_met": is_target_met,
                    "unmet_metrics": analysis_result.get("unmet_metrics", [])
                },
                "timestamp": datetime.now().isoformat()
            }
            
            iteration_history = list(state.get("iteration_history", []))
            iteration_history.append(iteration_record)
            results["iteration_history"] = iteration_history
            
            # ========== 阶段5: 分析完成，返回结果给用户 ==========
            # 先返回分析结果，让用户看到对比图
            # last_completed_agent = "experimenter" 会触发Supervisor询问用户
            results["continue_iteration_flag"] = False  # 默认不继续，等用户确认
            logger.info(f"[Experimenter] 分析完成，等待用户决定是否继续迭代")
        
        # 返回结果
        return {
            **results,
            "current_agent": "experimenter",
            "messages": messages,
            "last_completed_agent": None if results.get("continue_iteration_flag") else "experimenter"
        }
    
    except GraphInterrupt:
        logger.info("[Experimenter] GraphInterrupt 触发，等待用户输入")
        raise
    
    except Exception as e:
        logger.error(f"[Experimenter] 执行失败: {str(e)}", exc_info=True)
        
        return {
            "current_agent": "experimenter",
            "error_message": str(e),
            "messages": [AIMessage(content=f"❌ **实验管理出错**\n\n{str(e)}")],
            "last_completed_agent": "experimenter"
        }

