"""
统一的LLM服务 v2.0 - 基于 LangChain ChatOpenAI 重构

特性：
1. 使用 ChatOpenAI 通过 OpenAI 兼容模式调用 DashScope (Qwen)
2. 支持 enable_thinking 深度思考模式
3. 支持流式输出（包含 reasoning_content）
4. 完全兼容 LangChain 生态

API 配置：
- base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
- api_key: DASHSCOPE_API_KEY 环境变量
- model: qwen-plus / qwen-max / qwen-turbo 等
"""
import os
import logging
from typing import Optional, Callable, List, Any, Dict, Iterator, AsyncIterator
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage, 
    SystemMessage, 
    HumanMessage, 
    AIMessage,
    AIMessageChunk
)
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# 常量配置
# ============================================================================

# DashScope OpenAI 兼容模式 API 地址
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 默认模型
DEFAULT_MODEL = "qwen-plus"

# 支持思考模式的模型列表
THINKING_SUPPORTED_MODELS = ["qwen-plus", "qwen-max", "qwen-turbo"]


# ============================================================================
# 材料专家提示词
# ============================================================================

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
# QwenChatOpenAI - 扩展 ChatOpenAI 支持思考模式
# ============================================================================

class QwenChatOpenAI(ChatOpenAI):
    """
    Qwen 聊天模型 - 基于 ChatOpenAI，通过 OpenAI 兼容模式调用 DashScope
    
    扩展功能：
    - 支持 enable_thinking 深度思考模式
    - 支持流式输出 reasoning_content
    
    使用示例：
        >>> llm = QwenChatOpenAI(
        ...     model="qwen-plus",
        ...     enable_thinking=True
        ... )
        >>> response = llm.invoke("你好")
    """
    
    # 是否启用思考模式
    enable_thinking: bool = False
    
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.6,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        streaming: bool = True,
        enable_thinking: bool = False,
        max_tokens: int = 4096,
        **kwargs
    ):
        """
        初始化 Qwen 聊天模型
        
        Args:
            model: 模型名称 (qwen-plus/qwen-max/qwen-turbo等)
            temperature: 温度参数 (0-2)
            api_key: API密钥 (默认从 DASHSCOPE_API_KEY 环境变量获取)
            base_url: API地址 (默认使用 DashScope OpenAI 兼容地址)
            streaming: 是否启用流式输出
            enable_thinking: 是否启用思考模式
            max_tokens: 最大输出 token 数
        """
        # 获取 API 密钥
        resolved_api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not resolved_api_key:
            raise ValueError(
                "请设置 DASHSCOPE_API_KEY 环境变量或传入 api_key 参数。\n"
                "获取方式：https://dashscope.console.aliyun.com/apiKey"
            )
        
        # 设置 base_url
        resolved_base_url = base_url or DASHSCOPE_BASE_URL
        
        # 构建 model_kwargs，用于传递额外参数
        model_kwargs = kwargs.pop("model_kwargs", {})
        
        # 如果启用思考模式，设置 extra_body（显式参数，避免警告）
        extra_body = None
        if enable_thinking and model in THINKING_SUPPORTED_MODELS:
            extra_body = {"enable_thinking": True}
            logger.info(f"[Qwen] 启用思考模式: model={model}")
        
        # 调用父类初始化
        init_kwargs = {
            "model": model,
            "temperature": temperature,
            "openai_api_key": resolved_api_key,
            "openai_api_base": resolved_base_url,
            "streaming": streaming,
            "max_tokens": max_tokens,
            **kwargs
        }
        if model_kwargs:
            init_kwargs["model_kwargs"] = model_kwargs
        if extra_body:
            init_kwargs["extra_body"] = extra_body
        
        super().__init__(**init_kwargs)
        
        # 在 super().__init__() 之后设置属性（Pydantic 要求）
        object.__setattr__(self, '_api_key', resolved_api_key)
        object.__setattr__(self, '_base_url', resolved_base_url)
        object.__setattr__(self, '_max_tokens', max_tokens)
        object.__setattr__(self, '_temperature', temperature)
        object.__setattr__(self, '_model_name', model)
        
        self.enable_thinking = enable_thinking
        
        logger.info(
            f"[Qwen] 初始化完成: model={model}, temp={temperature}, "
            f"thinking={enable_thinking}, streaming={streaming}"
        )
    
    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs
    ) -> Iterator[Any]:
        """
        重写流式输出方法，支持 reasoning_content（思考过程）
        
        将 reasoning_content 放入 AIMessageChunk 的 additional_kwargs 中，
        以便在 LangGraph 的 astream_events 中捕获
        """
        from openai import OpenAI
        from langchain_core.outputs import ChatGenerationChunk
        
        # 如果没有启用思考模式，使用父类方法
        if not self.enable_thinking:
            yield from super()._stream(messages, stop, run_manager, **kwargs)
            return
        
        # 使用 OpenAI 客户端直接调用（支持 reasoning_content）
        client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url
        )
        
        # 转换消息格式
        openai_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                openai_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                openai_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                openai_messages.append({"role": "assistant", "content": msg.content})
        
        try:
            # 流式调用
            completion = client.chat.completions.create(
                model=self._model_name,
                messages=openai_messages,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                extra_body={"enable_thinking": True},
                stream=True
            )
            
            for chunk in completion:
                delta = chunk.choices[0].delta
                
                # 处理思考内容 (reasoning_content)
                reasoning = None
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    reasoning = delta.reasoning_content
                
                # 处理正文内容
                content = delta.content if hasattr(delta, "content") and delta.content else ""
                
                # 构建 AIMessageChunk，将 reasoning_content 放入 additional_kwargs
                additional_kwargs = {}
                if reasoning:
                    additional_kwargs["reasoning_content"] = reasoning
                
                # 只有当有内容时才 yield ChatGenerationChunk
                if content or reasoning:
                    chunk_msg = AIMessageChunk(
                        content=content,
                        additional_kwargs=additional_kwargs
                    )
                    # 包装成 ChatGenerationChunk
                    yield ChatGenerationChunk(message=chunk_msg)
                    
        except Exception as e:
            logger.error(f"[Qwen] 思考模式流式生成失败: {e}")
            raise
    
    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs
    ) -> AsyncIterator[Any]:
        """
        异步流式输出，支持 reasoning_content（思考过程）
        """
        from openai import AsyncOpenAI
        from langchain_core.outputs import ChatGenerationChunk
        
        # 如果没有启用思考模式，使用父类方法
        if not self.enable_thinking:
            async for chunk in super()._astream(messages, stop, run_manager, **kwargs):
                yield chunk
            return
        
        # 使用异步 OpenAI 客户端
        client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url
        )
        
        # 转换消息格式
        openai_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                openai_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                openai_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                openai_messages.append({"role": "assistant", "content": msg.content})
        
        try:
            # 异步流式调用
            completion = await client.chat.completions.create(
                model=self._model_name,
                messages=openai_messages,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                extra_body={"enable_thinking": True},
                stream=True
            )
            
            async for chunk in completion:
                delta = chunk.choices[0].delta
                
                # 处理思考内容
                reasoning = None
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    reasoning = delta.reasoning_content
                
                # 处理正文内容
                content = delta.content if hasattr(delta, "content") and delta.content else ""
                
                # 构建 AIMessageChunk
                additional_kwargs = {}
                if reasoning:
                    additional_kwargs["reasoning_content"] = reasoning
                
                if content or reasoning:
                    chunk_msg = AIMessageChunk(
                        content=content,
                        additional_kwargs=additional_kwargs
                    )
                    # 包装成 ChatGenerationChunk
                    yield ChatGenerationChunk(message=chunk_msg)
                    
        except Exception as e:
            logger.error(f"[Qwen] 异步思考模式流式生成失败: {e}")
            raise
    
    def stream_with_thinking(
        self,
        messages: List[BaseMessage],
        thinking_callback: Optional[Callable[[str], None]] = None,
        content_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, str]:
        """
        流式生成，分别处理思考过程和最终内容
        
        Args:
            messages: 消息列表
            thinking_callback: 思考内容回调（流式）
            content_callback: 最终内容回调（流式）
        
        Returns:
            {"thinking": 思考内容, "content": 最终内容}
        """
        thinking_content = ""
        final_content = ""
        is_answering = False
        
        try:
            # 使用底层 OpenAI 客户端进行流式调用
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.openai_api_key,
                base_url=self.openai_api_base
            )
            
            # 转换消息格式
            openai_messages = []
            for msg in messages:
                if isinstance(msg, SystemMessage):
                    openai_messages.append({"role": "system", "content": msg.content})
                elif isinstance(msg, HumanMessage):
                    openai_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    openai_messages.append({"role": "assistant", "content": msg.content})
            
            # 流式调用
            completion = client.chat.completions.create(
                model=self.model_name,
                messages=openai_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                extra_body={"enable_thinking": True},
                stream=True
            )
            
            for chunk in completion:
                delta = chunk.choices[0].delta
                
                # 处理思考内容 (reasoning_content)
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    thinking_content += delta.reasoning_content
                    if thinking_callback:
                        thinking_callback(delta.reasoning_content)
                
                # 处理最终内容
                if hasattr(delta, "content") and delta.content:
                    if not is_answering:
                        is_answering = True
                    final_content += delta.content
                    if content_callback:
                        content_callback(delta.content)
            
            return {"thinking": thinking_content, "content": final_content}
            
        except Exception as e:
            logger.error(f"[Qwen] 思考模式流式生成失败: {e}")
            raise


