"""
FastAPI后端服务 - 提供API和WebSocket接口
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
import json
import uuid
import logging
from datetime import datetime

from ..graph.workflow import CoatingWorkflowManager
from ..models.coating_models import CoatingInput, CoatingTask

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="TopMat Agent API",
    description="硬质合金涂层优化专家系统API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局工作流管理器
workflow_manager = CoatingWorkflowManager(use_memory=True)

# WebSocket连接管理
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
            # 注意：不删除client_tasks映射，以便重连时恢复
    
    def bind_task(self, client_id: str, task_id: str):
        """绑定客户端和任务"""
        self.client_tasks[client_id] = task_id
        self.task_clients[task_id] = client_id
        logger.info(f"绑定 {client_id} -> {task_id}")
    
    def get_task_id(self, client_id: str) -> Optional[str]:
        """获取客户端关联的任务ID"""
        return self.client_tasks.get(client_id)
    
    def get_client_id(self, task_id: str) -> Optional[str]:
        """获取任务关联的客户端ID"""
        return self.task_clients.get(task_id)
    
    def rebind_task(self, new_client_id: str, task_id: str):
        """重新绑定任务到新客户端（用于重连）"""
        # 清除旧的客户端绑定
        old_client_id = self.task_clients.get(task_id)
        if old_client_id and old_client_id in self.client_tasks:
            del self.client_tasks[old_client_id]
        
        # 建立新绑定
        self.client_tasks[new_client_id] = task_id
        self.task_clients[task_id] = new_client_id
        logger.info(f"重新绑定任务 {task_id}: {old_client_id} -> {new_client_id}")
    
    async def send_personal_message(self, message: str, client_id: str):
        """发送个人消息"""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
    
    async def send_json(self, data: dict, client_id: str):
        """发送JSON数据"""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(data)
    
    async def broadcast(self, message: str):
        """广播消息"""
        for connection in self.active_connections.values():
            await connection.send_text(message)

# 实例化连接管理器
manager = ConnectionManager()


# API模型定义
class TaskCreateRequest(BaseModel):
    """任务创建请求"""
    coating_input: CoatingInput
    user_id: Optional[str] = None


class TaskUpdateRequest(BaseModel):
    """任务更新请求"""
    task_id: str
    action: str  # "select_optimization" | "add_results"
    data: Dict[str, Any]


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


# API路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "TopMat Agent API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/coating/submit", response_model=TaskResponse)
async def submit_coating_task(request: TaskCreateRequest):
    """
    提交涂层优化任务
    """
    try:
        # 生成任务ID
        task_id = f"TASK_{uuid.uuid4().hex[:8]}"
        thread_id = f"THREAD_{uuid.uuid4().hex[:8]}"
        
        # 准备输入数据
        input_data = {
            "composition": request.coating_input.composition.model_dump(),
            "process_params": request.coating_input.process_params.model_dump(),
            "structure_design": request.coating_input.structure_design.model_dump(),
            "target_requirements": request.coating_input.target_requirements.model_dump()
        }
        
        # 启动任务（异步）
        asyncio.create_task(
            process_task_async(task_id, input_data, thread_id)
        )
        
        return TaskResponse(
            task_id=task_id,
            status="started",
            message="任务已提交，正在处理中",
            data={"thread_id": thread_id}
        )
    
    except Exception as e:
        logger.error(f"提交任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/coating/task/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """
    获取任务状态
    """
    try:
        state = workflow_manager.get_task_state(task_id)
        return TaskResponse(
            task_id=task_id,
            status=state.get("workflow_status", "unknown"),
            message="获取任务状态成功",
            data={
                "current_step": state.get("current_step"),
                "predictions": state.get("performance_prediction"),
                "suggestions": state.get("optimization_suggestions")
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/coating/optimize")
async def request_optimization(request: TaskUpdateRequest):
    """
    请求优化建议
    """
    try:
        if request.action == "select_optimization":
            # 更新用户选择的优化方案
            workflow_manager.update_task_selection(
                request.task_id,
                request.data
            )
            return TaskResponse(
                task_id=request.task_id,
                status="optimization_selected",
                message="优化方案已选择",
                data=request.data
            )
        else:
            raise ValueError(f"不支持的操作: {request.action}")
    
    except Exception as e:
        logger.error(f"优化请求失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/coating/iterate")
async def iterate_optimization(request: TaskUpdateRequest):
    """
    执行迭代优化
    """
    try:
        if request.action == "add_results":
            # 添加实验结果
            workflow_manager.add_experimental_results(
                request.task_id,
                request.data
            )
            return TaskResponse(
                task_id=request.task_id,
                status="results_added",
                message="实验结果已添加",
                data=request.data
            )
        else:
            raise ValueError(f"不支持的操作: {request.action}")
    
    except Exception as e:
        logger.error(f"迭代优化失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks")
async def list_tasks():
    """
    列出所有活动任务
    """
    try:
        tasks = workflow_manager.list_active_tasks()
        return {
            "total": len(tasks),
            "tasks": tasks
        }
    except Exception as e:
        logger.error(f"列出任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket路由
@app.websocket("/ws")
async def websocket_general_endpoint(websocket: WebSocket):
    """
    通用WebSocket端点 - 支持动态任务创建和管理
    """
    client_id = f"CLIENT_{uuid.uuid4().hex[:8]}"
    await manager.connect(websocket, client_id)
    current_task_id = None
    
    try:
        # 发送初始连接确认
        await manager.send_json({
            "type": "connected",
            "status": "success",
            "client_id": client_id,
            "message": "WebSocket连接成功"
        }, client_id)
        
        # 保持连接并处理消息
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            logger.info(f"收到客户端消息: {data.get('type')}")
            
            # 处理不同类型的消息
            if data["type"] == "ping":
                # 心跳检测
                await manager.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, client_id)
            
            elif data["type"] == "reconnect":
                # 重连并恢复任务
                task_id = data.get("task_id")
                if task_id:
                    try:
                        # 尝试获取任务状态
                        state = workflow_manager.get_task_state(task_id)
                        
                        # 重新绑定任务到新客户端
                        manager.rebind_task(client_id, task_id)
                        current_task_id = task_id
                        
                        # 发送任务状态恢复确认
                        await manager.send_json({
                            "type": "task_restored",
                            "task_id": task_id,
                            "state": {
                                "current_step": state.get("current_step"),
                                "workflow_status": state.get("workflow_status"),
                                "performance_prediction": state.get("performance_prediction"),
                                "optimization_suggestions": state.get("optimization_suggestions"),
                                "optimization_contents": state.get("optimization_contents")
                            },
                            "message": f"任务 {task_id} 已恢复"
                        }, client_id)
                        logger.info(f"任务 {task_id} 已恢复到客户端 {client_id}")
                        
                    except ValueError:
                        await manager.send_json({
                            "type": "error",
                            "message": f"任务 {task_id} 不存在或已过期"
                        }, client_id)
                else:
                    await manager.send_json({
                        "type": "error",
                        "message": "缺少任务ID，无法恢复"
                    }, client_id)
            
            elif data["type"] == "start_workflow":
                # 启动新的工作流任务
                current_task_id = f"TASK_{uuid.uuid4().hex[:8]}"
                thread_id = f"THREAD_{uuid.uuid4().hex[:8]}"
                
                # 绑定任务到客户端
                manager.bind_task(client_id, current_task_id)
                
                await manager.send_json({
                    "type": "status",
                    "node": "system",
                    "message": f"正在创建任务 {current_task_id}..."
                }, client_id)
                
                # 异步执行工作流并流式返回结果
                asyncio.create_task(
                    execute_workflow_stream(current_task_id, thread_id, data.get("data"), client_id)
                )
            
            elif data["type"] == "select_optimization":
                # 用户选择优化方案
                # 优先使用current_task_id，如果为空则从manager获取
                task_id_to_use = current_task_id or manager.get_task_id(client_id)
                
                if task_id_to_use:
                    await manager.send_json({
                        "type": "status",
                        "task_id": task_id_to_use,
                        "node": "optimization",
                        "message": "已接收优化方案选择，继续执行工作流..."
                    }, client_id)
                    
                    # 更新任务选择
                    try:
                        workflow_manager.update_task_selection(
                            task_id_to_use,
                            data["data"]
                        )
                        
                        # 继续执行工作流
                        asyncio.create_task(
                            continue_workflow_after_selection(task_id_to_use, client_id)
                        )
                        
                        # 更新局部变量
                        current_task_id = task_id_to_use
                    except ValueError as e:
                        logger.error(f"更新任务选择失败: {str(e)}")
                        await manager.send_json({
                            "type": "error",
                            "message": f"任务不存在或已过期，请重新提交"
                        }, client_id)
                else:
                    await manager.send_json({
                        "type": "error",
                        "message": "没有活动的任务，请先提交涂层数据"
                    }, client_id)
            
            elif data["type"] == "get_state":
                # 获取当前任务状态
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


@app.websocket("/ws/coating/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """
    WebSocket端点 - 实时通信（带任务ID）
    """
    client_id = f"CLIENT_{uuid.uuid4().hex[:8]}"
    await manager.connect(websocket, client_id)
    
    try:
        # 发送初始连接确认
        await manager.send_json({
            "type": "connection",
            "status": "connected",
            "task_id": task_id,
            "client_id": client_id
        }, client_id)
        
        # 获取任务状态
        try:
            state = workflow_manager.get_task_state(task_id)
            await manager.send_json({
                "type": "state_update",
                "data": state
            }, client_id)
        except ValueError:
            # 任务不存在，创建新任务
            await manager.send_json({
                "type": "info",
                "message": "任务不存在，请先创建任务"
            }, client_id)
        
        # 保持连接并处理消息
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            
            # 处理不同类型的消息
            if data["type"] == "ping":
                # 心跳检测
                await manager.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, client_id)
            
            elif data["type"] == "get_state":
                # 获取当前状态
                state = workflow_manager.get_task_state(task_id)
                await manager.send_json({
                    "type": "state_update",
                    "data": state
                }, client_id)
            
            elif data["type"] == "stream_start":
                # 开始流式处理
                await stream_task_updates(task_id, client_id, data.get("input_data"))
            
            elif data["type"] == "user_input":
                # 处理用户输入（如选择优化方案）
                workflow_manager.update_task_selection(
                    task_id,
                    data["selection"]
                )
                await manager.send_json({
                    "type": "selection_confirmed",
                    "data": data["selection"]
                }, client_id)
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"WebSocket连接断开: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
        manager.disconnect(client_id)


async def process_task_async(task_id: str, input_data: Dict, thread_id: str):
    """
    异步处理任务
    """
    try:
        # 执行工作流
        result = await workflow_manager.start_task(
            task_id=task_id,
            input_data=input_data,
            thread_id=thread_id
        )
        logger.info(f"任务 {task_id} 处理完成")
    except Exception as e:
        logger.error(f"任务 {task_id} 处理失败: {str(e)}")


async def continue_workflow_after_selection(task_id: str, client_id: str):
    """
    用户选择后继续执行工作流 - 传递用户选择到interrupt
    """
    try:
        logger.info(f"继续执行任务 {task_id}")
        
        # 获取当前任务状态
        task_state = workflow_manager.get_task_state(task_id)
        thread_id = task_state.get("thread_id", task_id)
        selected_plan = task_state.get("selected_optimization_plan", {})
        
        logger.info(f"用户选择的方案: {selected_plan}")
        
        # 设置流式输出回调 - 动态获取客户端ID
        async def stream_callback(node: str, content: str):
            """LLM流式输出回调 - 动态获取最新客户端ID"""
            try:
                current_client = manager.get_client_id(task_id) or client_id
                await manager.send_json({
                    "type": "llm_stream",
                    "node": node,
                    "content": content
                }, current_client)
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"流式输出回调失败: {str(e)}")
        
        workflow_manager.set_stream_callback(stream_callback)
        
        # 使用Command恢复工作流，传递用户选择
        from langgraph.types import Command
        resume_command = Command(resume=selected_plan)
        logger.info(f"使用Command恢复工作流，传递选择: {selected_plan}")
        
        # 继续流式执行工作流，传递Command
        current_node = None
        async for chunk in workflow_manager.stream_task(task_id, resume_command, thread_id):
            # 多模式返回：("updates", data) 或 ("messages", data)
            if isinstance(chunk, tuple) and len(chunk) == 2:
                mode, data = chunk
                
                # 处理节点更新
                if mode == "updates":
                    if isinstance(data, dict):
                        for node_name, node_data in data.items():
                            # 处理中断（用户选择）
                            if node_name == "__interrupt__":
                                if isinstance(node_data, tuple) and len(node_data) > 0:
                                    interrupt_data = node_data[0] if isinstance(node_data, tuple) else node_data
                                    if isinstance(interrupt_data, dict) and interrupt_data.get("type") == "user_selection_required":
                                        logger.info(f"检测到工作流中断 - 等待用户选择")
                                        current_client = manager.get_client_id(task_id) or client_id
                                        await manager.send_json({
                                            "type": "await_user_selection",
                                            "task_id": task_id,
                                            "node": "user_selection",
                                            "message": interrupt_data.get("message", "请选择优化方案"),
                                            "suggestions": interrupt_data.get("suggestions", {}),
                                            "options": interrupt_data.get("options", []),
                                            "comprehensive_recommendation": interrupt_data.get("comprehensive_recommendation", "")
                                        }, current_client)
                                        logger.info(f"任务 {task_id} 已中断，等待用户选择")
                                        return
                                continue
                            
                            if node_name != "__interrupt__":
                                current_node = node_name
                                logger.info(f"节点更新: {node_name}")
                                
                                # 动态获取最新客户端
                                current_client = manager.get_client_id(task_id) or client_id
                                await manager.send_json({
                                    "type": "status",
                                    "node": node_name,
                                    "message": f"正在执行 {node_name}..."
                                }, current_client)
                                
                                if isinstance(node_data, dict):
                                    # 迭代结果 - 立即发送
                                    if "iteration_plan" in node_data:
                                        current_client = manager.get_client_id(task_id) or client_id
                                        await manager.send_json({
                                            "type": "node_result",
                                            "node": "iteration_result",
                                            "result": node_data
                                        }, current_client)
                                        logger.info("已发送迭代结果")
                                        await asyncio.sleep(0.1)
                                    
                                    # 最终总结 - 立即发送
                                    if "final_summary" in node_data:
                                        current_client = manager.get_client_id(task_id) or client_id
                                        await manager.send_json({
                                            "type": "node_result",
                                            "node": "result_summary",
                                            "result": node_data
                                        }, current_client)
                                        logger.info("已发送最终总结")
                                        await asyncio.sleep(0.1)
                
                # 处理LLM消息流
                elif mode == "messages":
                    if isinstance(data, tuple) and len(data) == 2:
                        message, metadata = data
                        if hasattr(message, 'content') and message.content:
                            current_client = manager.get_client_id(task_id) or client_id
                            await manager.send_json({
                                "type": "llm_stream",
                                "node": current_node or "unknown",
                                "content": message.content
                            }, current_client)
                            # 添加微小延迟，确保流式输出平滑
                            await asyncio.sleep(0.01)
            
            # 兼容旧格式
            elif isinstance(chunk, dict):
                for node_name, node_data in chunk.items():
                    if node_name != "__interrupt__":
                        current_node = node_name
                        logger.info(f"节点更新(兼容格式): {node_name}")
        
        current_client = manager.get_client_id(task_id) or client_id
        await manager.send_json({
            "type": "complete",
            "task_id": task_id,
            "message": "工作流全部完成"
        }, current_client)
        
    except Exception as e:
        logger.error(f"继续执行工作流失败: {str(e)}", exc_info=True)
        current_client = manager.get_client_id(task_id) or client_id
        await manager.send_json({
            "type": "error",
            "message": f"继续执行失败: {str(e)}"
        }, current_client)


async def execute_workflow_stream(task_id: str, thread_id: str, input_data: Dict, client_id: str):
    """
    执行工作流并流式发送结果
    """
    try:
        logger.info(f"开始执行工作流任务: {task_id}")
        
        # 辅助函数：动态获取当前客户端ID
        def get_current_client():
            return manager.get_client_id(task_id) or client_id
        
        # 通知开始执行
        await manager.send_json({
            "type": "status",
            "node": "workflow",
            "message": "工作流已启动"
        }, get_current_client())
        
        # 设置流式输出回调 - 直接通过WebSocket发送
        async def stream_callback(node: str, content: str):
            """LLM流式输出回调 - 动态获取最新客户端ID"""
            try:
                await manager.send_json({
                    "type": "llm_stream",
                    "node": node,
                    "content": content
                }, get_current_client())
                await asyncio.sleep(0.01)  # 小延迟确保平滑输出
            except Exception as e:
                logger.error(f"流式输出回调失败: {str(e)}")
        
        workflow_manager.set_stream_callback(stream_callback)
        
        # 使用workflow_manager流式执行任务
        current_node = None
        llm_streaming_node = None  # 跟踪LLM流式输出的节点
        async for event in workflow_manager.stream_task(task_id, input_data, thread_id):
            # astream_events返回：(event_type, data)
            if isinstance(event, tuple) and len(event) == 2:
                event_type, data = event
                
                # 处理节点状态
                if event_type == "status":
                    node_name = data.get("node")
                    if node_name:
                        current_node = node_name
                        # 只有LLM节点才设置llm_streaming_node
                        if node_name in ["integrated_analysis", "p1_composition_optimization", 
                                        "p2_structure_optimization", "p3_process_optimization"]:
                            llm_streaming_node = node_name
                            logger.info(f"设置LLM流式输出节点: {node_name}")
                        
                        # 发送节点状态
                        await manager.send_json({
                            "type": "status",
                            "task_id": task_id,
                            "node": node_name,
                            "message": f"正在执行 {node_name}..."
                        }, get_current_client())
                
                # 处理节点更新
                elif event_type == "updates":
                    if isinstance(data, dict):
                        for node_name, node_data in data.items():
                            # 处理中断（用户选择）
                            if node_name == "__interrupt__":
                                if isinstance(node_data, tuple) and len(node_data) > 0:
                                    interrupt_data = node_data[0] if isinstance(node_data, tuple) else node_data
                                    if isinstance(interrupt_data, dict) and interrupt_data.get("type") == "user_selection_required":
                                        logger.info(f"检测到工作流中断 - 等待用户选择")
                                        await manager.send_json({
                                            "type": "await_user_selection",
                                            "task_id": task_id,
                                            "node": "user_selection",
                                            "message": interrupt_data.get("message", "请选择优化方案"),
                                            "suggestions": interrupt_data.get("suggestions", {}),
                                            "options": interrupt_data.get("options", []),
                                            "comprehensive_recommendation": interrupt_data.get("comprehensive_recommendation", "")
                                        }, get_current_client())
                                        logger.info(f"任务 {task_id} 已中断，等待用户选择")
                                        return
                                continue
                            
                            if node_name != "__interrupt__":
                                current_node = node_name
                                # 只有LLM节点才设置llm_streaming_node
                                if node_name in ["integrated_analysis", "p1_composition_optimization", 
                                                "p2_structure_optimization", "p3_process_optimization"]:
                                    llm_streaming_node = node_name
                                    logger.info(f"设置LLM流式输出节点: {node_name}")
                                logger.info(f"节点更新: {node_name}")
                                
                                # 发送节点状态
                                await manager.send_json({
                                    "type": "status",
                                    "task_id": task_id,
                                    "node": node_name,
                                    "message": f"正在执行 {node_name}..."
                                }, get_current_client())
                                
                                # 检查节点数据中的关键结果 - 立即发送，不等待
                                if isinstance(node_data, dict):
                                    # 输入验证完成 - 只记录日志，不发送额外消息
                                    if node_name == "input_validation":
                                        if node_data.get("input_validated"):
                                            logger.info("输入验证完成")
                                            # 不再发送额外的node_result，由前端根据status自动创建消息
                                    
                                    # TopPhi模拟完成
                                    if node_name == "topphi_simulation" and "topphi_simulation" in node_data:
                                        await manager.send_json({
                                            "type": "node_result",
                                            "node": "topphi_simulation",
                                            "result": node_data.get("topphi_simulation")
                                        }, get_current_client())
                                        logger.info("已发送TopPhi模拟结果")
                                        await asyncio.sleep(0.3)  # 增加延迟让前端有时间渲染
                                    
                                    # ML模型预测完成
                                    if node_name == "ml_prediction" and "ml_prediction" in node_data:
                                        await manager.send_json({
                                            "type": "node_result",
                                            "node": "ml_prediction",
                                            "result": node_data.get("ml_prediction")
                                        }, get_current_client())
                                        logger.info("已发送ML模型预测结果")
                                        await asyncio.sleep(0.3)
                                    
                                    # 历史数据比对完成
                                    if node_name == "historical_comparison" and "historical_comparison" in node_data:
                                        await manager.send_json({
                                            "type": "node_result",
                                            "node": "historical_comparison",
                                            "result": node_data.get("historical_comparison")
                                        }, get_current_client())
                                        logger.info("已发送历史数据比对结果")
                                        await asyncio.sleep(0.3)
                                    
                                    # 综合分析完成 - 性能预测最终结果
                                    if node_name == "integrated_analysis" and "performance_prediction" in node_data:
                                        await manager.send_json({
                                            "type": "node_result",
                                            "node": "performance_prediction",
                                            "result": {
                                                "performance_prediction": node_data.get("performance_prediction"),
                                                "root_cause_analysis": node_data.get("root_cause_analysis", "")
                                            }
                                        }, get_current_client())
                                        logger.info("已发送性能预测结果")
                                        await asyncio.sleep(0.1)
                                    
                                    # P1成分优化完成 - 发送内容
                                    if node_name == "p1_composition_optimization" and "p1_content" in node_data:
                                        logger.info("P1成分优化完成")
                                        await manager.send_json({
                                            "type": "node_result",
                                            "node": "p1_composition_optimization",
                                            "result": {
                                                "content": node_data.get("p1_content"),
                                                "suggestions": node_data.get("p1_suggestions", [])
                                            }
                                        }, get_current_client())
                                        await asyncio.sleep(0.1)
                                    
                                    # P2结构优化完成 - 发送内容
                                    if node_name == "p2_structure_optimization" and "p2_content" in node_data:
                                        logger.info("P2结构优化完成")
                                        await manager.send_json({
                                            "type": "node_result",
                                            "node": "p2_structure_optimization",
                                            "result": {
                                                "content": node_data.get("p2_content"),
                                                "suggestions": node_data.get("p2_suggestions", [])
                                            }
                                        }, get_current_client())
                                        await asyncio.sleep(0.1)
                                    
                                    # P3工艺优化完成 - 发送内容
                                    if node_name == "p3_process_optimization" and "p3_content" in node_data:
                                        logger.info("P3工艺优化完成")
                                        await manager.send_json({
                                            "type": "node_result",
                                            "node": "p3_process_optimization",
                                            "result": {
                                                "content": node_data.get("p3_content"),
                                                "suggestions": node_data.get("p3_suggestions", [])
                                            }
                                        }, get_current_client())
                                        await asyncio.sleep(0.1)
                                    
                                    # 优化建议汇总完成 - 立即发送
                                    if node_name == "optimization_summary" and "optimization_suggestions" in node_data:
                                        await manager.send_json({
                                            "type": "node_result",
                                            "node": "optimization_suggestion",
                                            "result": {
                                                "optimization_suggestions": node_data.get("optimization_suggestions")
                                            }
                                        }, get_current_client())
                                        logger.info("已发送优化建议")
                                        await asyncio.sleep(0.1)
                                    
                                    # 等待用户选择
                                    if node_data.get("workflow_status") == "awaiting_optimization_selection":
                                        await manager.send_json({
                                            "type": "await_user_selection",
                                            "task_id": task_id,
                                            "node": "user_selection",
                                            "message": "请选择优化方案"
                                        }, get_current_client())
                                        logger.info(f"任务 {task_id} 等待用户选择")
                                        # 工作流暂停，等待用户输入
                                        return
                
                # 处理LLM流式输出 - 这是关键！
                elif event_type == "llm_stream":
                    chunk = data.get("chunk")
                    metadata = data.get("metadata", {})
                    
                    if chunk and hasattr(chunk, 'content') and chunk.content:
                        # 使用llm_streaming_node确定目标节点
                        target_node = llm_streaming_node or current_node or "unknown"
                        
                        # 只有当目标节点是LLM节点时才发送流式输出
                        if target_node in ["integrated_analysis", "p1_composition_optimization", 
                                         "p2_structure_optimization", "p3_process_optimization"]:
                            content_preview = chunk.content[:50] if len(chunk.content) > 50 else chunk.content
                            logger.info(f"[LLM流式] 节点={target_node} 内容长度={len(chunk.content)} 预览=[{content_preview}...]")
                            await manager.send_json({
                                "type": "llm_stream",
                                "node": target_node,
                                "content": chunk.content
                            }, get_current_client())
                            # 添加微小延迟，确保流式输出平滑
                            await asyncio.sleep(0.01)
                        else:
                            logger.warning(f"[LLM流式] 忽略非LLM节点 {target_node} 的流式输出")
                
                # LLM开始
                elif event_type == "llm_start":
                    logger.info(f"[LLM开始] 节点={llm_streaming_node or current_node}")
                
                # LLM结束
                elif event_type == "llm_end":
                    logger.info(f"[LLM结束] 节点={llm_streaming_node or current_node}")
            
            # 兼容旧格式
            elif isinstance(chunk, dict):
                for node_name, node_data in chunk.items():
                    if node_name != "__interrupt__":
                        current_node = node_name
                        logger.info(f"节点更新(兼容格式): {node_name}")
        
        # 发送完成信号
        await manager.send_json({
            "type": "complete",
            "task_id": task_id,
            "message": "工作流执行完成"
        }, get_current_client())
        
        logger.info(f"工作流任务完成: {task_id}")
        
    except Exception as e:
        logger.error(f"工作流执行失败: {str(e)}", exc_info=True)
        await manager.send_json({
            "type": "error",
            "message": f"工作流执行失败: {str(e)}"
        }, get_current_client())


async def stream_task_updates(task_id: str, client_id: str, input_data: Optional[Dict] = None):
    """
    流式发送任务更新
    """
    try:
        # 流式执行工作流
        async for chunk in workflow_manager.stream_task(task_id, input_data):
            # 发送更新到客户端
            await manager.send_json({
                "type": "stream_update",
                "data": chunk
            }, client_id)
            
            # 如果是消息类型，特殊处理
            if "messages" in chunk:
                for msg in chunk["messages"]:
                    await manager.send_json({
                        "type": "message",
                        "content": msg.content if hasattr(msg, 'content') else str(msg)
                    }, client_id)
        
        # 发送完成信号
        await manager.send_json({
            "type": "stream_complete",
            "task_id": task_id
        }, client_id)
    
    except Exception as e:
        logger.error(f"流式更新失败: {str(e)}")
        await manager.send_json({
            "type": "error",
            "message": str(e)
        }, client_id)


# 错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    全局异常处理
    """
    logger.error(f"全局异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
