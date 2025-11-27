"""
WebSocket 路由注册

对话式多Agent系统 v2.0
"""
import logging
import uuid
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from .manager import manager
from .chat_handlers import handle_chat_message
from ..security import decode_token

logger = logging.getLogger(__name__)

# 存储每个客户端的后台任务
_client_tasks: dict = {}


def setup_websocket_routes(app):
    """
    设置 WebSocket 路由
    
    Args:
        app: FastAPI 应用实例
    """
    
    @app.websocket("/ws/coating/chat")
    async def websocket_chat_endpoint(websocket: WebSocket):
        """
        对话式多Agent WebSocket端点 (v2.0)
        
        特点：
        - 用户消息驱动，而非流程驱动
        - 智能路由到合适的专家
        - 每条消息独立处理，支持多轮对话
        - Agent 会主动与用户沟通，而非无脑执行
        
        消息类型：
        - chat_message: 发送对话消息
        - set_parameters: 设置涂层参数
        - get_session_state: 获取会话状态
        - clear_session: 清除会话
        """
        token = websocket.query_params.get("token")
        payload = decode_token(token) if token else None
        if not payload or "sub" not in payload:
            logger.warning("[Chat] 未授权的连接请求")
            await websocket.close(code=1008)
            return
        
        user_id = payload["sub"]
        client_id = f"CHAT_{uuid.uuid4().hex[:8]}_U{user_id}"
        session_id = f"SESSION_{uuid.uuid4().hex[:8]}"
        
        await manager.connect(websocket, client_id)
        
        try:
            # 发送连接确认
            await manager.send_json({
                "type": "connection",
                "status": "connected",
                "client_id": client_id,
                "session_id": session_id,
                "mode": "conversational",
                "message": "对话式智能助手已就绪"
            }, client_id)
            
            # 发送欢迎消息
            await manager.send_json({
                "type": "system_message",
                "content": """## 👋 欢迎使用 TopMat 涂层研发智能助手

我是专注于 **硬质合金涂层**（AlTiN 等）研发的多智能体系统，支持从参数验证到实验迭代的全流程。

---

### 🎯 核心能力

| 功能 | 说明 |
|:-----|:-----|
| **🛡️ 参数验证** | 检查成分配比、工艺参数的合理性，评估是否满足目标性能 |
| **📈 性能预测** | ML 模型预测硬度、结合力等指标；TopPhi 模拟微观结构 |
| **💡 方案优化** | 生成成分(P1) / 结构(P2) / 工艺(P3)优化方案 |
| **🔬 实验管理** | 生成实验工单，录入结果并分析，支持多轮迭代 |
| **💬 智能问答** | 解释预测结果、回答专业问题 |

---

### 💬 你可以这样问我

> - 帮我验证当前的涂层参数
> - 预测这个配方的硬度和结合力
> - 如何提高涂层的耐磨性？
> - 生成一份实验工单
> - 为什么预测的硬度是 28 GPa？

---

*💡 提示：可以先在左侧面板填写参数，我会基于这些参数进行分析。*"""
            }, client_id)
            
            # 初始化客户端任务列表
            _client_tasks[client_id] = []
            
            # 消息处理循环
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type", "unknown")
                logger.info(f"[Chat] 收到消息: {msg_type}")
                
                # ping/pong 心跳 - 立即响应，不阻塞
                if msg_type == "ping":
                    await manager.send_json({"type": "pong"}, client_id)
                    continue
                
                # 终止生成 - 取消所有正在进行的任务
                if msg_type == "stop_generate":
                    cancelled_count = 0
                    for task in _client_tasks.get(client_id, []):
                        if not task.done():
                            task.cancel()
                            cancelled_count += 1
                    _client_tasks[client_id] = []
                    logger.info(f"[Chat] 终止生成: 取消了 {cancelled_count} 个任务")
                    await manager.send_json({
                        "type": "generate_stopped",
                        "message": "生成已终止"
                    }, client_id)
                    continue
                
                # 发送新消息前，先取消之前未完成的任务（避免旧响应干扰新对话）
                if msg_type == "chat_message":
                    for task in _client_tasks.get(client_id, []):
                        if not task.done():
                            task.cancel()
                            logger.info(f"[Chat] 发送新消息，取消之前的任务")
                    _client_tasks[client_id] = []
                
                # 清理已完成的任务
                _client_tasks[client_id] = [
                    t for t in _client_tasks[client_id] if not t.done()
                ]
                
                # 将消息处理放入后台任务，避免阻塞心跳响应
                task = asyncio.create_task(
                    handle_chat_message(data, client_id, session_id)
                )
                _client_tasks[client_id].append(task)
        
        except WebSocketDisconnect:
            # 取消该客户端所有未完成的任务
            for task in _client_tasks.get(client_id, []):
                if not task.done():
                    task.cancel()
            _client_tasks.pop(client_id, None)
            manager.disconnect(client_id)
            logger.info(f"[Chat] 连接断开: {client_id}")
        except Exception as e:
            logger.error(f"[Chat] 错误: {str(e)}", exc_info=True)
            # 取消该客户端所有未完成的任务
            for task in _client_tasks.get(client_id, []):
                if not task.done():
                    task.cancel()
            _client_tasks.pop(client_id, None)
            await manager.send_json({
                "type": "error",
                "message": f"发生错误: {str(e)}"
            }, client_id)
            manager.disconnect(client_id)
