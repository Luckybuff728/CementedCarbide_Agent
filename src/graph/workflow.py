"""
LangGraph主工作流定义 - 修复版本
修复了并行执行逻辑错误和边定义问题
"""
from typing import Literal, Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from ..graph.state import CoatingWorkflowState
# 使用最完整的节点实现
from .nodes import (
    # 基础节点
    input_validation_node,
    error_handler_node,
    # 性能预测模块
    topphi_simulation_node,
    ml_model_prediction_node, 
    historical_comparison_node,
    integrated_analysis_node,
    # 优化建议模块
    p1_composition_optimization_node,
    p2_structure_optimization_node, 
    p3_process_optimization_node,
    optimization_summary_node,
    # 迭代优化节点
    await_user_selection_node,
    experiment_workorder_node,
    await_experiment_results_node
)
import logging

logger = logging.getLogger(__name__)


def should_continue_after_validation(state: CoatingWorkflowState) -> Literal["topphi_simulation", "error_handler"]:
    """验证后的路由决策"""
    if state.get("input_validated", False):
        return "topphi_simulation"
    else:
        return "error_handler"


def should_continue_iteration(state: CoatingWorkflowState) -> Literal["historical_comparison", "END"]:
    """根据用户决策判断是否继续迭代"""
    continue_iteration = state.get("continue_iteration", False)
    
    if continue_iteration:
        logger.info(f"[迭代判断] 用户选择继续，开始第 {state.get('current_iteration')} 轮迭代")
        return "historical_comparison"
    else:
        logger.info(f"[迭代判断] 用户选择完成，结束迭代")
        return "END"


def create_coating_workflow(
    use_memory: bool = True,
    enable_streaming: bool = True
) -> StateGraph:
    """
    创建涂层优化工作流 - 修复版
    
    主要修复：
    1. 修复P1/P2/P3并行执行导致的optimization_summary多重触发
    2. 简化工作流路径，避免循环依赖
    3. 修复条件边的类型注解
    """
    workflow = StateGraph(CoatingWorkflowState)
    
    # ==================== 添加所有节点 ====================
    # 基础节点
    workflow.add_node("input_validation", input_validation_node)
    workflow.add_node("error_handler", error_handler_node)
    
    # 性能预测模块 - 顺序执行避免并发问题
    workflow.add_node("topphi_simulation", topphi_simulation_node)
    workflow.add_node("ml_prediction", ml_model_prediction_node)
    workflow.add_node("historical_comparison", historical_comparison_node)
    workflow.add_node("integrated_analysis", integrated_analysis_node)
    
    # 优化建议模块 - P1/P2/P3并行生成，然后汇总
    workflow.add_node("p1_composition_optimization", p1_composition_optimization_node)
    workflow.add_node("p2_structure_optimization", p2_structure_optimization_node)
    workflow.add_node("p3_process_optimization", p3_process_optimization_node)
    workflow.add_node("optimization_summary", optimization_summary_node)
    
    # 迭代优化节点
    workflow.add_node("await_user_selection", await_user_selection_node)
    workflow.add_node("experiment_workorder", experiment_workorder_node)
    workflow.add_node("await_experiment_results", await_experiment_results_node)
    
    # ==================== 设置工作流路径 ====================
    # 入口点
    workflow.set_entry_point("input_validation")
    
    # 验证分支
    workflow.add_conditional_edges(
        "input_validation",
        should_continue_after_validation,
        {
            "topphi_simulation": "topphi_simulation",
            "error_handler": "error_handler"
        }
    )
    
    # 性能预测链 - 顺序执行
    workflow.add_edge("topphi_simulation", "ml_prediction")
    workflow.add_edge("ml_prediction", "historical_comparison")
    workflow.add_edge("historical_comparison", "integrated_analysis")
    
    # 优化建议链 - P1/P2/P3并行生成，然后汇总
    workflow.add_edge("integrated_analysis", "p1_composition_optimization")
    workflow.add_edge("integrated_analysis", "p2_structure_optimization")
    workflow.add_edge("integrated_analysis", "p3_process_optimization")
    
    # 三个优化节点完成后进入汇总节点
    workflow.add_edge("p1_composition_optimization", "optimization_summary")
    workflow.add_edge("p2_structure_optimization", "optimization_summary")
    workflow.add_edge("p3_process_optimization", "optimization_summary")
    
    # 优化汇总后进入迭代循环
    workflow.add_edge("optimization_summary", "await_user_selection")
    workflow.add_edge("await_user_selection", "experiment_workorder")
    workflow.add_edge("experiment_workorder", "await_experiment_results")
    
    # 根据用户决策判断是否继续迭代
    workflow.add_conditional_edges(
        "await_experiment_results",
        should_continue_iteration,
        {
            "historical_comparison": "historical_comparison",  # 继续迭代
            "END": END  # 完成优化
        }
    )
    
    # ==================== 终端边 ====================
    workflow.add_edge("error_handler", END)
    
    # ==================== 编译工作流 ====================
    if use_memory:
        checkpointer = InMemorySaver()
        memory = InMemoryStore()
        compiled = workflow.compile(checkpointer=checkpointer, store=memory)
    else:
        compiled = workflow.compile()
    
    logger.info("涂层优化工作流创建完成")
    return compiled


