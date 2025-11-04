"""
统一错误处理器
"""
import logging
from typing import Dict, Any, Optional
from .exceptions import TopMatError, ValidationError, WorkflowError, OptimizationError, MCPError

logger = logging.getLogger(__name__)


class ErrorHandler:
    """统一错误处理器"""
    
    @staticmethod
    def handle_validation_error(errors: list, context: Optional[Dict] = None) -> Dict[str, Any]:
        """处理验证错误"""
        error_message = "输入验证失败:\n" + "\n".join(errors)
        
        logger.error(f"验证错误: {errors}")
        if context:
            logger.error(f"上下文: {context}")
        
        return {
            "error_type": "ValidationError",
            "error_message": error_message,
            "validation_errors": errors,
            "workflow_status": "validation_failed",
            "current_step": "error",
            "next_step": None,
            "recovery_suggestions": [
                "检查输入参数的格式和范围",
                "确保所有必需字段都已填写",
                "验证数值的合理性"
            ]
        }
    
    @staticmethod
    def handle_workflow_error(error: Exception, node: str, state: Dict) -> Dict[str, Any]:
        """处理工作流执行错误"""
        error_message = f"工作流节点 {node} 执行失败: {str(error)}"
        
        logger.error(f"工作流错误 - 节点: {node}, 错误: {str(error)}", exc_info=True)
        
        return {
            "error_type": "WorkflowError",
            "error_message": error_message,
            "failed_node": node,
            "workflow_status": "error",
            "current_step": "error",
            "next_step": None,
            "recovery_suggestions": [
                "检查输入数据的完整性",
                "稍后重试该节点",
                "联系技术支持"
            ]
        }
    
    @staticmethod
    def handle_optimization_error(error: Exception, opt_type: str) -> Dict[str, Any]:
        """处理优化建议生成错误"""
        error_message = f"{opt_type}优化建议生成失败: {str(error)}"
        
        logger.error(f"优化错误 - 类型: {opt_type}, 错误: {str(error)}", exc_info=True)
        
        return {
            "error_type": "OptimizationError", 
            "error_message": error_message,
            "optimization_type": opt_type,
            "fallback_suggestion": f"系统正在重新生成{opt_type}建议，请稍候...",
            "recovery_suggestions": [
                "检查性能预测结果是否完整",
                "重新生成优化建议",
                "使用默认优化策略"
            ]
        }
    
    @staticmethod
    def handle_mcp_error(error: Exception, tool_name: str, server: str) -> Dict[str, Any]:
        """处理MCP工具调用错误"""
        error_message = f"MCP工具 {tool_name} 调用失败: {str(error)}"
        
        logger.error(f"MCP错误 - 工具: {tool_name}, 服务器: {server}, 错误: {str(error)}", exc_info=True)
        
        return {
            "error_type": "MCPError",
            "error_message": error_message,
            "tool_name": tool_name,
            "server": server,
            "fallback_mode": True,
            "recovery_suggestions": [
                "检查MCP服务器连接状态",
                "使用降级模式继续执行",
                "稍后重试MCP调用"
            ]
        }
    
    @staticmethod
    def create_safe_wrapper(func, error_type: str = "WorkflowError"):
        """创建安全包装器，捕获异常并返回错误状态"""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except TopMatError as e:
                logger.error(f"TopMat错误: {e.message}")
                return e.to_dict()
            except Exception as e:
                logger.error(f"未预期错误: {str(e)}", exc_info=True)
                return {
                    "error_type": error_type,
                    "error_message": f"执行失败: {str(e)}",
                    "workflow_status": "error"
                }
        return wrapper
