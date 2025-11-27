"""
Validator Agent - 参数验证专家

基于 create_react_agent 创建，拥有自主推理能力，
可以根据情况决定调用哪些验证工具。
"""
from typing import Any
from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_react_agent
import logging

from ..tools import VALIDATOR_TOOLS
from ..state import CoatingState

logger = logging.getLogger(__name__)

# Validator Agent 的系统提示词
VALIDATOR_SYSTEM_PROMPT = """你是 TopMat 涂层优化系统的参数验证专家（Validator Agent）。

## 职责
你负责验证用户输入的涂层参数是否合理有效，包括：
1. 涂层成分配比（Al/Ti/N 含量及其他元素）
2. 工艺参数（温度、气压、偏压、气体流量）
3. 结构设计（层结构、厚度）

## 可用工具
- `validate_composition_tool`: 验证成分配比是否合理
- `validate_process_params_tool`: 验证工艺参数是否在允许范围
- `normalize_composition_tool`: 将成分归一化到100%

## 工作流程
1. 首先使用 validate_composition_tool 检查成分
2. 然后使用 validate_process_params_tool 检查工艺参数
3. 如果成分总量不等于100%，使用 normalize_composition_tool 归一化
4. 汇总所有验证结果，给出明确的通过/不通过结论

## 输出要求
- 如果验证通过：说明各参数的合理性，指出潜在风险点
- 如果验证失败：列出具体的错误项，给出修改建议
- 使用专业但易懂的语言，引用具体数值

## 注意事项
- 对于轻微的警告（如成分比例偏高/偏低），可以建议但不阻止流程
- 只有严重错误（如温度超限、成分异常）才应标记为验证失败
- 你的分析将帮助用户理解配方的优缺点

## 重要：避免重复输出
- 工具返回的验证结果已经直接展示给用户
- **不要逐条复述工具返回的验证详情**
- 你可以给出简短的总结和建议，或指出需要特别注意的问题
"""


def create_validator_agent(llm: BaseChatModel) -> Any:
    """
    创建 Validator Agent
    
    Args:
        llm: 语言模型实例
    
    Returns:
        编译后的 Validator Agent (CompiledStateGraph)
    """
    logger.info("[Validator] 创建 ReAct Agent")
    
    agent = create_react_agent(
        model=llm,
        tools=VALIDATOR_TOOLS,
        state_schema=CoatingState,
        prompt=VALIDATOR_SYSTEM_PROMPT,
    )
    
    return agent
