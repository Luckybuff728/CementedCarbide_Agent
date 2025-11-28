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
import logging
import json
from typing import Dict, Any, Optional, AsyncIterator, List, Literal
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from .state import CoatingState
from .content_extractor import extract_structured_content

logger = logging.getLogger(__name__)


# ==================== 系统提示词 ====================

ROUTER_SYSTEM_PROMPT = """你是 TopMat 涂层研发智能助手的路由器。

根据用户的消息内容，判断应该由哪个专家来处理。

## 路由规则（按优先级）

### 0. **assistant** - 解释性/对话性问题（最高优先级）
用户只是想了解、询问、解释已有结果时，必须返回 assistant：
- 问"为什么"、"怎么理解"、"什么意思"、"解释一下"
- 追问已有结果的原因，如"为什么硬度是28GPa"、"预测结果怎么来的"
- 一般问候、闲聊、询问系统功能
- 对已有分析结果的疑问
- **关键判断**：如果用户是在追问/理解已有内容，而不是请求新操作，选 assistant

### 1. **validator** - 参数验证专家
用户**新提供**参数并希望验证时：
- 用户提供了涂层成分（Al、Ti、N含量）
- 用户提供了工艺参数（温度、偏压、气压）
- 用户明确说"验证"、"检查"、"合理吗"
- 消息中包含【涂层成分】、【工艺参数】等标记
   
### 2. **analyst** - 性能预测专家
用户请求**调用工具获取数据**时：
- 用户说“预测性能”、“预测硬度”、“ML预测”
- 用户说“模拟”、“TopPhi”、“微观结构”
- 用户说“查找历史案例”、“对比历史”
- **关键词**：预测、模拟、历史案例（需要调用工具的操作）
   
### 3. **optimizer** - 优化建议专家
用户请求生成优化方案时：
- 用户说"帮我优化"、"如何提高"、"给出改善方案"
   
### 4. **experimenter** - 实验方案专家
涉及实验工单和实验数据时：
- 用户要生成实验工单
- 用户提交实验结果数据
- 用户说"生成工单"、"实验数据"、"开始迭代"

## 输出格式
请只返回一个词：validator / analyst / optimizer / experimenter / assistant

## 重要提示（请仔细区分）

| 用户说... | 真实意图 | 路由到 |
|-----------|---------|--------|
| “预测性能”、“预测硬度” | 调用ML工具 | analyst |
| “分析一下”、“分析结果” | 解释已有数据 | assistant |
| “为什么硬度是28GPa” | 解释已有预测 | assistant |
| “帮我做个全面分析” | 调用多个工具 | analyst |
| “这个结果怎么理解” | 解释已有数据 | assistant |

**核心区分**：预测=调用工具，分析/解释=解读已有数据
"""

