"""
涂层研发对话式多Agent系统 (v2.1)

设计理念：
- 对话驱动，而非流程驱动
- Agent 主动与用户沟通，而非无脑执行
- 用户可以随时介入、修改方向
- 智能路由，根据对话内容决定调用哪个专家

更新说明 (v2.1)：
- 简化会话管理，依赖 Checkpointer 自动持久化
    - 工具使用 ToolRuntime 访问状态
"""
import json
from typing import Dict, Any, Optional, AsyncIterator, List, Literal
from loguru import logger
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from .state import CoatingState
from .content_extractor import extract_structured_content


# ==================== 系统提示词 ====================

ROUTER_SYSTEM_PROMPT = """你是 TopMat 涂层研发智能助手的路由器。根据用户消息选择处理专家。

## 核心区分原则

**analyst vs assistant 的关键区别：**
- **analyst**：用户想要**系统计算/预测**当前涂层参数的性能数据（需调用 ML/TopPhi/历史对比工具）
- **assistant**：用户想要**查阅文献知识**或**解释已有结果**（需调用 RAG 或直接回答）

## 路由规则（按优先级判断）

### 1. **validator** - 参数验证
用户提供涂层参数并要求验证时：
- **触发词**：验证、检查参数、参数合理吗、帮我看看参数
- **典型输入**："Al含量27.5%，验证一下"、"这个配方合理吗"

### 2. **analyst** - 性能预测与计算 
**用户要求系统对当前参数进行计算/预测时**：
- **触发词**：预测、预测性能、预测硬度、ML预测、分析性能、计算
- **触发词**：模拟、TopPhi模拟、相场模拟、微观结构预测
- **触发词**：历史案例、相似案例、案例对比、全面分析
- **典型输入**：
  - "预测一下性能" ← analyst
  - "帮我分析这个配方的性能" ← analyst（要计算）
  - "用ML预测硬度" ← analyst
  - "做个全面分析" ← analyst

### 3. **optimizer** - 优化方案生成
用户需要生成优化方案时：
- **触发词**：优化、生成方案、怎么改进、怎么提升、调整配方
- **触发词**：成分优化、工艺优化、结构优化、P1、P2、P3
- **典型输入**："帮我优化"、"怎么提高硬度"、"生成优化方案"

### 4. **experimenter** - 实验数据处理
用户提交实验结果或要生成工单时：
- **触发词**：实验结果、测试数据、实验完成、实测、录入数据
- **触发词**：生成工单、实验工单、选择方案
- **典型输入**："实验完成，硬度29GPa"、"选择P1，生成工单"

### 5. **assistant** - 知识查询与解释（默认） 
**用户想查阅文献资料或解释原理时**：
- **触发词**：文献、论文、资料、查一下、查询、搜索
- **触发词**：原理、机理、为什么、怎么理解、解释、什么是
- **触发词**：制备工艺、沉积方法、PVD、CVD（知识性问题）
- **典型输入**：
  - "TiAlN涂层的制备工艺" ← assistant（查文献）
  - "为什么硬度这么高" ← assistant（解释原理）
  - "查一下相关文献" ← assistant
  - "PVD和CVD有什么区别" ← assistant（知识问题）

## 输出格式
只返回一个词：validator / analyst / optimizer / experimenter / assistant

## 判断示例（重点区分 analyst vs assistant）
| 用户说... | 路由到 | 原因 |
|-----------|--------|------|
| "预测性能" | analyst | 需要ML计算 |
| "预测一下硬度" | analyst | 需要ML计算 |
| "分析这个配方" | analyst | 需要系统分析 |
| "全面分析" | analyst | 需要调用多个工具 |
| "历史相似案例" | analyst | 需要检索历史数据 |
| "TiAlN的制备工艺" | assistant | 查文献知识 |
| "为什么硬度高" | assistant | 解释原理 |
| "查一下文献" | assistant | 明确要查文献 |
| "PVD原理是什么" | assistant | 知识问题 |
| "帮我优化" | optimizer | 生成方案 |
| "验证参数" | validator | 参数检查 |
| "实验完成" | experimenter | 提交结果 |
"""

# ASSISTANT_SYSTEM_PROMPT 已移至 prompts/assistant.py


