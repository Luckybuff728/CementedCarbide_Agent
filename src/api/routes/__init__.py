"""
API路由模块
"""

from .vtk_routes import router as vtk_router
from .auth_routes import router as auth_router
from ..websocket.routes import setup_websocket_routes

__all__ = [
    "vtk_router",
    "auth_router",
    "setup_websocket_routes"
]
