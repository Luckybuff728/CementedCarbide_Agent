"""
工单生成服务 - 独立于工作流的工单生成功能
"""
from typing import Dict, Any, Callable, Optional
import logging
from ..llm import get_llm_service

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
        统一结构的结果字典 {status, data, message, error, meta}
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
        
        # 从LLM生成的文本中提取关键信息
        workorder_data = _extract_workorder_info(
            workorder_content, 
            optimization_name, 
            selected_option,
            task_state
        )
        
        logger.info(f"[工单生成] 完成，内容长度: {len(workorder_content)}")
        logger.info(f"[工单生成] 提取的工单ID: {workorder_data.get('workorder_id', 'N/A')}")
        logger.info(f"[工单生成] 方案名称: {workorder_data.get('solution_name', 'N/A')}")
        logger.info(f"[工单生成] 关键参数数量: {len(workorder_data.get('key_parameters', []))}")
        
        # 使用统一结构封装返回
        result = {
            "status": "success",
            "data": workorder_data,
            "message": "实验工单生成完成",
            "error": None,
            "meta": {}
        }
        
        logger.info(f"[工单生成] 返回结果类型: {type(result)}, 键: {list(result.keys())}")
        
        return result
        
    except Exception as e:
        logger.error(f"[工单生成] 失败: {str(e)}")
        raise  # 直接抛出异常，由调用者处理


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
    other_elements_str = ', '.join([f"{e.get('name', 'Unknown')} {e.get('content', 0)} at.%" for e in other_elements]) if other_elements else '无'
    
    # 构建其他气体字符串
    other_gases = process_params.get('other_gases', [])
    other_gases_str = ', '.join([f"{g.get('type', 'Unknown')} {g.get('flow', 0)} sccm" for g in other_gases]) if other_gases else '无'
    
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
- Al含量: {composition.get('al_content', 0)} at.%
- Ti含量: {composition.get('ti_content', 0)} at.%
- N含量: {composition.get('n_content', 0)} at.%
- 其他元素: {other_elements_str}

**工艺参数**：
- 工艺类型: {process_params.get('process_type', 'N/A')}
- 沉积温度: {process_params.get('deposition_temperature', 0)} ℃
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

---

**输出格式要求**：
1. 严格按照以下Markdown模板生成，不要添加任何额外内容
2. 实验名称要具体反映优化重点（成分/结构/工艺）
3. 实验目标用一句话概括核心优化目标
4. 参数调整必须使用表格格式
5. 总字数控制在600-800字
6. 只输出工单内容，不要输出"要求"、"注意"等额外说明

---

**输出模板（请严格遵循）**：

## 实验名称
[具体的实验名称，例如：高Al/微Si掺杂提升抗氧化与硬度等]

## 实验目标
[一句话说明本次实验的核心优化目标，明确想要达成的效果]

## 优化要点
- [核心改进措施1，说明具体做什么]
- [核心改进措施2]
- [核心改进措施3]
- [核心改进措施4，如有需要]

## 参数调整
| 参数名称 | 当前值 | 优化值 | 调整原因 |
|---------|-------|-------|---------|
| [参数1] | [当前数值] | [优化后数值] | [为什么这样调整] |
| [参数2] | [当前数值] | [优化后数值] | [为什么这样调整] |
| [参数3] | [当前数值] | [优化后数值] | [为什么这样调整] |

## 实验步骤
1. [步骤1的具体操作]
2. [步骤2的具体操作]
3. [步骤3的具体操作]
4. [步骤4的具体操作]
5. [步骤5的具体操作]

## 检测项目
- **硬度测试**: [测试方法和要求]
- **结合力测试**: [测试方法和要求]
- **耐磨性测试**: [测试方法和要求]
- **其他检测**: [根据优化方案需要]

## 预期性能
- [性能指标1]: [预期数值或改善程度]
- [性能指标2]: [预期数值或改善程度]
- [性能指标3]: [预期数值或改善程度]

