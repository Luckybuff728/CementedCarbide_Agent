"""
统一的LLM服务 - 整合所有LLM相关功能

包含：
1. DashScopeChatModel - 阿里云百炼模型封装
2. LLMService - 统一的LLM服务类
3. get_llm_service() - 获取单例服务
4. get_llm() - 向后兼容函数
"""
import os
import logging
from typing import Optional, Callable, List, Any, Dict
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun
from dashscope import Generation
import dashscope
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


# ============================================================================
# 第一部分：DashScope模型封装
# ============================================================================

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
        dashscope_messages = self._convert_messages_to_dashscope_format(messages)
        
        response = Generation.call(
            model=self.model_name,
            messages=dashscope_messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            result_format='message',
            stream=False
        )
        
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


# ============================================================================
# 第二部分：材料专家提示词
# ============================================================================

# 材料领域专家系统提示词
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
- 提供量化的预期改进效果
- 使用Markdown格式组织内容，使用标题、列表、表格等使内容清晰易读"""


# ============================================================================
# 第三部分：统一的LLM服务类
# ============================================================================

class LLMService:
    """
    统一的LLM服务
    
    职责：
    - 管理LLM实例的创建和配置
    - 提供统一的LLM调用接口
    - 处理流式输出和回调
    - 统一错误处理
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.6,
        system_prompt: str = MATERIAL_EXPERT_PROMPT
    ):
        """
        初始化LLM服务
        
        Args:
            model_name: 模型名称（默认从环境变量读取）
            temperature: 温度参数，控制输出的随机性
            system_prompt: 系统提示词
        """
        self.system_prompt = system_prompt
        self.llm = DashScopeChatModel(
            model_name=model_name or "qwen-max",
            temperature=temperature,
            streaming=True
        )
        logger.info(f"LLM服务初始化完成: model={self.llm.model_name}, temp={temperature}")
    
    def generate_stream(
        self,
        prompt: str,
        stream_callback: Optional[Callable[[str], None]] = None,
        additional_messages: Optional[List[BaseMessage]] = None
    ) -> str:
        """
        流式生成文本内容
        
        Args:
            prompt: 用户提示词
            stream_callback: 流式输出回调函数，接收每个chunk
            additional_messages: 额外的对话消息（可选）
        
        Returns:
            完整的生成内容
        """
        # 构建消息列表
        messages = [
            SystemMessage(content=self.system_prompt),
        ]
        
        # 添加额外消息（如有）
        if additional_messages:
            messages.extend(additional_messages)
        
        # 添加用户提示
        messages.append(HumanMessage(content=prompt))
        
        # 流式生成
        content = ""
        try:
            logger.debug(f"开始LLM流式生成，提示词长度: {len(prompt)}")
            
            for chunk in self.llm.stream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    content += chunk.content
                    # 调用回调函数发送chunk
                    if stream_callback:
                        try:
                            stream_callback(chunk.content)
                        except Exception as e:
                            logger.warning(f"流式回调失败（不影响生成）: {e}")
            
            logger.info(f"LLM生成完成，内容长度: {len(content)}")
            return content
            
        except Exception as e:
            logger.error(f"LLM生成失败: {e}", exc_info=True)
            raise RuntimeError(f"LLM生成失败: {e}")
    
    def generate(
        self,
        prompt: str,
        additional_messages: Optional[List[BaseMessage]] = None
    ) -> str:
        """
        生成文本内容（非流式）
        
        Args:
            prompt: 用户提示词
            additional_messages: 额外的对话消息（可选）
        
        Returns:
            完整的生成内容
        """
        messages = [
            SystemMessage(content=self.system_prompt),
        ]
        
        if additional_messages:
            messages.extend(additional_messages)
        
        messages.append(HumanMessage(content=prompt))
        
        try:
            result = self.llm._generate(messages)
            content = result.generations[0].message.content
            logger.info(f"LLM生成完成（非流式），内容长度: {len(content)}")
            return content
        except Exception as e:
            logger.error(f"LLM生成失败: {e}", exc_info=True)
            raise RuntimeError(f"LLM生成失败: {e}")


# ============================================================================
# 第四部分：服务获取函数
# ============================================================================

# 全局LLM服务实例（单例模式）
_llm_service_instance: Optional[LLMService] = None


def get_llm_service(
    model_name: Optional[str] = None,
    temperature: float = 0.6,
    force_new: bool = False
) -> LLMService:
    """
    获取LLM服务实例（单例模式）
    
    Args:
        model_name: 模型名称
        temperature: 温度参数
        force_new: 是否强制创建新实例
    
    Returns:
        LLM服务实例
    """
    global _llm_service_instance
    
    if _llm_service_instance is None or force_new:
        _llm_service_instance = LLMService(
            model_name=model_name,
            temperature=temperature
        )
    
    return _llm_service_instance


def get_llm(
    model_name: Optional[str] = None,
    temperature: float = 0.6
) -> DashScopeChatModel:
    """
    获取配置好的LLM实例（向后兼容）
    
    注意：建议使用 get_llm_service() 来获取统一的LLM服务
    
    Args:
        model_name: 模型名称，默认使用环境变量配置
        temperature: 温度参数
    
    Returns:
        配置好的LLM实例
    """
    model = model_name or os.getenv("DASHSCOPE_MODEL_NAME", "qwen-max")
    
    return DashScopeChatModel(
        model_name=model,
        temperature=temperature,
        streaming=True
    )
