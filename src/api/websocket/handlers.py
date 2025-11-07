"""
WebSocket消息处理器 - 处理各类客户端消息
"""
import logging
import uuid
import asyncio
from typing import Dict, Any
from datetime import datetime
from .manager import manager
from .executors import execute_workflow_stream, execute_workorder_generation
from ...graph.workflow_manager import workflow_manager

logger = logging.getLogger(__name__)


async def handle_websocket_message(data: Dict[str, Any], client_id: str, current_task_id: str):
    """
    处理WebSocket消息 - 消息路由
    
    Args:
        data: 消息数据
        client_id: 客户端ID
        current_task_id: 当前任务ID
    """
    message_type = data.get("type")
    
    if message_type == "ping":
        # 心跳检测 - 立即响应pong
        await handle_ping(client_id)
    
    elif message_type == "start_workflow":
        # 启动新的工作流任务
        await handle_start_workflow(data, client_id)
    
    elif message_type == "generate_workorder":
        # 生成实验工单
        await handle_generate_workorder(data, client_id, current_task_id)
    
    elif message_type == "select_optimization":
        # 处理用户选择优化方案
        await handle_select_optimization(data, client_id, current_task_id)
    
    elif message_type == "submit_experiment_results":
        # 处理实验数据提交
        await handle_submit_experiment_results(data, client_id, current_task_id)
    
    elif message_type == "reconnect":
        # 重连并恢复任务
        await handle_reconnect(data, client_id)
    
    elif message_type == "get_state":
        # 获取任务状态
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


async def handle_start_workflow(data: Dict, client_id: str):
    """
    处理工作流启动
    
    Args:
        data: {"type": "start_workflow", "data": {...涂层参数}}
        client_id: 客户端ID
    """
    task_id = f"TASK_{uuid.uuid4().hex[:8]}"
    thread_id = f"THREAD_{uuid.uuid4().hex[:8]}"
    
    # 绑定任务到客户端
    manager.bind_task(client_id, task_id)
    
    logger.info(f"启动工作流任务: {task_id}")
    
    await manager.send_json({
        "type": "status",
        "node": "system",
        "message": f"正在创建任务 {task_id}..."
    }, client_id)
    
    # 异步执行工作流
    asyncio.create_task(
        execute_workflow_stream(task_id, thread_id, data.get("data"), client_id)
    )


async def handle_generate_workorder(data: Dict, client_id: str, current_task_id: str):
    """
    处理工单生成请求
    
    Args:
        data: {"type": "generate_workorder", "selected_option": "P1/P2/P3"}
        client_id: 客户端ID
        current_task_id: 当前任务ID
    """
    task_id_to_use = current_task_id or manager.get_task_id(client_id)
    
    if not task_id_to_use:
        await manager.send_json({
            "type": "error",
            "message": "没有活动的任务，请先提交涂层数据"
        }, client_id)
        return
    
    try:
        # 获取用户选择的方案
        selected_option = data.get("selected_option")
        if not selected_option or selected_option not in ["P1", "P2", "P3"]:
            raise ValueError(f"无效的优化方案: {selected_option}")
        
        logger.info(f"[工单生成] 任务 {task_id_to_use}，用户选择: {selected_option}")
        
        # 获取任务状态
        try:
            task_state = workflow_manager.get_task_state(task_id_to_use)
        except ValueError:
            await manager.send_json({
                "type": "error",
                "message": "任务不存在或已过期，请重新提交"
            }, client_id)
            return
        
        # 异步执行工单生成
        asyncio.create_task(
            execute_workorder_generation(task_id_to_use, selected_option, task_state, client_id)
        )
        
    except Exception as e:
        logger.error(f"[工单生成] 处理请求失败: {str(e)}")
        await manager.send_json({
            "type": "error",
            "message": f"工单生成失败: {str(e)}"
        }, client_id)


