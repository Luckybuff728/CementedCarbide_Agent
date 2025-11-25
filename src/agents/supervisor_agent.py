"""
Supervisor Agent - 多Agent系统的总控节点
负责：
1. 理解用户需求
2. 自主决定下一步行动（调用Worker / 请求用户输入 / 结束）
3. 协调各个Worker Agent
4. 与用户进行多轮对话
"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from ..graph.agent_state import CoatingAgentState
from ..llm import get_llm_service
import logging
import json

logger = logging.getLogger(__name__)

# Supervisor 的系统提示词
SUPERVISOR_SYSTEM_PROMPT = """你是 TopMat 涂层优化系统的总控 Agent（Supervisor）。

**核心理念：对话式协作，而非自动化流水线**

你的工作方式：
1. 每执行一个操作后，必须向用户报告并等待反馈
2. 用户可以随时提问、修改需求、或要求继续
3. 你需要理解用户意图，而不是机械地执行固定流程

**可调度的专家Agent：**
- **Validator**: 参数验证专家（检查输入参数有效性）
- **Analyst**: 性能分析专家（TopPhi模拟+ML预测+根因分析）
- **Optimizer**: 优化方案专家（生成P1/P2/P3优化建议）
- **Experimenter**: 实验工单专家（生成实验指导）

**关键决策规则（必须严格遵守）：**

1. **每个Agent执行完后，必须先与用户对话（ask_user）**
   - Validator完成 → ask_user 询问："参数验证完成，是否继续进行性能分析？"
   - Analyst完成 → ask_user 询问："性能分析完成，您对结果有疑问吗？要继续生成优化方案吗？"
   - Optimizer完成 → ask_user 询问："已生成3个优化方案，您想了解哪个？或直接选择？"
   - Experimenter完成 → ask_user 询问："工单已生成，请问还需要什么帮助？"

2. **只有在用户明确表示继续时，才调用下一个Agent**
   - 用户说"继续"/"下一步"/"好的"/"可以" → 调用下一个Agent
   - 用户提问 → ask_user 回答问题，不调用新Agent
   - 用户要修改 → ask_user 确认需求，可能需要重新调用之前的Agent

3. **初始状态判断（重要！检查状态摘要中的参数信息）**
   - 如果状态显示"用户提供的涂层成分: Al X%, Ti Y%" → 参数已提供，ask_user确认："我看到您提供了涂层参数(Al X%, Ti Y%)，要开始验证吗？"
   - 如果状态显示"用户未提供涂层成分参数" → 参数缺失，ask_user询问："请提供涂层参数（Al、Ti、N含量等），我才能开始分析"
   - 如果用户只说"帮我优化"但没有参数 → ask_user："请先提供涂层参数"

4. **永远不要连续调用多个Agent**
   - 错误：Validator → Analyst → Optimizer（自动执行）
   - 正确：Validator → ask_user → (等用户确认) → Analyst → ask_user → ...

5. **特殊情况**
   - 用户提供实验结果 → 根据continue_iteration决定是否继续
   - 用户说"结束"/"完成" → FINISH
   - 不确定用户意图 → ask_user 询问澄清

**输出格式（JSON）：**
```json
{{
  "next_action": "Validator | Analyst | Optimizer | Experimenter | ask_user | FINISH",
  "reason": "决策理由",
  "message_to_user": "给用户的消息（如果是ask_user则必填）",
  "parameters": {{}}
}}
```

**决策示例（标准流程 - 对话式）：**

场景1：用户首次提交参数
```json
{{
  "next_action": "ask_user",
  "reason": "新任务开始，需要与用户确认",
  "message_to_user": "您好！我看到您提供了AlTiN涂层参数（Al 60%, Ti 40%），目标是提升硬度。我现在开始验证参数可以吗？",
  "parameters": {{}}
}}
```

场景2：用户确认后，开始验证
```json
{{
  "next_action": "Validator",
  "reason": "用户确认开始，执行参数验证",
  "message_to_user": null,
  "parameters": {{}}
}}
```

场景3：Validator完成后（关键！必须ask_user）
```json
{{
  "next_action": "ask_user",
  "reason": "验证完成，需要向用户报告并询问下一步",
  "message_to_user": "参数验证通过！您的配方成分和工艺参数都在合理范围内。下一步我可以进行性能预测分析（包括TopPhi模拟、ML预测），大约需要30秒。要继续吗？",
  "parameters": {{}}
}}
```

