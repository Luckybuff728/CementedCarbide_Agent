"""
LangGraph主工作流定义
"""
from typing import Literal, Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from ..graph.state import CoatingWorkflowState
from ..graph.nodes import (
    input_validation_node,
    # 性能预测模块拆分为4个子节点
    topphi_simulation_node,
    ml_model_prediction_node,
    historical_comparison_node,
    integrated_analysis_node,
    # 优化建议模块重构
    p1_composition_optimization_node,
    p2_structure_optimization_node,
    p3_process_optimization_node,
    optimization_summary_node,
    iteration_planning_node,
    result_summary_node,
    # 实验闭环节点（已从experiment_nodes.py整合到nodes.py）
    await_user_selection_node,
    performance_improvement_prediction_node,
    experiment_workorder_generation_node,
    await_experiment_results_node,
    experiment_result_analysis_node,
    decide_next_iteration_node,
    await_plan_confirmation_node
)
import logging

logger = logging.getLogger(__name__)


def should_continue_after_validation(state: CoatingWorkflowState) -> Literal["topphi_simulation", "error_handler"]:
    """验证后的路由决策 - 进入性能预测第一步"""
    if state.get("input_validated", False):
        return "topphi_simulation"
    else:
        return "error_handler"


def should_continue_after_optimization(state: CoatingWorkflowState) -> Literal["await_user_selection", "iteration_planning"]:
    """优化建议后的路由决策"""
    # 如果已有选择的优化方案，进入迭代规划
    if state.get("selected_optimization_plan"):
        return "iteration_planning"
    else:
        return "await_user_selection"


def should_continue_after_iteration(state: CoatingWorkflowState) -> Literal["topphi_simulation", "result_summary"]:
    """迭代后的路由决策 - 重新进入性能预测流程"""
    if state.get("convergence_achieved", False) or state.get("current_iteration", 0) >= state.get("max_iterations", 5):
        return "result_summary"
    else:
        return "topphi_simulation"


def should_continue_after_await_results(state: CoatingWorkflowState) -> Literal["experiment_result_analysis", "END"]:
    """等待实验结果后的路由决策"""
    import logging
    logger = logging.getLogger(__name__)
    
    workflow_status = state.get("workflow_status")
    has_results = state.get("experiment_results")
    
    logger.info(f"[路由决策] workflow_status={workflow_status}, has_results={bool(has_results)}")
    
    # 检查是否有实验结果数据
    if has_results:
        # 有实验结果，继续分析
        logger.info("[路由决策] 有实验结果，继续分析 -> experiment_result_analysis")
        return "experiment_result_analysis"
    elif workflow_status == "awaiting_experiment_results":
        # 明确等待状态，暂停工作流
        logger.info("[路由决策] 等待实验结果，暂停工作流 -> END")
        return "END"
    else:
        # 没有结果也没有等待状态，暂停工作流等待用户输入
        logger.warning(f"[路由决策] 未检测到实验结果或等待状态(status={workflow_status})，暂停工作流 -> END")
        return "END"


def should_continue_after_iteration_decision(state: CoatingWorkflowState) -> Literal["result_summary", "performance_improvement_prediction", "p1_composition_optimization"]:
    """迭代决策后的路由"""
    next_action = state.get("next_action", "complete")
    next_step = state.get("next_step", "result_summary")
    
    if next_action == "complete":
        return "result_summary"
    elif next_action == "continue_current":
        return "performance_improvement_prediction"
    else:  # try_other
        return "p1_composition_optimization"


def error_handler_node(state: CoatingWorkflowState) -> Dict:
    """错误处理节点"""
    errors = state.get("validation_errors", [])
    error_message = "输入验证失败:\n" + "\n".join(errors)
    
    # 调试：输出错误处理信息
    logger.error(f"[调试] 错误处理节点被调用")
    logger.error(f"  - validation_errors: {errors}")
    logger.error(f"  - input_validated: {state.get('input_validated')}")
    logger.error(f"  - workflow_status: {state.get('workflow_status')}")
    
    return {
        "error_message": error_message,
        "workflow_status": "error",
        "current_step": "error",
        "next_step": None
    }


# 节点定义已移至nodes.py，这里只保留路由函数