def create_conversational_graph(
    llm=None,
    use_memory: bool = True
):
    """
    创建对话式涂层研发Agent图
    
    特点：
    - 用户消息驱动
    - 智能路由到合适的专家
    - 每个专家都能与用户对话
    """
    logger.info("[Graph] 创建对话式多Agent图")
    
    # 获取 LLM（普通模式，用于 router 和其他专家）
    if llm is None:
        from ..llm import get_llm, QwenChatOpenAI
        llm = get_llm()  # 不启用思考模式
    
    # 创建思考模式 LLM（仅用于 Assistant）
    from ..llm import QwenChatOpenAI
    import os
    thinking_llm = QwenChatOpenAI(
        model=os.getenv("DASHSCOPE_MODEL_NAME", "qwen-plus"),
        temperature=0.6,
        enable_thinking=True  # 只有 Assistant 启用思考模式
    )
    logger.info("[Graph] Assistant 使用思考模式 LLM")
    
    # ==================== 路由节点 ====================
    async def router_node(state: CoatingState) -> dict:
        """根据用户消息智能路由"""
        messages = state.get("messages", [])
        if not messages:
            return {"next": "assistant"}
        
        last_message = messages[-1]
        if not isinstance(last_message, HumanMessage):
            return {"next": "assistant"}
        
        # 使用 LLM 判断路由
        router_messages = [
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=f"用户消息: {last_message.content}")
        ]
        
        try:
            response = await llm.ainvoke(router_messages)
            route = response.content.strip().lower()
            
            valid_routes = ["validator", "analyst", "optimizer", "experimenter", "assistant"]
            if route not in valid_routes:
                route = "assistant"
            
            logger.info(f"[Router] 路由到: {route}")
            return {"next": route}
        except Exception as e:
            logger.error(f"[Router] 路由失败: {e}")
            return {"next": "assistant"}
    
    # ==================== 通用助手节点（使用思考模式） ====================
    async def assistant_node(state: CoatingState) -> dict:
        """通用对话助手 - 使用思考模式 LLM"""
        messages = state.get("messages", [])
        context = _build_state_summary(state)
        
        system_prompt = ASSISTANT_SYSTEM_PROMPT.format(context=context)
        
        chat_messages = [SystemMessage(content=system_prompt)] + list(messages)
        
        try:
            # 使用思考模式 LLM
            response = await thinking_llm.ainvoke(chat_messages)
            return {
                "messages": [response],
                "current_agent": "assistant"    
            }
        except Exception as e:
            logger.error(f"[Assistant] 生成失败: {e}")
            return {
                "messages": [AIMessage(content="抱歉，我遇到了一些问题。请稍后再试。")],
                "current_agent": "assistant"
            }
    
    # ==================== 专家节点（使用中间件简化） ====================
    def create_expert_node(expert_name: str, expert_prompt: str, tools: list):
        """
        创建专家节点（支持对话+工具调用）
        
        v2.1 更新：
        - 使用中间件注入上下文，替代手动构建
        - 支持对话摘要，优化长对话
        """
        from langchain.agents import create_agent
        from .middleware import get_middleware_stack
        
        # 获取预配置的中间件栈（上下文注入 + 对话摘要 + 调用限制）
        middleware = get_middleware_stack(
            expert_name=expert_name,
            enable_summarization=True,   # 启用对话摘要
            enable_model_limit=True,     # 启用调用限制
            enable_tool_retry=False,     # 暂不启用重试
        )
        
        # 创建 Agent（中间件自动处理上下文注入和摘要）
        expert_agent = create_agent(
            model=llm,
            tools=tools,
            state_schema=CoatingState,
            system_prompt=expert_prompt,
            middleware=middleware,  # v2.1: 使用中间件栈
        )
        
        async def expert_node_func(state: CoatingState) -> dict:
            logger.info(f"[{expert_name}] 开始处理")
            try:
                # 直接传递状态，中间件自动处理上下文注入
                result = await expert_agent.ainvoke(dict(state))
                logger.info(f"[{expert_name}] 处理完成")
                
                # 更新状态
                updates = {
                    "messages": result.get("messages", []),
                    "current_agent": expert_name.lower()
                }
                
                # 根据专家类型更新特定字段
                if expert_name == "Validator" and "validation_passed" in result:
                    updates["validation_passed"] = result["validation_passed"]
                
                return updates
            except Exception as e:
                logger.error(f"[{expert_name}] 处理失败: {e}")
                return {
                    "messages": [AIMessage(content=f"抱歉，{expert_name}处理时遇到问题：{str(e)}")],
                    "current_agent": expert_name.lower()
                }
        
        return expert_node_func
    
    # ==================== 导入工具和提示词 ====================
    from .tools import VALIDATOR_TOOLS, ANALYST_TOOLS, OPTIMIZER_TOOLS, EXPERIMENTER_TOOLS, SHARED_TOOLS
    from .prompts.assistant import ASSISTANT_SYSTEM_PROMPT
    from .prompts.validator import VALIDATOR_SYSTEM_PROMPT
    from .prompts.analyst import ANALYST_SYSTEM_PROMPT
    from .prompts.optimizer import OPTIMIZER_SYSTEM_PROMPT
    from .prompts.experimenter import EXPERIMENTER_SYSTEM_PROMPT
    
    # ==================== 创建图 ====================
    workflow = StateGraph(CoatingState)
    
    # Assistant 使用 RAG 工具（通过 create_expert_node 创建以支持工具调用）
    ASSISTANT_TOOLS = SHARED_TOOLS  # RAG 工具
    
    # 添加节点（5 个专家）
    workflow.add_node("router", router_node)
    # Assistant 使用 create_expert_node 以支持 RAG 工具调用
    workflow.add_node("assistant", create_expert_node("Assistant", ASSISTANT_SYSTEM_PROMPT.format(context=""), ASSISTANT_TOOLS))
    workflow.add_node("validator", create_expert_node("Validator", VALIDATOR_SYSTEM_PROMPT, VALIDATOR_TOOLS))
    workflow.add_node("analyst", create_expert_node("Analyst", ANALYST_SYSTEM_PROMPT, ANALYST_TOOLS))
    workflow.add_node("optimizer", create_expert_node("Optimizer", OPTIMIZER_SYSTEM_PROMPT, OPTIMIZER_TOOLS))
    workflow.add_node("experimenter", create_expert_node("Experimenter", EXPERIMENTER_SYSTEM_PROMPT, EXPERIMENTER_TOOLS))
    
    # 设置入口
    workflow.set_entry_point("router")
    
    # 路由条件边（精简版）
    def route_next(state: CoatingState) -> str:
        return state.get("next", "assistant")
    
    workflow.add_conditional_edges(
        "router",
        route_next,
        {
            "validator": "validator",
            "analyst": "analyst",
            "optimizer": "optimizer",
            "experimenter": "experimenter",
            "assistant": "assistant",
        }
    )
    
    # 所有专家节点完成后结束
    workflow.add_edge("assistant", END)
    workflow.add_edge("validator", END)
    workflow.add_edge("analyst", END)
    workflow.add_edge("optimizer", END)
    workflow.add_edge("experimenter", END)
    
    # 编译
    if use_memory:
        checkpointer = MemorySaver()
        compiled = workflow.compile(checkpointer=checkpointer)
    else:
        compiled = workflow.compile()
    
    logger.info("[Graph] 对话式图创建完成")
    return compiled


