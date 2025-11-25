"""
Validator Agent - 参数验证专家
负责验证用户输入的涂层参数是否合理有效
"""
from typing import Dict, Any
from langchain_core.messages import AIMessage, HumanMessage
from ..graph.agent_state import CoatingAgentState
from .tools import validate_input_tool
import logging

logger = logging.getLogger(__name__)


def validator_agent_node(state: CoatingAgentState) -> Dict[str, Any]:
    """
    Validator Agent 节点
    
    功能：
    1. 验证涂层成分配比
    2. 验证工艺参数
    3. 验证结构设计
    4. 归一化数据
    
    Returns:
        更新validation_result和validation_passed
    """
    logger.info(f"[Validator] 任务 {state.get('task_id')} 开始验证")
    
    try:
        # 调用验证工具
        result = validate_input_tool.invoke({
            "coating_composition": state.get("coating_composition", {}),
            "process_params": state.get("process_params", {}),
            "structure_design": state.get("structure_design", {}),
            "target_requirements": state.get("target_requirements", "")
        })
        
        # 检查是否有错误
        if "error" in result:
            logger.error(f"[Validator] 验证失败: {result['error']}")
            
            return {
                "validation_result": result,
                "validation_passed": False,
                "current_agent": "validator",
                "messages": [
                    AIMessage(content=f"❌ **参数验证失败**\n\n{result['error']}\n\n请修正后重新提交。")
                ]
            }
        
        # 验证成功
        validated = result.get("input_validated", False)
        
        if validated:
            logger.info(f"[Validator] 验证成功")
            
            # 更新归一化后的参数
            normalized_composition = result.get("coating_composition", state.get("coating_composition"))
            
            message = "✅ **参数验证通过**\n\n"
            message += f"- 涂层成分：Al {normalized_composition.get('al_content', 0):.1f}%, "
            message += f"Ti {normalized_composition.get('ti_content', 0):.1f}%, "
            message += f"N {normalized_composition.get('n_content', 0):.1f}%\n"
            message += f"- 工艺类型：{state.get('process_params', {}).get('process_type', 'N/A')}\n"
            message += f"- 结构设计：{state.get('structure_design', {}).get('structure_type', '单层')}\n\n"

            
            return {
                "validation_result": result,
                "validation_passed": True,
                "coating_composition": normalized_composition,  # 更新为归一化后的值
                "current_agent": "validator",
                "messages": [AIMessage(content=message)],
                # 标记：Validator刚完成，Supervisor应该ask_user
                "last_completed_agent": "validator"
            }
        else:
            # 验证不通过
            errors = result.get("validation_errors", ["未知错误"])
            error_message = "❌ **参数验证失败**\n\n" + "\n".join([f"- {e}" for e in errors])
            error_message += "\n\n请修正后重新提交。"
            
            logger.warning(f"[Validator] 验证不通过: {errors}")
            
            return {
                "validation_result": result,
                "validation_passed": False,
                "current_agent": "validator",
                "messages": [AIMessage(content=error_message)]
            }
    
    except Exception as e:
        logger.error(f"[Validator] 执行失败: {str(e)}", exc_info=True)
        
        return {
            "validation_result": {"error": str(e)},
            "validation_passed": False,
            "current_agent": "validator",
            "error_message": str(e),
            "messages": [AIMessage(content=f"❌ 验证过程出错: {str(e)}")]
        }

