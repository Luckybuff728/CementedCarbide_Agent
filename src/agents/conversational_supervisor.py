"""
Conversational Supervisor Agent - 对话式总控Agent

核心理念：
1. Supervisor是一个对话式Agent，自然地与用户交流
2. 理解用户意图，主动引导用户
3. 通过Tool Calling调度专业的Worker Agent
4. 每个Worker Agent专注于自己的任务

与之前的区别：
- 之前：靠复杂提示词输出JSON决策 → 代码解析 → 调用Agent
- 现在：LLM原生Tool Calling → 自然对话回复
"""

from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
import logging
import json

from ..llm import get_llm_service

logger = logging.getLogger(__name__)


# ==================== Agent调度工具定义 ====================
# 这些工具让Supervisor可以调用其他Agent

class CallValidatorSchema(BaseModel):
    """调用验证Agent的参数"""
    coating_composition: Dict[str, Any] = Field(..., description="涂层成分配比，如 {al_content: 60, ti_content: 40, n_content: 50}")
    process_params: Dict[str, Any] = Field(..., description="工艺参数，如 {process_type: 'PVD', deposition_temperature: 450}")
    structure_design: Dict[str, Any] = Field(default_factory=dict, description="结构设计，如 {structure_type: '单层'}")
    target_requirements: str = Field(default="", description="用户的目标需求描述")


class CallAnalystSchema(BaseModel):
    """调用分析Agent的参数"""
    task_type: str = Field(
        default="full_analysis",
        description="分析类型：'full_analysis'(完整分析) / 'topphi_only'(仅TopPhi模拟) / 'ml_only'(仅ML预测) / 'historical_only'(仅历史对比)"
    )


class CallOptimizerSchema(BaseModel):
    """调用优化Agent的参数"""
    optimization_types: List[str] = Field(
        default=["P1", "P2", "P3"],
        description="需要生成的优化类型：P1(成分优化)、P2(结构优化)、P3(工艺优化)"
    )


class CallExperimenterSchema(BaseModel):
    """调用实验Agent的参数"""
    action: str = Field(
        ..., 
        description="动作类型：'generate_workorder'(生成实验工单) / 'analyze_results'(分析实验结果)"
    )
    selected_optimization: Optional[str] = Field(
        default=None, 
        description="用户选择的优化方案：P1/P2/P3（生成工单时必填）"
    )
    experiment_results: Optional[Dict[str, Any]] = Field(
        default=None,
        description="实验结果数据（分析结果时必填）"
    )


# ==================== 对话式Supervisor类 ====================