class CoatingWorkflowManager:
    """涂层工作流管理器 - 修复版本"""
    
    def __init__(self, use_memory: bool = True):
        """初始化工作流管理器"""
        self.workflow = create_coating_workflow(use_memory=use_memory)
        self.active_tasks = {}
        self.stream_callback = None
        logger.info(f"涂层工作流管理器初始化完成 (use_memory={use_memory})")
    
    def set_stream_callback(self, callback):
        """设置流式输出回调函数"""
        self.stream_callback = callback
    
    async def stream_task(
        self,
        task_id: str,
        input_data: Dict[str, Any] = None,
        thread_id: str = None
    ):
        """流式执行任务"""
        # 设置流式输出回调到上下文
        from .stream_callback import set_stream_callback
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
                "current_iteration": 1,  # 初始化为第1轮
                "max_iterations": 5,
                "iteration_history": [],  # 迭代历史
                "experiment_results": {},  # 实验结果
                "continue_iteration": False,  # 继续迭代标志
                "convergence_achieved": False,  # 收敛标志
                "selected_optimization_name": None,  # 选择的优化方案名称
                "experiment_workorder": None,  # 实验工单内容
                "messages": [],
                "stream_outputs": [],
                "workflow_status": "started"
            }
            
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
            
            # 流式执行
            async for chunk in self.workflow.astream(initial_state, config):
                # 更新存储的状态（关键：同步节点输出到state）
                if chunk and isinstance(chunk, dict):
                    for node_name, node_output in chunk.items():
                        if isinstance(node_output, dict):
                            # 将节点输出合并到state中
                            self.active_tasks[task_id]["state"].update(node_output)
                
                yield "node_output", chunk
        
        else:
            # 恢复任务或处理Command
            if task_id in self.active_tasks:
                config = self.active_tasks[task_id]["config"]
                
                if is_command:
                    # 使用Command恢复
                    async for chunk in self.workflow.astream(input_data, config):
                        # 更新存储的状态
                        if chunk and isinstance(chunk, dict):
                            for node_name, node_output in chunk.items():
                                if isinstance(node_output, dict):
                                    self.active_tasks[task_id]["state"].update(node_output)
                        yield "node_output", chunk
                else:
                    # 恢复执行
                    async for chunk in self.workflow.astream(None, config):
                        # 更新存储的状态
                        if chunk and isinstance(chunk, dict):
                            for node_name, node_output in chunk.items():
                                if isinstance(node_output, dict):
                                    self.active_tasks[task_id]["state"].update(node_output)
                        yield "node_output", chunk
    
    def get_task_state(self, task_id: str) -> Dict:
        """获取任务状态"""
        if task_id not in self.active_tasks:
            raise ValueError(f"任务 {task_id} 不存在")
        
        return self.active_tasks[task_id]["state"]
    
    def update_task_selection(self, task_id: str, selection_data: Dict):
        """更新任务的用户选择"""
        if task_id in self.active_tasks:
            state = self.active_tasks[task_id]["state"]
            state["selected_optimization_plan"] = selection_data
            logger.info(f"任务 {task_id} 用户选择已更新")
    
    def update_experiment_results(self, task_id: str, results_data: Dict):
        """更新任务的实验结果"""
        if task_id in self.active_tasks:
            state = self.active_tasks[task_id]["state"]
            state["experiment_results"] = results_data
            logger.info(f"任务 {task_id} 实验结果已更新")
    
    def list_active_tasks(self) -> List[str]:
        """列出所有活动任务"""
        return list(self.active_tasks.keys())