# ============================================================================
# LLMService - 统一的 LLM 服务类
# ============================================================================

class LLMService:
    """
    统一的 LLM 服务
    
    职责：
    - 管理 LLM 实例的创建和配置
    - 提供统一的 LLM 调用接口
    - 处理流式输出和回调
    - 统一错误处理
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.6,
        system_prompt: str = MATERIAL_EXPERT_PROMPT,
        enable_thinking: bool = False,
        max_tokens: int = 4096
    ):
        """
        初始化 LLM 服务
        
        Args:
            model_name: 模型名称（默认从环境变量读取）
            temperature: 温度参数
            system_prompt: 系统提示词
            enable_thinking: 是否启用思考模式
            max_tokens: 最大输出 token 数
        """
        self.system_prompt = system_prompt
        self.enable_thinking = enable_thinking
        
        # 从环境变量读取模型名称
        resolved_model = model_name or os.getenv("DASHSCOPE_MODEL_NAME", DEFAULT_MODEL)
        
        # 创建 LLM 实例
        self.llm = QwenChatOpenAI(
            model=resolved_model,
            temperature=temperature,
            streaming=True,
            enable_thinking=enable_thinking,
            max_tokens=max_tokens
        )
        
        logger.info(
            f"[LLMService] 初始化完成: model={resolved_model}, "
            f"temp={temperature}, thinking={enable_thinking}"
        )
    
    @property
    def model_name(self) -> str:
        """获取当前模型名称"""
        return self.llm.model_name
    
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
            stream_callback: 流式输出回调函数
            additional_messages: 额外的对话消息
        
        Returns:
            完整的生成内容
        """
        # 构建消息列表
        messages = [SystemMessage(content=self.system_prompt)]
        
        if additional_messages:
            messages.extend(additional_messages)
        
        messages.append(HumanMessage(content=prompt))
        
        # 流式生成
        content = ""
        try:
            logger.debug(f"[LLMService] 开始流式生成，提示词长度: {len(prompt)}")
            
            for chunk in self.llm.stream(messages):
                if hasattr(chunk, "content") and chunk.content:
                    content += chunk.content
                    if stream_callback:
                        try:
                            stream_callback(chunk.content)
                        except Exception as e:
                            logger.warning(f"[LLMService] 流式回调失败: {e}")
            
            logger.info(f"[LLMService] 生成完成，长度: {len(content)}")
            return content
            
        except Exception as e:
            logger.error(f"[LLMService] 生成失败: {e}", exc_info=True)
            raise RuntimeError(f"LLM生成失败: {e}")
    
    def generate_agent_stream(
        self,
        node: str,
        prompt: str,
        additional_messages: Optional[List[BaseMessage]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        为 Agent 提供的流式生成方法
        
        自动通过 contextvars 将流式内容发送到前端
        
        Args:
            node: Agent 节点名称（如 "analyst", "optimizer"）
            prompt: 用户提示词
            additional_messages: 额外的对话消息
            system_prompt: 自定义系统提示词
        
        Returns:
            完整的生成内容
        """
        from ..graph.stream_callback import send_stream_chunk_sync
        
        messages = [SystemMessage(content=system_prompt or self.system_prompt)]
        
        if additional_messages:
            messages.extend(additional_messages)
        
        messages.append(HumanMessage(content=prompt))
        
        content = ""
        try:
            logger.debug(f"[{node}] 开始流式生成，提示词长度: {len(prompt)}")
            
            for chunk in self.llm.stream(messages):
                if hasattr(chunk, "content") and chunk.content:
                    content += chunk.content
                    try:
                        send_stream_chunk_sync(node=node, content=chunk.content)
                    except Exception as e:
                        logger.warning(f"[{node}] 流式回调失败: {e}")
            
            logger.info(f"[{node}] 生成完成，长度: {len(content)}")
            return content
            
        except Exception as e:
            logger.error(f"[{node}] 生成失败: {e}", exc_info=True)
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
            additional_messages: 额外的对话消息
        
        Returns:
            完整的生成内容
        """
        messages = [SystemMessage(content=self.system_prompt)]
        
        if additional_messages:
            messages.extend(additional_messages)
        
        messages.append(HumanMessage(content=prompt))
        
        try:
            # 使用 invoke 进行非流式调用
            response = self.llm.invoke(messages)
            content = response.content
            logger.info(f"[LLMService] 非流式生成完成，长度: {len(content)}")
            return content
            
        except Exception as e:
            logger.error(f"[LLMService] 生成失败: {e}", exc_info=True)
            raise RuntimeError(f"LLM生成失败: {e}")
    
    def generate_with_thinking(
        self,
        prompt: str,
        thinking_callback: Optional[Callable[[str], None]] = None,
        content_callback: Optional[Callable[[str], None]] = None,
        additional_messages: Optional[List[BaseMessage]] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, str]:
        """
        带思考过程的流式生成
        
        Args:
            prompt: 用户提示词
            thinking_callback: 思考内容回调（流式）
            content_callback: 最终内容回调（流式）
            additional_messages: 额外的对话消息
            system_prompt: 自定义系统提示词
        
        Returns:
            {"thinking": 思考内容, "content": 最终内容}
        """
        messages = [SystemMessage(content=system_prompt or self.system_prompt)]
        
        if additional_messages:
            messages.extend(additional_messages)
        
        messages.append(HumanMessage(content=prompt))
        
        try:
            logger.debug(f"[LLMService] 开始思考模式生成，提示词长度: {len(prompt)}")
            
            result = self.llm.stream_with_thinking(
                messages,
                thinking_callback=thinking_callback,
                content_callback=content_callback
            )
            
            logger.info(
                f"[LLMService] 思考模式完成，"
                f"思考: {len(result['thinking'])}字，内容: {len(result['content'])}字"
            )
            return result
            
        except Exception as e:
            logger.error(f"[LLMService] 思考模式生成失败: {e}", exc_info=True)
            raise RuntimeError(f"LLM生成失败: {e}")


# ============================================================================
# 服务获取函数
# ============================================================================

# 全局 LLM 服务实例（单例模式）
_llm_service_instance: Optional[LLMService] = None


def get_llm_service(
    model_name: Optional[str] = None,
    temperature: float = 0.6,
    force_new: bool = False
) -> LLMService:
    """
    获取 LLM 服务实例（单例模式）
    
    Args:
        model_name: 模型名称
        temperature: 温度参数
        force_new: 是否强制创建新实例
    
    Returns:
        LLMService 实例
    """
    global _llm_service_instance
    
    if _llm_service_instance is None or force_new:
        enable_thinking = os.getenv("ENABLE_THINKING", "false").lower() == "true"
        
        _llm_service_instance = LLMService(
            model_name=model_name,
            temperature=temperature,
            enable_thinking=enable_thinking
        )
    
    return _llm_service_instance


def get_llm(
    model_name: Optional[str] = None,
    temperature: float = 0.6
) -> QwenChatOpenAI:
    """
    获取配置好的 LLM 实例（向后兼容）
    
    Args:
        model_name: 模型名称
        temperature: 温度参数
    
    Returns:
        QwenChatOpenAI 实例
    """
    resolved_model = model_name or os.getenv("DASHSCOPE_MODEL_NAME", DEFAULT_MODEL)
    
    return QwenChatOpenAI(
        model=resolved_model,
        temperature=temperature,
        streaming=True
    )


# ============================================================================
# 向后兼容别名
# ============================================================================

# 保持与旧版本的兼容性
DashScopeChatModel = QwenChatOpenAI
