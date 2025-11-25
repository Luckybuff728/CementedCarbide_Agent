"""
WebSocket路由注册

包含三种模式：
1. /ws/coating - 原有的单一工作流模式
2. /ws/coating/agent - 多Agent模式（Supervisor-Workers）
3. /ws/coating/chat - 对话式Agent模式（推荐）
"""
import logging
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from .manager import manager
from .handlers import handle_websocket_message
from .multi_agent_handlers import handle_multi_agent_message
from .conversational_handlers import get_conversational_handler
from ..security import decode_token

logger = logging.getLogger(__name__)


def setup_websocket_routes(app):
    """
    设置WebSocket路由
    
    Args:
        app: FastAPI应用实例
    """
    
    @app.websocket("/ws/coating")
    async def websocket_endpoint(websocket: WebSocket):
        """主WebSocket端点 - 实时通信，要求客户端提供JWT token"""
        token = websocket.query_params.get("token")
        payload = decode_token(token) if token else None
        if not payload or "sub" not in payload:
            logger.warning("[WebSocket] 未授权的连接请求，缺少或无效的token")
            await websocket.close(code=1008)
            return

        user_id = payload["sub"]
        client_id = f"CLIENT_{uuid.uuid4().hex[:8]}_U{user_id}"
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
                
                # 路由到对应的handler
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
    
    @app.websocket("/ws/coating/agent")
    async def websocket_agent_endpoint(websocket: WebSocket):
        """
        多Agent模式WebSocket端点
        
        支持：
        1. LLM驱动的Supervisor-Workers架构
        2. 任意环节的多轮对话
        3. 动态路由和智能调度
        """
        token = websocket.query_params.get("token")
        payload = decode_token(token) if token else None
        if not payload or "sub" not in payload:
            logger.warning("[WebSocket Agent] 未授权的连接请求")
            await websocket.close(code=1008)
            return
        
        user_id = payload["sub"]
        client_id = f"AGENT_CLIENT_{uuid.uuid4().hex[:8]}_U{user_id}"
        await manager.connect(websocket, client_id)
        current_task_id = None
        
        try:
            # 发送连接确认
            await manager.send_json({
                "type": "connection",
                "status": "connected",
                "client_id": client_id,
                "mode": "multi-agent",
                "message": "多Agent系统已就绪"
            }, client_id)
            
            # 消息处理循环
            while True:
                data = await websocket.receive_json()
                logger.info(f"[Agent] 收到消息: {data.get('type')}")
                
                # 路由到多Agent处理器
                await handle_multi_agent_message(data, client_id, current_task_id)
                
                # 更新task_id
                if data["type"] == "start_agent_task":
                    current_task_id = manager.get_task_id(client_id)
        
        except WebSocketDisconnect:
            manager.disconnect(client_id)
            logger.info(f"[Agent] WebSocket连接断开: {client_id}")
        except Exception as e:
            logger.error(f"[Agent] WebSocket错误: {str(e)}", exc_info=True)
            await manager.send_json({
                "type": "error",
                "message": f"WebSocket错误: {str(e)}"
            }, client_id)
            manager.disconnect(client_id)
    
    @app.websocket("/ws/coating/chat")
    async def websocket_chat_endpoint(websocket: WebSocket):
        """
        对话式Agent WebSocket端点（推荐使用）
        
        特点：
        1. 自然多轮对话
        2. 根据用户意图自动调度Agent
        3. 主动引导用户下一步操作
        4. 无固定流程，灵活响应
        
        消息格式：
        - 发送: {"type": "chat", "content": "用户消息"}
        - 接收: {"type": "ai_message", "content": "AI回复"}
        """
        token = websocket.query_params.get("token")
        payload = decode_token(token) if token else None
        if not payload or "sub" not in payload:
            logger.warning("[Chat] 未授权的连接请求")
            await websocket.close(code=1008)
            return
        
        user_id = payload["sub"]
        session_id = f"CHAT_{uuid.uuid4().hex[:8]}_U{user_id}"
        
        logger.info(f"[Chat] 新的对话式Agent连接: {session_id}")
        
        # 使用对话式Handler处理连接
        handler = get_conversational_handler()
        await handler.handle_connection(websocket, session_id)
