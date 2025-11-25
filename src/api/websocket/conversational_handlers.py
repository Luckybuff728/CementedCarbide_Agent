"""
对话式Agent的WebSocket处理器

支持与ConversationalSupervisor进行多轮对话
"""

from typing import Dict, Any, Optional
from fastapi import WebSocket
import logging
import json
import asyncio

logger = logging.getLogger(__name__)


class ConversationalAgentHandler:
    """
    对话式Agent的WebSocket处理器
    
    职责：
    1. 管理WebSocket连接
    2. 转发用户消息给ConversationalSupervisor
    3. 将AI回复发送给前端
    4. 管理会话状态
    """
    
    def __init__(self):
        # 存储活跃的会话
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def handle_connection(self, websocket: WebSocket, session_id: str):
        """
        处理新的WebSocket连接
        
        Args:
            websocket: WebSocket连接
            session_id: 会话ID
        """
        await websocket.accept()
        logger.info(f"[ConversationalHandler] 新连接: {session_id}")
        
        # 延迟导入，避免循环依赖
        from ...agents.conversational_supervisor import get_conversational_supervisor
        
        # 获取或创建Supervisor
        supervisor = get_conversational_supervisor()
        
        # 存储会话信息
        self.active_sessions[session_id] = {
            "websocket": websocket,
            "supervisor": supervisor
        }
        
        try:
            # 发送欢迎消息
            await self._send_message(websocket, {
                "type": "ai_message",
                "content": "你好！我是 TopMat 涂层优化助手。\n\n"
                          "我可以帮你：\n"
                          "- 🔍 验证涂层参数\n"
                          "- 📊 分析涂层性能\n"
                          "- 🎯 生成优化方案\n"
                          "- 📋 生成实验工单\n\n"
                          "请告诉我你的涂层参数，或者直接说你想做什么。"
            })
            
            # 消息循环
            while True:
                try:
                    data = await websocket.receive_json()
                    await self._handle_message(websocket, session_id, data)
                except Exception as e:
                    if "disconnect" in str(e).lower():
                        break
                    logger.error(f"[ConversationalHandler] 消息处理错误: {e}")
                    await self._send_error(websocket, str(e))
        
        except Exception as e:
            logger.error(f"[ConversationalHandler] 连接错误: {e}")
        
        finally:
            # 清理会话
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            logger.info(f"[ConversationalHandler] 连接关闭: {session_id}")
    
    async def _handle_message(self, websocket: WebSocket, session_id: str, data: Dict[str, Any]):
        """
        处理用户消息
        
        Args:
            websocket: WebSocket连接
            session_id: 会话ID
            data: 消息数据
        """
        msg_type = data.get("type", "chat")
        
        if msg_type == "chat":
            await self._handle_chat(websocket, session_id, data)
        
        elif msg_type == "set_params":
            await self._handle_set_params(websocket, session_id, data)
        
        elif msg_type == "reset":
            await self._handle_reset(websocket, session_id)
        
        elif msg_type == "get_state":
            await self._handle_get_state(websocket, session_id)
        
        else:
            await self._send_error(websocket, f"未知消息类型: {msg_type}")
    
    async def _handle_chat(self, websocket: WebSocket, session_id: str, data: Dict[str, Any]):
        """处理聊天消息"""
        user_message = data.get("content", "")
        
        if not user_message.strip():
            return
        
        logger.info(f"[ConversationalHandler] 用户消息: {user_message[:50]}...")
        
        # 发送"正在思考"状态
        await self._send_message(websocket, {
            "type": "status",
            "status": "thinking",
            "message": "正在思考..."
        })
        
        try:
            # 获取Supervisor
            session = self.active_sessions.get(session_id)
            if not session:
                await self._send_error(websocket, "会话已过期，请刷新页面")
                return
            
            supervisor = session["supervisor"]
            
            # 调用Supervisor处理消息
            response = await supervisor.chat(user_message, session_id)
            
            # 发送AI回复
            await self._send_message(websocket, {
                "type": "ai_message",
                "content": response
            })
            
            # 发送更新后的状态
            await self._send_message(websocket, {
                "type": "state_update",
                "state": supervisor.get_session_state()
            })
        
        except Exception as e:
            logger.error(f"[ConversationalHandler] 处理错误: {e}", exc_info=True)
            await self._send_error(websocket, f"处理消息时出错: {str(e)}")
    
    async def _handle_set_params(self, websocket: WebSocket, session_id: str, data: Dict[str, Any]):
        """
        处理参数设置（从前端表单直接设置参数）
        
        这允许用户通过表单输入参数，而不必在对话中描述
        """
        session = self.active_sessions.get(session_id)
        if not session:
            await self._send_error(websocket, "会话已过期")
            return
        
        supervisor = session["supervisor"]
        
        # 更新会话状态
        if "coating_composition" in data:
            supervisor.session_state["coating_composition"] = data["coating_composition"]
        if "process_params" in data:
            supervisor.session_state["process_params"] = data["process_params"]
        if "structure_design" in data:
            supervisor.session_state["structure_design"] = data["structure_design"]
        if "target_requirements" in data:
            supervisor.session_state["target_requirements"] = data["target_requirements"]
        
        await self._send_message(websocket, {
            "type": "ai_message",
            "content": "✅ 参数已更新。你可以让我验证参数、进行分析，或者直接生成优化方案。"
        })
        
        await self._send_message(websocket, {
            "type": "state_update",
            "state": supervisor.get_session_state()
        })
    
    async def _handle_reset(self, websocket: WebSocket, session_id: str):
        """处理重置请求"""
        session = self.active_sessions.get(session_id)
        if session:
            session["supervisor"].reset_session()
        
        await self._send_message(websocket, {
            "type": "ai_message",
            "content": "会话已重置。请告诉我你的涂层参数，我们重新开始。"
        })
        
        await self._send_message(websocket, {
            "type": "state_update",
            "state": {}
        })
    
    async def _handle_get_state(self, websocket: WebSocket, session_id: str):
        """获取当前状态"""
        session = self.active_sessions.get(session_id)
        state = session["supervisor"].get_session_state() if session else {}
        
        await self._send_message(websocket, {
            "type": "state_update",
            "state": state
        })
    
    async def _send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """发送消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"[ConversationalHandler] 发送消息失败: {e}")
    
    async def _send_error(self, websocket: WebSocket, error: str):
        """发送错误消息"""
        await self._send_message(websocket, {
            "type": "error",
            "message": error
        })


# 全局单例
_handler_instance: Optional[ConversationalAgentHandler] = None


def get_conversational_handler() -> ConversationalAgentHandler:
    """获取对话式Handler单例"""
    global _handler_instance
    if _handler_instance is None:
        _handler_instance = ConversationalAgentHandler()
    return _handler_instance
