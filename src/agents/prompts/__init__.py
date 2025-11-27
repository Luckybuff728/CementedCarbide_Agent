"""
Agent 模块 - 基于 create_react_agent 创建真正的 Agent

设计原则：
1. 每个 Agent 是一个独立的 ReAct Agent，拥有自己的工具集
2. Agent 可以自主决定调用哪些工具、调用顺序
3. 使用官方 create_react_agent 而非纯函数节点
4. 支持 Handoff 工具进行 Agent 间任务转交
"""

from .validator import create_validator_agent
from .analyst import create_analyst_agent
from .optimizer import create_optimizer_agent
from .experimenter import create_experimenter_agent
from .supervisor import create_supervisor

__all__ = [
    "create_validator_agent",
    "create_analyst_agent",
    "create_optimizer_agent",
    "create_experimenter_agent",
    "create_supervisor",
]
