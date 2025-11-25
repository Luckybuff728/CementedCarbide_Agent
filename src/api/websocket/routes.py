"""
WebSocket路由注册

包含两种模式：
1. /ws/coating - 原有的单一工作流模式
2. /ws/coating/agent - 多Agent模式（Supervisor-Workers）
"""
import logging
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from .manager import manager
from .handlers import handle_websocket_message
from .multi_agent_handlers import handle_multi_agent_message
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
            
            # 发送系统欢迎消息（引导用户操作）
            welcome_message = """👋 **欢迎使用 TopMat 涂层优化智能助手！**

我是由多个专业AI Agent协作的智能系统，可以帮助您优化AlTiN涂层配方。

---

🎯 **我能做什么：**
- **参数验证** - 检查您输入的涂层成分、工艺参数是否合理
- **性能分析** - 通过TopPhi相场模拟和ML预测分析涂层性能
- **优化建议** - 提供成分优化(P1)、结构优化(P2)、工艺优化(P3)三类方案
- **实验管理** - 生成实验工单，记录并分析实验结果

---

📝 **如何开始：**
1. 在左侧面板填写您的涂层参数（或选择示例场景快速开始）
2. 点击「开始分析」按钮提交
3. 我将自动进行分析并与您对话，您可以随时提问或调整方向

准备好了吗？请在左侧填写参数后开始！"""
            
            await manager.send_json({
                "type": "system_welcome",
                "content": welcome_message,
                "timestamp": None  # 前端会自动添加时间戳
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
