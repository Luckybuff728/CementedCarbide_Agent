"""
LLM配置和初始化模块 - 集成阿里云百炼
"""
import os
from typing import Optional, Any, List, Dict
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun
from dashscope import Generation
import dashscope
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class DashScopeChatModel(BaseChatModel):
    """阿里云百炼聊天模型封装"""
    
    model_name: str = "qwen-plus"
    api_key: Optional[str] = None
    temperature: float = 0.5
    top_p: float = 0.8
    max_tokens: int = 4096
    streaming: bool = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置API密钥
        if self.api_key:
            dashscope.api_key = self.api_key
        elif os.getenv("DASHSCOPE_API_KEY"):
            dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
        else:
            raise ValueError("请设置DASHSCOPE_API_KEY环境变量或传入api_key参数")
    
    @property
    def _llm_type(self) -> str:
        """返回LLM类型"""
        return "dashscope"
    
    def _convert_messages_to_dashscope_format(self, messages: List[BaseMessage]) -> List[Dict]:
        """将LangChain消息格式转换为DashScope格式"""
        dashscope_messages = []
        for message in messages:
            if isinstance(message, SystemMessage):
                dashscope_messages.append({
                    "role": "system",
                    "content": message.content
                })
            elif isinstance(message, HumanMessage):
                dashscope_messages.append({
                    "role": "user", 
                    "content": message.content
                })
            elif isinstance(message, AIMessage):
                dashscope_messages.append({
                    "role": "assistant",
                    "content": message.content
                })
        return dashscope_messages
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any
    ) -> ChatResult:
        """生成响应"""
        # 转换消息格式
        dashscope_messages = self._convert_messages_to_dashscope_format(messages)
        
        # 调用DashScope API
        response = Generation.call(
            model=self.model_name,
            messages=dashscope_messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            result_format='message',
            stream=False
        )
        
        # 处理响应
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            message = AIMessage(content=content)
            generation = ChatGeneration(message=message)
            return ChatResult(generations=[generation])
        else:
            raise Exception(f"DashScope API调用失败: {response.message}")
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any
    ) -> ChatResult:
        """异步生成响应"""
        # 暂时使用同步方法
        return self._generate(messages, stop, run_manager, **kwargs)
    
    def stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any
    ):
        """流式生成响应"""
        dashscope_messages = self._convert_messages_to_dashscope_format(messages)
        
        responses = Generation.call(
            model=self.model_name,
            messages=dashscope_messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            result_format='message',
            stream=True,
            incremental_output=True
        )
        
        for response in responses:
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                yield AIMessage(content=content)
            else:
                raise Exception(f"DashScope API流式调用失败: {response.message}")


def get_llm(
    model_name: Optional[str] = None,
    temperature: float = 0.5,
    streaming: bool = True
) -> DashScopeChatModel:
    """
    获取配置好的LLM实例
    
    Args:
        model_name: 模型名称，默认使用环境变量配置
        temperature: 温度参数
        streaming: 是否启用流式输出
    
    Returns:
        配置好的LLM实例
    """
    model = model_name or os.getenv("DASHSCOPE_MODEL_NAME", "qwen-max")
    
    return DashScopeChatModel(
        model_name=model,
        temperature=temperature,
        streaming=streaming
    )


def get_structured_llm(schema: Any):
    """
    获取结构化输出的LLM
    
    Args:
        schema: Pydantic模型或JSON Schema
    
    Returns:
        支持结构化输出的LLM实例
    """
    llm = get_llm(temperature=0.3)  # 使用较低温度以获得更稳定的结构化输出
    # 绑定结构化输出schema
    return llm.with_structured_output(schema)


# 材料领域专用的系统提示词
MATERIAL_EXPERT_PROMPT = """你是一位专业的材料科学专家，特别擅长硬质合金涂层的研发和优化。
你具备以下专业知识：
1. 深入理解涂层成分(Al, Ti, N等元素)对性能的影响
2. 熟悉各种沉积工艺参数(气压、流量、偏压、温度等)的作用机理
3. 掌握涂层结构设计(厚度、多层结构)的优化原则
4. 了解不同应用场景对涂层性能的需求

在提供建议时，请：
- 基于科学原理和实验数据进行分析
- 给出具体、可操作的优化方案
- 考虑实际生产的可行性
- 提供量化的预期改进效果"""


def get_material_expert_llm():
    """获取材料专家LLM实例"""
    llm = get_llm(temperature=0.6)
    # 可以在这里添加特定的系统提示
    return llm
