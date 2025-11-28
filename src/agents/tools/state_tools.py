"""
状态更新工具 - 使用 Command 更新 Agent 状态

使用 langgraph.types.Command 实现真正的状态更新。
状态更新后，所有后续工具和上下文都使用新值。
"""
from typing import Dict, Any
from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage
from langgraph.types import Command
import logging

logger = logging.getLogger(__name__)

@tool
def update_params(
    runtime: ToolRuntime,
    coating_composition: Dict[str, Any] = None,
    process_params: Dict[str, Any] = None,
    structure_design: Dict[str, Any] = None,
    target_requirements: Dict[str, Any] = None,
) -> Command:
    """
    更新涂层参数。当用户要求修改参数后再预测/模拟时，先调用此工具更新参数。

    支持一次更新多个类别的参数，只传递需要修改的字段。

    Args:
        coating_composition: 成分参数 {"al_content": 28, "ti_content": 22, "n_content": 50}
        process_params: 工艺参数 {"deposition_temperature": 500, "bias_voltage": -120}
        structure_design: 结构设计 {"structure_type": "multi_layer", "total_thickness": 3.0}
        target_requirements: 性能需求 {"working_temperature": 800}

    示例：
        # 用户: "把Al改成28%，温度改成500°C"
        update_params(
            coating_composition={"al_content": 28},
            process_params={"deposition_temperature": 500}
        )

    Returns:
        Command 更新状态
    """
    state = runtime.state
    updates = {}
    changes = []

    # 更新成分
    if coating_composition:
        current = dict(state.get("coating_composition", {}))
        for key, val in coating_composition.items():
            old_val = current.get(key, 0)
            current[key] = val
            changes.append(f"{key}: {old_val} → {val}")
        updates["coating_composition"] = current

    # 更新工艺
    if process_params:
        current = dict(state.get("process_params", {}))
        for key, val in process_params.items():
            old_val = current.get(key, 0)
            current[key] = val
            changes.append(f"{key}: {old_val} → {val}")
        updates["process_params"] = current

    # 更新结构
    if structure_design:
        current = dict(state.get("structure_design", {}))
        for key, val in structure_design.items():
            old_val = current.get(key, "")
            current[key] = val
            changes.append(f"{key}: {old_val} → {val}")
        updates["structure_design"] = current

    # 更新性能需求
    if target_requirements:
        current = dict(state.get("target_requirements", {}))
        for key, val in target_requirements.items():
            old_val = current.get(key, "")
            current[key] = val
            changes.append(f"{key}: {old_val} → {val}")
        updates["target_requirements"] = current

    change_msg = ', '.join(changes) if changes else "无变更"
    logger.info(f"[State] 参数更新: {change_msg}")

    # update 中必须包含 messages 以响应工具调用
    updates["messages"] = [
        ToolMessage(
            content=f"参数已更新: {change_msg}",
            tool_call_id=runtime.tool_call_id
        )
    ]
    
    return Command(update=updates)
