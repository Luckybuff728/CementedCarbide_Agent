"""
数据序列化工具 - 清理不可序列化的对象
"""
from typing import Any
from langchain_core.messages import BaseMessage


def clean_data_for_json(data: Any) -> Any:
    """
    清理数据中不可序列化的对象
    
    Args:
        data: 待清理的数据
    
    Returns:
        可序列化的数据
    """
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            # 跳过以__开头的内部字段
            if key.startswith("__"):
                continue
            # 跳过messages字段（LangChain消息对象）
            if key == "messages":
                continue
            cleaned[key] = clean_data_for_json(value)
        return cleaned
    
    elif isinstance(data, list):
        return [clean_data_for_json(item) for item in data]
    
    elif isinstance(data, tuple):
        return [clean_data_for_json(item) for item in data]
    
    elif isinstance(data, BaseMessage):
        # LangChain消息对象转为字典
        return {
            "type": data.type,
            "content": data.content
        }
    
    elif hasattr(data, "__dict__"):
        # 其他对象转为字典
        return clean_data_for_json(data.__dict__)
    
    else:
        # 基本类型直接返回
        return data
