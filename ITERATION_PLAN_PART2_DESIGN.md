# 迭代优化功能 - 技术方案设计（第2部分）

## 📋 方案概览

基于第1部分的架构分析，本文档提供详细的技术设计方案。

---

## 1️⃣ 后端工作流重构

### 1.1 新增节点

**需要添加的节点：**

```python
# src/graph/nodes.py

def experiment_workorder_generation_node(state: CoatingWorkflowState) -> Dict:
    """生成实验工单节点 - 集成现有workorder_service"""
    # ⚠️ 使用已存在的workorder_service，不需要创建新的
    from ..services.workorder_service import generate_workorder
    
    logger.info(f"[工单生成] 任务 {state['task_id']}, 迭代 {state['current_iteration']}")
    
    # 确定用户选择的方案
    selected_option = state.get("selected_optimization_type")  # "P1", "P2", "P3"
    if not selected_option:
        # 如果用户未选择，默认使用P1
        logger.warning("用户未选择方案，默认使用P1")
        selected_option = "P1"
    
    # 流式输出回调
    def stream_callback(node: str, content: str):
        send_stream_chunk_sync("experiment_workorder", content)
    
    # 调用现有的工单生成服务
    result = generate_workorder(
        task_id=state['task_id'],
        selected_option=selected_option,
        task_state=state,
        stream_callback=stream_callback
    )
    
    if not result.get("success"):
        logger.error(f"工单生成失败: {result.get('error')}")
        return {
            "error_message": result.get("error"),
            "workflow_status": "error"
        }
    
    logger.info(f"[工单生成] 完成")
    
    return {
        "experiment_workorder": result.get("experiment_workorder"),
        "selected_optimization_name": result.get("selected_optimization_name"),
        "current_step": "workorder_generated",
        "workflow_status": "waiting_for_experiment"
    }


def await_experiment_results_node(state: CoatingWorkflowState) -> Dict:
    """等待实验结果节点 - 使用Interrupt暂停工作流"""
    from langgraph.types import interrupt
    
    logger.info(f"[等待实验] 任务 {state['task_id']}, 迭代 {state['current_iteration']}")
    
    # 暂停工作流，等待外部输入
    experiment_data = interrupt({
        "action": "await_experiment_results",
        "task_id": state["task_id"],
        "iteration": state["current_iteration"],
        "workorder_id": state.get("experiment_workorder", {}).get("id")
    })
    
    logger.info(f"[实验结果接收] 任务 {state['task_id']}, 数据: {experiment_data}")
    
    # 验证实验数据完整性
    required_fields = ["hardness", "adhesion_strength", "oxidation_temperature"]
    for field in required_fields:
        if field not in experiment_data:
            raise ValueError(f"实验数据缺少必填字段: {field}")
    
    # 记录到迭代历史
    iteration_record = {
        "iteration": state["current_iteration"],
        "timestamp": datetime.now().isoformat(),
        "parameters": {
            "composition": state["coating_composition"],
            "process": state["process_params"],
            "structure": state["structure_design"]
        },
        "prediction": state.get("performance_prediction"),
        "experiment_result": experiment_data
    }
    
    iteration_history = state.get("iteration_history", [])
    iteration_history.append(iteration_record)
    
    return {
        "experimental_results": experiment_data,
        "iteration_history": iteration_history,
        "current_iteration": state["current_iteration"] + 1,
        "current_step": "experiment_received",
        "workflow_status": "analyzing_results"
    }


def convergence_check_node(state: CoatingWorkflowState) -> Dict:
    """收敛检查节点 - 判断是否继续迭代"""
    logger.info(f"[收敛检查] 任务 {state['task_id']}, 迭代 {state['current_iteration']}")
    
    from ..services.convergence_service import ConvergenceService
    
    convergence_service = ConvergenceService()
    result = convergence_service.check_convergence(state)
    
    return {
        "convergence_achieved": result["is_converged"],
        "convergence_reason": result["reason"],
        "current_step": "convergence_checked",
        "workflow_status": "converged" if result["is_converged"] else "continuing"
    }
```

### 1.2 工作流图重构

**新的工作流结构：**

