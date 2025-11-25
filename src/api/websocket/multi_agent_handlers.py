"""
多Agent模式的WebSocket消息处理器
支持：
1. 启动多Agent任务
2. 发送对话消息
3. 恢复被interrupt的任务
4. 实时流式输出
"""
import logging
import uuid
import asyncio
from typing import Dict, Any
from datetime import datetime
from .manager import manager
from ...graph.multi_agent_graph import multi_agent_manager

logger = logging.getLogger(__name__)


async def handle_multi_agent_message(data: Dict[str, Any], client_id: str, current_task_id: str):
    """
    处理多Agent模式的WebSocket消息
    
    消息类型：
    - start_agent_task: 启动新的Agent任务
    - send_message: 发送对话消息给Agent
    - select_optimization: 用户选择优化方案
    - submit_experiment: 提交实验结果
    - ping: 心跳检测
    """
    message_type = data.get("type")
    
    if message_type == "ping":
        await handle_ping(client_id)
    
    elif message_type == "start_agent_task":
        await handle_start_agent_task(data, client_id)
    
    elif message_type == "send_message":
        await handle_send_message(data, client_id, current_task_id)
    
    elif message_type == "select_optimization":
        await handle_select_optimization(data, client_id, current_task_id)
    
    elif message_type == "submit_experiment":
        await handle_submit_experiment(data, client_id, current_task_id)
    
    elif message_type == "get_state":
        await handle_get_state(client_id, current_task_id)
    
    else:
        await manager.send_json({
            "type": "error",
            "message": f"不支持的消息类型: {message_type}"
        }, client_id)


async def handle_ping(client_id: str):
    """处理心跳检测"""
    await manager.send_json({
        "type": "pong",
        "timestamp": datetime.now().isoformat(),
        "client_id": client_id
    }, client_id)
    logger.debug(f"[心跳] 响应客户端 {client_id}")


async def handle_start_agent_task(data: Dict, client_id: str):
    """
    启动新的Agent任务
    
    消息格式：
    {
        "type": "start_agent_task",
        "data": {
            "composition": {...},
            "process_params": {...},
            "structure_design": {...},
            "target_requirements": "..."
        }
    }
    """
    task_id = f"AGENT_{uuid.uuid4().hex[:8]}"
    thread_id = f"THREAD_{uuid.uuid4().hex[:8]}"
    
    # 绑定任务到客户端
    manager.bind_task(client_id, task_id)
    
    logger.info(f"[MultiAgent] 启动任务: {task_id}")
    
    await manager.send_json({
        "type": "task_started",
        "task_id": task_id,
        "thread_id": thread_id,
        "message": "多Agent系统已启动"
    }, client_id)
    
    # 异步执行任务
    asyncio.create_task(
        execute_agent_task(task_id, thread_id, data.get("data"), client_id)
    )


