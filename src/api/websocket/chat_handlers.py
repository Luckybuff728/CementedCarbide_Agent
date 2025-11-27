"""
对话式多Agent WebSocket处理器 (v2.0)

设计理念：
- 用户消息驱动，而非任务驱动
- 每条消息独立处理，支持多轮对话
- 实时流式输出
"""
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from .manager import manager

logger = logging.getLogger(__name__)


async def handle_chat_message(data: Dict[str, Any], client_id: str, session_id: Optional[str] = None):
    """
    处理对话消息
    
    消息格式：
    {
        "type": "chat_message",
        "content": "用户消息内容",
        "session_id": "可选的会话ID",
        "context": {  // 可选的上下文数据
            "coating_composition": {...},
            "process_params": {...},
            "target_requirements": "..."
        }
    }
    """
    message_type = data.get("type")
    
    if message_type == "chat_message":
        await handle_user_message(data, client_id, session_id)
    elif message_type == "set_parameters":
        await handle_set_parameters(data, client_id, session_id)
    elif message_type == "get_session_state":
        await handle_get_session_state(data, client_id, session_id)
    elif message_type == "clear_session":
        await handle_clear_session(data, client_id, session_id)
    else:
        await manager.send_json({
            "type": "error",
            "message": f"未知的消息类型: {message_type}"
        }, client_id)


async def handle_user_message(data: Dict[str, Any], client_id: str, session_id: Optional[str] = None):
    """
    处理用户对话消息
    
    流程：
    1. 接收用户消息
    2. 路由到合适的专家
    3. 流式返回响应
    """
    user_content = data.get("content", "").strip()
    if not user_content:
        await manager.send_json({
            "type": "error",
            "message": "消息内容不能为空"
        }, client_id)
        return
    
    # 获取或生成会话ID
    session_id = session_id or data.get("session_id") or f"SESSION_{uuid.uuid4().hex[:8]}"
    context_data = data.get("context", {})
    
    logger.info(f"[Chat] 收到消息: session={session_id}, content={user_content[:50]}...")
    
    # 通知前端开始处理
    await manager.send_json({
        "type": "chat_start",
        "session_id": session_id,
        "timestamp": datetime.now().isoformat()
    }, client_id)
    
    try:
        # 获取对话管理器
        from ...agents.graph import get_conversational_manager
        chat_manager = get_conversational_manager()
        
        current_node = None
        full_response = ""
        
        # 流式处理
        async for event in chat_manager.chat(session_id, user_content, context_data):
            event_type = event.get("type")
            
            if event_type == "node_start":
                node = event.get("node")
                current_node = node
                await manager.send_json({
                    "type": "agent_start",
                    "agent": node,
                    "display_name": _get_agent_display_name(node)
                }, client_id)
            
            elif event_type == "node_end":
                node = event.get("node")
                await manager.send_json({
                    "type": "agent_end",
                    "agent": node
                }, client_id)
            
            elif event_type == "token":
                content = event.get("content", "")
                full_response += content
                await manager.send_json({
                    "type": "chat_token",
                    "content": content,
                    "agent": current_node
                }, client_id)
            
            elif event_type == "thinking_token":
                # 思考内容流式输出
                content = event.get("content", "")
                await manager.send_json({
                    "type": "thinking_token",
                    "content": content,
                    "agent": current_node
                }, client_id)
            
            elif event_type == "tool_start":
                tool = event.get("tool")
                await manager.send_json({
                    "type": "tool_start",
                    "tool": tool,
                    "display_name": _get_tool_display_name(tool)
                }, client_id)
            
            elif event_type == "tool_end":
                tool = event.get("tool")
                await manager.send_json({
                    "type": "tool_end",
                    "tool": tool
                }, client_id)
            
            elif event_type == "tool_result":
                tool = event.get("tool")
                result = event.get("result", {})
                logger.info(f"[Chat] 发送工具结果: {tool}")
                await manager.send_json({
                    "type": "tool_result",
                    "tool": tool,
                    "result": result,
                    "display_name": _get_tool_display_name(tool)
                }, client_id)
            
            elif event_type == "structured_content":
                # 发送提取的结构化内容（优化方案摘要、工单信息等）
                structured_data = event.get("data", {})
                logger.info(f"[Chat] 发送结构化内容: {structured_data.get('type')}")
                await manager.send_json({
                    "type": "structured_content",
                    "data": structured_data
                }, client_id)
            
            elif event_type == "done":
                await manager.send_json({
                    "type": "chat_complete",
                    "session_id": session_id,
                    "full_response": full_response
                }, client_id)
            
            elif event_type == "error":
                await manager.send_json({
                    "type": "chat_error",
                    "message": event.get("message", "未知错误")
                }, client_id)
        
        logger.info(f"[Chat] 消息处理完成: session={session_id}")
        
    except Exception as e:
        logger.error(f"[Chat] 处理失败: {e}", exc_info=True)
        await manager.send_json({
            "type": "chat_error",
            "message": str(e)
        }, client_id)