ASSISTANT_SYSTEM_PROMPT = """你是 TopMat 涂层研发智能助手，专注于硬质合金涂层（如 AlTiN）的研发优化。

## 你的核心职责
1. **回答解释性问题**：用户追问"为什么预测是XX"、"怎么理解这个结果"时，基于对话历史和专业知识给出解释
2. **引导对话**：帮助用户理解系统功能，引导他们进行参数验证、性能预测、优化等操作
3. **总结和澄清**：总结已完成的分析结果，澄清用户的疑问

## 回答解释性问题的要点
当用户问"为什么硬度预测是28GPa"这类问题时：
- 从对话历史中找到相关的预测结果
- 解释影响该指标的主要因素（成分、工艺、结构等）
- 结合用户当前的参数配置进行具体分析
- 如果是ML预测，说明这是基于历史数据的统计模型

## 专业知识参考
- AlTiN 涂层硬度主要受 Al/Ti 比例、N 含量、沉积温度影响
- 较高的 Al 含量（50-67%）通常有利于高温硬度
- 沉积温度 400-500°C 有利于形成立方相结构
- 偏压 -80~-150V 影响膜层致密度和内应力
- 结合力受界面过渡层、表面清洁度、基材匹配度影响

## 交互风格
- 直接回答用户问题，不要重复调用工具
- 给出解释时引用具体数据

## 当前状态
{context}

请根据对话历史直接回答用户的问题。如果用户需要新的分析操作，建议他们明确请求。
"""


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
    def router_node(state: CoatingState) -> dict:
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
            response = llm.invoke(router_messages)
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
    def assistant_node(state: CoatingState) -> dict:
        """通用对话助手 - 使用思考模式 LLM"""
        messages = state.get("messages", [])
        context = _build_state_summary(state)
        
        system_prompt = ASSISTANT_SYSTEM_PROMPT.format(context=context)
        
        chat_messages = [SystemMessage(content=system_prompt)] + list(messages)
        
        try:
            # 使用思考模式 LLM
            response = thinking_llm.invoke(chat_messages)
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
        
        def expert_node_func(state: CoatingState) -> dict:
            logger.info(f"[{expert_name}] 开始处理")
            try:
                # 直接传递状态，中间件自动处理上下文注入
                result = expert_agent.invoke(dict(state))
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
    from .tools import VALIDATOR_TOOLS, ANALYST_TOOLS, OPTIMIZER_TOOLS, EXPERIMENTER_TOOLS
    from .prompts.validator import VALIDATOR_SYSTEM_PROMPT
    from .prompts.analyst import ANALYST_SYSTEM_PROMPT
    from .prompts.optimizer import OPTIMIZER_SYSTEM_PROMPT
    from .prompts.experimenter import EXPERIMENTER_SYSTEM_PROMPT
    
    # ==================== 创建图 ====================
    workflow = StateGraph(CoatingState)
    
    # 添加节点
    workflow.add_node("router", router_node)
    workflow.add_node("assistant", assistant_node)
    workflow.add_node("validator", create_expert_node("Validator", VALIDATOR_SYSTEM_PROMPT, VALIDATOR_TOOLS))
    workflow.add_node("analyst", create_expert_node("Analyst", ANALYST_SYSTEM_PROMPT, ANALYST_TOOLS))
    workflow.add_node("optimizer", create_expert_node("Optimizer", OPTIMIZER_SYSTEM_PROMPT, OPTIMIZER_TOOLS))
    workflow.add_node("experimenter", create_expert_node("Experimenter", EXPERIMENTER_SYSTEM_PROMPT, EXPERIMENTER_TOOLS))
    
    # 设置入口
    workflow.set_entry_point("router")
    
    # 路由条件边
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
    
    # 所有专家节点完成后结束（等待下一条用户消息）
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
        
        # 构建输入状态
        input_state = {
            "messages": [HumanMessage(content=user_message)],
            "remaining_steps": 25,
        }
        
        # 优先使用临时缓存的参数（来自 get_or_create_session / set_parameters）
        pending = getattr(self, '_pending_params', {}).get(session_id, {})
        if pending:
            if pending.get("coating_composition"):
                input_state["coating_composition"] = pending["coating_composition"]
            if pending.get("process_params"):
                input_state["process_params"] = pending["process_params"]
            if pending.get("structure_design"):
                input_state["structure_design"] = pending["structure_design"]
            if pending.get("target_requirements"):
                input_state["target_requirements"] = pending["target_requirements"]
        
        # 如果有额外的 context_data，覆盖
        if context_data:
            if context_data.get("coating_composition"):
                input_state["coating_composition"] = context_data["coating_composition"]
            if context_data.get("process_params"):
                input_state["process_params"] = context_data["process_params"]
            if context_data.get("structure_design"):
                input_state["structure_design"] = context_data["structure_design"]
            if context_data.get("target_requirements"):
                input_state["target_requirements"] = context_data["target_requirements"]
        
        logger.info(f"[Manager] 会话参数: comp={input_state.get('coating_composition')}, proc={input_state.get('process_params')}")
        
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
                            if content_lower in ["validator", "analyst", "optimizer", "experimenter", "assistant", "supervisor", "router"]:
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
                    logger.info(f"[Manager] 工具完成: {tool_name}, 结果类型: {type(tool_output)}")
                    
                    # 发送工具结束事件
                    yield {"type": "tool_end", "tool": tool_name}
                    
                    # 提取工具结果（处理 ToolMessage 对象）
                    result_data = None
                    if tool_output is not None:
                        # 如果是 ToolMessage，提取 content
                        if hasattr(tool_output, 'content'):
                            content = tool_output.content
                            # 尝试解析 JSON 字符串
                            if isinstance(content, str):
                                try:
                                    result_data = json.loads(content)
                                except json.JSONDecodeError:
                                    result_data = {"message": content}
                            else:
                                result_data = content
                        # 如果是字典，直接使用
                        elif isinstance(tool_output, dict):
                            result_data = tool_output
                    
                    # 发送工具结果（用于前端展示）
                    if result_data:
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
        logger.warning("[Manager] InMemorySaver 不支持单独清除会话，建议生产环境使用 PostgresSaver")


# ==================== 单例 ====================

_conversational_manager: Optional[ConversationalGraphManager] = None

def get_conversational_manager() -> ConversationalGraphManager:
    """获取对话式管理器单例"""
    global _conversational_manager
    if _conversational_manager is None:
        _conversational_manager = ConversationalGraphManager(use_memory=True)
    return _conversational_manager