场景4：用户说"继续"或"好的"
```json
{{
  "next_action": "Analyst",
  "reason": "用户确认继续，执行性能分析",
  "message_to_user": null,
  "parameters": {{}}
}}
```

场景5：Analyst完成后（必须ask_user）
```json
{{
  "next_action": "ask_user",
  "reason": "分析完成，报告结果并征询意见",
  "message_to_user": "性能分析完成！预测硬度：32.5 GPa，结合力：45 N。主要问题：Al含量偏高导致脆性增加。您对这个结果有疑问吗？或者我直接生成优化方案？",
  "parameters": {{}}
}}
```

场景5a：Optimizer完成后（已生成 P1/P2/P3 三个方案，但用户还未选择）
```json
{{
  "next_action": "ask_user",
  "reason": "优化方案已生成，右侧UI会自动显示选择器，用户可以对话或选择",
  "message_to_user": "已生成3个优化方案（P1/P2/P3）。您可以：\n- 在右侧面板查看并选择方案\n- 或继续询问方案细节、要求调整等",
  "parameters": {{}}
}}
```

场景5b：用户在右侧UI选择了方案后（状态中有 selected_optimization_type）
```json
{{
  "next_action": "Experimenter",
  "reason": "用户已选择方案，生成实验工单",
  "message_to_user": null,
  "parameters": {{}}
}}
```

场景5c：工单已生成但尚未输入实验结果（状态摘要会显示"待输入实验结果"）
```json
{{
  "next_action": "Experimenter",
  "reason": "工单已生成，再次调用Experimenter进入等待实验结果状态",
  "message_to_user": null,
  "parameters": {{}}
}}
```

场景6：Experimenter完成实验结果分析后（状态中有experiment_analysis）
- ⚠️ 关键：必须先询问用户是否继续迭代，让用户看到分析对比图后再决定
```json
{{
  "next_action": "ask_user",
  "reason": "实验分析完成，询问用户是否继续迭代",
  "message_to_user": "实验结果分析完成！请查看右侧的性能对比图。您可以看到实验数据与ML预测的对比情况。\n\n是否需要继续优化？我可以基于分析结果生成新的优化方案。",
  "parameters": {{}}
}}
```

场景7：用户确认"继续迭代"/"继续优化"后
- 此时应该设置continue_iteration_flag并重新开始分析流程
```json
{{
  "next_action": "Analyst",
  "reason": "用户确认继续迭代，基于优化建议的新参数重新进行性能分析",
  "message_to_user": null,
  "parameters": {{"continue_iteration": true}}
}}
```

场景8：用户说"不继续"/"结束"或目标已达成
```json
{{
  "next_action": "FINISH",
  "reason": "优化流程完成",
  "message_to_user": "优化流程已完成！感谢使用 TopMat 系统。您可以下载实验报告。",
  "parameters": {{}}
}}
```

**关键原则：**
1. 每个Agent完成后，必须调用 ask_user 向用户报告
2. 只有用户明确表示继续时，才调用下一个Agent
3. 用户提问时，用 ask_user 回答，不要继续执行
4. 迭代场景：Experimenter 完成后，如果 continue_iteration_flag=True，自动调用 Analyst 开始新一轮

