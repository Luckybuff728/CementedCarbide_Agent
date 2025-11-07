"""
WebSocket连接管理器
"""
import logging
from typing import Dict
from fastapi import WebSocket
import time

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器 - 负责连接、任务绑定、消息发送"""
    
    def __init__(self):
        # 活动连接
        self.active_connections: Dict[str, WebSocket] = {}
        # 客户端->任务映射
        self.client_tasks: Dict[str, str] = {}
        # 任务->客户端映射（反向索引）
        self.task_clients: Dict[str, str] = {}
        # 任务最后活动时间
        self.task_last_active: Dict[str, float] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """建立WebSocket连接"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"客户端 {client_id} 已连接")
    
    def disconnect(self, client_id: str):
        """断开连接 - 完整清理所有映射关系"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"客户端 {client_id} 已断开")
        
        # ✅ 清理task映射
        if client_id in self.client_tasks:
            task_id = self.client_tasks[client_id]
            del self.client_tasks[client_id]
            
            # ✅ 同时清理反向映射
            if task_id in self.task_clients:
                del self.task_clients[task_id]
            if task_id in self.task_last_active:
                del self.task_last_active[task_id]
            
            logger.info(f"清理任务映射: task_id={task_id}")
    
    def bind_task(self, client_id: str, task_id: str):
        """绑定客户端到任务"""
        self.client_tasks[client_id] = task_id
        self.task_clients[task_id] = client_id
        self.task_last_active[task_id] = time.time()
        logger.info(f"绑定任务: client={client_id}, task={task_id}")
    
    def rebind_task(self, client_id: str, task_id: str):
        """重新绑定任务（用于重连）"""
        # 如果该任务已绑定到其他客户端，先解绑
        if task_id in self.task_clients:
            old_client = self.task_clients[task_id]
            if old_client in self.client_tasks:
                del self.client_tasks[old_client]
        
        # 绑定到新客户端
        self.bind_task(client_id, task_id)
    
    def unbind_task(self, task_id: str):
        """主动解绑任务（任务完成时调用）"""
        if task_id in self.task_clients:
            client_id = self.task_clients[task_id]
            
            # 清理双向映射
            if client_id in self.client_tasks:
                del self.client_tasks[client_id]
            del self.task_clients[task_id]
            
            if task_id in self.task_last_active:
                del self.task_last_active[task_id]
            
            logger.info(f"任务 {task_id} 已解绑")
    
    def get_task_id(self, client_id: str) -> str:
        """获取客户端绑定的任务ID"""
        return self.client_tasks.get(client_id)
    
    def get_client_id(self, task_id: str) -> str:
        """获取任务绑定的客户端ID"""
        return self.task_clients.get(task_id)
    
    def update_task_activity(self, task_id: str):
        """更新任务活动时间"""
        self.task_last_active[task_id] = time.time()
    
    def cleanup_stale_tasks(self, max_age_seconds: int = 7200):
        """清理2小时无活动的任务"""
        current_time = time.time()
        stale_tasks = [
            task_id for task_id, last_active in self.task_last_active.items()
            if current_time - last_active > max_age_seconds
        ]
        
        for task_id in stale_tasks:
            self.unbind_task(task_id)
            logger.warning(f"清理过期任务: {task_id}")
        
        return len(stale_tasks)
    
    async def send_json(self, message: dict, client_id: str):
        """发送JSON消息给客户端"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"发送消息失败: client={client_id}, error={str(e)}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict):
        """广播消息给所有客户端"""
        for client_id in list(self.active_connections.keys()):
            await self.send_json(message, client_id)


# 全局单例
manager = ConnectionManager()