async def handle_set_parameters(data: Dict[str, Any], client_id: str, session_id: Optional[str] = None):
    """
    设置涂层参数到会话
    
    用户可以通过UI设置参数，然后在对话中引用
    """
    session_id = session_id or data.get("session_id")
    if not session_id:
        await manager.send_json({
            "type": "error",
            "message": "需要 session_id"
        }, client_id)
        return
    
    from ...agents.graph import get_conversational_manager
    chat_manager = get_conversational_manager()
    
    session = chat_manager.get_or_create_session(session_id)
    
    # 更新参数
    if "coating_composition" in data:
        session["coating_composition"] = data["coating_composition"]
    if "process_params" in data:
        session["process_params"] = data["process_params"]
    if "structure_design" in data:
        session["structure_design"] = data["structure_design"]
    if "target_requirements" in data:
        session["target_requirements"] = data["target_requirements"]
    
    await manager.send_json({
        "type": "parameters_set",
        "session_id": session_id,
        "message": "参数已更新"
    }, client_id)
    
    logger.info(f"[Chat] 参数已设置: session={session_id}")


async def handle_get_session_state(data: Dict[str, Any], client_id: str, session_id: Optional[str] = None):
    """获取当前会话状态"""
    session_id = session_id or data.get("session_id")
    if not session_id:
        await manager.send_json({
            "type": "error",
            "message": "需要 session_id"
        }, client_id)
        return
    
    from ...agents.graph import get_conversational_manager
    chat_manager = get_conversational_manager()
    
    state = chat_manager.get_session_state(session_id)
    
    # 过滤敏感/大型数据
    safe_state = {
        "session_id": session_id,
        "coating_composition": state.get("coating_composition", {}),
        "process_params": state.get("process_params", {}),
        "validation_passed": state.get("validation_passed", False),
        "has_prediction": bool(state.get("performance_prediction")),
        "has_optimization": bool(state.get("comprehensive_recommendation")),
        "message_count": len(state.get("messages", []))
    }
    
    await manager.send_json({
        "type": "session_state",
        "state": safe_state
    }, client_id)


async def handle_clear_session(data: Dict[str, Any], client_id: str, session_id: Optional[str] = None):
    """清除会话"""
    session_id = session_id or data.get("session_id")
    if not session_id:
        await manager.send_json({
            "type": "error",
            "message": "需要 session_id"
        }, client_id)
        return
    
    from ...agents.graph import get_conversational_manager
    chat_manager = get_conversational_manager()
    chat_manager.clear_session(session_id)
    
    await manager.send_json({
        "type": "session_cleared",
        "session_id": session_id
    }, client_id)
    
    logger.info(f"[Chat] 会话已清除: {session_id}")


def _get_agent_display_name(agent: str) -> str:
    """获取Agent显示名称"""
    names = {
        "router": "🔀 智能路由",
        "assistant": "研发助手",
        "validator": "参数验证专家",
        "analyst": "性能分析专家",
        "optimizer": "优化建议专家",
        "experimenter": "实验方案专家"
    }
    return names.get(agent, agent)


def _get_tool_display_name(tool: str) -> str:
    """获取工具显示名称"""
    names = {
        "validate_composition_tool": "验证成分配比",
        "validate_process_params_tool": "验证工艺参数",
        "run_topphi_simulation_tool": "TopPhi 模拟",
        "predict_performance_tool": "ML 性能预测",
        "optimize_composition_tool": "成分优化",
        "optimize_process_tool": "工艺优化",
        "generate_workorder_tool": "生成实验工单"
    }
    return names.get(tool, tool)
