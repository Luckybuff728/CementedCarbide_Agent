"""
Optimizer Agent - 优化方案专家
负责生成 P1/P2/P3 优化建议
"""
from typing import Dict, Any
from langchain_core.messages import AIMessage
from ..graph.agent_state import CoatingAgentState
from .tools import (
    generate_p1_optimization_tool,
    generate_p2_optimization_tool,
    generate_p3_optimization_tool
)
from ..services.coating_service import CoatingService
import logging

logger = logging.getLogger(__name__)

coating_service = CoatingService()


def optimizer_agent_node(state: CoatingAgentState) -> Dict[str, Any]:
    """
    Optimizer Agent 节点
    
    并行生成三种优化建议：
    1. P1 - 成分优化
    2. P2 - 结构优化
    3. P3 - 工艺优化
    
    然后生成综合建议
    
    Returns:
        更新p1_content, p2_content, p3_content, comprehensive_recommendation
    """
    logger.info(f"[Optimizer] 任务 {state.get('task_id')} 开始生成优化方案")
    
    messages = []
    results = {}
    
    try:
        # 获取根因分析结果
        analysis_result = state.get("integrated_analysis", {})
        
        if not analysis_result:
            raise Exception("缺少根因分析结果，无法生成优化方案")
        
        # 获取所有相关数据（关键！用于优化方案生成）
        coating_composition = state.get("coating_composition", {})
        process_params = state.get("process_params", {})
        structure_design = state.get("structure_design", {})
        performance_prediction = state.get("performance_prediction", {})
        target_requirements = state.get("target_requirements", "")
        
        logger.info(f"[Optimizer] 当前参数: composition={coating_composition}, process={process_params}")
        
        # ========== 1. 生成 P1 成分优化 ==========
        logger.info("[Optimizer] 生成P1成分优化")
        
        p1_result = generate_p1_optimization_tool.invoke({
            "analysis_result": analysis_result,
            "optimization_type": "P1",
            "coating_composition": coating_composition,
            "process_params": process_params,
            "structure_design": structure_design,
            "performance_prediction": performance_prediction,
            "target_requirements": target_requirements
        })
        
        if "error" in p1_result:
            logger.error(f"[Optimizer] P1生成失败: {p1_result['error']}")
            p1_content = f"P1生成失败: {p1_result['error']}"
        else:
            p1_content = p1_result.get("content", "")
        
        results["p1_content"] = p1_content
        logger.info(f"[Optimizer] P1完成，长度: {len(p1_content)}")
        
        # ========== 2. 生成 P2 结构优化 ==========
        logger.info("[Optimizer] 生成P2结构优化")
        
        p2_result = generate_p2_optimization_tool.invoke({
            "analysis_result": analysis_result,
            "optimization_type": "P2",
            "coating_composition": coating_composition,
            "process_params": process_params,
            "structure_design": structure_design,
            "performance_prediction": performance_prediction,
            "target_requirements": target_requirements
        })
        
        if "error" in p2_result:
            logger.error(f"[Optimizer] P2生成失败: {p2_result['error']}")
            p2_content = f"P2生成失败: {p2_result['error']}"
        else:
            p2_content = p2_result.get("content", "")
        
        results["p2_content"] = p2_content
        logger.info(f"[Optimizer] P2完成，长度: {len(p2_content)}")
        
        # ========== 3. 生成 P3 工艺优化 ==========
        logger.info("[Optimizer] 生成P3工艺优化")
        
        p3_result = generate_p3_optimization_tool.invoke({
            "analysis_result": analysis_result,
            "optimization_type": "P3",
            "coating_composition": coating_composition,
            "process_params": process_params,
            "structure_design": structure_design,
            "performance_prediction": performance_prediction,
            "target_requirements": target_requirements
        })
        
        if "error" in p3_result:
            logger.error(f"[Optimizer] P3生成失败: {p3_result['error']}")
            p3_content = f"P3生成失败: {p3_result['error']}"
        else:
            p3_content = p3_result.get("content", "")
        
        results["p3_content"] = p3_content
        logger.info(f"[Optimizer] P3完成，长度: {len(p3_content)}")
        
        messages.append(AIMessage(content="✅ **P1/P2/P3 优化方案已生成**\n\n正在生成综合建议..."))
        
        # ========== 4. 生成综合建议 ==========
        logger.info("[Optimizer] 生成综合建议")
        
        # 更新state以便coating_service访问
        temp_state = dict(state)
        temp_state.update(results)
        
        summary_result = coating_service.generate_optimization_summary(temp_state)
        
        if summary_result.get("status") == "success":
            comprehensive = summary_result.get("data", {}).get("comprehensive_recommendation", "")
            results["comprehensive_recommendation"] = comprehensive
            
            messages.append(AIMessage(content=f"✅ **综合建议已生成**\n\n{comprehensive}"))
        else:
            logger.error(f"[Optimizer] 综合建议生成失败: {summary_result.get('message')}")
            results["comprehensive_recommendation"] = "综合建议生成失败"
        
        logger.info(f"[Optimizer] 优化方案生成完成")
        
        return {
            **results,
            "current_agent": "optimizer", 
            "messages": messages,
            # ✅ 标记完成，让 Supervisor → ask_user
            # 前端收到 p1/p2/p3 数据后，会在右侧自动显示 OptimizationSelector
            # 用户可以继续对话，也可以直接在右侧选择
            "last_completed_agent": "optimizer"
        }
    
    except Exception as e:
        logger.error(f"[Optimizer] 执行失败: {str(e)}", exc_info=True)
        
        messages.append(AIMessage(content=f"❌ **优化方案生成出错**\n\n{str(e)}\n\n请重试或联系技术支持。"))
        
        return {
            "current_agent": "optimizer",
            "error_message": str(e),
            "messages": messages
        }

