"""
数据序列化工具 - 清理不可序列化的对象
"""
from typing import Any


def clean_data_for_json(data: Any) -> Any:
    """
    清理数据中不可序列化的对象（主要是LangChain messages）
    
    LangGraph state是Dict[str, Any]，基本都可序列化，
    只需要跳过messages字段（LangChain消息对象）
    
    Args:
        data: 待清理的数据
    
    Returns:
        可序列化的数据
    """
    if isinstance(data, dict):
        # 只跳过messages字段和内部字段
        return {
            key: clean_data_for_json(value)
            for key, value in data.items()
            if not key.startswith("__") and key != "messages"
        }
    elif isinstance(data, (list, tuple)):
        return [clean_data_for_json(item) for item in data]
    else:
        # Dict/List/基本类型都可序列化，直接返回
        return data
