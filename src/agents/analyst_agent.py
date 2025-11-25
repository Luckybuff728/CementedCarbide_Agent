"""
Analyst Agent - 性能分析专家
负责：
1. 调用TopPhi模拟
2. 调用ML模型预测
3. 检索历史案例
4. 进行综合根因分析
"""
from typing import Dict, Any
from langchain_core.messages import AIMessage
from ..graph.agent_state import CoatingAgentState
from .tools import (
    simulate_topphi_tool,
    predict_ml_performance_tool,
    compare_historical_tool
)
from ..services.coating_service import CoatingService
import logging

logger = logging.getLogger(__name__)


def analyst_agent_node(state: CoatingAgentState) -> Dict[str, Any]:
    """
    Analyst Agent 节点
    
    执行完整的性能分析流程：
    1. TopPhi模拟 → 微观结构预测
    2. ML模型 → 性能预测
    3. 历史对比 → 相似案例
    4. 根因分析 → 综合评价
    
    Returns:
        更新分析结果到状态
    """
    logger.info(f"[Analyst] 任务 {state.get('task_id')} 开始分析")
    
    # 准备参数
    composition = state.get("coating_composition", {})
    process_params = state.get("process_params", {})
    structure_design = state.get("structure_design", {})
    target_requirements = state.get("target_requirements", "")
    
    try:
        # ========== 1. TopPhi 模拟 ==========
        logger.info("[Analyst] 步骤 1/4: TopPhi模拟")
        
        topphi_result = simulate_topphi_tool.invoke({
            "coating_composition": composition,
            "process_params": process_params
        })
        
        if "error" in topphi_result:
            raise Exception(f"TopPhi模拟失败: {topphi_result['error']}")
        
        topphi_data = topphi_result.get("topphi_simulation", {})
        
        # ========== 2. ML 性能预测 ==========
        logger.info("[Analyst] 步骤 2/4: ML性能预测")
        
        ml_result = predict_ml_performance_tool.invoke({
            "coating_composition": composition,
            "process_params": process_params,
            "structure_design": structure_design
        })
        
        if "error" in ml_result:
            raise Exception(f"ML预测失败: {ml_result['error']}")
        
        ml_data = ml_result.get("ml_prediction", {})
        perf_data = ml_result.get("performance_prediction", {})
        
        # ========== 3. 历史数据对比 ==========
        logger.info("[Analyst] 步骤 3/4: 历史数据对比")
        
        historical_result = compare_historical_tool.invoke({
            "coating_composition": composition,
            "process_params": process_params
        })
        
        if "error" in historical_result:
            logger.warning(f"[Analyst] 历史对比警告: {historical_result['error']}")
            historical_data = {"total_cases": 0, "similar_cases": []}
        else:
            historical_data = historical_result.get("historical_comparison", {})
        
        # ========== 4. 根因分析（调用统一的服务层） ==========
        logger.info("[Analyst] 步骤 4/4: 综合根因分析")
        
        # 构建完整状态，调用coating_service的根因分析
        analysis_state = {
            "task_id": state.get("task_id"),
            "coating_composition": composition,
            "process_params": process_params,
            "structure_design": structure_design,
            "target_requirements": target_requirements,
            "topphi_simulation": topphi_data,
            "ml_prediction": ml_data,
            "historical_comparison": historical_data
        }
        
        coating_service = CoatingService()
        root_cause_result = coating_service.integrate_analysis(analysis_state)
        
        if root_cause_result.get("status") != "success":
            logger.warning(f"[Analyst] 根因分析警告: {root_cause_result.get('message')}")
            integrated_data = {
                "summary": "根因分析生成失败，请稍后重试。",
                "root_cause_analysis": "",
                "key_findings": [],
                "recommendations": []
            }
        else:
            integrated_data = root_cause_result.get("data", {}).get("integrated_analysis", {})
        
        logger.info(f"[Analyst] 分析完成")
        
        # 添加完成消息
        completion_message = AIMessage(
            content=f"✅ **性能分析完成**\n\n"
                   f"- TopPhi模拟：晶粒尺寸 {topphi_data.get('grain_size_nm', 0)} nm\n"
                   f"- 性能预测：硬度 {perf_data.get('hardness', 0):.1f} GPa\n"
                   f"- 综合分析：已生成详细报告"
        )
        
        # 返回所有结果（一次性返回）
        return {
            "topphi_simulation": topphi_data,
            "ml_prediction": ml_data,
            "performance_prediction": perf_data,
            "historical_comparison": historical_data,
            "integrated_analysis": integrated_data,
            "current_agent": "analyst",
            "messages": [completion_message],  # 添加完成消息
            "last_completed_agent": "analyst"  # 重要：标记完成
        }
    
    except Exception as e:
        logger.error(f"[Analyst] 执行失败: {str(e)}", exc_info=True)
        
        return {
            "current_agent": "analyst",
            "error_message": str(e),
            "messages": [AIMessage(content=f"❌ 分析失败: {str(e)}")],
            "last_completed_agent": "analyst"  # 即使失败也标记完成，避免循环
        }