async def handle_select_optimization(data: Dict, client_id: str, task_id: str):
    """
    处理用户选择优化方案 - 恢复workflow
    
    Args:
        data: {"type": "select_optimization", "optimization_type": "P1/P2/P3", ...}
        client_id: 客户端ID
        task_id: 任务ID
    """
    from langgraph.types import Command
    
    if not task_id:
        await manager.send_json({
            "type": "error",
            "message": "没有活动的任务"
        }, client_id)
        return
    
    try:
        # ✅ 修复：兼容前端发送的 selected_option 字段
        selected = data.get("selected_option") or data.get("optimization_type")
        
        # ✅ 构建resume数据 - 字段名与nodes.py保持一致
        resume_value = {
            "selected_optimization_type": selected,  # 与await_user_selection_node返回的字段一致
            "selected_optimization_name": data.get("optimization_name"),
            "continue_iteration": True
        }
        
        logger.info(f"[选择优化] 任务 {task_id}，用户选择: {resume_value}")
        
        # 恢复workflow执行
        command = Command(resume=resume_value)
        
        # 异步继续执行workflow
        asyncio.create_task(
            continue_workflow_after_interrupt(task_id, command, client_id)
        )
        
    except Exception as e:
        logger.error(f"[选择优化] 失败: {str(e)}")
        await manager.send_json({
            "type": "error",
            "message": f"恢复工作流失败: {str(e)}"
        }, client_id)


async def handle_submit_experiment_results(data: Dict, client_id: str, task_id: str):
    """
    处理实验结果提交 - 恢复workflow进入下一轮迭代
    
    Args:
        data: {"type": "submit_experiment_results", "experimental_results": {...}}
        client_id: 客户端ID
        task_id: 任务ID
    """
    from langgraph.types import Command
    
    if not task_id:
        await manager.send_json({
            "type": "error",
            "message": "没有活动的任务"
        }, client_id)
        return
    
    try:
        # ✅ 修复：兼容前端发送的字段名
        # 前端发送的数据格式: { type: "submit_experiment_results", data: { experiment_data: {...}, continue_iteration: bool } }
        payload = data.get("data", data)  # 兼容嵌套和非嵌套格式
        
        experiment_data = payload.get("experiment_data") or payload.get("experimental_results")
        continue_iteration = payload.get("continue_iteration", False)  # ✅ 从前端读取，默认False
        
        # 构建resume数据
        resume_value = {
            "experiment_data": experiment_data,
            "continue_iteration": continue_iteration
        }
        
        logger.info(f"[实验结果] 任务 {task_id}，提交实验数据")
        logger.info(f"[实验结果] experiment_data: {experiment_data}")
        logger.info(f"[实验结果] continue_iteration: {continue_iteration}")
        
        # 恢复workflow执行
        command = Command(resume=resume_value)
        
        # 异步继续执行workflow
        asyncio.create_task(
            continue_workflow_after_interrupt(task_id, command, client_id)
        )
        
    except Exception as e:
        logger.error(f"[实验结果] 提交失败: {str(e)}")
        await manager.send_json({
            "type": "error",
            "message": f"提交实验结果失败: {str(e)}"
        }, client_id)


async def handle_reconnect(data: Dict, client_id: str):
    """
    处理重连请求
    
    Args:
        data: {"type": "reconnect", "task_id": "TASK_xxx"}
        client_id: 客户端ID
    """
    task_id = data.get("task_id")
    if task_id:
        try:
            state = workflow_manager.get_task_state(task_id)
            manager.rebind_task(client_id, task_id)
            
            await manager.send_json({
                "type": "task_restored",
                "task_id": task_id,
                "state": {
                    "current_step": state.get("current_step"),
                    "workflow_status": state.get("workflow_status"),
                    "performance_prediction": state.get("performance_prediction"),
                    "optimization_suggestions": state.get("optimization_suggestions")
                },
                "message": f"任务 {task_id} 已恢复"
            }, client_id)
            
        except ValueError:
            await manager.send_json({
                "type": "error",
                "message": f"任务 {task_id} 不存在或已过期"
            }, client_id)


