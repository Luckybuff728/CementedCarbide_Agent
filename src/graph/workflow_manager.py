"""
全局工作流管理器实例
"""
from .workflow import CoatingWorkflowManager

# 全局工作流管理器实例
workflow_manager = CoatingWorkflowManager(use_memory=True)

__all__ = ["workflow_manager"]