def _build_state_summary(state: CoatingState) -> str:
    """
    构建当前状态摘要（供 assistant 回答解释性问题使用）
    
    包含详细的预测结果数据，让 assistant 能够解释这些数据
    """
    parts = []
    
    # 涂层成分
    comp = state.get("coating_composition", {})
    if comp:
        al = comp.get('al_content', 0) or 0
        ti = comp.get('ti_content', 0) or 0
        n = comp.get('n_content', 0) or 0
        parts.append(f"**当前涂层成分：** Al {al:.1f}%, Ti {ti:.1f}%, N {n:.1f}%")
    
    # 工艺参数
    proc = state.get("process_params", {})
    if proc:
        temp = proc.get('deposition_temperature', 0)
        bias = proc.get('bias_voltage', 0)
        pressure = proc.get('deposition_pressure', 0)
        parts.append(f"**工艺参数：** 温度 {temp}°C, 偏压 {bias}V, 气压 {pressure}Pa")
    
    # 验证状态
    if state.get("validation_passed"):
        parts.append("**参数验证：** ✅ 已通过")
    elif state.get("validation_result"):
        parts.append("**参数验证：** ❌ 未通过")
    
    # ML预测结果（详细数据，供解释使用）
    ml_pred = state.get("ml_prediction", {})
    if ml_pred:
        parts.append("**ML性能预测结果：**")
        if 'hardness' in ml_pred:
            parts.append(f"  - 硬度: {ml_pred['hardness']} GPa")
        if 'elastic_modulus' in ml_pred:
            parts.append(f"  - 弹性模量: {ml_pred['elastic_modulus']} GPa")
        if 'adhesion_strength' in ml_pred:
            parts.append(f"  - 结合力: {ml_pred['adhesion_strength']} N")
        if 'wear_rate' in ml_pred:
            parts.append(f"  - 磨损率: {ml_pred['wear_rate']}")
        if 'confidence' in ml_pred:
            parts.append(f"  - 置信度: {ml_pred['confidence']}")
    
    # TopPhi模拟结果
    topphi = state.get("topphi_simulation", {})
    if topphi:
        parts.append("**TopPhi模拟结果：**")
        if 'phase' in topphi:
            parts.append(f"  - 相结构: {topphi['phase']}")
        if 'lattice_constant' in topphi:
            parts.append(f"  - 晶格常数: {topphi['lattice_constant']}")
    
    # 历史对比
    hist = state.get("historical_comparison", {})
    if hist and hist.get("similar_cases"):
        parts.append(f"**历史案例对比：** 找到 {len(hist['similar_cases'])} 个相似案例")
    
    # 优化建议
    if state.get("comprehensive_recommendation"):
        parts.append("**优化建议：** ✅ 已生成")
    
    return "\n".join(parts) if parts else "暂无数据"


