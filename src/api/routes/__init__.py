"""
API路由模块
"""

from .vtk_routes import router as vtk_router
from ..websocket.routes import setup_websocket_routes

__all__ = [
    "vtk_router",
    "setup_websocket_routes"
]
