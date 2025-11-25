"""
多Agent Graph - 基于 Supervisor-Workers 模式
支持LLM驱动的动态路由和多轮对话
"""
from typing import Literal, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langchain_core.messages import HumanMessage, AIMessage
import logging

from .agent_state import CoatingAgentState
from ..agents.supervisor_agent import supervisor_node, create_supervisor_router
from ..agents.validator_agent import validator_agent_node
from ..agents.analyst_agent import analyst_agent_node
from ..agents.optimizer_agent import optimizer_agent_node
from ..agents.experimenter_agent import experimenter_agent_node

logger = logging.getLogger(__name__)


def ask_user_node(state: CoatingAgentState) -> dict:
    """
    ask_user 节点 - 处理Supervisor想要与用户对话的情况
    
    这个节点会暂停工作流，等待用户回复
    然后返回Supervisor继续决策
    """
    from langgraph.types import interrupt
    
    logger.info("[AskUser] 等待用户输入")
    
    # 从最后一条消息中提取Supervisor的问题
    messages = state.get("messages", [])
    last_message = messages[-1].content if messages else "有什么我可以帮助您的吗？"
    
    # 使用interrupt等待用户输入
    user_response = interrupt({
        "type": "ask_user",
        "question": last_message
    })
    
    logger.info(f"[AskUser] 收到用户回复: {user_response}")
    
    # 准备返回的状态更新
    result = {
        "current_agent": "user",
        "last_completed_agent": None  # 清除标记
    }
    
    # 将用户回复添加到消息历史
    if isinstance(user_response, str):
        result["messages"] = [HumanMessage(content=user_response)]
    elif isinstance(user_response, dict):
        # ✅ 关键修复：提取特殊字段并更新到状态
        if "message" in user_response:
            result["messages"] = [HumanMessage(content=user_response["message"])]
        
        # ✅ 如果包含优化方案选择，更新到状态
        if "selected_optimization_type" in user_response:
            result["selected_optimization_type"] = user_response["selected_optimization_type"]
            logger.info(f"[AskUser] 更新选择方案到状态: {user_response['selected_optimization_type']}")
        
        if "selected_optimization_name" in user_response:
            result["selected_optimization_name"] = user_response["selected_optimization_name"]
    else:
        result["messages"] = [HumanMessage(content=str(user_response))]
    
    return result


def create_multi_agent_graph(
    use_memory: bool = True
) -> StateGraph:
    """
    创建多Agent Graph
    
    架构：
    1. Supervisor - 总控节点，LLM驱动决策
    2. Validator - 参数验证Agent
    3. Analyst - 性能分析Agent
    4. Optimizer - 优化建议Agent
    5. Experimenter - 实验管理Agent
    6. AskUser - 用户对话节点
    
    流程：
    - 所有Agent执行完后都返回Supervisor
    - Supervisor决定下一步行动
    - 支持任意环节与用户对话
    - 支持迭代优化
    
    Args:
        use_memory: 是否使用持久化内存（支持断点续传）
        
    Returns:
        编译后的Graph
    """
    logger.info("开始创建多Agent Graph")
    
    # 创建Graph
    workflow = StateGraph(CoatingAgentState)
    
    # ==================== 添加所有节点 ====================
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("validator", validator_agent_node)
    workflow.add_node("analyst", analyst_agent_node)
    workflow.add_node("optimizer", optimizer_agent_node)
    workflow.add_node("experimenter", experimenter_agent_node)
    workflow.add_node("ask_user", ask_user_node)
    
    # ==================== 设置入口点 ====================
    # 总是从Supervisor开始
    workflow.set_entry_point("supervisor")
    
    # ==================== 设置路由 ====================
    # Supervisor的动态路由（基于LLM决策）
    workflow.add_conditional_edges(
        "supervisor",
        create_supervisor_router,  # 路由函数
        {
            "validator": "validator",
            "analyst": "analyst",
            "optimizer": "optimizer",
            "experimenter": "experimenter",
            "ask_user": "ask_user",
            "FINISH": END
        }
    )
    
    # 所有Worker Agent完成后返回Supervisor
    workflow.add_edge("validator", "supervisor")
    workflow.add_edge("analyst", "supervisor")
    workflow.add_edge("optimizer", "supervisor")
    workflow.add_edge("experimenter", "supervisor")
    workflow.add_edge("ask_user", "supervisor")  # 用户回复后返回Supervisor
    
    # ==================== 编译Graph ====================
    if use_memory:
        checkpointer = MemorySaver()
        memory = InMemoryStore()
        compiled = workflow.compile(checkpointer=checkpointer, store=memory)
    else:
        compiled = workflow.compile()
    
    logger.info("多Agent Graph 创建完成")
    
    return compiled


