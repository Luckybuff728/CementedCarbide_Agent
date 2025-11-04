"""
WebSocket路由处理
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any
import asyncio
import json
import uuid
import logging
from datetime import datetime

from ...graph.workflow import CoatingWorkflowManager

logger = logging.getLogger(__name__)


def clean_data_for_json(data: Any) -> Any:
    """
    清理数据，移除不可JSON序列化的对象
    主要处理LangGraph的Interrupt对象
    """
    if data is None:
        return None
    
    # 检查是否是Interrupt对象（通过类名判断，避免导入依赖）
    if hasattr(data, '__class__') and 'Interrupt' in data.__class__.__name__:
        # Interrupt对象通常包含一个value属性
        if hasattr(data, 'value'):
            return clean_data_for_json(data.value)
        return None
    
    # 处理字典
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            # 跳过不可序列化的键或值
            try:
                cleaned_value = clean_data_for_json(value)
                if cleaned_value is not None or value is None:
                    cleaned[key] = cleaned_value
            except Exception as e:
                logger.warning(f"跳过不可序列化的字段 {key}: {e}")
                continue
        return cleaned
    
    # 处理列表
    if isinstance(data, (list, tuple)):
        cleaned = []
        for item in data:
            try:
                cleaned_item = clean_data_for_json(item)
                if cleaned_item is not None or item is None:
                    cleaned.append(cleaned_item)
            except Exception:
                continue
        return cleaned
    
    # 基本类型直接返回
    if isinstance(data, (str, int, float, bool)):
        return data
    
    # 尝试转换为字符串
    try:
        json.dumps(data)
        return data
    except (TypeError, ValueError):
        logger.warning(f"无法序列化对象类型: {type(data).__name__}")
        return str(data)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_tasks: Dict[str, str] = {}  # client_id -> task_id 映射
        self.task_clients: Dict[str, str] = {}  # task_id -> client_id 映射
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """建立连接"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"客户端 {client_id} 已连接")
    
    def disconnect(self, client_id: str):
        """断开连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"客户端 {client_id} 已断开")
    
    def bind_task(self, client_id: str, task_id: str):
        """绑定客户端和任务"""
        self.client_tasks[client_id] = task_id
        self.task_clients[task_id] = client_id
        logger.info(f"绑定 {client_id} -> {task_id}")
    
    def get_task_id(self, client_id: str) -> str:
        """获取客户端关联的任务ID"""
        return self.client_tasks.get(client_id)
    
    def get_client_id(self, task_id: str) -> str:
        """获取任务关联的客户端ID"""
        return self.task_clients.get(task_id)
    
    def rebind_task(self, new_client_id: str, task_id: str):
        """重新绑定任务到新客户端"""
        old_client_id = self.task_clients.get(task_id)
        if old_client_id and old_client_id in self.client_tasks:
            del self.client_tasks[old_client_id]
        
        self.client_tasks[new_client_id] = task_id
        self.task_clients[task_id] = new_client_id
        logger.info(f"重新绑定任务 {task_id}: {old_client_id} -> {new_client_id}")
    
    async def send_json(self, data: dict, client_id: str):
        """发送JSON数据"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(data)
            except Exception as e:
                logger.error(f"发送消息失败 {client_id}: {e}")


# 全局连接管理器和工作流管理器
manager = ConnectionManager()
workflow_manager = CoatingWorkflowManager(use_memory=True)


def setup_websocket_routes(app):
    """设置WebSocket路由"""
    
    @app.websocket("/ws/coating")
    async def websocket_endpoint(websocket: WebSocket):
        """
        主WebSocket端点 - 实时通信
        """
        client_id = f"CLIENT_{uuid.uuid4().hex[:8]}"
        await manager.connect(websocket, client_id)
        current_task_id = None
        
        try:
            # 发送初始连接确认
            await manager.send_json({
                "type": "connection",
                "status": "connected",
                "client_id": client_id,
                "message": "WebSocket连接已建立"
            }, client_id)
            
            # 消息处理循环
            while True:
                data = await websocket.receive_json()
                logger.info(f"收到客户端消息: {data.get('type')}")
                
                await handle_websocket_message(data, client_id, current_task_id)
                
                # 更新current_task_id
                if data["type"] == "start_workflow":
                    current_task_id = manager.get_task_id(client_id)
        
        except WebSocketDisconnect:
            manager.disconnect(client_id)
            logger.info(f"WebSocket连接断开: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket错误: {str(e)}")
            await manager.send_json({
                "type": "error",
                "message": f"WebSocket错误: {str(e)}"
            }, client_id)
            manager.disconnect(client_id)


