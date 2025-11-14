"""
工作流执行器 - 负责工作流的执行和流式输出
"""
import logging
import asyncio
from typing import Dict, Any
from .manager import manager
from .serializers import clean_data_for_json
from ...graph.workflow_manager import workflow_manager

logger = logging.getLogger(__name__)


async def execute_workflow_stream(task_id: str, thread_id: str, input_data: Dict, client_id: str):
    """
    流式执行工作流
    
    Args:
        task_id: 任务ID
        thread_id: 线程ID
        input_data: 输入数据（涂层参数）
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
        
        # 流式执行工作流
        async for event_type, event_data in workflow_manager.stream_task(
            task_id, input_data, thread_id
        ):
            # 检查是否是interrupt（工作流暂停）
            if event_type == "node_output" and isinstance(event_data, dict) and "__interrupt__" in event_data:
                interrupt_data = event_data["__interrupt__"]
                # 完整interrupt内容仅在debug级别记录，避免INFO日志过长
                logger.debug(f"[工作流暂停] 检测到interrupt详细数据: {interrupt_data}")
                
                # 解析interrupt数据
                interrupt_info = None
                if isinstance(interrupt_data, (list, tuple)) and len(interrupt_data) > 0:
                    first_item = interrupt_data[0]
                    # 检查是否是Interrupt对象
                    if hasattr(first_item, 'value'):
                        interrupt_info = first_item.value
                    elif isinstance(first_item, dict):
                        interrupt_info = first_item
                
                if interrupt_info and isinstance(interrupt_info, dict) and interrupt_info.get("type"):
                    reason = interrupt_info.get("type")
                    logger.info(f"[工作流暂停] 原因: {reason}")
                    
                    await manager.send_json({
                        "type": "workflow_paused",
                        "reason": reason,
                        "data": interrupt_info
                    }, client_id)
                    
                    logger.info(f"[工作流暂停] 已发送workflow_paused消息，停止当前流")
                    # interrupt后停止发送，等待用户响应
                    continue
            
            # 清理数据，移除不可序列化的对象（详细内容仅在debug级别记录）
            cleaned_data = clean_data_for_json(event_data)
            
            # ✅ 检测新迭代开始或完成
            if event_type == "node_output" and isinstance(cleaned_data, dict):
                # 检测 await_experiment_results 节点返回
                for node_name, node_data in cleaned_data.items():
                    if node_name == "await_experiment_results" and isinstance(node_data, dict):
                        continue_iteration = node_data.get("continue_iteration", False)
                        current_iteration = node_data.get("current_iteration")
                        
                        logger.info(f"[实验结果节点] continue_iteration={continue_iteration}, current_iteration={current_iteration}")
                        
                        if continue_iteration and current_iteration:
                            logger.info(f"[新迭代] 检测到第 {current_iteration} 轮迭代开始")
                            # 发送 iteration_started 消息
                            await manager.send_json({
                                "type": "iteration_started",
                                "iteration": current_iteration
                            }, client_id)
                        elif not continue_iteration:
                            logger.info(f"[优化完成] 用户选择完成，工作流即将结束 (continue_iteration={continue_iteration})")
                            # 发送 optimization_completed 消息
                            await manager.send_json({
                                "type": "optimization_completed",
                                "message": "优化流程已完成"
                            }, client_id)
                            logger.info(f"[优化完成] 已发送optimization_completed消息")
            
            # 发送前的摘要日志（详细字段在debug级别记录）
            logger.info(f"[WS发送] type={event_type}, data键={list(cleaned_data.keys()) if isinstance(cleaned_data, dict) else 'N/A'}")
            if event_type == "node_output" and isinstance(cleaned_data, dict):
                for node_name, node_data in cleaned_data.items():
                    logger.debug(f"[WS发送] 节点={node_name}, 数据类型={type(node_data)}")
                    if isinstance(node_data, dict):
                        logger.debug(f"[WS发送] 节点={node_name}, 数据键={list(node_data.keys())[:10]}")
            
            # 发送节点输出数据
            await manager.send_json({
                "type": event_type,
                "data": cleaned_data
            }, client_id)
            
            # 添加小延迟避免消息过快
            await asyncio.sleep(0.01)
        
        # ✅ 工作流正常结束（没有interrupt）
        logger.info(f"[工作流完成] 任务 {task_id} 正常结束")
        await manager.send_json({
            "type": "optimization_completed",
            "message": "优化流程已完成"
        }, client_id)
    
    except Exception as e:
        logger.error(f"工作流执行出错: {str(e)}")
        await manager.send_json({
            "type": "error",
            "message": f"工作流执行失败: {str(e)}"
        }, client_id)


async def execute_workorder_generation(task_id: str, selected_option: str, task_state: Dict, client_id: str):
    """
    执行工单生成（独立于工作流）
    
    Args:
        task_id: 任务ID
        selected_option: 用户选择的优化方案（P1/P2/P3）
        task_state: 任务状态
        client_id: 客户端ID
    """
    try:
        logger.info(f"[工单生成] 开始执行，任务: {task_id}，方案: {selected_option}")
        
        # 发送开始消息
        await manager.send_json({
            "type": "workorder_generation_started",
            "selected_option": selected_option,
            "message": f"正在生成 {selected_option} 的实验工单..."
        }, client_id)
        
        # 获取当前事件循环（用于从线程中调度任务）
        loop = asyncio.get_event_loop()
        
        # 设置流式输出回调（需要通过事件循环调度）
        def sync_stream_callback(node: str, content: str):
            # 使用call_soon_threadsafe在正确的事件循环中调度任务
            asyncio.run_coroutine_threadsafe(
                manager.send_json({
                    "type": "llm_stream",
                    "node": "experiment_workorder",
                    "content": content
                }, client_id),
                loop
            )
        
        # 调用工单生成服务（在线程池中运行，因为它是同步的）
        from ...services.workorder_service import generate_workorder
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(
                pool,
                generate_workorder,
                task_id,
                selected_option,
                task_state,
                sync_stream_callback
            )
        
        # 兼容统一的 {status,data,message,error,meta} 返回结构
        if not isinstance(result, dict):
            raise Exception("工单生成服务返回格式错误")

        status = result.get("status")
        data = result.get("data", {}) if isinstance(result.get("data"), dict) else {}

        if status == "success":
            # 工单生成成功
            await manager.send_json({
                "type": "workorder_generated",
                "data": {
                    # 完整的工单数据
                    "experiment_workorder": data,
                    # 兼容旧字段，便于前端直接使用
                    "selected_optimization": data.get("selected_optimization"),
                    "selected_optimization_name": data.get("solution_name") or data.get("optimization_name")
                },
                "message": result.get("message", "实验工单生成完成")
            }, client_id)
            logger.info(f"[工单生成] 完成，任务: {task_id}")
        else:
            # 工单生成失败
            error_msg = None
            if isinstance(result.get("error"), dict):
                error_msg = result["error"].get("message") or result["error"].get("details")
            error_msg = error_msg or result.get("message") or "未知错误"
            raise Exception(error_msg)
    
    except Exception as e:
        logger.error(f"[工单生成] 失败: {str(e)}")
        await manager.send_json({
            "type": "error",
            "message": f"工单生成失败: {str(e)}"
        }, client_id)
