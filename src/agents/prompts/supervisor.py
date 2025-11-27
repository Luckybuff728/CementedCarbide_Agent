"""
Supervisor Agent - 多Agent系统的总控节点

基于 LangGraph Supervisor 模式实现，负责：
1. 理解用户需求
2. 决定调用哪个 Worker Agent
3. 与用户进行多轮对话
4. 管理整体工作流程
"""
from typing import List, Any, Literal
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
import logging

from ..state import CoatingState

logger = logging.getLogger(__name__)

# Supervisor 的系统提示词
SUPERVISOR_SYSTEM_PROMPT = """你是 TopMat 涂层优化系统的总控 Agent（Supervisor）。

# 1. 角色与能力
- 你负责在多个专家 Agent 之间做"调度与解释"
- 可调度的专家 Agent：
  - **Validator**：参数验证专家，检查成分/工艺是否在合理范围
  - **Analyst**：性能分析专家，整合 TopPhi 模拟 / ML 预测 / 历史数据
  - **Optimizer**：优化方案专家，生成 P1/P2/P3 三类优化方案
  - **Experimenter**：实验专家，生成工单、分析实验结果

# 2. 交互原则（非常重要）
1. **对话式交互**：每完成一个重要步骤，先向用户说明进度，再询问下一步
2. **不要自动串联**：完成一个 Agent 后，必须等待用户确认才能调用下一个
3. **用户优先**：不确定时选择询问用户，用户说"结束"时选择 FINISH

# 3. 决策框架
根据当前状态选择下一步行动：

## 3.1 初始阶段
- 如果没有涂层参数 → 引导用户输入参数
- 如果有参数但未验证 → 建议调用 Validator

## 3.2 验证后
- 验证通过 → 解释结果，询问是否进行性能分析
- 验证失败 → 说明问题，让用户修改参数

## 3.3 分析后
- 分析完成 → 展示结果，询问是否生成优化方案

## 3.4 优化后
- 方案生成 → 解释三类方案，让用户选择
- 用户选择后 → 调用 Experimenter 生成工单

## 3.5 实验后
- 有实验结果 → 分析是否达标
- 达标 → 询问是否结束或继续微调
- 未达标 → 询问是否继续迭代

# 4. 输出格式
你必须以 JSON 格式输出决策：
```json
{
  "next": "validator | analyst | optimizer | experimenter | FINISH",
  "reason": "决策理由",
  "message": "给用户的消息（如果需要）"
}
```

# 5. 沟通风格
- 像资深专家一样提供有深度的分析
- 引用具体数据和材料学原理
- 专业但易懂，避免机械复述
"""