def create_coating_workflow(
    use_memory: bool = True,
    enable_streaming: bool = True
) -> StateGraph:
    """
    创建涂层优化工作流
    
    Args:
        use_memory: 是否启用内存存储
        enable_streaming: 是否启用流式输出
    
    Returns:
        编译好的工作流图
    """
    # 创建工作流图
    workflow = StateGraph(CoatingWorkflowState)
    
    # 添加节点
    workflow.add_node("input_validation", input_validation_node)
    
    # 性能预测模块 - 拆分为4个子节点，支持流式输出
    workflow.add_node("topphi_simulation", topphi_simulation_node)
    workflow.add_node("ml_prediction", ml_model_prediction_node)
    workflow.add_node("historical_comparison", historical_comparison_node)
    workflow.add_node("integrated_analysis", integrated_analysis_node)
    
    # 优化建议模块 - 拆分为P1/P2/P3 + 汇总
    workflow.add_node("p1_composition_optimization", p1_composition_optimization_node)
    workflow.add_node("p2_structure_optimization", p2_structure_optimization_node)
    workflow.add_node("p3_process_optimization", p3_process_optimization_node)
    workflow.add_node("optimization_summary", optimization_summary_node)
    
    workflow.add_node("iteration_planning", iteration_planning_node)
    workflow.add_node("result_summary", result_summary_node)
    workflow.add_node("error_handler", error_handler_node)
    workflow.add_node("await_user_selection", await_user_selection_node)
    workflow.add_node("performance_improvement_prediction", performance_improvement_prediction_node)
    workflow.add_node("experiment_workorder_generation", experiment_workorder_generation_node)
    workflow.add_node("await_experiment_results", await_experiment_results_node)
    workflow.add_node("experiment_result_analysis", experiment_result_analysis_node)
    workflow.add_node("decide_next_iteration", decide_next_iteration_node)
    workflow.add_node("await_plan_confirmation", await_plan_confirmation_node)
    
    # 设置入口点
    workflow.set_entry_point("input_validation")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "input_validation",
        should_continue_after_validation,
        {
            "topphi_simulation": "topphi_simulation",
            "error_handler": "error_handler"
        }
    )
    
    # 性能预测模块内部流程 - 顺序执行4个子节点
    workflow.add_edge("topphi_simulation", "ml_prediction")
    workflow.add_edge("ml_prediction", "historical_comparison")
    workflow.add_edge("historical_comparison", "integrated_analysis")
    
    # 优化建议模块流程 - P1/P2/P3并行，然后汇总
    workflow.add_edge("integrated_analysis", "p1_composition_optimization")
    workflow.add_edge("integrated_analysis", "p2_structure_optimization")
    workflow.add_edge("integrated_analysis", "p3_process_optimization")
    
    workflow.add_edge("p1_composition_optimization", "optimization_summary")
    workflow.add_edge("p2_structure_optimization", "optimization_summary")
    workflow.add_edge("p3_process_optimization", "optimization_summary")
    
    workflow.add_conditional_edges(
        "optimization_summary",
        should_continue_after_optimization,
        {
            "await_user_selection": "await_user_selection",
            "iteration_planning": "iteration_planning"
        }
    )
    
    workflow.add_conditional_edges(
        "iteration_planning",
        should_continue_after_iteration,
        {
            "topphi_simulation": "topphi_simulation",
            "result_summary": "result_summary"
        }
    )
    
    # 实验闭环流程（完整迭代）
    # await_user_selection → performance_improvement_prediction → experiment_workorder_generation 
    # → await_experiment_results → (等待用户输入 | experiment_result_analysis) → decide_next_iteration
    # → (完成|继续优化|尝试其他方案)
    workflow.add_edge("await_user_selection", "performance_improvement_prediction")
    workflow.add_edge("performance_improvement_prediction", "experiment_workorder_generation")
    workflow.add_edge("experiment_workorder_generation", "await_experiment_results")
    
    # 条件边：根据是否有实验结果决定是否继续
    workflow.add_conditional_edges(
        "await_experiment_results",
        should_continue_after_await_results,
        {
            "experiment_result_analysis": "experiment_result_analysis",
            "END": END  # 暂停工作流，等待用户输入
        }
    )
    
    workflow.add_edge("experiment_result_analysis", "decide_next_iteration")
    
    # 迭代决策的条件边
    workflow.add_conditional_edges(
        "decide_next_iteration",
        should_continue_after_iteration_decision,
        {
            "result_summary": "result_summary",
            "performance_improvement_prediction": "performance_improvement_prediction",
            "p1_composition_optimization": "p1_composition_optimization"
        }
    )
    
    # 结束边
    workflow.add_edge("result_summary", END)
    workflow.add_edge("error_handler", END)
    
    # 编译工作流
    if use_memory:
        checkpointer = InMemorySaver()
        memory_store = InMemoryStore()
        compiled = workflow.compile(
            checkpointer=checkpointer,
            store=memory_store
        )
    else:
        compiled = workflow.compile()
    
    return compiled