class ConversationalSupervisor:
    """
    对话式Supervisor Agent
    
    职责：
    1. 与用户自然对话，理解需求
    2. 主动引导用户，建议下一步操作
    3. 调度专业Worker Agent执行具体任务
    4. 将执行结果转化为自然语言回复用户
    """
    
    # Supervisor的系统提示词 - 简洁明确，聚焦对话而非流程控制
    SYSTEM_PROMPT = """你是 TopMat 涂层优化系统的AI助手。

**你的角色：**
- 与用户自然对话，理解他们的涂层优化需求
- 主动引导用户，建议下一步可以做什么
- 调用专业工具完成具体任务

**你可以调用的工具：**
1. `call_validator` - 验证涂层参数是否合理
2. `call_analyst` - 执行性能分析（TopPhi模拟、ML预测、历史对比、根因分析）
3. `call_optimizer` - 生成优化方案（P1成分/P2结构/P3工艺）
4. `call_experimenter` - 生成实验工单或分析实验结果

**对话原则：**
1. 用户说什么就理解什么，不要假设固定流程
2. 每次执行完任务，用自然语言总结结果，并建议下一步
3. 如果用户意图不明确，主动询问澄清
4. 如果缺少必要参数，友好地询问用户

**示例对话：**
- 用户："帮我分析一下这个配方" → 调用 call_analyst
- 用户："我想优化成分" → 调用 call_optimizer(optimization_types=["P1"])
- 用户："这个参数合理吗" → 调用 call_validator
- 用户："生成实验工单" → 调用 call_experimenter(action="generate_workorder")
- 用户："接下来该做什么" → 根据当前状态给出建议

**当前会话状态：**
{context_summary}
"""

    def __init__(self):
        """初始化对话式Supervisor"""
        self.llm_service = get_llm_service()
        self.llm = self.llm_service.llm
        
        # 会话状态（存储中间结果）
        self.session_state: Dict[str, Any] = {}
        
        # 创建Agent工具
        self.tools = self._create_agent_tools()
        
        # 创建ReAct Agent
        self.agent = self._create_agent()
        
        logger.info("[ConversationalSupervisor] 初始化完成")
    
    def _create_agent_tools(self) -> List:
        """创建Agent调度工具"""
        
        @tool(args_schema=CallValidatorSchema)
        def call_validator(
            coating_composition: Dict[str, Any],
            process_params: Dict[str, Any],
            structure_design: Dict[str, Any] = None,
            target_requirements: str = ""
        ) -> str:
            """
            调用验证Agent，检查涂层参数是否合理有效。
            返回验证结果和建议。
            """
            from .validator_agent import validator_agent_node
            
            # 保存到会话状态
            self.session_state["coating_composition"] = coating_composition
            self.session_state["process_params"] = process_params
            self.session_state["structure_design"] = structure_design or {}
            self.session_state["target_requirements"] = target_requirements
            
            # 构建状态并调用
            state = {
                "task_id": "conversational",
                "coating_composition": coating_composition,
                "process_params": process_params,
                "structure_design": structure_design or {},
                "target_requirements": target_requirements,
                "messages": []
            }
            
            result = validator_agent_node(state)
            
            # 保存结果
            self.session_state["validation_result"] = result.get("validation_result")
            self.session_state["validation_passed"] = result.get("validation_passed", False)
            
            # 返回自然语言描述
            if result.get("validation_passed"):
                return f"✅ 参数验证通过！涂层成分和工艺参数都在合理范围内。"
            else:
                errors = result.get("validation_result", {}).get("validation_errors", ["验证失败"])
                return f"❌ 参数验证失败：{', '.join(errors)}"
        
        @tool(args_schema=CallAnalystSchema)
        def call_analyst(task_type: str = "full_analysis") -> str:
            """
            调用分析Agent，执行性能预测和分析。
            
            可选分析类型：
            - full_analysis: 完整分析（TopPhi + ML + 历史对比 + 根因分析）
            - topphi_only: 仅TopPhi第一性原理模拟
            - ml_only: 仅机器学习预测
            - historical_only: 仅历史数据对比
            """
            from .analyst_agent import analyst_agent_node
            
            # 检查前置条件
            if not self.session_state.get("coating_composition"):
                return "⚠️ 请先提供涂层参数，我才能进行分析。需要的参数包括：涂层成分(Al、Ti、N含量)和工艺参数(工艺类型、温度等)。"
            
            # 构建状态
            state = {
                "task_id": "conversational",
                "coating_composition": self.session_state.get("coating_composition", {}),
                "process_params": self.session_state.get("process_params", {}),
                "structure_design": self.session_state.get("structure_design", {}),
                "target_requirements": self.session_state.get("target_requirements", ""),
                "messages": []
            }
            
            result = analyst_agent_node(state)
            
            # 保存结果
            self.session_state["topphi_simulation"] = result.get("topphi_simulation")
            self.session_state["ml_prediction"] = result.get("ml_prediction")
            self.session_state["performance_prediction"] = result.get("performance_prediction")
            self.session_state["historical_comparison"] = result.get("historical_comparison")
            self.session_state["integrated_analysis"] = result.get("integrated_analysis")
            self.session_state["analysis_completed"] = True
            
            # 生成自然语言总结
            perf = result.get("performance_prediction", {})
            topphi = result.get("topphi_simulation", {})
            analysis = result.get("integrated_analysis", {})
            
            summary = "📊 **性能分析完成**\n\n"
            summary += f"**微观结构预测（TopPhi）：**\n"
            summary += f"- 晶粒尺寸：{topphi.get('grain_size_nm', 'N/A')} nm\n"
            summary += f"- 择优取向：{topphi.get('preferred_orientation', 'N/A')}\n\n"
            summary += f"**性能预测（ML）：**\n"
            summary += f"- 硬度：{perf.get('hardness', 'N/A')} GPa\n"
            summary += f"- 弹性模量：{perf.get('elastic_modulus', 'N/A')} GPa\n"
            summary += f"- 结合力：{perf.get('adhesion_strength', 'N/A')} N\n\n"
            
            if analysis.get("summary"):
                summary += f"**分析总结：**\n{analysis.get('summary')}"
            
            return summary
        
        @tool(args_schema=CallOptimizerSchema)
        def call_optimizer(optimization_types: List[str] = None) -> str:
            """
            调用优化Agent，生成优化方案。
            
            优化类型：
            - P1: 成分优化（调整Al、Ti、N等元素配比）
            - P2: 结构优化（单层/多层/梯度设计）
            - P3: 工艺优化（温度、偏压、气体流量等）
            """
            from .optimizer_agent import optimizer_agent_node
            
            # 检查前置条件
            if not self.session_state.get("integrated_analysis"):
                return "⚠️ 请先进行性能分析，我才能生成有针对性的优化方案。要我先帮你分析吗？"
            
            optimization_types = optimization_types or ["P1", "P2", "P3"]
            
            # 构建状态
            state = {
                "task_id": "conversational",
                "coating_composition": self.session_state.get("coating_composition", {}),
                "process_params": self.session_state.get("process_params", {}),
                "structure_design": self.session_state.get("structure_design", {}),
                "target_requirements": self.session_state.get("target_requirements", ""),
                "integrated_analysis": self.session_state.get("integrated_analysis", {}),
                "performance_prediction": self.session_state.get("performance_prediction", {}),
                "messages": []
            }
            
            result = optimizer_agent_node(state)
            
            # 保存结果
            self.session_state["p1_content"] = result.get("p1_content")
            self.session_state["p2_content"] = result.get("p2_content")
            self.session_state["p3_content"] = result.get("p3_content")
            self.session_state["comprehensive_recommendation"] = result.get("comprehensive_recommendation")
            self.session_state["optimization_completed"] = True
            
            # 生成自然语言总结
            summary = "🎯 **优化方案已生成**\n\n"
            
            if "P1" in optimization_types and result.get("p1_content"):
                summary += "**P1 成分优化：** 已生成\n"
            if "P2" in optimization_types and result.get("p2_content"):
                summary += "**P2 结构优化：** 已生成\n"
            if "P3" in optimization_types and result.get("p3_content"):
                summary += "**P3 工艺优化：** 已生成\n"
            
            if result.get("comprehensive_recommendation"):
                summary += f"\n**综合建议：**\n{result.get('comprehensive_recommendation')}"
            
            summary += "\n\n你可以问我任何一个方案的详细内容，或者选择一个方案生成实验工单。"
            
            return summary
        
        @tool(args_schema=CallExperimenterSchema)
        def call_experimenter(
            action: str,
            selected_optimization: str = None,
            experiment_results: Dict[str, Any] = None
        ) -> str:
            """
            调用实验Agent，生成实验工单或分析实验结果。
            
            动作类型：
            - generate_workorder: 根据选择的优化方案生成详细实验工单
            - analyze_results: 分析用户提交的实验结果，对比预测值
            """
            if action == "generate_workorder":
                if not selected_optimization:
                    return "⚠️ 请告诉我你选择哪个优化方案（P1/P2/P3）？"
                
                content_key = f"{selected_optimization.lower()}_content"
                optimization_content = self.session_state.get(content_key)
                
                if not optimization_content:
                    return f"⚠️ 还没有生成{selected_optimization}优化方案，要我先帮你生成吗？"
                
                from .tools import generate_workorder_tool
                
                result = generate_workorder_tool.invoke({
                    "selected_optimization": selected_optimization,
                    "optimization_content": optimization_content,
                    "coating_composition": self.session_state.get("coating_composition", {}),
                    "process_params": self.session_state.get("process_params", {}),
                    "structure_design": self.session_state.get("structure_design", {}),
                    "target_requirements": self.session_state.get("target_requirements", "")
                })
                
                if result.get("error"):
                    return f"❌ 工单生成失败：{result['error']}"
                
                self.session_state["experiment_workorder"] = result
                self.session_state["selected_optimization"] = selected_optimization
                
                return f"📋 **{selected_optimization}实验工单已生成**\n\n实验完成后，你可以告诉我实验结果，我来帮你分析对比。"
            
            elif action == "analyze_results":
                if not experiment_results:
                    return "⚠️ 请提供实验结果数据，包括：硬度(GPa)、弹性模量(GPa)、磨损率、结合力(N)等。"
                
                from ..services.experiment_analysis_service import get_experiment_analysis_service
                
                analysis_service = get_experiment_analysis_service()
                prediction_data = self.session_state.get("performance_prediction", {})
                
                result = analysis_service.analyze_experiment_results(
                    experiment_data=experiment_results,
                    prediction_data=prediction_data,
                    target_requirements=self.session_state.get("target_requirements", {}),
                    historical_best=None
                )
                
                self.session_state["experiment_results"] = experiment_results
                self.session_state["experiment_analysis"] = result
                
                is_met = result.get("is_target_met", False)
                
                if is_met:
                    return f"🎉 **实验结果达标！**\n\n{result.get('analysis_report', '')}\n\n恭喜！优化目标已达成。"
                else:
                    unmet = result.get("unmet_metrics", [])
                    return f"📊 **实验结果分析**\n\n未达标指标：{', '.join(unmet)}\n\n{result.get('analysis_report', '')}\n\n要我帮你生成新的优化方案继续迭代吗？"
            
            return "⚠️ 未知的操作类型，请使用 'generate_workorder' 或 'analyze_results'"
        
        return [call_validator, call_analyst, call_optimizer, call_experimenter]
    
    def _create_agent(self):
        """创建ReAct Agent"""
        # 使用LangGraph的create_react_agent
        checkpointer = MemorySaver()
        
        agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            checkpointer=checkpointer
        )
        
        return agent
    
    def _get_context_summary(self) -> str:
        """生成当前会话状态摘要"""
        summary_parts = []
        
        # 参数状态
        if self.session_state.get("coating_composition"):
            comp = self.session_state["coating_composition"]
            summary_parts.append(f"- 涂层成分：Al {comp.get('al_content', 0)}%, Ti {comp.get('ti_content', 0)}%, N {comp.get('n_content', 0)}%")
        
        if self.session_state.get("process_params"):
            proc = self.session_state["process_params"]
            summary_parts.append(f"- 工艺参数：{proc.get('process_type', 'N/A')}, {proc.get('deposition_temperature', 0)}°C")
        
        # 完成的步骤
        completed = []
        if self.session_state.get("validation_passed"):
            completed.append("参数验证✓")
        if self.session_state.get("analysis_completed"):
            completed.append("性能分析✓")
        if self.session_state.get("optimization_completed"):
            completed.append("优化方案✓")
        if self.session_state.get("experiment_workorder"):
            completed.append("实验工单✓")
        
        if completed:
            summary_parts.append(f"- 已完成：{', '.join(completed)}")
        
        if not summary_parts:
            return "用户刚开始对话，尚未提供任何参数。"
        
        return "\n".join(summary_parts)
    
    async def chat(self, user_message: str, thread_id: str = "default") -> str:
        """
        处理用户消息，返回回复
        
        Args:
            user_message: 用户输入
            thread_id: 会话ID，用于保持对话历史
            
        Returns:
            AI回复
        """
        logger.info(f"[ConversationalSupervisor] 收到消息: {user_message[:50]}...")
        
        # 构建带上下文的系统提示
        system_prompt = self.SYSTEM_PROMPT.format(
            context_summary=self._get_context_summary()
        )
        
        # 调用Agent
        config = {"configurable": {"thread_id": thread_id}}
        
        result = await self.agent.ainvoke(
            {
                "messages": [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_message)
                ]
            },
            config=config
        )
        
        # 提取最后的AI回复
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                return msg.content
        
        return "抱歉，我没有理解你的意思。你可以告诉我涂层参数，或者问我可以做什么。"
    
    def chat_sync(self, user_message: str, thread_id: str = "default") -> str:
        """同步版本的chat方法"""
        import asyncio
        return asyncio.run(self.chat(user_message, thread_id))
    
    def reset_session(self):
        """重置会话状态"""
        self.session_state = {}
        logger.info("[ConversationalSupervisor] 会话状态已重置")
    
    def get_session_state(self) -> Dict[str, Any]:
        """获取当前会话状态"""
        return self.session_state.copy()
    
    def set_session_state(self, state: Dict[str, Any]):
        """设置会话状态（用于恢复会话）"""
        self.session_state = state.copy()


# ==================== 便捷函数 ====================

_supervisor_instance: Optional[ConversationalSupervisor] = None


def get_conversational_supervisor() -> ConversationalSupervisor:
    """获取对话式Supervisor单例"""
    global _supervisor_instance
    if _supervisor_instance is None:
        _supervisor_instance = ConversationalSupervisor()
    return _supervisor_instance