def create_supervisor(
    llm: BaseChatModel,
    agents: dict,
    agent_names: List[str] = None
) -> StateGraph:
    """
    创建 Supervisor 多Agent系统
    
    使用 LangGraph 官方推荐的 Supervisor 模式：
    - Supervisor 负责决策和路由
    - Worker Agents 负责具体任务
    - 所有 Agent 执行后返回 Supervisor
    
    Args:
        llm: 语言模型实例
        agents: Worker Agent 字典 {name: agent}
        agent_names: Agent 名称列表
    
    Returns:
        编译后的 StateGraph
    """
    logger.info("[Supervisor] 创建多Agent系统")
    
    if agent_names is None:
        agent_names = ["validator", "analyst", "optimizer", "experimenter"]
    
    # 创建路由选项
    options = agent_names + ["FINISH"]
    
    def supervisor_node(state: CoatingState) -> dict:
        """
        Supervisor 决策节点
        
        基于当前状态决定下一步行动
        """
        from langchain_core.messages import HumanMessage, AIMessage
        import json
        
        logger.info("[Supervisor] 开始决策")
        
        # 构建上下文信息
        context = _build_context(state)
        
        # 构建消息
        messages = [
            SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
            SystemMessage(content=f"当前状态摘要：\n{context}"),
        ]
        
        # 添加对话历史
        for msg in state.get("messages", [])[-10:]:  # 最近10条
            messages.append(msg)
        
        messages.append(HumanMessage(content="请决定下一步行动（JSON格式）"))
        
        # 调用 LLM
        try:
            response = llm.invoke(messages)
            decision = _parse_decision(response.content)
            
            logger.info(f"[Supervisor] 决策: {decision.get('next')}")
            
            # 构建返回
            result = {
                "current_agent": "supervisor",
                "next": decision.get("next", "FINISH"),
            }
            
            # 如果有消息要发给用户
            if decision.get("message"):
                result["messages"] = [AIMessage(content=decision["message"])]
            
            return result
            
        except Exception as e:
            logger.error(f"[Supervisor] 决策失败: {e}")
            return {
                "current_agent": "supervisor",
                "next": "FINISH",
                "error": {"message": str(e)}
            }
    
    def route_supervisor(state: CoatingState) -> str:
        """路由函数：根据 next 字段决定下一个节点"""
        next_action = state.get("next", "FINISH")
        
        logger.info(f"[Supervisor] 路由决策: next_action={next_action}, agent_names={agent_names}")
        
        if next_action in agent_names:
            logger.info(f"[Supervisor] 路由到: {next_action}")
            return next_action
        else:
            logger.info(f"[Supervisor] 路由到: end (next_action 不在 agent_names 中)")
            return "end"
    
    # 创建图
    workflow = StateGraph(CoatingState)
    
    # 添加 Supervisor 节点
    workflow.add_node("supervisor", supervisor_node)
    
    # 添加 Worker Agent 节点
    for name in agent_names:
        if name in agents:
            workflow.add_node(name, agents[name])
    
    # 设置入口点
    workflow.set_entry_point("supervisor")
    
    # 添加 Supervisor 的条件路由
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {name: name for name in agent_names} | {"end": END}
    )
    
    # 所有 Worker 完成后返回 Supervisor
    for name in agent_names:
        if name in agents:
            workflow.add_edge(name, "supervisor")
    
    logger.info("[Supervisor] 图构建完成")
    
    return workflow


def _build_context(state: CoatingState) -> str:
    """构建当前状态的上下文摘要"""
    lines = []
    
    # 任务信息
    lines.append(f"- 任务ID: {state.get('task_id', 'N/A')}")
    lines.append(f"- 迭代次数: {state.get('current_iteration', 1)}/{state.get('max_iterations', 5)}")
    
    # 已完成步骤
    completed = []
    if state.get("validation_passed"):
        completed.append("✓ 参数验证")
    if state.get("integrated_analysis"):
        completed.append("✓ 性能分析")
    if state.get("p1_optimization"):
        completed.append("✓ 优化方案")
    if state.get("experiment_workorder"):
        completed.append("✓ 实验工单")
    if state.get("experiment_results"):
        completed.append("✓ 实验结果")
    
    if completed:
        lines.append(f"- 已完成: {', '.join(completed)}")
    else:
        lines.append("- 已完成: 无（新任务）")
    
    # 用户输入
    comp = state.get("coating_composition", {})
    if comp:
        al = comp.get("al_content", 0)
        ti = comp.get("ti_content", 0)
        n = comp.get("n_content", 0)
        lines.append(f"- 涂层成分: Al {al}%, Ti {ti}%, N {n}%")
    
    # 选择的优化方案
    if state.get("selected_optimization"):
        lines.append(f"- 已选择方案: {state.get('selected_optimization')}")
    
    # 实验分析
    analysis = state.get("experiment_analysis")
    if analysis:
        is_met = analysis.get("is_target_met", False)
        lines.append(f"- 目标达成: {'是' if is_met else '否'}")
    
    return "\n".join(lines)


def _parse_decision(content: str) -> dict:
    """解析 LLM 输出的决策 JSON"""
    import json
    import re
    
    # 尝试直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # 尝试从代码块提取
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # 尝试查找 JSON 对象
    obj_match = re.search(r'\{[^{}]*"next"[^{}]*\}', content, re.DOTALL)
    if obj_match:
        try:
            return json.loads(obj_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # 默认返回
    logger.warning(f"[Supervisor] 无法解析决策: {content[:100]}")
    return {"next": "FINISH", "reason": "解析失败"}