class CoatingWorkflowManager:
    """涂层工作流管理器"""
    
    def __init__(self, use_memory: bool = True):
        """初始化工作流管理器
        
        Args:
            use_memory: 是否启用内存存储，默认为True
        """
        self.workflow = create_coating_workflow(use_memory=use_memory)
        self.active_tasks = {}
        self.stream_callback = None  # 流式输出回调函数
        logger.info(f"涂层工作流管理器初始化完成 (use_memory={use_memory})")
    
    def set_stream_callback(self, callback):
        """设置流式输出回调函数"""
        self.stream_callback = callback
    
    async def start_task(
        self, 
        task_id: str,
        input_data: Dict[str, Any],
        thread_id: str = None
    ) -> Dict:
        """
        启动新的优化任务
        
        Args:
            task_id: 任务ID
            input_data: 输入数据
            thread_id: 线程ID（用于会话管理）
        
        Returns:
            初始执行结果
        """
        # 准备初始状态
        initial_state = {
            "task_id": task_id,
            "thread_id": thread_id or task_id,
            "coating_composition": input_data.get("composition", {}),
            "process_params": input_data.get("process_params", {}),
            "structure_design": input_data.get("structure_design", {}),
            "target_requirements": input_data.get("target_requirements", ""),
            "current_iteration": 0,
            "max_iterations": 5,
            "messages": [],
            "stream_outputs": [],
            "workflow_status": "started"
        }
        
        # 配置
        config = {
            "configurable": {
                "thread_id": thread_id or task_id
            }
        }
        
        # 存储任务
        self.active_tasks[task_id] = {
            "state": initial_state,
            "config": config
        }
        
        # 执行工作流
        result = await self.workflow.ainvoke(initial_state, config)
        return result
    
    async def stream_task(
        self,
        task_id: str,
        input_data: Dict[str, Any] = None,
        thread_id: str = None
    ):
        """
        流式执行任务
        
        Args:
            task_id: 任务ID
            input_data: 输入数据（新任务）
            thread_id: 线程ID（用于恢复任务）
        
        Yields:
            工作流执行的流式输出
        """
        # 设置流式输出回调到上下文
        from ..graph.stream_callback import set_stream_callback
        if self.stream_callback:
            set_stream_callback(self.stream_callback)
        
        # 检查是否是Command对象（用于恢复interrupt）
        from langgraph.types import Command
        is_command = isinstance(input_data, Command)
        
        if input_data and not is_command:
            # 新任务
            initial_state = {
                "task_id": task_id,
                "thread_id": thread_id or task_id,
                "coating_composition": input_data.get("composition", {}),
                "process_params": input_data.get("process_params", {}),
                "structure_design": input_data.get("structure_design", {}),
                "target_requirements": input_data.get("target_requirements", ""),
                "current_iteration": 0,
                "max_iterations": 5,
                "messages": [],
                "stream_outputs": [],
                "workflow_status": "started"
            }
            
            # 调试：打印构建的初始状态
            logger.info(f"[调试] 任务 {task_id} 初始状态构建:")
            logger.info(f"  - coating_composition: {initial_state['coating_composition']}")
            logger.info(f"  - process_params: {initial_state['process_params']}")
            logger.info(f"  - structure_design: {initial_state['structure_design']}")
            logger.info(f"  - target_requirements: {initial_state['target_requirements']}")
            
            config = {
                "configurable": {
                    "thread_id": thread_id or task_id
                }
            }
            
            # 存储任务到active_tasks，以便后续更新选择
            self.active_tasks[task_id] = {
                "state": initial_state,
                "config": config
            }
            logger.info(f"任务 {task_id} 已存储到active_tasks")
        else:
            # 继续现有任务或恢复interrupt
            if task_id not in self.active_tasks:
                raise ValueError(f"任务 {task_id} 不存在")
            initial_state = self.active_tasks[task_id]["state"]
            config = self.active_tasks[task_id]["config"]
            
            # 如果是Command对象，用于恢复interrupt
            if is_command:
                initial_state = input_data
                logger.info(f"使用Command对象恢复工作流: {task_id}")
        
        # 流式执行 - 使用astream_events捕获LLM流式输出
        # 参考: https://docs.langchain.com/oss/python/langchain/streaming
        try:
            async for event in self.workflow.astream_events(
                initial_state,
                config,
                version="v2"  # 使用v2版本的事件流
            ):
                event_type = event.get("event")
                
                # 节点开始
                if event_type == "on_chain_start":
                    node_name = event.get("name")
                    if node_name and node_name != "LangGraph":
                        yield ("status", {"node": node_name, "status": "started"})
                
                # 节点结束 - 包含节点输出
                elif event_type == "on_chain_end":
                    node_name = event.get("name")
                    output = event.get("data", {}).get("output", {})
                    if node_name and node_name != "LangGraph" and output:
                        # 同步更新active_tasks中的状态
                        if task_id in self.active_tasks and isinstance(output, dict):
                            self.active_tasks[task_id]["state"].update(output)
                        yield ("updates", {node_name: output})
                
                # LLM流式输出 - 这是关键！
                elif event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, 'content') and chunk.content:
                        # 从metadata中获取节点信息
                        metadata = event.get("metadata", {})
                        yield ("llm_stream", {"chunk": chunk, "metadata": metadata})
                
                # LLM开始
                elif event_type == "on_chat_model_start":
                    metadata = event.get("metadata", {})
                    yield ("llm_start", {"metadata": metadata})
                
                # LLM结束
                elif event_type == "on_chat_model_end":
                    output = event.get("data", {}).get("output")
                    metadata = event.get("metadata", {})
                    yield ("llm_end", {"output": output, "metadata": metadata})
                    
        except Exception as e:
            logger.error(f"流式执行出错: {str(e)}")
            raise
    
    def update_task_selection(
        self,
        task_id: str,
        selection: Dict[str, Any]
    ) -> None:
        """
        更新任务的用户选择
        
        Args:
            task_id: 任务ID
            selection: 用户选择的优化方案
        """
        if task_id not in self.active_tasks:
            raise ValueError(f"任务 {task_id} 不存在")
        
        # 更新状态
        self.active_tasks[task_id]["state"]["selected_optimization_type"] = selection.get("type")
        self.active_tasks[task_id]["state"]["selected_optimization_plan"] = selection
        logger.info(f"任务 {task_id} 已选择优化方案: {selection.get('type')}")
    
    def add_experimental_results(
        self,
        task_id: str,
        results: Dict[str, Any]
    ) -> None:
        """
        添加实验结果
        
        Args:
            task_id: 任务ID
            results: 实验结果数据
        """
        if task_id not in self.active_tasks:
            raise ValueError(f"任务 {task_id} 不存在")
        
        # 更新实验结果
        self.active_tasks[task_id]["state"]["experimental_results"] = results
        logger.info(f"任务 {task_id} 已添加实验结果")
    
    def update_experiment_results(
        self,
        task_id: str,
        results: Dict[str, Any]
    ) -> None:
        """
        更新实验结果到工作流状态
        
        Args:
            task_id: 任务ID
            results: 实验结果数据
        """
        if task_id not in self.active_tasks:
            raise ValueError(f"任务 {task_id} 不存在")
        
        # 更新状态中的实验结果
        self.active_tasks[task_id]["state"]["experiment_results"] = results
        self.active_tasks[task_id]["state"]["workflow_status"] = "experiment_results_received"
        logger.info(f"任务 {task_id} 已更新实验结果，准备恢复工作流")
    
    def get_task_state(self, task_id: str) -> Dict:
        """获取任务当前状态"""
        if task_id not in self.active_tasks:
            raise ValueError(f"任务 {task_id} 不存在")
        return self.active_tasks[task_id]["state"]
    
    def list_active_tasks(self) -> List[str]:
        """列出所有活动任务"""
        return list(self.active_tasks.keys())