```python
# src/graph/workflow.py

def create_coating_workflow_with_iteration(
    use_memory: bool = True,
    enable_streaming: bool = True
) -> StateGraph:
    """创建支持迭代的涂层优化工作流"""
    workflow = StateGraph(CoatingWorkflowState)
    
    # ========== 添加所有节点 ==========
    # 基础节点
    workflow.add_node("input_validation", input_validation_node)
    workflow.add_node("error_handler", error_handler_node)
    
    # 性能预测模块
    workflow.add_node("topphi_simulation", topphi_simulation_node)
    workflow.add_node("ml_prediction", ml_model_prediction_node)
    workflow.add_node("historical_comparison", historical_comparison_node)
    workflow.add_node("integrated_analysis", integrated_analysis_node)
    
    # 优化建议模块
    workflow.add_node("p1_composition_optimization", p1_composition_optimization_node)
    workflow.add_node("p2_structure_optimization", p2_structure_optimization_node)
    workflow.add_node("p3_process_optimization", p3_process_optimization_node)
    workflow.add_node("optimization_summary", optimization_summary_node)
    
    # 🆕 迭代相关节点
    workflow.add_node("experiment_workorder", experiment_workorder_generation_node)
    workflow.add_node("await_experiment_results", await_experiment_results_node)
    workflow.add_node("convergence_check", convergence_check_node)
    
    # ========== 设置工作流路径 ==========
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
    
    # 性能预测链
    workflow.add_edge("topphi_simulation", "ml_prediction")
    workflow.add_edge("ml_prediction", "historical_comparison")
    workflow.add_edge("historical_comparison", "integrated_analysis")
    
    # 优化建议链
    workflow.add_edge("integrated_analysis", "p1_composition_optimization")
    workflow.add_edge("integrated_analysis", "p2_structure_optimization")
    workflow.add_edge("integrated_analysis", "p3_process_optimization")
    
    workflow.add_edge("p1_composition_optimization", "optimization_summary")
    workflow.add_edge("p2_structure_optimization", "optimization_summary")
    workflow.add_edge("p3_process_optimization", "optimization_summary")
    
    # 🆕 优化汇总后等待用户选择（通过Interrupt）
    workflow.add_edge("optimization_summary", "experiment_workorder")
    
    # 🆕 工单生成后等待实验结果
    workflow.add_edge("experiment_workorder", "await_experiment_results")
    
    # 🆕 实验结果接收后检查收敛
    workflow.add_edge("await_experiment_results", "convergence_check")
    
    # 🆕 收敛检查的条件分支
    workflow.add_conditional_edges(
        "convergence_check",
        should_continue_iteration,
        {
            "continue": "historical_comparison",  # 循环回去
            "end": END  # 收敛，结束
        }
    )
    
    # 错误处理终端
    workflow.add_edge("error_handler", END)
    
    # ========== 编译工作流 ==========
    # 🆕 使用SQLite持久化
    from langgraph.checkpoint.sqlite import SqliteSaver
    checkpointer = SqliteSaver.from_conn_string("workflow_checkpoints.db")
    
    if use_memory:
        memory = InMemoryStore()
        compiled = workflow.compile(checkpointer=checkpointer, store=memory)
    else:
        compiled = workflow.compile(checkpointer=checkpointer)
    
    logger.info("迭代优化工作流创建完成")
    return compiled


def should_continue_iteration(state: CoatingWorkflowState) -> Literal["continue", "end"]:
    """判断是否继续迭代"""
    # 检查是否收敛
    if state.get("convergence_achieved", False):
        logger.info(f"[迭代终止] 任务 {state['task_id']}: {state.get('convergence_reason')}")
        return "end"
    
    # 检查最大迭代次数
    if state.get("current_iteration", 0) >= state.get("max_iterations", 5):
        logger.info(f"[迭代终止] 任务 {state['task_id']}: 达到最大迭代次数")
        return "end"
    
    logger.info(f"[继续迭代] 任务 {state['task_id']}, 第 {state['current_iteration']} 轮")
    return "continue"
```

### 1.3 新增服务

**✅ 工单生成服务已存在**

现有的 `src/services/workorder_service.py` 已经提供了完善的工单生成功能：
- `generate_workorder(task_id, selected_option, task_state, stream_callback)` 函数
- 支持P1/P2/P3三种方案
- 使用LLM生成专业的实验工单
- 支持流式输出