async def handle_get_state(client_id: str, current_task_id: str):
    """
    处理状态查询
    
    Args:
        client_id: 客户端ID
        current_task_id: 当前任务ID
    """
    if current_task_id:
        try:
            state = workflow_manager.get_task_state(current_task_id)
            await manager.send_json({
                "type": "state_update",
                "data": state
            }, client_id)
        except ValueError:
            await manager.send_json({
                "type": "error",
                "message": "任务不存在"
            }, client_id)


async def continue_workflow_after_interrupt(task_id: str, command, client_id: str):
    """
    在interrupt后继续执行workflow
    
    Args:
        task_id: 任务ID
        command: LangGraph Command对象
        client_id: 客户端ID
    """
    try:
        # 设置流式输出回调
        async def stream_callback(node: str, content: str):
            await manager.send_json({
                "type": "llm_stream",
                "node": node,
                "content": content
            }, client_id)
        
        workflow_manager.set_stream_callback(stream_callback)
        
        # ✅ 修复：使用stream_task而不是resume_task
        async for event_type, event_data in workflow_manager.stream_task(task_id, command):
            # ✅ 检测新迭代开始或完成
            if event_type == "node_output" and isinstance(event_data, dict):
                for node_name, node_data in event_data.items():
                    if node_name == "await_experiment_results" and isinstance(node_data, dict):
                        continue_iteration = node_data.get("continue_iteration", False)
                        current_iteration = node_data.get("current_iteration")
                        
                        logger.info(f"[继续工作流-实验结果] continue_iteration={continue_iteration}, current_iteration={current_iteration}")
                        
                        if continue_iteration and current_iteration:
                            logger.info(f"[继续工作流-新迭代] 检测到第 {current_iteration} 轮迭代开始")
                            await manager.send_json({
                                "type": "iteration_started",
                                "iteration": current_iteration
                            }, client_id)
                        elif not continue_iteration:
                            logger.info(f"[继续工作流-完成] 用户选择完成，工作流即将结束 (continue_iteration={continue_iteration})")
                            await manager.send_json({
                                "type": "optimization_completed",
                                "message": "优化流程已完成"
                            }, client_id)
                            logger.info(f"[继续工作流-完成] 已发送optimization_completed消息")
            
            # ✅ 检查是否是interrupt（工作流暂停）
            if event_type == "node_output" and isinstance(event_data, dict) and "__interrupt__" in event_data:
                interrupt_data = event_data["__interrupt__"]
                logger.info(f"[继续工作流-暂停] 检测到interrupt: {interrupt_data}")
                
                # 解析interrupt数据
                interrupt_info = None
                if isinstance(interrupt_data, (list, tuple)) and len(interrupt_data) > 0:
                    first_item = interrupt_data[0]
                    if hasattr(first_item, 'value'):
                        interrupt_info = first_item.value
                    elif isinstance(first_item, dict):
                        interrupt_info = first_item
                
                if interrupt_info and isinstance(interrupt_info, dict) and interrupt_info.get("type"):
                    reason = interrupt_info.get("type")
                    logger.info(f"[继续工作流-暂停] 原因: {reason}")
                    
                    await manager.send_json({
                        "type": "workflow_paused",
                        "reason": reason,
                        "data": interrupt_info
                    }, client_id)
                    
                    logger.info(f"[继续工作流-暂停] 已发送workflow_paused消息，停止当前流")
                    # interrupt后停止发送，等待用户响应
                    continue
            
            # 处理事件（与execute_workflow_stream相同的逻辑）
            from .serializers import clean_data_for_json
            cleaned_data = clean_data_for_json(event_data)
            
            await manager.send_json({
                "type": event_type,
                "data": cleaned_data
            }, client_id)
            
            await asyncio.sleep(0.01)
    
    except Exception as e:
        logger.error(f"继续工作流失败: {str(e)}")
        await manager.send_json({
            "type": "error",
            "message": f"继续工作流失败: {str(e)}"
        }, client_id)