现在，请基于对话历史和当前状态，做出下一步决策。
"""


def supervisor_node(state: CoatingAgentState) -> Dict[str, Any]:
    """
    Supervisor Agent 节点 - LLM驱动的决策中心
    
    Args:
        state: 当前Agent状态
        
    Returns:
        更新后的状态，包含next_action字段
    """
    logger.info(f"[Supervisor] 任务 {state.get('task_id')} 开始决策")
    
    # 构建上下文提示
    context_info = _build_context_info(state)
    
    # 构建Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", SUPERVISOR_SYSTEM_PROMPT),
        ("system", f"**当前状态摘要：**\n{context_info}"),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "请基于以上信息，输出你的决策（JSON格式）：")
    ])
    
    # 调用LLM
    llm_service = get_llm_service()
    llm = llm_service.llm
    
    try:
        # 准备消息
        formatted_messages = prompt.invoke({"messages": state.get("messages", [])})
        
        # ===== 重要：使用非流式调用，避免JSON被流式输出到前端 =====
        # 临时禁用streaming，只获取最终结果
        original_streaming = llm.streaming
        llm.streaming = False
        
        try:
            # 调用LLM生成决策（非流式）
            response = llm.invoke(formatted_messages)
        finally:
            # 恢复原始streaming设置
            llm.streaming = original_streaming
        
        # 解析LLM输出
        decision = _parse_llm_decision(response.content)
        
        logger.info(f"[Supervisor] 决策: {decision['next_action']}, 理由: {decision['reason']}")
        
        # ===== 关键保护：防止重复调用刚完成的Agent =====
        last_completed = state.get("last_completed_agent")
        
        # 普通场景：防止重复调用刚完成的Agent
        if last_completed and decision["next_action"].lower() == last_completed.lower():
            logger.warning(f"[Supervisor] ⚠️ 检测到循环：{last_completed}刚完成，但决策要再次调用它！强制改为ask_user")
            decision["next_action"] = "ask_user"
            if not decision.get("message_to_user"):
                decision["message_to_user"] = f"✅ {last_completed.title()}已完成，请问您还需要什么帮助？"
        
        # 只添加给用户的消息，不添加JSON响应（避免前端显示结构化数据）
        new_messages = []
        state_updates = {}
        
        if decision.get("message_to_user"):
            # 只添加格式化的用户消息
            new_messages.append(AIMessage(content=decision["message_to_user"]))
        
        # ===== 🔄 迭代场景处理：用户确认继续迭代时，更新参数 =====
        params = decision.get("parameters", {})
        if params.get("continue_iteration") and decision["next_action"].lower() == "analyst":
            logger.info("[Supervisor] 🔄 用户确认继续迭代，准备更新参数...")
            
            # 从优化建议中提取新参数
            from ..services.experiment_analysis_service import get_experiment_analysis_service
            analysis_service = get_experiment_analysis_service()
            
            selected_type = state.get("selected_optimization_type", "P1")
            optimization_content = state.get(f"{selected_type.lower()}_content", "")
            
            new_params = analysis_service.extract_new_parameters_from_optimization(
                selected_type=selected_type,
                optimization_content=optimization_content,
                current_composition=state.get("coating_composition", {}),
                current_process=state.get("process_params", {})
            )
            
            # 更新状态
            state_updates = {
                "coating_composition": new_params.get("new_composition"),
                "process_params": new_params.get("new_process"),
                "parameter_update_source": selected_type,
                "current_iteration": state.get("current_iteration", 1) + 1,
                "continue_iteration_flag": True,
                # 清理旧数据，准备新一轮
                "experiment_workorder": None,
                "experiment_results": None,
                "experiment_analysis": None,
                "performance_comparison": None,
                "selected_optimization_type": None,
                "selected_optimization_name": None,
                "p1_content": None,
                "p2_content": None,
                "p3_content": None,
                "comprehensive_recommendation": None,
            }
            
            logger.info(f"[Supervisor] 参数已更新，开始第 {state_updates['current_iteration']} 轮迭代")
            new_messages.append(AIMessage(
                content=f"🔄 **开始第 {state_updates['current_iteration']} 轮迭代**\n\n"
                       f"已采用 {selected_type} 优化建议中的参数，正在重新分析..."
            ))
        
        # 清除last_completed_agent标记（已经处理过了）
        return {
            **state_updates,
            "next_action": decision["next_action"],
            "current_agent": "supervisor",
            "messages": new_messages,
            "last_completed_agent": None  # 清除标记，避免重复检查
        }
        
    except Exception as e:
        logger.error(f"[Supervisor] 决策失败: {str(e)}")
        
        # 降级策略：基于状态做简单决策
        fallback_action = _fallback_decision(state)
        
        return {
            "next_action": fallback_action,
            "current_agent": "supervisor",
            "messages": [AIMessage(content=f"系统正在处理您的请求...")]
        }


def _build_context_info(state: CoatingAgentState) -> str:
    """构建当前状态的摘要信息"""
    info_parts = []
    
    # 任务基本信息
    info_parts.append(f"- 任务ID: {state.get('task_id', 'N/A')}")
    info_parts.append(f"- 当前迭代: {state.get('current_iteration', 1)}/{state.get('max_iterations', 5)}")
    
    # 迭代标志与参数更新
    continue_iteration = state.get("continue_iteration_flag", False)
    if continue_iteration:
        param_source = state.get("parameter_update_source", "")
        info_parts.append(f"- 🔄 用户已选择继续迭代（参数已更新自 {param_source} 优化建议）")
    
    # **关键**：刚完成的Agent
    last_completed = state.get("last_completed_agent")
    if last_completed:
        agent_names = {
            "validator": "Validator（参数验证）",
            "analyst": "Analyst（性能分析）",
            "optimizer": "Optimizer（优化方案）",
            "experimenter": "Experimenter（实验工单）"
        }
        info_parts.append(f"- ⚠️ 刚完成: {agent_names.get(last_completed, last_completed)} - 必须先与用户对话！")
    
    # 已完成的步骤
    completed_steps = []
    if state.get("validation_passed"):
        completed_steps.append("✓ 参数验证")
    if state.get("integrated_analysis"):
        completed_steps.append("✓ 性能分析")
    
    # ✅ 特别标记：Optimizer刚完成，应直接调用Experimenter
    has_optimization = state.get("p1_content") and state.get("p2_content") and state.get("p3_content")
    has_selection = state.get("selected_optimization_type")
    
    if has_optimization and not has_selection:
        completed_steps.append("✓ 优化建议（⚠️ 待选择方案 → 直接调用Experimenter显示选择器）")
    elif has_optimization and has_selection:
        completed_steps.append(f"✓ 优化建议（已选择: {state.get('selected_optimization_type')}）")
    
    has_workorder = state.get("experiment_workorder")
    has_results = state.get("experiment_results")
    
    if has_workorder and not has_results:
        completed_steps.append("✓ 实验工单（⚠️ 待输入实验结果 → 再次调用Experimenter等待输入）")
    elif has_workorder and has_results:
        completed_steps.append("✓ 实验工单 + 实验结果")
    
    # 实验分析状态（关键：决定是否询问用户继续迭代）
    has_analysis = state.get("experiment_analysis")
    if has_analysis:
        is_met = has_analysis.get("is_target_met", False)
        if is_met:
            completed_steps.append("✓ 实验分析（🎉 目标达成！→ 询问用户是否继续或结束）")
        else:
            completed_steps.append("✓ 实验分析（⚠️ 部分未达标 → 必须询问用户是否继续迭代）")
    
    if completed_steps:
        info_parts.append(f"- 已完成步骤: {', '.join(completed_steps)}")
    else:
        info_parts.append("- 已完成步骤: 无（新任务）")
    
    # 用户输入状态
    composition = state.get("coating_composition", {})
    process_params = state.get("process_params", {})
    target_requirements = state.get("target_requirements")
    
    # 目标需求
    if target_requirements:
        if isinstance(target_requirements, dict):
            # 格式化字典为易读文本
            req_parts = []
            if target_requirements.get("substrate"):
                req_parts.append(f"基材:{target_requirements['substrate']}")
            if target_requirements.get("bonding_strength"):
                req_parts.append(f"结合力:{target_requirements['bonding_strength']}N")
            if target_requirements.get("elastic_modulus"):
                req_parts.append(f"弹性模量:{target_requirements['elastic_modulus']}GPa")
            if target_requirements.get("working_temperature"):
                req_parts.append(f"工作温度:{target_requirements['working_temperature']}°C")
            if target_requirements.get("cutting_speed"):
                req_parts.append(f"切削速度:{target_requirements['cutting_speed']}m/min")
            if target_requirements.get("application_scenario"):
                req_parts.append(f"应用场景:{target_requirements['application_scenario']}")
            if target_requirements.get("special_requirements"):
                req_parts.append(f"特殊要求:{target_requirements['special_requirements']}")
            
            if req_parts:
                info_parts.append(f"- 目标需求: {', '.join(req_parts)}")
        else:
            # 字符串格式
            info_parts.append(f"- 目标需求: {target_requirements}")
    
    if composition and any(composition.values()):
        # 有涂层成分数据
        al = composition.get("al_content", 0)
        ti = composition.get("ti_content", 0)
        n = composition.get("n_content", 0)
        info_parts.append(f"- 用户提供的涂层成分: Al {al}%, Ti {ti}%, N {n}%")
    else:
        info_parts.append("- ⚠️ 用户未提供涂层成分参数")
    
    if process_params:
        process_type = process_params.get("process_type", "N/A")
        temp = process_params.get("deposition_temperature", 0)
        info_parts.append(f"- 用户提供的工艺参数: {process_type}, {temp}°C")
    else:
        info_parts.append("- ⚠️ 用户未提供工艺参数")
    
    if state.get("selected_optimization_type"):
        info_parts.append(f"- 用户已选择: {state.get('selected_optimization_type')} 优化方案")
    
    # 实验分析结果
    experiment_analysis = state.get("experiment_analysis")
    if experiment_analysis:
        is_met = experiment_analysis.get("is_target_met", False)
        unmet = experiment_analysis.get("unmet_metrics", [])
        if is_met:
            info_parts.append("- ✅ 实验结果：目标已达成")
        else:
            metric_names = {"hardness": "硬度", "elastic_modulus": "弹性模量", 
                          "wear_rate": "磨损率", "adhesion_strength": "结合力"}
            unmet_names = [metric_names.get(m, m) for m in unmet]
            info_parts.append(f"- ⚠️ 实验结果：{', '.join(unmet_names)} 未达标")
    
    return "\n".join(info_parts)


def _parse_llm_decision(llm_output: str) -> Dict[str, Any]:
    """
    解析LLM输出的决策JSON
    
    支持多种格式：
    1. 纯JSON
    2. Markdown代码块中的JSON
    3. 混合文本中的JSON
    """
    try:
        # 尝试直接解析
        decision = json.loads(llm_output)
        
        # 验证必需字段
        if "next_action" not in decision:
            raise ValueError("缺少 next_action 字段")
        
        return decision
        
    except json.JSONDecodeError:
        # 尝试从Markdown代码块中提取
        import re
        
        # 匹配 ```json ... ``` 或 ``` ... ```
        json_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        matches = re.findall(json_pattern, llm_output, re.DOTALL)
        
        if matches:
            try:
                decision = json.loads(matches[0])
                if "next_action" in decision:
                    return decision
            except:
                pass
        
        # 尝试查找任何JSON对象
        json_object_pattern = r'\{[^{}]*"next_action"[^{}]*\}'
        matches = re.findall(json_object_pattern, llm_output, re.DOTALL)
        
        if matches:
            try:
                decision = json.loads(matches[0])
                return decision
            except:
                pass
        
        # 解析失败，返回错误
        logger.error(f"[Supervisor] 无法解析LLM输出: {llm_output[:200]}")
        raise ValueError("无法解析LLM决策输出")


def _fallback_decision(state: CoatingAgentState) -> str:
    """
    降级决策逻辑（当LLM解析失败时）
    
    遵循对话式原则：优先ask_user而非自动执行
    """
    # 获取最后几条消息
    messages = state.get("messages", [])
    last_completed = state.get("last_completed_agent")
    
    # **核心规则**：如果刚完成某个Worker Agent，必须先ask_user
    if last_completed in ["validator", "analyst", "optimizer", "experimenter"]:
        logger.info(f"[Fallback] {last_completed}刚完成，强制返回ask_user")
        return "ask_user"  # 报告结果给用户
    
    # 如果用户刚发送消息（last message是HumanMessage），判断意图
    if messages and len(messages) > 0:
        from langchain_core.messages import HumanMessage
        last_msg = messages[-1]
        if isinstance(last_msg, HumanMessage):
            content_lower = last_msg.content.lower()
            
            # 用户说继续
            if any(word in content_lower for word in ["继续", "下一步", "好的", "可以", "开始", "yes", "ok"]):
                # 根据当前进度决定下一个Agent
                if not state.get("validation_passed"):
                    return "Validator"
                elif not state.get("integrated_analysis"):
                    return "Analyst"
                elif not state.get("p1_content"):
                    return "Optimizer"
                elif state.get("selected_optimization_type") and not state.get("experiment_workorder"):
                    return "Experimenter"
            
            # 默认：用户在提问或表达其他意图
            return "ask_user"
    
    # 初始状态：有参数但未验证
    composition = state.get("coating_composition", {})
    if composition and any(composition.values()) and not state.get("validation_passed"):
        # 有实际数据且未验证，询问用户是否开始
        return "ask_user"
    
    # 默认：与用户对话
    return "ask_user"


def create_supervisor_router(state: CoatingAgentState) -> str:
    """
    Supervisor的路由函数
    
    根据next_action决定下一个节点
    """
    next_action = state.get("next_action", "FINISH")
    
    logger.info(f"[Supervisor Router] next_action = {next_action}")
    
    # 映射到实际的节点名称
    action_mapping = {
        "Validator": "validator",
        "Analyst": "analyst",
        "Optimizer": "optimizer",
        "Experimenter": "experimenter",
        "ask_user": "ask_user",
        "FINISH": "FINISH"
    }
    
    return action_mapping.get(next_action, "FINISH")