**⚠️ 无需创建新的WorkorderService类！** 直接使用现有函数即可。

---

**ConvergenceService（收敛判断服务）：**

✨ **需要新建**

```python
# src/services/convergence_service.py

class ConvergenceService:
    """收敛判断服务"""
    
    def check_convergence(self, state: CoatingWorkflowState) -> Dict:
        """检查是否达到收敛条件"""
        target = state.get("target_requirements", {})
        experiment = state.get("experimental_results", {})
        history = state.get("iteration_history", [])
        
        # 条件1：性能达标
        performance_met = self._check_performance_target(experiment, target)
        
        # 条件2：连续改善率低
        improvement_stalled = self._check_improvement_trend(history)
        
        # 条件3：预测与实际误差小
        prediction_accurate = self._check_prediction_accuracy(state)
        
        if performance_met:
            return {
                "is_converged": True,
                "reason": "性能指标达标",
                "details": {
                    "hardness_achieved": experiment.get("hardness"),
                    "target_hardness": target.get("min_hardness")
                }
            }
        
        if improvement_stalled and len(history) >= 3:
            return {
                "is_converged": True,
                "reason": "连续3轮改善不明显，建议终止",
                "details": {"recent_improvements": [...]}
            }
        
        return {
            "is_converged": False,
            "reason": "继续优化",
            "current_gap": {
                "hardness": target.get("min_hardness", 0) - experiment.get("hardness", 0),
                ...
            }
        }
    
    def _check_performance_target(self, experiment: Dict, target: Dict) -> bool:
        """检查性能是否达标"""
        if not experiment or not target:
            return False
        
        checks = [
            experiment.get("hardness", 0) >= target.get("min_hardness", 999),
            experiment.get("adhesion_strength", 0) >= target.get("min_adhesion", 999),
            experiment.get("oxidation_temperature", 0) >= target.get("min_oxidation", 999)
        ]
        
        return all(checks)
    
    def _check_improvement_trend(self, history: List[Dict]) -> bool:
        """检查改善趋势是否停滞"""
        if len(history) < 3:
            return False
        
        recent_3 = history[-3:]
        improvements = []
        
        for i in range(1, len(recent_3)):
            prev_hardness = recent_3[i-1]["experiment_result"].get("hardness", 0)
            curr_hardness = recent_3[i]["experiment_result"].get("hardness", 0)
            improvement = (curr_hardness - prev_hardness) / max(prev_hardness, 1)
            improvements.append(improvement)
        
        # 连续改善率都小于5%
        return all(imp < 0.05 for imp in improvements)
    
    def _check_prediction_accuracy(self, state: CoatingWorkflowState) -> bool:
        """检查预测准确性"""
        prediction = state.get("performance_prediction", {})
        experiment = state.get("experimental_results", {})
        
        if not prediction or not experiment:
            return False
        
        pred_hardness = prediction.get("hardness", 0)
        exp_hardness = experiment.get("hardness", 0)
        
        error_rate = abs(pred_hardness - exp_hardness) / max(exp_hardness, 1)
        
        return error_rate < 0.10  # 误差小于10%
```

---

## 2️⃣ WebSocket API扩展

### 2.1 新增消息类型