# ==================== 废弃函数（保留兼容性） ====================
# 注意：此函数已被 middleware/context_middleware.py 中的 CoatingContextMiddleware 替代
# 保留仅用于向后兼容，新代码应使用中间件

def _build_expert_context(state: CoatingState, expert_name: str) -> str:
    """
    [已废弃] 为专家构建上下文 - 请使用 CoatingContextMiddleware 替代
    
    此函数保留仅用于向后兼容。新代码应使用：
    
        from .middleware import CoatingContextMiddleware
        
        middleware = [CoatingContextMiddleware(expert_name="Validator")]
    
    中间件方式的优势：
    - 声明式上下文管理
    - 自动注入到系统消息
    - 与对话摘要等其他中间件协同工作
    """
    import warnings
    warnings.warn(
        "_build_expert_context 已废弃，请使用 CoatingContextMiddleware 中间件",
        DeprecationWarning,
        stacklevel=2
    )
    
    # 简化的兼容实现
    comp = state.get("coating_composition", {})
    proc = state.get("process_params", {})
    
    if not comp and not proc:
        return ""
    
    parts = [f"【{expert_name} 上下文】"]
    
    if comp:
        al = comp.get('al_content', 0) or 0
        ti = comp.get('ti_content', 0) or 0
        n = comp.get('n_content', 0) or 0
        parts.append(f"成分: Al {al:.1f}%, Ti {ti:.1f}%, N {n:.1f}%")
    
    if proc:
        temp = proc.get('deposition_temperature', 0)
        parts.append(f"工艺: {temp}°C")
    
    return "\n".join(parts)


# ==================== 对话式管理器（简化版，依赖 Checkpointer） ====================