async def execute_agent_task(
    task_id: str,
    thread_id: str,
    input_data: Dict,
    client_id: str
):
    """
    执行Agent任务（使用stream_events进行细粒度流式处理）
    
    处理所有事件：节点、工具调用、LLM token流、interrupt
    """
    try:
        logger.info(f"[执行任务] {task_id} 开始")
        
        # ===== 设置流式输出回调（用于Agent内部的流式输出） =====
        from ...graph.stream_callback import set_stream_callback
        
        async def stream_callback(node: str, content: str) -> bool:
            """流式输出回调：将content发送到前端"""
            try:
                await manager.send_json({
                    "type": "agent_token",
                    "token": content,
                    "node": node,
                    "timestamp": datetime.now().isoformat()
                }, client_id)
                return True
            except Exception as e:
                logger.error(f"[流式回调] 发送失败: {str(e)}")
                return False
        
        # 设置回调（contextvars会自动传递到子任务）
        set_stream_callback(stream_callback)
        
        current_node = None
        current_tool = None
        current_message_buffer = ""  # 用于累积LLM输出
        
        async for event in multi_agent_manager.start_task_stream_events(
            task_id, input_data, thread_id
        ):
            event_type = event.get("event")
            event_name = event.get("name", "")
            event_data = event.get("data", {})
            metadata = event.get("metadata", {})
            
            # 1. 节点开始
            if event_type == "on_chain_start" and "langgraph_node" in metadata:
                current_node = metadata["langgraph_node"]
                logger.info(f"[节点] {current_node} 开始")
                
                await manager.send_json({
                    "type": "node_start",
                    "node": current_node,
                    "timestamp": datetime.now().isoformat()
                }, client_id)
            
            # 2. 节点结束
            elif event_type == "on_chain_end" and "langgraph_node" in metadata:
                node_name = metadata["langgraph_node"]
                node_output = event_data.get("output", {})
                
                logger.info(f"[节点] {node_name} 完成")
                
                # 发送节点输出（数据更新）
                if isinstance(node_output, dict):
                    await send_node_output(client_id, node_name, node_output)
                
                # 检查是否有interrupt
                if isinstance(node_output, dict) and "__interrupt__" in node_output:
                    break
                
                current_node = None
            
            # 3. 工具调用开始
            elif event_type == "on_tool_start":
                current_tool = event_name
                tool_input = event_data.get("input", {})
                
                logger.info(f"[工具] {current_tool} 开始执行")
                
                # 发送工具执行状态
                await manager.send_json({
                    "type": "tool_start",
                    "tool": current_tool,
                    "node": current_node,
                    "timestamp": datetime.now().isoformat()
                }, client_id)
            
            # 4. 工具调用结束（立即发送数据更新）
            elif event_type == "on_tool_end":
                tool_name = event_name
                tool_output = event_data.get("output", {})
                
                logger.info(f"[工具] {tool_name} 执行完成，输出类型: {type(tool_output)}")
                
                # 发送工具完成消息
                await manager.send_json({
                    "type": "tool_end",
                    "tool": tool_name,
                    "node": current_node,
                    "timestamp": datetime.now().isoformat()
                }, client_id)
                
                # 立即发送工具的数据更新到前端（实现实时显示）
                if isinstance(tool_output, dict):
                    data_update = {}
                    
                    # TopPhi模拟结果
                    if "topphi_simulation" in tool_output:
                        data_update["topphi_simulation"] = tool_output["topphi_simulation"]
                        logger.info(f"[工具] 发送TopPhi模拟结果")
                    
                    # ML预测结果
                    if "ml_prediction" in tool_output:
                        data_update["ml_prediction"] = tool_output["ml_prediction"]
                    if "performance_prediction" in tool_output:
                        data_update["performance_prediction"] = tool_output["performance_prediction"]
                        logger.info(f"[工具] 发送性能预测结果")
                    
                    # 历史对比结果
                    if "historical_comparison" in tool_output:
                        data_update["historical_comparison"] = tool_output["historical_comparison"]
                        logger.info(f"[工具] 发送历史对比结果")
                    
                    # 根因分析结果
                    if "integrated_analysis" in tool_output:
                        data_update["integrated_analysis"] = tool_output["integrated_analysis"]
                        logger.info(f"[工具] 发送根因分析结果")
                    
                    # 验证结果
                    if "validation_result" in tool_output:
                        data_update["validation_result"] = tool_output["validation_result"]
                        data_update["validation_passed"] = tool_output.get("validation_passed")
                        logger.info(f"[工具] 发送验证结果")
                    
                    # 立即发送数据更新
                    if data_update:
                        await manager.send_json({
                            "type": "data_update",
                            "agent": current_node,
                            "data": data_update,
                            "timestamp": datetime.now().isoformat()
                        }, client_id)
                
                current_tool = None
            
            # 5. LLM token流
            elif event_type == "on_chat_model_stream":
                chunk = event_data.get("chunk", {})
                if hasattr(chunk, "content") and chunk.content:
                    token = chunk.content
                    current_message_buffer += token
                    
                    # 过滤：不发送Supervisor的JSON决策流
                    # Supervisor输出JSON格式，不适合流式显示给用户
                    if current_node and current_node.lower() != "supervisor":
                        # 只发送非Supervisor节点的token到前端
                        await manager.send_json({
                            "type": "agent_token",
                            "token": token,
                            "node": current_node,
                            "timestamp": datetime.now().isoformat()
                        }, client_id)
            
            # 6. LLM结束（发送完整消息）
            elif event_type == "on_chat_model_end":
                if current_message_buffer:
                    logger.info(f"[LLM] 输出完成: {current_message_buffer[:50]}...")
                    current_message_buffer = ""
            
            await asyncio.sleep(0.001)  # 微小延迟，避免过快
        
        # 检查任务是否真正完成
        if multi_agent_manager.is_task_finished(task_id):
            logger.info(f"[执行任务] {task_id} 完成")
            
            await manager.send_json({
                "type": "task_completed",
                "task_id": task_id,
                "message": "任务执行完成"
            }, client_id)
        else:
            # 任务未完成，检查是否有interrupt信息
            interrupt_info = multi_agent_manager.get_task_interrupt_info(task_id)
            if interrupt_info:
                logger.info(f"[执行任务] {task_id} 遇到interrupt，等待用户输入")
                await handle_interrupt_event(task_id, client_id, interrupt_info)
            else:
                logger.info(f"[执行任务] {task_id} 暂停 (未知原因)")
    
    except Exception as e:
        logger.error(f"[执行任务] {task_id} 失败: {str(e)}", exc_info=True)
        
        await manager.send_json({
            "type": "error",
            "task_id": task_id,
            "message": f"任务执行失败: {str(e)}"
        }, client_id)


