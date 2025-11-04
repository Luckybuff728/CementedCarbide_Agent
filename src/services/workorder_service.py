"""
工单生成服务 - 独立于工作流的工单生成功能
"""
from typing import Dict, Any, Callable, Optional
import logging
from ..llm.llm_config import get_material_expert_llm

logger = logging.getLogger(__name__)


def generate_workorder(
    task_id: str,
    selected_option: str,
    task_state: Dict[str, Any],
    stream_callback: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    根据用户选择生成实验工单
    
    Args:
        task_id: 任务ID
        selected_option: 用户选择的方案 (P1/P2/P3)
        task_state: 任务状态数据（包含P1/P2/P3内容、配方参数等）
        stream_callback: 流式输出回调函数
    
    Returns:
        包含工单内容的字典
    """
    logger.info(f"[工单生成] 任务 {task_id} 开始，选择: {selected_option}")
    
    try:
        # 获取对应的优化建议内容
        if selected_option == "P1":
            optimization_content = task_state.get("p1_content", "")
            optimization_name = "P1 成分优化"
        elif selected_option == "P2":
            optimization_content = task_state.get("p2_content", "")
            optimization_name = "P2 结构优化"
        elif selected_option == "P3":
            optimization_content = task_state.get("p3_content", "")
            optimization_name = "P3 工艺优化"
        else:
            raise ValueError(f"无效的优化方案: {selected_option}")
        
        if not optimization_content:
            raise ValueError(f"优化方案内容为空: {selected_option}")
        
        logger.info(f"[工单生成] 优化建议内容长度: {len(optimization_content)}")
        
        # 使用LLM生成实验工单
        workorder_content = _generate_workorder_by_llm(
            optimization_name,
            optimization_content,
            task_state,
            stream_callback
        )
        
        logger.info(f"[工单生成] 完成，内容长度: {len(workorder_content)}")
        
        return {
            "success": True,
            "experiment_workorder": workorder_content,
            "selected_optimization": selected_option,
            "selected_optimization_name": optimization_name
        }
        
    except Exception as e:
        logger.error(f"[工单生成] 失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def _generate_workorder_by_llm(
    optimization_name: str,
    optimization_content: str,
    state: Dict,
    stream_callback=None
) -> str:
    """使用LLM根据优化建议生成实验工单"""
    
    # 获取当前配方参数
    composition = state.get("coating_composition", {})
    process_params = state.get("process_params", {})
    structure_design = state.get("structure_design", {})
    target_requirements = state.get("target_requirements", {})
    
    # 构建其他元素字符串
    other_elements = composition.get('other_elements', [])
    other_elements_str = ', '.join([f"{e.get('element', 'Unknown')} {e.get('content', 0)}%" for e in other_elements]) if other_elements else '无'
    
    # 构建其他气体字符串
    other_gases = process_params.get('other_gases', [])
    other_gases_str = ', '.join([f"{g.get('gas', 'Unknown')} {g.get('flow', 0)} sccm" for g in other_gases]) if other_gases else '无'
    
    # 构建结构设计显示
    structure_str = f"{structure_design.get('structure_type', '单层')}"
    if structure_design.get('structure_type') == 'multi' and structure_design.get('layers'):
        layers_str = '; '.join([f"第{i+1}层({l.get('type', '')}, {l.get('thickness', 0)}μm)" for i, l in enumerate(structure_design.get('layers', []))])
        structure_str += f" - {layers_str}"
    else:
        structure_str += f" - 总厚度: {structure_design.get('total_thickness', 0)} μm"
    
    # 构建提示词
    prompt = f"""
作为涂层工艺专家，请根据以下优化建议生成一份标准的实验工单：

## 当前配方参数
**涂层成分**：
- Al含量: {composition.get('al_content', 0)}%
- Ti含量: {composition.get('ti_content', 0)}%
- N含量: {composition.get('n_content', 0)}%
- 其他元素: {other_elements_str}

**工艺参数**：
- 工艺类型: {process_params.get('process_type', 'N/A')}
- 沉积温度: {process_params.get('deposition_temperature', 0)}°C
- 沉积气压: {process_params.get('deposition_pressure', 0)} Pa
- 偏压: {process_params.get('bias_voltage', 0)} V
- N₂流量: {process_params.get('n2_flow', 0)} sccm
- 其他气体: {other_gases_str}

**结构设计**：
{structure_str}

**性能需求**：
- 基材材料: {target_requirements.get('substrate_material', 'N/A')}
- 目标硬度: {target_requirements.get('target_hardness', 0)} GPa
- 目标弹性模量: {target_requirements.get('elastic_modulus', 0)} GPa
- 工作温度: {target_requirements.get('working_temperature', 0)}°C
- 应用场景: {target_requirements.get('application_scenario', 'N/A')}

## 选定的优化方案
**{optimization_name}**

{optimization_content}

## 请生成实验工单，包含以下内容：

1. **工单编号**：WO-{state.get('task_id', 'XXXX')[-8:]}-{optimization_name[1]}
2. **实验目标**：简要说明本次实验的优化目标
3. **优化方案说明**：总结选定的优化建议的核心要点
4. **调整后的参数**：列出具体修改的参数（相对于当前配方）
5. **实验步骤**：详细的实验操作步骤
6. **检测项目**：需要进行的性能检测项目
7. **预期结果**：预期达到的性能指标
8. **注意事项**：实验过程中需要注意的关键点

请以清晰、专业的格式生成工单内容。
"""
    
    from langchain_core.messages import SystemMessage, HumanMessage
    from ..llm.llm_config import MATERIAL_EXPERT_PROMPT
    
    llm = get_material_expert_llm()
    
    # 使用流式输出（使用messages格式）
    if stream_callback:
        workorder_parts = []
        for chunk in llm.stream([
            SystemMessage(content=MATERIAL_EXPERT_PROMPT),
            HumanMessage(content=prompt)
        ]):
            content = chunk.content
            workorder_parts.append(content)
            stream_callback("experiment_workorder", content)
        return ''.join(workorder_parts)
    else:
        response = llm.invoke([
            SystemMessage(content=MATERIAL_EXPERT_PROMPT),
            HumanMessage(content=prompt)
        ])
        return response.content
