"""
WebSocket模块 - 拆分后的WebSocket功能模块
"""
from .manager import ConnectionManager
from .routes import setup_websocket_routes

__all__ = ["ConnectionManager", "setup_websocket_routes"]