async def send_node_output(client_id: str, node_name: str, node_output: Any):
    """
    发送节点输出到前端
    
    处理不同类型的输出：
    1. messages: 对话消息
    2. 数据更新: 验证结果、分析结果等
    
    注意：为了避免重复显示，需要过滤掉已经由工具(on_tool_end)发送过的数据
    """
    if not isinstance(node_output, dict):
        return
    
    # 提取消息（只发送AI消息，不发送用户消息，避免重复显示）
    from langchain_core.messages import AIMessage, HumanMessage
    messages = node_output.get("messages", [])
    for msg in messages:
        if hasattr(msg, "content"):
            # 只发送AIMessage，过滤掉HumanMessage（用户消息由前端直接显示）
            if isinstance(msg, AIMessage):
                await manager.send_json({
                    "type": "agent_message",
                    "agent": node_name,
                    "content": msg.content,
                    "timestamp": datetime.now().isoformat()
                }, client_id)
    
    # 提取数据更新
    data_update = {}
    
    # Validator数据
    if "validation_result" in node_output:
        data_update["validation_result"] = node_output["validation_result"]
        data_update["validation_passed"] = node_output.get("validation_passed")
    
    # Analyst数据
    # 注意：Topphi/ML/Historical通常由工具发送，节点结束时不应重复发送
    # Integrated Analysis目前是在节点内生成的，所以需要发送
    if node_name != "analyst":
        if "topphi_simulation" in node_output:
            data_update["topphi_simulation"] = node_output["topphi_simulation"]
        if "ml_prediction" in node_output:
            data_update["ml_prediction"] = node_output["ml_prediction"]
        if "performance_prediction" in node_output:
            data_update["performance_prediction"] = node_output["performance_prediction"]
        if "historical_comparison" in node_output:
            data_update["historical_comparison"] = node_output["historical_comparison"]
    
    # 始终发送 integrated_analysis (因为它是在节点中生成的，不是工具)
    if "integrated_analysis" in node_output:
        data_update["integrated_analysis"] = node_output["integrated_analysis"]
    
    # Optimizer数据
    if "p1_content" in node_output:
        data_update["p1_content"] = node_output["p1_content"]
    if "p2_content" in node_output:
        data_update["p2_content"] = node_output["p2_content"]
    if "p3_content" in node_output:
        data_update["p3_content"] = node_output["p3_content"]
    if "comprehensive_recommendation" in node_output:
        data_update["comprehensive_recommendation"] = node_output["comprehensive_recommendation"]
    
    # Experimenter数据
    if "experiment_workorder" in node_output:
        data_update["experiment_workorder"] = node_output["experiment_workorder"]
    if "experiment_results" in node_output:
        data_update["experiment_results"] = node_output["experiment_results"]
    
    # 实验分析结果（对比图数据）
    if "experiment_analysis" in node_output:
        data_update["experiment_analysis"] = node_output["experiment_analysis"]
    if "performance_comparison" in node_output:
        data_update["performance_comparison"] = node_output["performance_comparison"]
        logger.info(f"[节点输出] 发送性能对比数据")
    
    # 发送数据更新
    if data_update:
        await manager.send_json({
            "type": "data_update",
            "agent": node_name,
            "data": data_update,
            "timestamp": datetime.now().isoformat()
        }, client_id)