---
请立即开始生成工单，只输出上述模板内容，不要添加任何额外说明。
"""
# 简洁明了，不超过100字
# - 600-800字

    from langchain_core.messages import SystemMessage, HumanMessage
    from ..llm import MATERIAL_EXPERT_PROMPT
    
    llm_service = get_llm_service()
    
    # 使用LLM服务生成工单
    def _callback(content):
        if stream_callback:
            stream_callback("experiment_workorder", content)
    
    workorder_content = llm_service.generate_stream(
        prompt=prompt,
        stream_callback=_callback if stream_callback else None
    )
    
    return workorder_content


def _extract_workorder_info(
    workorder_content: str,
    optimization_name: str,
    selected_option: str,
    task_state: Dict
) -> Dict[str, Any]:
    """简化的工单信息提取，从LLM生成内容中提取关键信息"""
    
    lines = workorder_content.split('\n')
    solution_name = ""
    experiment_goal = ""
    
    # 提取实验名称和目标
    in_name_section = False
    in_goal_section = False
    
    for i, line in enumerate(lines[:30]):  # 扩大搜索范围到前30行
        line = line.strip()
        
        # 检测实验名称章节（新格式：## 实验名称）
        if not solution_name and ("## 实验名称" in line or "##实验名称" in line):
            in_name_section = True
            logger.info(f"[工单提取] 第{i+1}行检测到实验名称章节")
            continue
        
        # 提取实验名称（章节格式：下一行内容）
        if in_name_section and not solution_name and line and not line.startswith('#'):
            solution_name = line.rstrip("。").replace('[', '').replace(']', '').strip()
            logger.info(f"[工单提取] 第{i+1}行找到实验名称(章节格式): {solution_name}")
            in_name_section = False
        
        # 提取实验名称（旧格式兼容：**实验名称**: 内容）
        if not solution_name and ("实验名称" in line or "**实验名称**" in line) and ":" in line:
            solution_name = line.split(":", 1)[1].strip().rstrip("。").replace('**', '').replace('[', '').replace(']', '').strip()
            logger.info(f"[工单提取] 第{i+1}行找到实验名称(内联格式): {solution_name}")
        
        # 检测实验目标章节
        if not experiment_goal and ("## 实验目标" in line or "##实验目标" in line):
            in_goal_section = True
            logger.info(f"[工单提取] 第{i+1}行检测到实验目标章节")
            continue
        
        # 提取实验目标（章节格式：下一行内容）
        if in_goal_section and not experiment_goal and line and not line.startswith('#'):
            experiment_goal = line.rstrip("。").replace('[', '').replace(']', '').strip()
            logger.info(f"[工单提取] 第{i+1}行找到实验目标(章节格式): {experiment_goal}")
            in_goal_section = False
        
        # 提取实验目标（旧格式兼容：**实验目标**: 内容）
        if not experiment_goal and ("实验目标" in line or "**实验目标**" in line) and ":" in line:
            experiment_goal = line.split(":", 1)[1].strip().rstrip("。").replace('**', '').replace('[', '').replace(']', '').strip()
            logger.info(f"[工单提取] 第{i+1}行找到实验目标(内联格式): {experiment_goal}")
        
        # 如果都找到了就退出
        if solution_name and experiment_goal:
            break
    
    # 默认值（如果LLM没有生成）
    if not solution_name:
        name_map = {
            "P1": "TiAlN成分优化实验",
            "P2": "TiAlN结构优化实验",
            "P3": "TiAlN工艺优化实验"
        }
        solution_name = name_map.get(selected_option, "TiAlN优化实验")
        logger.info(f"[工单提取] 未找到实验名称，使用默认值: {solution_name}")
    else:
        logger.info(f"[工单提取] 提取的实验名称: {solution_name}")
    
    if not experiment_goal:
        goal_map = {
            "P1": "提升TiAlN涂层硅度和耐磨性",
            "P2": "优化涂层结合力和结构稳定性",
            "P3": "改善沉积质量和性能一致性"
        }
        experiment_goal = goal_map.get(selected_option, "优化涂层性能")
        logger.info(f"[工单提取] 未找到实验目标，使用默认值: {experiment_goal}")
    else:
        logger.info(f"[工单提取] 提取的实验目标: {experiment_goal}")
    
    # 生成工单ID
    import time
    workorder_id = f"WO{int(time.time()) % 1000000:06d}"
    
    # 提取关键参数
    key_parameters = _extract_key_parameters_from_state(task_state, selected_option)
    
    return {
        "workorder_id": workorder_id,
        "experiment_id": workorder_id,
        "solution_name": solution_name,
        "experiment_goal": experiment_goal,
        "key_parameters": key_parameters,
        "selected_optimization": selected_option,
        "optimization_name": optimization_name,
        "content": workorder_content,
        "created_at": time.time()
    }


def _extract_key_parameters_from_state(task_state: Dict, selected_option: str) -> list:
    """从任务状态中提取与优化方案相关的关键参数"""
    key_parameters = []
    
    composition = task_state.get("coating_composition", {})
    process_params = task_state.get("process_params", {})
    structure = task_state.get("structure_design", {})
    
    if selected_option == "P1":  # 成分优化
        # 主要关注成分参数
        if composition.get("al_content"):
            key_parameters.append({"name": "Al含量", "value": f"{composition['al_content']} at.%"})
        if composition.get("ti_content"):
            key_parameters.append({"name": "Ti含量", "value": f"{composition['ti_content']} at.%"})
        if composition.get("n_content"):
            key_parameters.append({"name": "N含量", "value": f"{composition['n_content']} at.%"})
            
    elif selected_option == "P2":  # 结构优化
        # 主要关注结构参数
        if structure.get("structure_type"):
            struct_name = "多层结构" if structure["structure_type"] == "multi" else "单层结构"
            key_parameters.append({"name": "结构类型", "value": struct_name})
        if structure.get("total_thickness"):
            key_parameters.append({"name": "总厚度", "value": f"{structure['total_thickness']} μm"})
        # 也包含主要成分
        if composition.get("al_content"):
            key_parameters.append({"name": "Al含量", "value": f"{composition['al_content']} at.%"})
            
    elif selected_option == "P3":  # 工艺优化
        # 主要关注工艺参数
        if process_params.get("substrate_temperature"):
            key_parameters.append({"name": "基体温度", "value": f"{process_params['substrate_temperature']}°C"})
        if process_params.get("target_power"):
            key_parameters.append({"name": "靶材功率", "value": f"{process_params['target_power']} W"})
        if process_params.get("bias_voltage"):
            key_parameters.append({"name": "偏置电压", "value": f"{process_params['bias_voltage']} V"})
        if process_params.get("n2_flow_rate"):
            key_parameters.append({"name": "N₂流量", "value": f"{process_params['n2_flow_rate']} sccm"})
    
    return key_parameters[:4]  # 最多4个关键参数