class MultiAgentManager:
    """
    多Agent管理器 - 负责任务的创建、执行、状态管理
    """
    
    def __init__(self, use_memory: bool = True):
        """初始化多Agent管理器"""
        self.graph = create_multi_agent_graph(use_memory=use_memory)
        self.active_tasks = {}
        logger.info(f"多Agent管理器初始化完成 (use_memory={use_memory})")
    
    async def start_task_stream_events(
        self,
        task_id: str,
        input_data: dict,
        thread_id: str = None
    ):
        """
        启动新任务（使用astream_events获取细粒度事件）
        
        Args:
            task_id: 任务ID
            input_data: 输入数据（涂层参数）
            thread_id: 线程ID（用于持久化）
        
        Yields:
            (event_type, event_data) 元组
        """
        logger.info(f"[MultiAgent] 启动任务 {task_id} (stream_events)")
        
        thread_id = thread_id or task_id
        
        # 构建初始状态
        composition = input_data.get("coating_composition") or input_data.get("composition", {})
        process_params = input_data.get("process_params", {})
        structure_design = input_data.get("structure_design", {})
        target_requirements = input_data.get("target_requirements", "")
        
        # 构建初始消息：包含完整的参数描述
        initial_message_parts = ["请帮我优化涂层配方。"]
        
        # 添加目标需求（支持字符串和字典格式）
        if target_requirements:
            if isinstance(target_requirements, dict):
                # 格式化字典为易读文本
                req_parts = []
                if "substrate" in target_requirements:
                    req_parts.append(f"基材：{target_requirements['substrate']}")
                if "bonding_strength" in target_requirements:
                    req_parts.append(f"结合力：{target_requirements['bonding_strength']} N")
                if "elastic_modulus" in target_requirements:
                    req_parts.append(f"弹性模量：{target_requirements['elastic_modulus']} GPa")
                if "working_temperature" in target_requirements:
                    req_parts.append(f"工作温度：{target_requirements['working_temperature']}°C")
                if "cutting_speed" in target_requirements:
                    req_parts.append(f"切削速度：{target_requirements['cutting_speed']} m/min")
                if "application_scenario" in target_requirements:
                    req_parts.append(f"应用场景：{target_requirements['application_scenario']}")
                if "special_requirements" in target_requirements and target_requirements['special_requirements']:
                    req_parts.append(f"特殊要求：{target_requirements['special_requirements']}")
                
                if req_parts:
                    initial_message_parts.append(f"\n**目标需求：**\n" + "，".join(req_parts))
            else:
                # 字符串格式直接使用
                initial_message_parts.append(f"\n**目标需求：**\n{target_requirements}")
        
        # 添加涂层参数摘要
        if composition and any(composition.values()):
            al = composition.get("al_content", 0)
            ti = composition.get("ti_content", 0)
            n = composition.get("n_content", 0)
            initial_message_parts.append(f"\n**涂层成分：** Al {al}%, Ti {ti}%, N {n}%")
        
        if process_params:
            process_type = process_params.get("process_type", "")
            temp = process_params.get("deposition_temperature", 0)
            if process_type:
                initial_message_parts.append(f"\n**工艺参数：** {process_type}工艺, 沉积温度{temp}°C")
        
        if structure_design:
            struct_type = structure_design.get("structure_type", "")
            if struct_type:
                initial_message_parts.append(f"\n**结构设计：** {struct_type}")
        
        initial_message = "".join(initial_message_parts)
        
        initial_state = {
            "task_id": task_id,
            "thread_id": thread_id,
            "coating_composition": composition,
            "process_params": process_params,
            "structure_design": structure_design,
            "target_requirements": target_requirements,
            "current_iteration": 1,
            "max_iterations": 5,
            "iteration_history": [],
            "messages": [HumanMessage(content=initial_message)],
            "current_agent": "user",
            "last_completed_agent": None
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        logger.info(f"[MultiAgent] 初始状态构建完成")
        logger.info(f"  - 成分: {composition}")
        logger.info(f"  - 工艺: {process_params}")
        logger.info(f"  - 结构: {structure_design}")
        # 安全输出需求信息（可能是字符串或字典）
        if target_requirements:
            req_str = str(target_requirements) if isinstance(target_requirements, dict) else target_requirements
            logger.info(f"  - 需求: {req_str[:100]}..." if len(req_str) > 100 else f"  - 需求: {req_str}")
        else:
            logger.info(f"  - 需求: N/A")
        
        # 存储任务
        self.active_tasks[task_id] = {
            "state": initial_state,
            "config": config
        }
        
        # 使用 astream_events 获取细粒度事件
        async for event in self.graph.astream_events(initial_state, config, version="v2"):
            # 更新存储的状态
            if event.get("event") == "on_chain_end":
                # 从metadata中提取langgraph_node信息
                metadata = event.get("metadata", {})
                if "langgraph_node" in metadata:
                    event_data = event.get("data", {})
                    if "output" in event_data and isinstance(event_data["output"], dict):
                        self.active_tasks[task_id]["state"].update(event_data["output"])
            
            yield event
    
    async def start_task(
        self,
        task_id: str,
        input_data: dict,
        thread_id: str = None
    ):
        """
        启动新任务（保留原有接口兼容性）
        
        Args:
            task_id: 任务ID
            input_data: 输入数据（涂层参数）
            thread_id: 线程ID（用于持久化）
        """
        logger.info(f"[MultiAgent] 启动任务 {task_id}")
        
        thread_id = thread_id or task_id
        
        # 构建初始状态
        # 支持多种输入格式：兼容前端发送的键名
        composition = input_data.get("coating_composition") or input_data.get("composition", {})
        process_params = input_data.get("process_params", {})
        structure_design = input_data.get("structure_design", {})
        target_requirements = input_data.get("target_requirements", "")
        
        # 构建初始消息：包含完整的参数描述
        initial_message_parts = ["请帮我优化涂层配方。"]
        
        # 添加目标需求（支持字符串和字典格式）
        if target_requirements:
            if isinstance(target_requirements, dict):
                # 格式化字典为易读文本
                req_parts = []
                if "substrate" in target_requirements:
                    req_parts.append(f"基材：{target_requirements['substrate']}")
                if "bonding_strength" in target_requirements:
                    req_parts.append(f"结合力：{target_requirements['bonding_strength']} N")
                if "elastic_modulus" in target_requirements:
                    req_parts.append(f"弹性模量：{target_requirements['elastic_modulus']} GPa")
                if "working_temperature" in target_requirements:
                    req_parts.append(f"工作温度：{target_requirements['working_temperature']}°C")
                if "cutting_speed" in target_requirements:
                    req_parts.append(f"切削速度：{target_requirements['cutting_speed']} m/min")
                if "application_scenario" in target_requirements:
                    req_parts.append(f"应用场景：{target_requirements['application_scenario']}")
                if "special_requirements" in target_requirements and target_requirements['special_requirements']:
                    req_parts.append(f"特殊要求：{target_requirements['special_requirements']}")
                
                if req_parts:
                    initial_message_parts.append(f"\n**目标需求：**\n" + "，".join(req_parts))
            else:
                # 字符串格式直接使用
                initial_message_parts.append(f"\n**目标需求：**\n{target_requirements}")
        
        # 添加涂层参数摘要
        if composition and any(composition.values()):
            al = composition.get("al_content", 0)
            ti = composition.get("ti_content", 0)
            n = composition.get("n_content", 0)
            initial_message_parts.append(f"\n**涂层成分：** Al {al}%, Ti {ti}%, N {n}%")
        
        if process_params:
            process_type = process_params.get("process_type", "")
            temp = process_params.get("deposition_temperature", 0)
            if process_type:
                initial_message_parts.append(f"\n**工艺参数：** {process_type}工艺, 沉积温度{temp}°C")
        
        if structure_design:
            struct_type = structure_design.get("structure_type", "")
            if struct_type:
                initial_message_parts.append(f"\n**结构设计：** {struct_type}")
        
        initial_message = "".join(initial_message_parts)
        
        initial_state = {
            "task_id": task_id,
            "thread_id": thread_id,
            "coating_composition": composition,
            "process_params": process_params,
            "structure_design": structure_design,
            "target_requirements": target_requirements,
            "current_iteration": 1,
            "max_iterations": 5,
            "iteration_history": [],
            "validation_passed": False,
            "convergence_achieved": False,
            "current_agent": "supervisor",
            "last_completed_agent": None,  # 初始无完成的Agent
            "next_action": None,
            "workflow_status": "started",
            "messages": [
                HumanMessage(content=initial_message)
            ],
            "stream_outputs": []
        }
        
        logger.info(f"[MultiAgent] 任务初始化完成:")
        logger.info(f"  - 成分: {composition}")
        logger.info(f"  - 工艺: {process_params}")
        logger.info(f"  - 结构: {structure_design}")
        # 安全输出需求信息（可能是字符串或字典）
        if target_requirements:
            req_str = str(target_requirements) if isinstance(target_requirements, dict) else target_requirements
            logger.info(f"  - 需求: {req_str[:100]}..." if len(req_str) > 100 else f"  - 需求: {req_str}")
        else:
            logger.info(f"  - 需求: N/A")
        
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # 存储任务
        self.active_tasks[task_id] = {
            "state": initial_state,
            "config": config
        }
        
        # 流式执行
        async for chunk in self.graph.astream(initial_state, config):
            # 更新存储的状态
            if chunk and isinstance(chunk, dict):
                for node_name, node_output in chunk.items():
                    if isinstance(node_output, dict):
                        self.active_tasks[task_id]["state"].update(node_output)
            
            yield "node_output", chunk
    
    async def resume_task_stream_events(
        self,
        task_id: str,
        resume_value: any
    ):
        """
        恢复被interrupt的任务（使用astream_events获取细粒度事件）
        
        Args:
            task_id: 任务ID
            resume_value: 恢复值（用户输入等）
        
        Yields:
            事件对象
        """
        from langgraph.types import Command
        
        if task_id not in self.active_tasks:
            raise ValueError(f"任务 {task_id} 不存在")
        
        logger.info(f"[MultiAgent] 恢复任务 {task_id} (stream_events)")
        
        config = self.active_tasks[task_id]["config"]
        
        # 使用Command恢复
        command = Command(resume=resume_value)
        
        async for event in self.graph.astream_events(command, config, version="v2"):
            # 更新状态
            if event.get("event") == "on_chain_end":
                metadata = event.get("metadata", {})
                if "langgraph_node" in metadata:
                    event_data = event.get("data", {})
                    if "output" in event_data and isinstance(event_data["output"], dict):
                        self.active_tasks[task_id]["state"].update(event_data["output"])
            
            yield event
    
    async def resume_task(
        self,
        task_id: str,
        resume_value: any
    ):
        """
        恢复被interrupt的任务（保留原有接口兼容性）
        
        Args:
            task_id: 任务ID
            resume_value: 恢复值（用户输入等）
        """
        from langgraph.types import Command
        
        if task_id not in self.active_tasks:
            raise ValueError(f"任务 {task_id} 不存在")
        
        logger.info(f"[MultiAgent] 恢复任务 {task_id}")
        
        config = self.active_tasks[task_id]["config"]
        
        # 使用Command恢复
        command = Command(resume=resume_value)
        
        async for chunk in self.graph.astream(command, config):
            # 更新状态
            if chunk and isinstance(chunk, dict):
                for node_name, node_output in chunk.items():
                    if isinstance(node_output, dict):
                        self.active_tasks[task_id]["state"].update(node_output)
            
            yield "node_output", chunk
    
    def get_task_state(self, task_id: str) -> dict:
        """获取任务状态"""
        if task_id not in self.active_tasks:
            raise ValueError(f"任务 {task_id} 不存在")
        
        return self.active_tasks[task_id]["state"]
    
    def list_active_tasks(self) -> list:
        """列出所有活动任务"""
        return list(self.active_tasks.keys())

    def is_task_finished(self, task_id: str) -> bool:
        """检查任务是否已完成"""
        if task_id not in self.active_tasks:
            return True
        
        config = self.active_tasks[task_id]["config"]
        state = self.graph.get_state(config)
        # 如果没有下一步骤，说明任务已完成
        return len(state.next) == 0

    def get_task_interrupt_info(self, task_id: str) -> Any:
        """获取任务的中断信息"""
        if task_id not in self.active_tasks:
            return None
            
        config = self.active_tasks[task_id]["config"]
        state = self.graph.get_state(config)
        
        # 检查是否有中断信息
        if state.tasks and state.tasks[0].interrupts:
            return state.tasks[0].interrupts[0].value
            
        return None


# 全局单例
multi_agent_manager = MultiAgentManager(use_memory=True)