```python
# src/api/routes/websocket_routes.py

async def handle_websocket_message(message: Dict, client_id: str):
    """处理WebSocket消息"""
    message_type = message.get("type")
    data = message.get("data", {})
    current_task_id = message.get("task_id")
    
    if message_type == "start_workflow":
        await handle_start_workflow(data, client_id)
    
    # 🆕 提交实验结果
    elif message_type == "submit_experiment_results":
        await handle_submit_experiment_results(data, client_id, current_task_id)
    
    # 🆕 选择优化方案（移入工作流内部处理）
    elif message_type == "select_optimization":
        await handle_select_optimization(data, client_id, current_task_id)
    
    elif message_type == "get_state":
        await handle_get_state(client_id, current_task_id)
    
    elif message_type == "reconnect":
        await handle_reconnect(data, client_id)
    
    else:
        await manager.send_json({
            "type": "error",
            "message": f"不支持的消息类型: {message_type}"
        }, client_id)


async def handle_submit_experiment_results(
    data: Dict, 
    client_id: str, 
    task_id: str
):
    """处理实验结果提交"""
    if not task_id:
        task_id = manager.get_task_id(client_id)
    
    if not task_id:
        await manager.send_json({
            "type": "error",
            "message": "没有活动的任务"
        }, client_id)
        return
    
    try:
        # 验证实验数据
        experiment_data = data.get("experiment_results")
        if not experiment_data:
            raise ValueError("缺少实验数据")
        
        required_fields = ["hardness", "adhesion_strength", "oxidation_temperature"]
        for field in required_fields:
            if field not in experiment_data:
                raise ValueError(f"缺少必填字段: {field}")
        
        logger.info(f"[实验结果提交] 任务 {task_id}: {experiment_data}")
        
        # 🔑 使用Command恢复工作流，传入实验数据
        from langgraph.types import Command
        
        resume_command = Command(
            resume=experiment_data,  # 传递给interrupt的返回值
            update={"experimental_results": experiment_data}  # 更新state
        )
        
        # 恢复工作流执行
        asyncio.create_task(
            execute_workflow_stream(
                task_id, 
                None,  # thread_id从checkpointer中恢复
                resume_command,  # 使用Command恢复
                client_id
            )
        )
        
        await manager.send_json({
            "type": "experiment_received",
            "message": "实验结果已提交，继续分析..."
        }, client_id)
        
    except Exception as e:
        logger.error(f"[实验结果提交失败] {str(e)}")
        await manager.send_json({
            "type": "error",
            "message": f"提交失败: {str(e)}"
        }, client_id)


async def handle_select_optimization(
    data: Dict,
    client_id: str,
    task_id: str
):
    """处理优化方案选择"""
    if not task_id:
        task_id = manager.get_task_id(client_id)
    
    selected_type = data.get("selected_type")  # "P1", "P2", "P3"
    selected_plan = data.get("selected_plan")  # 具体方案数据
    
    logger.info(f"[方案选择] 任务 {task_id}: {selected_type}")
    
    # 更新state中的选择
    workflow_manager.update_task_selection(task_id, {
        "type": selected_type,
        "plan": selected_plan
    })
    
    # 🔑 继续工作流（从optimization_summary → experiment_workorder）
    # 工作流会自动执行，无需Command
    
    await manager.send_json({
        "type": "selection_confirmed",
        "message": f"已选择{selected_type}方案，正在生成工单..."
    }, client_id)
```

### 2.2 执行函数修改

```python
async def execute_workflow_stream(
    task_id: str, 
    thread_id: str, 
    input_data: Any,  # 可以是Dict或Command
    client_id: str
):
    """流式执行工作流"""
    try:
        # 检查是否是恢复执行（Command对象）
        from langgraph.types import Command
        is_resume = isinstance(input_data, Command)
        
        if is_resume:
            logger.info(f"[工作流恢复] 任务 {task_id}")
        else:
            logger.info(f"[工作流启动] 任务 {task_id}")
        
        # 流式执行
        async for event_type, event_data in workflow_manager.stream_task(
            task_id, input_data, thread_id
        ):
            cleaned_data = clean_data_for_json(event_data)
            
            # 详细日志
            logger.info(f"[WS发送] type={event_type}, data键={list(cleaned_data.keys())}")
            
            # 发送到前端
            await manager.send_json({
                "type": event_type,
                "data": cleaned_data
            }, client_id)
            
            # 短暂延迟，避免消息过快
            await asyncio.sleep(0.01)
        
        # 工作流完成或暂停
        logger.info(f"[工作流完成/暂停] 任务 {task_id}")
        
        await manager.send_json({
            "type": "workflow_paused" if is_resume else "workflow_completed",
            "task_id": task_id
        }, client_id)
        
    except Exception as e:
        logger.error(f"[工作流执行失败] {str(e)}", exc_info=True)
        await manager.send_json({
            "type": "error",
            "message": f"执行失败: {str(e)}"
        }, client_id)
```

---

## 📌 下一步：查看第3部分

前端UI设计和完整实施计划请查看：
- `ITERATION_PLAN_PART3_IMPLEMENTATION.md`