class ConversationalGraphManager:
    """
    对话式图管理器 (v2.1 简化版)
    
    核心特点：
    - 每条用户消息触发一次图执行
    - 依赖 Checkpointer 自动管理会话状态
    - 无需手动维护会话字典
    """
    
    def __init__(self, use_memory: bool = True):
        """
        初始化管理器
        
        Args:
            use_memory: 是否启用持久化（默认 True）
        """
        self.graph = create_conversational_graph(use_memory=use_memory)
        self.use_memory = use_memory
        logger.info("[Manager] 对话式管理器初始化完成（依赖 Checkpointer 自动管理会话）")
    
    async def chat(
        self,
        session_id: str,
        user_message: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        处理用户消息并流式返回响应
        
        Checkpointer 自动管理会话状态，无需手动维护。
        
        Args:
            session_id: 会话ID（作为 thread_id 传递给 Checkpointer）
            user_message: 用户消息
            context_data: 额外的上下文数据（如涂层参数）
        
        Yields:
            事件流（token、工具调用、完成等）
        """
        # 配置 thread_id，Checkpointer 会自动根据此 ID 恢复/保存状态
        config = {"configurable": {"thread_id": session_id}}
        
        # 先获取历史状态（如果存在）
        existing_state = self.graph.get_state(config)
        existing_values = existing_state.values if existing_state else {}
        
        # 构建输入状态 - 只包含新消息，其他参数通过合并历史状态获取
        input_state = {
            "messages": [HumanMessage(content=user_message)],
            "remaining_steps": 25,
        }
        
        # 合并参数逻辑：优先使用新传入的参数，否则保留历史状态中的参数
        # 这样确保参数不会因为后续消息没有带 context 而丢失
        if context_data and context_data.get("coating_composition"):
            input_state["coating_composition"] = context_data["coating_composition"]
        elif existing_values.get("coating_composition"):
            input_state["coating_composition"] = existing_values["coating_composition"]
            
        if context_data and context_data.get("process_params"):
            input_state["process_params"] = context_data["process_params"]
        elif existing_values.get("process_params"):
            input_state["process_params"] = existing_values["process_params"]
            
        if context_data and context_data.get("structure_design"):
            input_state["structure_design"] = context_data["structure_design"]
        elif existing_values.get("structure_design"):
            input_state["structure_design"] = existing_values["structure_design"]
            
        if context_data and context_data.get("target_requirements"):
            input_state["target_requirements"] = context_data["target_requirements"]
        elif existing_values.get("target_requirements"):
            input_state["target_requirements"] = existing_values["target_requirements"]
        
        # 保留历史状态中的工具结果（ml_prediction, historical_comparison 等）
        for key in ["ml_prediction", "historical_comparison", "topphi_simulation", "performance_prediction"]:
            if existing_values.get(key):
                input_state[key] = existing_values[key]
        
        logger.info(f"[Manager] 会话参数: comp={input_state.get('coating_composition')}, proc={input_state.get('process_params')}, target={input_state.get('target_requirements')}")
        
        # 用于收集完整输出内容（用于内容提取）
        collected_content = []
        current_agent = None
        
        # 当前节点名（用于判断是否显示思考内容）
        current_node = None
        
        # 流式执行（使用 input_state，Checkpointer 自动合并历史状态）
        try:
            async for event in self.graph.astream_events(input_state, config=config, version="v2"):
                event_type = event.get("event")
                
                # 节点开始/结束（不发送 router 的事件，避免显示空消息）
                if event_type == "on_chain_start":
                    node_name = event.get("name", "")
                    if node_name in ["router", "assistant", "validator", "analyst", "optimizer", "experimenter"]:
                        current_node = node_name  # 记录当前节点
                        # router 不发送 node_start，避免前端显示空消息
                        if node_name != "router":
                            yield {"type": "node_start", "node": node_name}
                        # 记录当前 Agent（用于内容提取）
                        if node_name in ["optimizer", "experimenter"]:
                            current_agent = node_name.capitalize()
                            collected_content = []  # 重置收集
                
                elif event_type == "on_chain_end":
                    node_name = event.get("name", "")
                    if node_name in ["assistant", "validator", "analyst", "optimizer", "experimenter"]:
                        yield {"type": "node_end", "node": node_name}
                
                # LLM 流式输出
                elif event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk:
                        # 获取 message（兼容 ChatGenerationChunk 和 AIMessageChunk）
                        msg = getattr(chunk, "message", chunk)
                        
                        # 只在 assistant 节点显示思考内容（不包括 router）
                        if current_node == "assistant":
                            additional_kwargs = getattr(msg, "additional_kwargs", {})
                            reasoning = additional_kwargs.get("reasoning_content")
                            if reasoning:
                                yield {"type": "thinking_token", "content": reasoning}
                        
                        # 处理正文内容
                        content = getattr(msg, "content", "") or ""
                        if content:
                            # 过滤掉单独的 agent 名称 token（LLM 有时会输出这些无意义的标识）
                            content_lower = content.strip().lower()
                            if content_lower in ["validator", "analyst", "experimenter", "assistant", "supervisor", "router"]:
                                continue
                            yield {"type": "token", "content": content}
                            # 收集内容用于结构化提取
                            if current_agent:
                                collected_content.append(content)
                
                # 工具调用
                elif event_type == "on_tool_start":
                    tool_name = event.get("name", "")
                    logger.info(f"[Manager] 工具开始: {tool_name}")
                    yield {"type": "tool_start", "tool": tool_name}
                
                elif event_type == "on_tool_end":
                    tool_name = event.get("name", "")
                    tool_output = event.get("data", {}).get("output")
                    logger.info(f"[Manager] 工具完成: {tool_name}, 结果类型: {type(tool_output).__name__}")
                    
                    # 发送工具结束事件
                    yield {"type": "tool_end", "tool": tool_name}
                    
                    # 提取工具结果
                    result_data = None
                    if tool_output is not None:
                        if isinstance(tool_output, dict):
                            result_data = tool_output
                        elif hasattr(tool_output, 'content'):
                            # ToolMessage
                            content = tool_output.content
                            if isinstance(content, str):
                                try:
                                    result_data = json.loads(content)
                                except json.JSONDecodeError:
                                    result_data = {"message": content}
                            else:
                                result_data = content
                    
                    # 根据工具名称缓存结果到 input_state（供后续工具使用）
                    # 这是最简单稳定的方案：在前端缓存数据
                    if result_data and not result_data.get("error"):
                        if "predict_ml" in tool_name:
                            input_state["ml_prediction"] = result_data
                            logger.debug(f"[Manager] 缓存 ML 预测结果到状态")
                        elif "compare_historical" in tool_name:
                            input_state["historical_comparison"] = result_data
                            logger.debug(f"[Manager] 缓存历史对比结果到状态")
                    
                    # 发送工具结果（用于前端展示）
                    if result_data:
                        logger.debug(f"[Manager] 工具结果: {tool_name} -> {list(result_data.keys()) if isinstance(result_data, dict) else type(result_data)}")
                        yield {
                            "type": "tool_result",
                            "tool": tool_name,
                            "result": result_data
                        }
            
            # Checkpointer 已自动保存状态，无需手动更新
            # 可以通过 get_state 获取最新状态用于日志或调试
            final_state = self.graph.get_state(config)
            if final_state and final_state.values:
                logger.debug(f"[Manager] 最终状态已由 Checkpointer 保存")
            
            # 提取结构化内容（优化方案摘要、工单信息等）
            if current_agent and collected_content:
                full_content = "".join(collected_content)
                structured_data = extract_structured_content(full_content, current_agent)
                if structured_data:
                    logger.info(f"[Manager] 提取到结构化内容: {structured_data.get('type')}")
                    yield {"type": "structured_content", "data": structured_data}
            
            yield {"type": "done"}
            
        except Exception as e:
            logger.error(f"[Manager] 执行失败: {e}")
            yield {"type": "error", "message": str(e)}
    
    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """
        获取或创建会话状态（兼容旧 API）
        
        由于使用 Checkpointer 自动管理，此方法主要用于：
        - 获取已有会话的状态
        - 为新会话返回初始状态结构
        
        Args:
            session_id: 会话 ID
        
        Returns:
            会话状态字典（可变，用于设置参数）
        """
        # 先尝试从 Checkpointer 获取
        state = self.get_session_state(session_id)
        
        # 如果没有状态，返回初始结构
        if not state:
            state = {
                "messages": [],
                "coating_composition": {},
                "process_params": {},
                "structure_design": {},
                "target_requirements": {},
            }
        
        # 存储到临时缓存，以便 chat() 时使用
        if not hasattr(self, '_pending_params'):
            self._pending_params = {}
        self._pending_params[session_id] = state
        
        return state
    
    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话状态
        
        从 Checkpointer 获取持久化的状态
        
        Args:
            session_id: 会话 ID
        
        Returns:
            会话状态字典
        """
        try:
            # 先检查临时缓存
            if hasattr(self, '_pending_params') and session_id in self._pending_params:
                return self._pending_params[session_id]
            
            config = {"configurable": {"thread_id": session_id}}
            state = self.graph.get_state(config)
            if state and state.values:
                return dict(state.values)
            return {}
        except Exception as e:
            logger.warning(f"[Manager] 获取会话状态失败: {e}")
            return {}
    
    def clear_session(self, session_id: str):
        """
        清除会话
        
        注意：当前使用 InMemorySaver，清除会话需要重新创建图
        生产环境建议使用支持删除的持久化存储（如 PostgresSaver）
        
        Args:
            session_id: 会话 ID
        """
        logger.info(f"[Manager] 清除会话请求: {session_id}")
        
        # 清理缓存的参数
        if hasattr(self, '_pending_params') and session_id in self._pending_params:
            del self._pending_params[session_id]
            logger.info(f"[Manager] 已清除会话缓存参数: {session_id}")
        
        logger.warning("[Manager] InMemorySaver 不支持单独清除会话历史，建议生产环境使用 PostgresSaver")


# ==================== 单例 ====================

_conversational_manager: Optional[ConversationalGraphManager] = None

def get_conversational_manager() -> ConversationalGraphManager:
    """获取对话式管理器单例"""
    global _conversational_manager
    if _conversational_manager is None:
        _conversational_manager = ConversationalGraphManager(use_memory=True)
    return _conversational_manager
