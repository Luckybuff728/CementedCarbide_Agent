"""
自定义异常类
"""
from typing import Optional, Dict, Any


class TopMatError(Exception):
    """TopMat系统基础异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class ValidationError(TopMatError):
    """输入验证异常"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["invalid_value"] = value
        super().__init__(message, details)


class WorkflowError(TopMatError):
    """工作流执行异常"""
    
    def __init__(self, message: str, node: Optional[str] = None, state: Optional[Dict] = None):
        details = {}
        if node:
            details["failed_node"] = node
        if state:
            details["current_state"] = state
        super().__init__(message, details)


class OptimizationError(TopMatError):
    """优化建议生成异常"""
    
    def __init__(self, message: str, optimization_type: Optional[str] = None):
        details = {}
        if optimization_type:
            details["optimization_type"] = optimization_type
        super().__init__(message, details)


class MCPError(TopMatError):
    """MCP工具调用异常"""
    
    def __init__(self, message: str, tool_name: Optional[str] = None, server: Optional[str] = None):
        details = {}
        if tool_name:
            details["tool_name"] = tool_name
        if server:
            details["server"] = server
        super().__init__(message, details)
