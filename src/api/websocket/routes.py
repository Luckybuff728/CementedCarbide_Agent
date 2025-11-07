"""
WebSocket路由注册
"""
import logging
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from .manager import manager
from .handlers import handle_websocket_message

logger = logging.getLogger(__name__)


def setup_websocket_routes(app):
    """
    设置WebSocket路由
    
    Args:
        app: FastAPI应用实例
    """
    
    @app.websocket("/ws/coating")
    async def websocket_endpoint(websocket: WebSocket):
        """
        主WebSocket端点 - 实时通信
        
        连接流程：
        1. 客户端连接
        2. 发送连接确认
        3. 循环接收消息并路由处理
        4. 断开时清理资源
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