async def handle_websocket_message(data: Dict[str, Any], client_id: str, current_task_id: str):
    """处理WebSocket消息"""
    message_type = data.get("type")
    
    if message_type == "ping":
        # 心跳检测
        await manager.send_json({
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        }, client_id)
    
    elif message_type == "start_workflow":
        # 启动新的工作流任务
        await handle_start_workflow(data, client_id)
    
    elif message_type == "generate_workorder":
        # 生成实验工单（新的独立请求）
        await handle_generate_workorder(data, client_id, current_task_id)
    
    # 简化版本：不再处理实验结果提交（迭代功能已删除）
    # elif message_type == "submit_experiment_results":
    #     await handle_experiment_results(data, client_id, current_task_id)
    
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


async def handle_start_workflow(data: Dict, client_id: str):
    """处理工作流启动"""
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
    """处理工单生成请求（新的独立接口）"""
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


# ==================== 以下函数已删除（简化版本不需要实验结果处理） ====================
"""
async def handle_experiment_results(data: Dict, client_id: str, current_task_id: str):
    处理实验结果提交（已删除）
    pass
"""


async def handle_reconnect(data: Dict, client_id: str):
    """处理重连请求"""
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
    """处理状态查询"""
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


async def execute_workflow_stream(task_id: str, thread_id: str, input_data: Dict, client_id: str):
    """流式执行工作流"""
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
            # 清理数据，移除不可序列化的对象
            cleaned_data = clean_data_for_json(event_data)
            
            # 详细日志：WebSocket发送的数据
            logger.info(f"[WS发送] type={event_type}, data键={list(cleaned_data.keys()) if isinstance(cleaned_data, dict) else 'N/A'}")
            if event_type == "node_output" and isinstance(cleaned_data, dict):
                for node_name, node_data in cleaned_data.items():
                    logger.info(f"[WS发送] 节点={node_name}, 数据类型={type(node_data)}")
                    if isinstance(node_data, dict):
                        logger.info(f"[WS发送] 节点={node_name}, 数据键={list(node_data.keys())[:10]}")  # 只显示前10个键
            
            # 发送节点输出数据
            await manager.send_json({
                "type": event_type,
                "data": cleaned_data
            }, client_id)
            
            # 检查是否工作流完成（到达optimization_summary节点）
            if cleaned_data and isinstance(cleaned_data, dict):
                if 'optimization_summary' in cleaned_data:
                    # 工作流正常结束，发送完成消息
                    await manager.send_json({
                        "type": "workflow_completed",
                        "message": "优化建议生成完成，请选择一个方案生成实验工单"
                    }, client_id)
                    logger.info(f"任务 {task_id} 工作流完成")
            
            # 添加小延迟避免消息过快
            await asyncio.sleep(0.01)
    
    except Exception as e:
        logger.error(f"工作流执行出错: {str(e)}")
        await manager.send_json({
            "type": "error",
            "message": f"工作流执行失败: {str(e)}"
        }, client_id)


async def execute_workorder_generation(task_id: str, selected_option: str, task_state: Dict, client_id: str):
    """执行工单生成（独立于工作流）"""
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
        
        if result.get("success"):
            # 工单生成成功
            await manager.send_json({
                "type": "workorder_generated",
                "data": {
                    "experiment_workorder": result.get("experiment_workorder"),
                    "selected_optimization": result.get("selected_optimization"),
                    "selected_optimization_name": result.get("selected_optimization_name")
                },
                "message": "实验工单生成完成"
            }, client_id)
            logger.info(f"[工单生成] 完成，任务: {task_id}")
        else:
            # 工单生成失败
            raise Exception(result.get("error", "未知错误"))
    
    except Exception as e:
        logger.error(f"[工单生成] 失败: {str(e)}")
        await manager.send_json({
            "type": "error",
            "message": f"工单生成失败: {str(e)}"
        }, client_id)


"""
async def continue_workflow_after_experiment(task_id: str, client_id: str, experiment_data: Dict):
    提交实验结果后继续执行工作流（已删除 - 简化版本不需要）
    pass
"""