async def handle_interrupt_event(task_id: str, client_id: str, interrupt_data: Any):
    """
    处理interrupt事件
    
    interrupt类型：
    1. await_user_selection: 等待用户选择优化方案
    2. await_experiment_results: 等待实验结果
    3. ask_user: Supervisor询问用户
    """
    logger.info(f"[Interrupt] 任务 {task_id} 暂停")
    
    # 解析interrupt数据（支持多种格式）
    interrupt_info = None
    
    # 格式1：直接是dict
    if isinstance(interrupt_data, dict):
        interrupt_info = interrupt_data
    # 格式2：list/tuple包含的dict
    elif isinstance(interrupt_data, (list, tuple)) and len(interrupt_data) > 0:
        first_item = interrupt_data[0]
        if hasattr(first_item, 'value'):
            interrupt_info = first_item.value
        elif isinstance(first_item, dict):
            interrupt_info = first_item
    
    if not interrupt_info or not isinstance(interrupt_info, dict):
        logger.error(f"[Interrupt] 无法解析interrupt数据: {interrupt_data}")
        # 降级处理：发送通用暂停消息
        await manager.send_json({
            "type": "workflow_paused",
            "task_id": task_id,
            "reason": "unknown",
            "data": {"type": "unknown", "question": "等待用户输入"},
            "timestamp": datetime.now().isoformat()
        }, client_id)
        return
    
    interrupt_type = interrupt_info.get("type")
    
    logger.info(f"[Interrupt] 类型: {interrupt_type}, 数据: {interrupt_info}")
    
    # 发送暂停事件给前端
    await manager.send_json({
        "type": "workflow_paused",
        "task_id": task_id,
        "reason": interrupt_type,
        "data": interrupt_info,
        "timestamp": datetime.now().isoformat()
    }, client_id)


async def handle_send_message(data: Dict, client_id: str, task_id: str):
    """
    处理用户发送的对话消息
    
    消息格式：
    {
        "type": "send_message",
        "message": "用户的问题或输入"
    }
    """
    if not task_id:
        await manager.send_json({
            "type": "error",
            "message": "没有活动的任务"
        }, client_id)
        return
    
    try:
        message = data.get("message", "")
        
        logger.info(f"[对话] 任务 {task_id}，用户消息: {message}")
        
        # 恢复任务，传入用户消息
        resume_value = {"message": message}
        
        asyncio.create_task(
            resume_agent_task(task_id, resume_value, client_id)
        )
    
    except Exception as e:
        logger.error(f"[对话] 处理失败: {str(e)}")
        await manager.send_json({
            "type": "error",
            "message": f"处理消息失败: {str(e)}"
        }, client_id)


async def handle_select_optimization(data: Dict, client_id: str, task_id: str):
    """
    处理用户选择优化方案
    
    消息格式：
    {
        "type": "select_optimization",
        "selected_option": "P1/P2/P3",
        "optimization_name": "方案名称（可选）"
    }
    
    ✅ 健壮修复：先检查任务状态，决定是resume还是直接更新
    """
    if not task_id:
        await manager.send_json({
            "type": "error",
            "message": "没有活动的任务"
        }, client_id)
        return
    
    try:
        selected = data.get("selected_option")
        name = data.get("optimization_name")
        
        logger.info(f"[选择方案] 任务 {task_id}，选择: {selected}")
        
        # ✅ 关键修复：检查任务是否在等待interrupt
        interrupt_info = multi_agent_manager.get_task_interrupt_info(task_id)
        
        if interrupt_info and isinstance(interrupt_info, (list, tuple)):
            # 任务正在等待用户选择（正常流程）
            logger.info(f"[选择方案] 任务正在等待interrupt，准备resume")
            resume_value = {
                "selected_optimization_type": selected,
                "selected_optimization_name": name
            }
            
            asyncio.create_task(
                resume_agent_task(task_id, resume_value, client_id)
            )
        else:
            # 任务不在interrupt状态（可能Supervisor直接调用了Experimenter）
            # 降级处理：更新状态后再调用resume
            logger.warning(f"[选择方案] 任务不在interrupt状态，尝试注入选择并触发Experimenter")
            
            # 发送一个特殊消息，让Supervisor理解用户选择
            resume_value = {
                "message": f"用户已通过UI选择: {selected}",
                "selected_optimization_type": selected,
                "selected_optimization_name": name
            }
            
            asyncio.create_task(
                resume_agent_task(task_id, resume_value, client_id)
            )
    
    except Exception as e:
        logger.error(f"[选择方案] 处理失败: {str(e)}")
        await manager.send_json({
            "type": "error",
            "message": f"处理选择失败: {str(e)}"
        }, client_id)


async def handle_submit_experiment(data: Dict, client_id: str, task_id: str):
    """
    处理用户提交实验结果
    
    消息格式：
    {
        "type": "submit_experiment",
        "data": {
            "experiment_data": {...},
            "continue_iteration": true/false
        }
    }
    """
    if not task_id:
        await manager.send_json({
            "type": "error",
            "message": "没有活动的任务"
        }, client_id)
        return
    
    try:
        payload = data.get("data", data)
        experiment_data = payload.get("experiment_data", {})
        continue_iteration = payload.get("continue_iteration", False)
        
        logger.info(f"[实验结果] 任务 {task_id}，continue={continue_iteration}")
        
        resume_value = {
            "experiment_data": experiment_data,
            "continue_iteration": continue_iteration
        }
        
        asyncio.create_task(
            resume_agent_task(task_id, resume_value, client_id)
        )
    
    except Exception as e:
        logger.error(f"[实验结果] 处理失败: {str(e)}")
        await manager.send_json({
            "type": "error",
            "message": f"提交实验结果失败: {str(e)}"
        }, client_id)


async def resume_agent_task(
    task_id: str,
    resume_value: Any,
    client_id: str
):
    """
    恢复被interrupt的Agent任务（使用stream_events）
    
    注意：对话式系统中，一次resume可能又遇到新的interrupt
    """
    try:
        logger.info(f"[恢复任务] {task_id}")
        
        # ===== 设置流式输出回调 =====
        from ...graph.stream_callback import set_stream_callback
        
        async def stream_callback(node: str, content: str) -> bool:
            """流式输出回调：将content发送到前端"""
            try:
                await manager.send_json({
                    "type": "agent_token",
                    "token": content,
                    "node": node,
                    "timestamp": datetime.now().isoformat()
                }, client_id)
                return True
            except Exception as e:
                logger.error(f"[流式回调] 发送失败: {str(e)}")
                return False
        
        set_stream_callback(stream_callback)
        
        current_node = None
        current_tool = None
        current_message_buffer = ""
        
        async for event in multi_agent_manager.resume_task_stream_events(
            task_id, resume_value
        ):
            event_type = event.get("event")
            event_name = event.get("name", "")
            event_data = event.get("data", {})
            metadata = event.get("metadata", {})
            
            # 1. 节点开始
            if event_type == "on_chain_start" and "langgraph_node" in metadata:
                current_node = metadata["langgraph_node"]
                logger.info(f"[节点] {current_node} 开始")
                
                await manager.send_json({
                    "type": "node_start",
                    "node": current_node,
                    "timestamp": datetime.now().isoformat()
                }, client_id)
            
            # 2. 节点结束
            elif event_type == "on_chain_end" and "langgraph_node" in metadata:
                node_name = metadata["langgraph_node"]
                node_output = event_data.get("output", {})
                
                logger.info(f"[节点] {node_name} 完成")
                
                # 发送节点输出
                if isinstance(node_output, dict):
                    await send_node_output(client_id, node_name, node_output)
                
                # 检查interrupt
                if isinstance(node_output, dict) and "__interrupt__" in node_output:
                    break
                
                current_node = None
            
            # 3. 工具调用开始
            elif event_type == "on_tool_start":
                current_tool = event_name
                logger.info(f"[工具] {current_tool} 开始执行")
                
                await manager.send_json({
                    "type": "tool_start",
                    "tool": current_tool,
                    "node": current_node,
                    "timestamp": datetime.now().isoformat()
                }, client_id)
            
            # 4. 工具调用结束（立即发送数据更新）
            elif event_type == "on_tool_end":
                tool_name = event_name
                tool_output = event_data.get("output", {})
                
                logger.info(f"[工具] {tool_name} 执行完成，输出类型: {type(tool_output)}")
                
                # 发送工具完成消息
                await manager.send_json({
                    "type": "tool_end",
                    "tool": tool_name,
                    "node": current_node,
                    "timestamp": datetime.now().isoformat()
                }, client_id)
                
                # 立即发送工具的数据更新到前端（实现实时显示）
                if isinstance(tool_output, dict):
                    data_update = {}
                    
                    # TopPhi模拟结果
                    if "topphi_simulation" in tool_output:
                        data_update["topphi_simulation"] = tool_output["topphi_simulation"]
                        logger.info(f"[工具] 发送TopPhi模拟结果")
                    
                    # ML预测结果
                    if "ml_prediction" in tool_output:
                        data_update["ml_prediction"] = tool_output["ml_prediction"]
                    if "performance_prediction" in tool_output:
                        data_update["performance_prediction"] = tool_output["performance_prediction"]
                        logger.info(f"[工具] 发送性能预测结果")
                    
                    # 历史对比结果
                    if "historical_comparison" in tool_output:
                        data_update["historical_comparison"] = tool_output["historical_comparison"]
                        logger.info(f"[工具] 发送历史对比结果")
                    
                    # 根因分析结果
                    if "integrated_analysis" in tool_output:
                        data_update["integrated_analysis"] = tool_output["integrated_analysis"]
                        logger.info(f"[工具] 发送根因分析结果")
                    
                    # 验证结果
                    if "validation_result" in tool_output:
                        data_update["validation_result"] = tool_output["validation_result"]
                        data_update["validation_passed"] = tool_output.get("validation_passed")
                        logger.info(f"[工具] 发送验证结果")
                    
                    # 立即发送数据更新
                    if data_update:
                        await manager.send_json({
                            "type": "data_update",
                            "agent": current_node,
                            "data": data_update,
                            "timestamp": datetime.now().isoformat()
                        }, client_id)
                
                current_tool = None
            
            # 5. LLM token流
            elif event_type == "on_chat_model_stream":
                chunk = event_data.get("chunk", {})
                if hasattr(chunk, "content") and chunk.content:
                    token = chunk.content
                    current_message_buffer += token
                    
                    # 过滤：不发送Supervisor的JSON决策流
                    if current_node and current_node.lower() != "supervisor":
                        await manager.send_json({
                            "type": "agent_token",
                            "token": token,
                            "node": current_node,
                            "timestamp": datetime.now().isoformat()
                        }, client_id)
            
            # 6. LLM结束
            elif event_type == "on_chat_model_end":
                if current_message_buffer:
                    logger.info(f"[LLM] 输出完成: {current_message_buffer[:50]}...")
                    current_message_buffer = ""
            
            await asyncio.sleep(0.001)
        
        # 检查任务是否真正完成
        if multi_agent_manager.is_task_finished(task_id):
            logger.info(f"[恢复任务] {task_id} 完成")
            
            await manager.send_json({
                "type": "task_completed",
                "task_id": task_id,
                "message": "任务执行完成"
            }, client_id)
        else:
            # 任务未完成，检查是否有interrupt信息
            interrupt_info = multi_agent_manager.get_task_interrupt_info(task_id)
            if interrupt_info:
                logger.info(f"[恢复任务] {task_id} 再次遇到interrupt，等待用户输入")
                await handle_interrupt_event(task_id, client_id, interrupt_info)
            else:
                logger.info(f"[恢复任务] {task_id} 暂停 (未知原因)")
    
    except Exception as e:
        logger.error(f"[恢复任务] {task_id} 失败: {str(e)}", exc_info=True)
        
        await manager.send_json({
            "type": "error",
            "task_id": task_id,
            "message": f"恢复任务失败: {str(e)}"
        }, client_id)


async def handle_get_state(client_id: str, task_id: str):
    """获取任务状态"""
    if not task_id:
        await manager.send_json({
            "type": "error",
            "message": "没有活动的任务"
        }, client_id)
        return
    
    try:
        state = multi_agent_manager.get_task_state(task_id)
        
        await manager.send_json({
            "type": "state_update",
            "task_id": task_id,
            "state": {
                "current_agent": state.get("current_agent"),
                "current_iteration": state.get("current_iteration"),
                "workflow_status": state.get("workflow_status"),
                "validation_passed": state.get("validation_passed"),
                # 只发送必要的数据，避免过大
            }
        }, client_id)
    
    except Exception as e:
        logger.error(f"[获取状态] 失败: {str(e)}")
        await manager.send_json({
            "type": "error",
            "message": f"获取状态失败: {str(e)}"
        }, client_id)

