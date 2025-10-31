"""
LangGraph工作流节点实现
"""
from typing import Dict, List, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from ..graph.state import CoatingWorkflowState
from ..llm.llm_config import get_material_expert_llm, MATERIAL_EXPERT_PROMPT
from ..models.coating_models import (
    CoatingComposition, 
    ProcessParameters,
    PerformancePrediction,
    OptimizationSuggestion
)
from ..graph.stream_callback import send_stream_chunk_sync
import json
import logging
import time

logger = logging.getLogger(__name__)


def input_validation_node(state: CoatingWorkflowState) -> Dict:
    """
    输入验证和预处理节点
    验证涂层参数的合理性并进行预处理
    """
    logger.info(f"开始验证任务 {state['task_id']} 的输入参数")
    
    # 调试：打印接收到的state
    logger.info(f"[调试] 接收到的state数据:")
    logger.info(f"  - coating_composition: {state.get('coating_composition')}")
    logger.info(f"  - process_params: {state.get('process_params')}")
    logger.info(f"  - structure_design: {state.get('structure_design')}")
    
    validation_errors = []
    
    # 验证涂层成分
    try:
        composition = state.get("coating_composition", {})
        logger.info(f"[调试] 成分数据: {composition}, 类型: {type(composition)}")
        
        # 过滤掉None值，只计算数值
        valid_values = [v for v in composition.values() if v is not None]
        total = sum(valid_values) if valid_values else 0
        logger.info(f"[调试] 成分总和: {total}, 有效值: {valid_values}")
        
        if total > 100:
            validation_errors.append(f"成分总和超过100%: {total}%")
        
        # 检查必要元素
        if "al_content" not in composition and "ti_content" not in composition:
            validation_errors.append("缺少主要元素(Al或Ti)")
    except Exception as e:
        logger.error(f"[调试] 成分验证异常: {str(e)}", exc_info=True)
        validation_errors.append(f"成分验证失败: {str(e)}")
    
    # 验证工艺参数
    try:
        params = state.get("process_params", {})
        logger.info(f"[调试] 工艺参数: {params}")
        
        deposition_pressure = params.get("deposition_pressure", 0)
        deposition_temperature = params.get("deposition_temperature", 0)
        logger.info(f"[调试] 沉积气压: {deposition_pressure}, 沉积温度: {deposition_temperature}")
        
        if deposition_pressure <= 0:
            validation_errors.append("沉积气压必须大于0")
        if deposition_temperature < 400 or deposition_temperature > 800:
            validation_errors.append("沉积温度应在400-800℃之间")
    except Exception as e:
        logger.error(f"[调试] 工艺参数验证异常: {str(e)}", exc_info=True)
        validation_errors.append(f"工艺参数验证失败: {str(e)}")
    
    # 预处理数据
    preprocessed_data = {
        "composition_normalized": normalize_composition(state.get("coating_composition", {})),
        "process_params_validated": state.get("process_params", {}),
        "structure_validated": state.get("structure_design", {})
    }
    
    # 更新状态
    result = {
        "input_validated": len(validation_errors) == 0,
        "validation_errors": validation_errors,
        "preprocessed_data": preprocessed_data,
        "current_step": "validation_complete",
        "next_step": "performance_prediction" if len(validation_errors) == 0 else "error",
        "workflow_status": "validated" if len(validation_errors) == 0 else "validation_failed"
    }
    
    # 调试：输出验证结果
    logger.info(f"[调试] 验证结果: input_validated={result['input_validated']}")
    if validation_errors:
        logger.error(f"[调试] 验证错误列表: {validation_errors}")
    
    return result


# ==================== 性能预测模块拆分 ====================
# 将性能预测拆分为多个独立节点，支持流式输出和MCP/RAG接口

def topphi_simulation_node(state: CoatingWorkflowState) -> Dict:
    """
    TopPhi模拟节点 - 预留MCP工具接口
    使用第一性原理模拟预测微观结构和性能
    """
    logger.info(f"[TopPhi模拟] 任务 {state['task_id']} 开始")
    
    composition = state.get("coating_composition", {})
    params = state.get("process_params", {})
    
    # 模拟计算时间（实际接入TopPhi时会有真实计算时间）
    time.sleep(4)
    
    # TODO: 接入MCP工具 - TopPhi模拟服务
    # 示例：使用MCP协议调用外部TopPhi模拟工具
    # mcp_result = await call_mcp_tool("topphi_simulate", {"composition": composition, "params": params})
    
    # 当前使用示例数据模拟
    topphi_result = {
        "grain_size_nm": 8.5,
        "preferred_orientation": "(111)",
        "residual_stress_gpa": -2.5,
        "lattice_constant": 4.15,
        "formation_energy": -0.85,
        "confidence": 0.82,
        "simulation_time": 120  # 秒
    }
    
    logger.info(f"[TopPhi模拟] 完成 - 晶粒尺寸: {topphi_result['grain_size_nm']} nm")
    
    return {
        "topphi_simulation": topphi_result,
        "current_step": "topphi_complete"
    }


def ml_model_prediction_node(state: CoatingWorkflowState) -> Dict:
    """
    ML模型预测节点 - 预留MCP工具接口
    使用机器学习模型预测涂层性能
    """
    logger.info(f"[ML模型预测] 任务 {state['task_id']} 开始")
    
    composition = state.get("coating_composition", {})
    params = state.get("process_params", {})
    structure = state.get("structure_design", {})
    
    # 模拟预测计算时间（实际接入ML模型时会有真实推理时间）
    time.sleep(4)
    
    # TODO: 接入MCP工具 - ML预测服务
    # 示例：使用MCP协议调用外部ML模型
    # mcp_result = await call_mcp_tool("ml_predict", {
    #     "composition": composition,
    #     "process_params": params,
    #     "structure": structure
    # })
    
    # 当前使用示例数据模拟
    ml_prediction = {
        "hardness_gpa": 28.5,
        "hardness_std": 1.2,
        "adhesion_level": "HF1",
        "wear_rate": 1.2e-6,
        "oxidation_temp_c": 850,
        "model_confidence": 0.85,
        "feature_importance": {
            "al_content": 0.35,
            "deposition_temp": 0.28,
            "bias_voltage": 0.22,
            "ti_content": 0.15
        }
    }
    
    logger.info(f"[ML模型预测] 完成 - 硬度: {ml_prediction['hardness_gpa']} GPa")
    
    return {
        "ml_prediction": ml_prediction,
        "current_step": "ml_complete"
    }


def historical_comparison_node(state: CoatingWorkflowState) -> Dict:
    """
    历史数据比对节点 - 预留RAG接口
    从历史数据库检索相似案例并进行对比分析
    """
    logger.info(f"[历史数据比对] 任务 {state['task_id']} 开始")
    
    composition = state.get("coating_composition", {})
    params = state.get("process_params", {})
    
    # 模拟数据库检索时间（实际接入RAG时会有真实检索时间）
    time.sleep(4)
    
    # TODO: 接入RAG系统 - 向量数据库检索
    # 示例：使用RAG检索相似的历史案例
    # similar_cases = await rag_retrieve(
    #     query_embedding=encode_coating_params(composition, params),
    #     top_k=5,
    #     similarity_threshold=0.85
    # )
    
    # 当前使用示例数据模拟
    historical_cases = [
        {
            "case_id": "CASE_2024_001",
            "similarity_score": 0.92,
            "composition": {"al_content": 32, "ti_content": 26, "n_content": 42},
            "actual_hardness": 27.8,
            "actual_adhesion": "HF1",
            "deviation_from_prediction": "+2.5%",
            "application": "高速切削"
        },
        {
            "case_id": "CASE_2024_015",
            "similarity_score": 0.88,
            "composition": {"al_content": 30, "ti_content": 28, "n_content": 42},
            "actual_hardness": 29.1,
            "actual_adhesion": "HF2",
            "deviation_from_prediction": "-1.8%",
            "application": "模具涂层"
        }
    ]
    
    logger.info(f"[历史数据比对] 完成 - 找到 {len(historical_cases)} 个相似案例")
    
    return {
        "historical_comparison": historical_cases,
        "current_step": "historical_complete"
    }


def integrated_analysis_node(state: CoatingWorkflowState) -> Dict:
    """
    综合分析节点 - LLM流式生成根因分析
    整合TopPhi、ML和历史数据，生成综合分析报告
    """
    logger.info(f"[综合分析] 任务 {state['task_id']} 开始")
    
    llm = get_material_expert_llm()
    
    # 获取前面节点的结果
    composition = state.get("coating_composition", {})
    params = state.get("process_params", {})
    topphi = state.get("topphi_simulation", {})
    ml_pred = state.get("ml_prediction", {})
    historical = state.get("historical_comparison", [])
    
    # 构建综合分析提示
    analysis_prompt = f"""
作为材料专家，请基于以下多源数据进行综合根因分析：

**涂层参数：**
成分: Al {composition.get('al_content', 0)}%, Ti {composition.get('ti_content', 0)}%, N {composition.get('n_content', 0)}%
工艺: 温度 {params.get('deposition_temperature', 0)}℃, 偏压 {params.get('bias_voltage', 0)}V

**TopPhi第一性原理模拟：**
- 晶粒尺寸: {topphi.get('grain_size_nm', 'N/A')} nm
- 择优取向: {topphi.get('preferred_orientation', 'N/A')}
- 残余应力: {topphi.get('residual_stress_gpa', 'N/A')} GPa

**ML模型预测：**
- 硬度预测: {ml_pred.get('hardness_gpa', 'N/A')} ± {ml_pred.get('hardness_std', 0)} GPa
- 结合力等级: {ml_pred.get('adhesion_level', 'N/A')}
- 抗氧化温度: {ml_pred.get('oxidation_temp_c', 'N/A')}℃

**历史相似案例：**
{len(historical)} 个相似案例，平均相似度 {sum(c.get('similarity_score', 0) for c in historical) / len(historical) if historical else 0:.2f}

请进行深入的根因分析：
1. **关键因素识别**：哪些参数对性能影响最大？
2. **微观机制分析**：成分-工艺-结构-性能的因果链
3. **预测可信度评估**：多源数据的一致性和可靠性
4. **历史经验借鉴**：相似案例的启示
5. **潜在风险提示**：可能的性能波动或失效模式

请以Markdown格式输出，使用列表、加粗等格式增强可读性。
"""
    
    # 将分析提示添加到消息历史
    messages = state.get("messages", []) + [
        SystemMessage(content=MATERIAL_EXPERT_PROMPT),
        HumanMessage(content=analysis_prompt)
    ]
    
    logger.info("[综合分析] LLM流式生成根因分析...")
    
    # 直接通过回调发送流式输出，不依赖LangGraph的astream_events
    root_cause_analysis = ""
    try:
        for chunk in llm.stream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                root_cause_analysis += chunk.content
                # 直接发送流式chunk到前端
                send_stream_chunk_sync("integrated_analysis", chunk.content)
        logger.info(f"[综合分析] 根因分析生成完成，长度: {len(root_cause_analysis)}")
    except Exception as e:
        logger.error(f"[综合分析] 失败: {str(e)}")
        root_cause_analysis = "综合分析生成失败，请稍后重试"
    
    # 整合性能预测结果
    performance_prediction = {
        "hardness": ml_pred.get("hardness_gpa", 0),
        "hardness_std": ml_pred.get("hardness_std", 0),
        "adhesion_level": ml_pred.get("adhesion_level", "N/A"),
        "wear_rate": ml_pred.get("wear_rate", 0),
        "oxidation_temperature": ml_pred.get("oxidation_temp_c", 0),
        "deposition_structure": {
            "grain_size": f"{topphi.get('grain_size_nm', 0)} nm",
            "preferred_orientation": topphi.get("preferred_orientation", "N/A"),
            "residual_stress": f"{topphi.get('residual_stress_gpa', 0)} GPa"
        },
        "confidence_score": (ml_pred.get("model_confidence", 0) + topphi.get("confidence", 0)) / 2,
        "data_sources": ["TopPhi模拟", "ML模型预测", "历史数据比对"]
    }
    
    logger.info(f"[综合分析] 完成 - 最终硬度预测: {performance_prediction['hardness']} GPa")
    
    return {
        "performance_prediction": performance_prediction,
        "root_cause_analysis": root_cause_analysis,
        "prediction_confidence": performance_prediction["confidence_score"],
        "messages": messages + [AIMessage(content=root_cause_analysis)],
        "current_step": "prediction_complete",
        "next_step": "optimization_suggestion",
        "workflow_status": "predicted"
    }


# ==================== 优化建议模块重构 ====================
# 拆分为P1/P2/P3独立节点 + 实验闭环节点

def p1_composition_optimization_node(state: CoatingWorkflowState) -> Dict:
    """
    P1成分优化建议生成节点
    - 调整主要元素配比（Al/Ti/N等）
    - 添加微量元素改性（Cr/Si/Y等）
    """
    logger.info(f"[P1成分优化] 任务 {state['task_id']} 开始")
    
    llm = get_material_expert_llm()
    
    # 获取当前性能和目标
    current_performance = state.get("performance_prediction", {})
    target_requirements = state.get("target_requirements", "")
    composition = state.get("coating_composition", {})
    params = state.get("process_params", {})
    
    # 生成三类优化建议 - 分别为每类生成
    suggestions = {}
    
    llm = get_material_expert_llm()
    
    current_performance = state.get("performance_prediction", {})
    target_requirements = state.get("target_requirements", "")
    composition = state.get("coating_composition", {})
    
    p1_prompt = f"""
作为材料专家，请基于当前涂层性能生成P1成分优化建议：

**当前参数：**
- 成分: Al {composition.get('al_content', 0)}%, Ti {composition.get('ti_content', 0)}%, N {composition.get('n_content', 0)}%
- 当前硬度: {current_performance.get('hardness', 0)} GPa
- 目标需求: {target_requirements}

**任务：**
请给出**1个**最优的成分优化方案，包含以下内容：
1. 方案名称（简短描述）
2. 具体的成分调整（需要精确数值）
3. 预期硬度提升范围
4. 实施难度（低/中/高）
5. 科学原理解释
6. 预期成本和周期

优化方向：
- 调整Al/Ti比例
- 添加Cr、Si、Y等微量元素
- 优化N含量

请以Markdown格式输出，清晰分条列出。
注意：只需要1个综合最优的方案，不要生成多个方案。
"""
    
    p1_content = ""
    try:
        logger.info("[P1成分优化] 开始LLM流式生成...")
        for chunk in llm.stream([
            SystemMessage(content=MATERIAL_EXPERT_PROMPT),
            HumanMessage(content=p1_prompt)
        ]):
            if hasattr(chunk, 'content') and chunk.content:
                p1_content += chunk.content
                # 直接发送流式chunk到前端
                send_stream_chunk_sync("p1_composition_optimization", chunk.content)
        logger.info(f"[P1成分优化] 建议生成完成，长度: {len(p1_content)}")
    except Exception as e:
        logger.error(f"[P1成分优化] 失败: {str(e)}")
        p1_content = "成分优化建议生成失败，请稍后重试"
    
    # 解析建议为结构化数据
    p1_suggestions = parse_optimization_suggestions(p1_content, "P1_成分优化")
    
    return {
        "p1_suggestions": p1_suggestions,
        "p1_content": p1_content
    }
    


def p2_structure_optimization_node(state: CoatingWorkflowState) -> Dict:
    """
    P2结构优化建议生成节点
    - 多层结构设计
    - 梯度结构设计
    - 纳米复合结构
    """
    logger.info(f"[P2结构优化] 任务 {state['task_id']} 开始")
    
    llm = get_material_expert_llm()
    
    current_performance = state.get("performance_prediction", {})
    target_requirements = state.get("target_requirements", "")
    structure = state.get("structure_design", {})
    
    p2_prompt = f"""
作为材料专家，请基于当前涂层性能生成P2结构优化建议：

**当前参数：**
- 结构类型: {structure.get('layer_type', '单层')}
- 总厚度: {structure.get('total_thickness', 0)} μm
- 当前硬度: {current_performance.get('hardness', 0)} GPa
- 当前结合力: {current_performance.get('adhesion_level', 'N/A')}
- 目标需求: {target_requirements}

**任务：**
请给出**1个**最优的结构优化方案，包含以下内容：
1. 方案名称
2. 详细的结构设计（层数、厚度、周期等）
3. 预期性能提升
4. 实施难度
5. 科学原理
6. 成本和周期

优化方向：
- 单层 vs 多层 vs 纳米复合
- 梯度结构设计
- 层厚和周期优化

请以Markdown格式输出，清晰分条列出。
注意：只需要1个综合最优的方案，不要生成多个方案。
"""
    
    p2_content = ""
    try:
        logger.info("[P2结构优化] 开始LLM流式生成...")
        for chunk in llm.stream([
            SystemMessage(content=MATERIAL_EXPERT_PROMPT),
            HumanMessage(content=p2_prompt)
        ]):
            if hasattr(chunk, 'content') and chunk.content:
                p2_content += chunk.content
                # 直接发送流式chunk到前端
                send_stream_chunk_sync("p2_structure_optimization", chunk.content)
        logger.info(f"[P2结构优化] 建议生成完成，长度: {len(p2_content)}")
    except Exception as e:
        logger.error(f"[P2结构优化] 失败: {str(e)}")
        p2_content = "结构优化建议生成失败，请稍后重试"
    
    p2_suggestions = parse_optimization_suggestions(p2_content, "P2_结构优化")
    
    return {
        "p2_suggestions": p2_suggestions,
        "p2_content": p2_content
    }
    


def p3_process_optimization_node(state: CoatingWorkflowState) -> Dict:
    """
    P3工艺优化建议生成节点
    - 调整沉积参数
    - 优化气氛控制
    - 改进温度曲线
    """
    logger.info(f"[P3工艺优化] 任务 {state['task_id']} 开始")
    
    llm = get_material_expert_llm()
    
    current_performance = state.get("performance_prediction", {})
    target_requirements = state.get("target_requirements", "")
    params = state.get("process_params", {})
    
    p3_prompt = f"""
作为材料专家，请基于当前涂层性能生成P3工艺优化建议：

**当前参数：**
- 沉积气压: {params.get('deposition_pressure', 0)} Pa
- 偏压: {params.get('bias_voltage', 0)} V
- 沉积温度: {params.get('deposition_temperature', 0)} ℃
- N2流量: {params.get('n2_flow', 0)} sccm
- Ar流量: {params.get('ar_flow', 0)} sccm
- 当前硬度: {current_performance.get('hardness', 0)} GPa
- 目标需求: {target_requirements}

**任务：**
请给出**1个**最优的工艺优化方案，包含以下内容：
1. 方案名称
2. 具体的工艺参数调整（需要精确数值）
3. 预期性能提升
4. 实施难度
5. 科学原理
6. 成本和周期

优化方向：
- 沉积温度调整
- 偏压优化
- 气体流量配比
- 靶材功率控制

请以Markdown格式输出，清晰分条列出。
注意：只需要1个综合最优的方案，不要生成多个方案。
"""
    
    p3_content = ""
    try:
        logger.info("[P3工艺优化] 开始LLM流式生成...")
        for chunk in llm.stream([
            SystemMessage(content=MATERIAL_EXPERT_PROMPT),
            HumanMessage(content=p3_prompt)
        ]):
            if hasattr(chunk, 'content') and chunk.content:
                p3_content += chunk.content
                # 直接发送流式chunk到前端
                send_stream_chunk_sync("p3_process_optimization", chunk.content)
        logger.info(f"[P3工艺优化] 建议生成完成，长度: {len(p3_content)}")
    except Exception as e:
        logger.error(f"[P3工艺优化] 失败: {str(e)}")
        p3_content = "工艺优化建议生成失败，请稍后重试"
    
    p3_suggestions = parse_optimization_suggestions(p3_content, "P3_工艺优化")
    
    return {
        "p3_suggestions": p3_suggestions,
        "p3_content": p3_content
    }


def optimization_summary_node(state: CoatingWorkflowState) -> Dict:
    """
    优化建议汇总节点
    汇总P1/P2/P3三类建议，包含完整内容和结构化建议，并生成综合推荐
    """
    logger.info(f"[优化汇总] 任务 {state['task_id']}")
    
    # 获取完整内容
    p1_content = state.get("p1_content", "")
    p2_content = state.get("p2_content", "")
    p3_content = state.get("p3_content", "")
    
    # 获取结构化建议（限制每个最多1个）
    p1_suggestions = state.get("p1_suggestions", [])[:1]
    p2_suggestions = state.get("p2_suggestions", [])[:1]
    p3_suggestions = state.get("p3_suggestions", [])[:1]
    
    logger.info(f"[优化汇总] P1方案数: {len(p1_suggestions)}, P2方案数: {len(p2_suggestions)}, P3方案数: {len(p3_suggestions)}")
    
    # 如果结构化建议为空或解析失败，创建基于完整内容的默认建议
    if not p1_suggestions and p1_content:
        p1_suggestions = [{
            "type": "P1_成分优化",
            "description": "详见完整建议内容",
            "full_content": p1_content,
            "expected_hardness_increase": 2.0,
            "implementation_difficulty": "中",
            "priority": 1
        }]
    
    if not p2_suggestions and p2_content:
        p2_suggestions = [{
            "type": "P2_结构优化",
            "description": "详见完整建议内容",
            "full_content": p2_content,
            "expected_hardness_increase": 2.0,
            "implementation_difficulty": "中",
            "priority": 1
        }]
    
    if not p3_suggestions and p3_content:
        p3_suggestions = [{
            "type": "P3_工艺优化",
            "description": "详见完整建议内容",
            "full_content": p3_content,
            "expected_hardness_increase": 2.0,
            "implementation_difficulty": "中",
            "priority": 1
        }]
    
    # 为每个建议添加完整内容
    for suggestion in p1_suggestions:
        if "full_content" not in suggestion:
            suggestion["full_content"] = p1_content
    
    for suggestion in p2_suggestions:
        if "full_content" not in suggestion:
            suggestion["full_content"] = p2_content
    
    for suggestion in p3_suggestions:
        if "full_content" not in suggestion:
            suggestion["full_content"] = p3_content
    
    optimization_suggestions = {
        "P1_成分优化": p1_suggestions,
        "P2_结构优化": p2_suggestions,
        "P3_工艺优化": p3_suggestions
    }
    
    # 同时保存完整内容供参考
    optimization_contents = {
        "P1_成分优化": p1_content,
        "P2_结构优化": p2_content,
        "P3_工艺优化": p3_content
    }
    
    # 生成综合建议（由LLM分析三类方案并给出推荐）
    comprehensive_recommendation = ""
    try:
        llm = get_material_expert_llm()
        
        # 提取每个方案的关键信息
        p1_summary = p1_suggestions[0].get("description", "无") if p1_suggestions else "无方案"
        p2_summary = p2_suggestions[0].get("description", "无") if p2_suggestions else "无方案"
        p3_summary = p3_suggestions[0].get("description", "无") if p3_suggestions else "无方案"
        
        p1_difficulty = p1_suggestions[0].get("implementation_difficulty", "中") if p1_suggestions else "中"
        p2_difficulty = p2_suggestions[0].get("implementation_difficulty", "中") if p2_suggestions else "中"
        p3_difficulty = p3_suggestions[0].get("implementation_difficulty", "中") if p3_suggestions else "中"
        
        p1_increase = p1_suggestions[0].get("expected_hardness_increase", 0) if p1_suggestions else 0
        p2_increase = p2_suggestions[0].get("expected_hardness_increase", 0) if p2_suggestions else 0
        p3_increase = p3_suggestions[0].get("expected_hardness_increase", 0) if p3_suggestions else 0
        
        current_performance = state.get("performance_prediction", {})
        target_requirements = state.get("target_requirements", "")
        
        recommendation_prompt = f"""
作为材料专家，请基于以下三类优化方案，给出综合推荐建议：

**当前性能：**
- 硬度: {current_performance.get('hardness', 0)} GPa
- 目标需求: {target_requirements}

**三类优化方案概览：**

**P1 - 成分优化：**
- 方案摘要: {p1_summary}
- 预期硬度提升: +{p1_increase} GPa
- 实施难度: {p1_difficulty}

**P2 - 结构优化：**
- 方案摘要: {p2_summary}
- 预期硬度提升: +{p2_increase} GPa
- 实施难度: {p2_difficulty}

**P3 - 工艺优化：**
- 方案摘要: {p3_summary}
- 预期硬度提升: +{p3_increase} GPa
- 实施难度: {p3_difficulty}

**任务：**
请给出综合建议，包含：
1. **推荐优先级**：基于预期效果、实施难度、成本等因素，推荐优先选择哪个方案
2. **选择理由**：详细说明为什么推荐该方案（考虑当前性能、目标需求、技术可行性、经济性等）
3. **实施建议**：如何实施该方案，注意事项
4. **组合可能性**（可选）：是否可以考虑多个方案组合实施
**注意：**
1. 不要出现人名

请以Markdown格式输出，简洁专业。
"""
        
        logger.info("[综合建议] 开始LLM生成...")
        from langchain_core.messages import SystemMessage, HumanMessage
        
        for chunk in llm.stream([
            SystemMessage(content=MATERIAL_EXPERT_PROMPT),
            HumanMessage(content=recommendation_prompt)
        ]):
            if hasattr(chunk, 'content') and chunk.content:
                comprehensive_recommendation += chunk.content
                # 流式发送
                send_stream_chunk_sync("optimization_summary", chunk.content)
        
        logger.info(f"[综合建议] 生成完成，长度: {len(comprehensive_recommendation)}")
    except Exception as e:
        logger.error(f"[综合建议] 生成失败: {str(e)}")
        comprehensive_recommendation = "综合建议生成失败，请根据各方案的具体情况自行判断。"
    
    logger.info(f"[优化汇总] 完成 - P1方案数: {len(p1_suggestions)}, P2方案数: {len(p2_suggestions)}, P3方案数: {len(p3_suggestions)}")
    
    return {
        "optimization_suggestions": optimization_suggestions,
        "optimization_contents": optimization_contents,
        "comprehensive_recommendation": comprehensive_recommendation,  # 新增：综合建议
        "current_step": "optimization_summary",
        "workflow_status": "awaiting_optimization_selection"
    }


def iteration_planning_node(state: CoatingWorkflowState) -> Dict:
    """
    迭代优化规划节点
    制定迭代优化计划
    """
    logger.info(f"制定任务 {state['task_id']} 的迭代计划")
    
    selected_optimization = state.get("selected_optimization_plan", {})
    current_iteration = state.get("current_iteration", 0)
    max_iterations = state.get("max_iterations", 5)
    
    # 检查是否达到收敛条件
    convergence_achieved = check_convergence(
        state.get("iteration_history", []),
        state.get("experimental_results", {})
    )
    
    if convergence_achieved or current_iteration >= max_iterations:
        return {
            "convergence_achieved": True,
            "current_step": "iteration_complete",
            "next_step": "result_summary",
            "workflow_status": "completed"
        }
    
    # 生成下一步迭代计划
    iteration_plan = {
        "iteration_number": current_iteration + 1,
        "optimization_action": selected_optimization,
        "expected_results": calculate_expected_results(selected_optimization),
        "experiment_design": design_experiment(selected_optimization),
        "success_criteria": define_success_criteria(state.get("target_requirements", ""))
    }
    
    # 更新迭代历史
    iteration_history = state.get("iteration_history", [])
    iteration_history.append(iteration_plan)
    
    return {
        "current_iteration": current_iteration + 1,
        "iteration_history": iteration_history,
        "current_step": "iteration_planned",
        "next_step": "await_experiment",
        "workflow_status": "iterating"
    }


def result_summary_node(state: CoatingWorkflowState) -> Dict:
    """
    结果汇总节点
    生成最终的优化报告
    """
    logger.info(f"生成任务 {state['task_id']} 的结果汇总")
    
    llm = get_material_expert_llm()
    
    # 汇总所有结果
    summary_prompt = f"""
    请生成涂层优化的完整报告：
    
    初始参数：
    - 成分: {json.dumps(state.get("coating_composition", {}), ensure_ascii=False)}
    - 工艺: {json.dumps(state.get("process_params", {}), ensure_ascii=False)}
    
    预测性能：
    {json.dumps(state.get("performance_prediction", {}), ensure_ascii=False, indent=2)}
    
    优化历程：
    - 迭代次数: {state.get("current_iteration", 0)}
    - 最终性能: {json.dumps(state.get("experimental_results", {}), ensure_ascii=False)}
    
    请总结：
    1. 关键改进点
    2. 性能提升幅度
    3. 后续建议
    """
    
    response = llm.invoke([
        SystemMessage(content=MATERIAL_EXPERT_PROMPT),
        HumanMessage(content=summary_prompt)
    ])
    
    summary = {
        "task_id": state["task_id"],
        "initial_performance": state.get("performance_prediction", {}),
        "final_performance": state.get("experimental_results", {}),
        "total_iterations": state.get("current_iteration", 0),
        "key_improvements": response.content,
        "recommendations": "继续优化工艺参数以进一步提升性能"
    }
    
    return {
        "stream_outputs": state.get("stream_outputs", []) + [summary],
        "current_step": "completed",
        "next_step": None,
        "workflow_status": "completed"
    }


# 辅助函数

def normalize_composition(composition: Dict[str, float]) -> Dict[str, float]:
    """归一化成分到100%"""
    # 过滤掉None值，只计算数值
    valid_values = {k: v for k, v in composition.items() if v is not None}
    total = sum(valid_values.values())
    if total == 0:
        return composition
    return {k: (v/total)*100 if v is not None else v for k, v in composition.items()}


def analyze_root_causes(composition: Dict, params: Dict, prediction: Dict) -> str:
    """分析性能的根本原因"""
    analysis = []
    
    # 基于成分分析
    if composition.get("al_content", 0) > 30:
        analysis.append("高Al含量有助于提高硬度和抗氧化性")
    
    # 基于工艺分析  
    if params.get("bias_voltage", 0) > 100:
        analysis.append("高偏压促进致密化，提高结合力")
    
    return "；".join(analysis) if analysis else "性能主要由成分和工艺共同决定"


def check_convergence(history: List, results: Dict) -> bool:
    """检查是否达到收敛条件"""
    if len(history) < 2:
        return False
    
    # 检查性能改进是否趋于稳定
    if len(history) >= 3:
        recent_improvements = [h.get("expected_results", {}).get("improvement", 0) for h in history[-3:]]
        if all(imp < 0.5 for imp in recent_improvements):  # 改进小于0.5%
            return True
    
    return False


def calculate_expected_results(optimization: Dict) -> Dict:
    """计算优化的预期结果"""
    return {
        "improvement": optimization.get("expected_improvement", 0),
        "confidence": 0.8
    }


def design_experiment(optimization: Dict) -> Dict:
    """设计验证实验"""
    return {
        "experiment_type": "coating_deposition",
        "parameters": optimization,
        "characterization": ["XRD", "SEM", "硬度测试", "划痕测试"]
    }


def define_success_criteria(requirements: str) -> Dict:
    """定义成功标准"""
    return {
        "hardness_target": 30.0,  # GPa
        "adhesion_target": "HF1",
        "improvement_threshold": 5.0  # %
    }


def parse_optimization_suggestions(llm_output: str, opt_type: str) -> List[Dict]:
    """
    解析LLM输出的优化建议
    
    Args:
        llm_output: LLM流式生成的建议内容
        opt_type: 优化类型（成分优化/结构优化/工艺优化）
    
    Returns:
        解析后的建议列表
    """
    import re
    
    suggestions = []
    
    # 只生成1个方案，直接使用完整内容
    # 不再按标题分割，将整个LLM输出作为一个完整方案
    
    # 提取前几行作为描述
    first_lines = []
    for line in llm_output.split('\n')[:5]:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('---'):
            # 去除列表标记
            line = re.sub(r'^[-*]\s*', '', line)
            first_lines.append(line)
            if len(' '.join(first_lines)) > 100:
                break
    
    description = ' '.join(first_lines)
    if len(description) > 150:
        description = description[:147] + "..."
    elif not description:
        description = "详见完整建议内容"
    
    # 从LLM输出中提取难度和预期提升（改进的正则匹配）
    difficulty = "中"
    expected_increase = 2.0
    
    # 匹配实施难度（支持更多表达方式）
    difficulty_patterns = [
        r'(?:实施)?难度[:：\s]*([低中高较][\u4e00-\u9fa5]{0,2})',  # 难度: 低/中/高/较低/较高
        r'难度.*?([低中高])',
        r'(?:实施|技术)难度.*?([容易简单中等困难复杂])',
    ]
    
    for pattern in difficulty_patterns:
        match = re.search(pattern, llm_output, re.IGNORECASE)
        if match:
            difficulty_text = match.group(1)
            # 标准化难度
            if '低' in difficulty_text or '易' in difficulty_text or '简单' in difficulty_text:
                difficulty = "低"
            elif '高' in difficulty_text or '难' in difficulty_text or '复杂' in difficulty_text:
                difficulty = "高"
            else:
                difficulty = "中"
            break
    
    # 匹配预期硬度提升（支持更多表达方式并验证合理性）
    hardness_patterns = [
        r'预期.*?提升.*?([+]?\s*\d+\.?\d*)\s*GPa',  # 预期提升: +2 GPa
        r'硬度.*?提升.*?([+]?\s*\d+\.?\d*)\s*GPa',  # 硬度提升: 2 GPa
        r'提升.*?硬度.*?([+]?\s*\d+\.?\d*)\s*GPa',  # 提升硬度: 2 GPa
        r'[+]\s*(\d+\.?\d*)\s*GPa',  # +2 GPa
        r'(\d+\.?\d*)\s*[-~至]\s*(\d+\.?\d*)\s*GPa',  # 2-3 GPa（取平均值）
        r'提升\s*(\d+\.?\d*)\s*GPa',  # 提升2 GPa
    ]
    
    for pattern in hardness_patterns:
        match = re.search(pattern, llm_output, re.IGNORECASE)
        if match:
            try:
                value = match.group(1).replace('+', '').strip()
                expected_increase = float(value)
                
                # 如果是范围值，取平均
                if ('-' in pattern or '~' in pattern or '至' in pattern) and match.lastindex >= 2:
                    try:
                        value2 = match.group(2).replace('+', '').strip()
                        expected_increase = (float(value) + float(value2)) / 2
                    except (ValueError, IndexError, AttributeError):
                        pass
                
                # 合理性检查：提升值通常在0.5-15 GPa之间
                if 0.5 <= expected_increase <= 15:
                    break
                else:
                    expected_increase = 2.0  # 不合理则使用默认值
            except (ValueError, IndexError, AttributeError):
                continue
    
    # 只创建1个方案
    suggestions.append({
        "type": opt_type,
        "description": description,
        "expected_hardness_increase": expected_increase,
        "implementation_difficulty": difficulty,
        "priority": 1,
        "full_content": llm_output
    })
    
    logger.info(f"[{opt_type}] 生成1个方案 - 难度:{difficulty}, 预期提升:{expected_increase}GPa")
    return suggestions
    
    # 下面的循环代码已废弃，保留供参考
    if False:
        # 尝试按"方案"关键词分割（只识别明确的方案标题）
        # 匹配"方案一"、"方案1"、"方案 1"等格式
        sections = re.split(r'\n(?=#{1,3}\s*.*?方案\s*[一二三1-3]|.*?方案\s*[一二三1-3].*?[:：])', llm_output)
        
        for section in sections:
            section = section.strip()
            if not section or len(section) < 10:  # 忽略太短的内容
                continue
            
            # 限制最多1个方案
            if len(suggestions) >= 1:
                logger.info(f"[{opt_type}] 已达到1个方案上限，停止解析")
                break
        
        lines = section.split('\n')
        title_line = lines[0].strip()
        
        # 提取标题作为description（去除markdown标记）
        description = re.sub(r'^#{1,3}\s*', '', title_line)
        description = re.sub(r'\*\*', '', description)  # 去除加粗
        
        # 提取前几行作为摘要（如果有的话）
        summary_lines = []
        for line in lines[1:6]:  # 取前5行非空内容
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('---'):
                # 去除列表标记
                line = re.sub(r'^[-*]\s*', '', line)
                summary_lines.append(line)
                if len(summary_lines) >= 2:  # 最多2行摘要
                    break
        
        # 合并标题和摘要
        if summary_lines:
            description = f"{description}: {' '.join(summary_lines[:1])}"
        
        # 限制描述长度
        if len(description) > 150:
            description = description[:147] + "..."
        
        suggestions.append({
            "type": opt_type,
            "description": description,
            "expected_hardness_increase": 2.0,  # 默认值
            "implementation_difficulty": "中",
            "priority": len(suggestions) + 1,
            "full_content": section
        })
    
    # 如果解析失败，返回默认建议（使用完整内容）
    if not suggestions:
        # 提取前200字符作为摘要
        first_lines = []
        for line in llm_output.split('\n')[:5]:
            line = line.strip()
            if line and not line.startswith('#'):
                line = re.sub(r'^[-*]\s*', '', line)
                first_lines.append(line)
                if len(' '.join(first_lines)) > 100:
                    break
        
        description = ' '.join(first_lines)
        if len(description) > 150:
            description = description[:147] + "..."
        elif not description:
            description = "详见完整建议内容"
        
        suggestions = [{
            "type": opt_type,
            "description": description,
            "expected_hardness_increase": 2.0,
            "implementation_difficulty": "中",
            "priority": 1,
            "full_content": llm_output
        }]
    
    return suggestions


# ==================== 实验闭环节点（从experiment_nodes.py整合） ====================

def await_user_selection_node(state: CoatingWorkflowState):
    """等待用户选择优化方案节点 - 使用interrupt暂停工作流"""
    from langgraph.types import interrupt
    
    logger.info(f"等待用户选择优化方案")
    
    suggestions = state.get("optimization_suggestions", {})
    comprehensive_recommendation = state.get("comprehensive_recommendation", "")
    
    # 准备选择选项
    options = []
    for opt_type, suggestions_list in suggestions.items():
        for idx, suggestion in enumerate(suggestions_list):
            options.append({
                "id": f"{opt_type}_{idx}",
                "type": opt_type,
                "description": suggestion.get("description", ""),
                "expected_improvement": suggestion.get("expected_improvement", 0)
            })
    
    # 使用interrupt()暂停工作流，等待用户输入
    user_selection = interrupt({
        "type": "user_selection_required",
        "options": options,
        "message": "请选择一个优化方案进行实施",
        "suggestions": suggestions,  # 传递完整的建议数据
        "comprehensive_recommendation": comprehensive_recommendation  # 传递综合建议
    })
    
    logger.info(f"用户选择: {user_selection}")
    
    return {
        "selected_optimization_plan": user_selection,
        "current_step": "user_selected",
        "workflow_status": "selection_confirmed"
    }


def performance_improvement_prediction_node(state: CoatingWorkflowState) -> Dict:
    """
    性能提升预测节点
    使用TopPhi模拟 + ML模型预测所选优化方案的性能提升
    """
    logger.info(f"[性能提升预测] 任务 {state['task_id']} 开始")
    
    selected_plan = state.get("selected_optimization_plan", {})
    current_performance = state.get("performance_prediction", {})
    
    # 构建优化后的参数
    optimized_params = apply_optimization_to_params(
        current_composition=state.get("coating_composition", {}),
        current_process=state.get("process_params", {}),
        current_structure=state.get("structure_design", {}),
        optimization_plan=selected_plan
    )
    
    # TODO: 接入MCP工具 - TopPhi模拟优化后的性能
    # TODO: 接入MCP工具 - ML模型预测优化后的性能
    
    # 当前使用示例数据模拟
    predicted_improvement = {
        "current_hardness": current_performance.get("hardness", 28.5),
        "predicted_hardness": 32.3,
        "improvement_value": 3.8,
        "improvement_percentage": 13.3,
        "confidence": 0.82,
        "risk_assessment": "低风险",
        "key_factors": [
            "Al含量提升导致AlN相增加",
            "晶粒细化效应增强",
            "残余压应力提高"
        ],
        "uncertainty": {
            "hardness_range": [31.5, 33.1],
            "factors": ["成分控制精度", "工艺稳定性"]
        }
    }
    
    logger.info(f"[性能提升预测] 完成 - 预测硬度: {predicted_improvement['predicted_hardness']} GPa")
    
    return {
        "performance_improvement": predicted_improvement,
        "optimized_parameters": optimized_params,
        "current_step": "improvement_predicted"
    }


def experiment_workorder_generation_node(state: CoatingWorkflowState) -> Dict:
    """
    自动生成标准化实验工单（使用LLM流式输出）
    """
    from datetime import datetime
    
    logger.info(f"[实验工单生成] 任务 {state['task_id']}")
    
    llm = get_material_expert_llm()
    selected_plan = state.get("selected_optimization_plan", {})
    optimized_params = state.get("optimized_parameters", {})
    predicted = state.get("performance_improvement", {})
    
    # 生成工单ID
    workorder_id = f"WO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 构建LLM提示生成详细实验工单
    prompt = f"""
作为材料实验专家，请生成详细的涂层制备实验工单：

**工单编号：** {workorder_id}
**实验类型：** {selected_plan.get('type', '涂层优化实验')}

**优化目标：**
- 当前硬度: {predicted.get('current_hardness', 0)} GPa
- 目标硬度: {predicted.get('predicted_hardness', 0)} GPa
- 预期提升: {predicted.get('improvement_percentage', 0):.1f}%

**优化后参数：**
成分: {json.dumps(optimized_params.get('composition', {}), ensure_ascii=False)}
工艺: {json.dumps(optimized_params.get('process_params', {}), ensure_ascii=False)}
结构: {json.dumps(optimized_params.get('structure_design', {}), ensure_ascii=False)}

请生成完整实验工单，包括：

## 1. 实验目标与背景

## 2. 基片准备
- 材料规格
- 预处理步骤

## 3. 沉积工艺流程
- 设备准备
- 工艺参数设置（详细列出每个参数）
- 操作步骤

## 4. 质量控制要求
- 厚度测量
- 硬度测试
- 结合力测试
- 其他表征

## 5. 安全注意事项

## 6. 预计工期

不要出现人物和单位等

使用Markdown格式，专业规范。
"""
    
    workorder_content = ""
    try:
        logger.info("[实验工单] 开始LLM流式生成...")
        for chunk in llm.stream([
            SystemMessage(content=MATERIAL_EXPERT_PROMPT),
            HumanMessage(content=prompt)
        ]):
            if hasattr(chunk, 'content') and chunk.content:
                workorder_content += chunk.content
                # 流式发送
                send_stream_chunk_sync("experiment_workorder_generation", chunk.content)
        logger.info(f"[实验工单] 生成完成 - 工单ID: {workorder_id}")
    except Exception as e:
        logger.error(f"[实验工单] 生成失败: {str(e)}")
        workorder_content = "实验工单生成失败，请稍后重试"
    
    workorder = {
        "workorder_id": workorder_id,
        "created_at": datetime.now().isoformat(),
        "content": workorder_content,
        "optimization_type": selected_plan.get("type", ""),
        "predicted_improvement": predicted,
        "parameters": optimized_params
    }
    
    return {
        "experiment_workorder": workorder,
        "workflow_status": "workorder_generated",
        "current_step": "workorder_ready"
    }


def await_experiment_results_node(state: CoatingWorkflowState) -> Dict:
    """等待用户输入实验测试结果
    
    当前使用示例数据演示完整迭代流程
    TODO: 后续改为真正等待用户输入
    """
    logger.info(f"[等待实验结果] 任务 {state['task_id']}")
    
    workorder = state.get("experiment_workorder", {})
    
    # 检查是否已有实验结果（用户输入后恢复）
    if state.get("experiment_results"):
        logger.info(f"[等待实验结果] 已收到实验结果，继续执行")
        return {
            "workflow_status": "experiment_results_received",
            "current_step": "results_received"
        }
    
    # 暂停等待用户输入实验结果
    logger.info(f"[等待实验结果] 等待用户手动输入实验测试数据")
    
    # 返回等待状态，触发工作流暂停
    return {
        "workflow_status": "awaiting_experiment_results",
        "workorder_id": workorder.get("workorder_id", ""),
        "current_step": "awaiting_results",
        # 告知前端需要采集的数据字段
        "required_data": {
            "hardness": {"type": "float", "unit": "GPa", "description": "涂层硬度"},
            "hardness_std": {"type": "float", "unit": "GPa", "description": "硬度标准差"},
            "adhesion_level": {"type": "string", "description": "结合力等级 (如HF1-HF6)"},
            "wear_rate": {"type": "float", "unit": "mm³/Nm", "description": "磨损率"},
            "coating_thickness": {"type": "float", "unit": "μm", "description": "涂层厚度"},
            "oxidation_temperature": {"type": "float", "unit": "℃", "description": "氧化温度"},
            "test_date": {"type": "string", "description": "测试日期"},
            "operator": {"type": "string", "description": "操作员"}
        }
    }


def experiment_result_analysis_node(state: CoatingWorkflowState) -> Dict:
    """
    分析实验结果 vs 预测结果
    使用LLM生成根因分析和改进建议
    """
    logger.info(f"[实验结果分析] 任务 {state['task_id']}")
    
    llm = get_material_expert_llm()
    
    predicted = state.get("performance_improvement", {})
    actual = state.get("experiment_results", {})
    workorder = state.get("experiment_workorder", {})
    
    # 计算偏差
    comparison = calculate_prediction_deviation(predicted, actual)
    
    # 构建分析提示
    analysis_prompt = f"""
作为材料专家，请分析以下实验结果：

**实验工单：** {workorder.get('workorder_id', '')}

**预测性能：**
- 硬度预测: {predicted.get('predicted_hardness', 0)} GPa
- 置信区间: [{predicted.get('uncertainty', {}).get('hardness_range', [0, 0])[0]}, 
              {predicted.get('uncertainty', {}).get('hardness_range', [0, 0])[1]}] GPa

**实际性能：**
- 实测硬度: {actual.get('hardness', 0)} ± {actual.get('hardness_std', 0)} GPa
- 结合力等级: {actual.get('adhesion_level', 'N/A')}

**偏差分析：**
- 硬度偏差: {comparison['hardness']['deviation']:.2f} GPa ({comparison['hardness']['deviation_percentage']:.1f}%)
- 是否在置信区间内: {comparison['hardness']['within_confidence']}

**请分析：**
1. 结果评价：实验结果是否符合预期？
2. 偏差原因：可能的原因分析
3. 改进建议：下一步应该如何调整？
4. 迭代方向：继续当前方向还是尝试其他方案？

请以Markdown格式输出。
"""
    
    analysis_content = ""
    try:
        logger.info("[实验结果分析] 开始LLM流式生成...")
        for chunk in llm.stream([
            SystemMessage(content=MATERIAL_EXPERT_PROMPT),
            HumanMessage(content=analysis_prompt)
        ]):
            if hasattr(chunk, 'content') and chunk.content:
                analysis_content += chunk.content
                send_stream_chunk_sync("experiment_result_analysis", chunk.content)
        logger.info("[实验结果分析] 分析报告生成完成")
    except Exception as e:
        logger.error(f"[实验结果分析] 失败: {str(e)}")
        analysis_content = "实验结果分析失败，请稍后重试"
    
    # 评估实验成功度
    success_level = evaluate_experiment_success(
        predicted=predicted,
        actual=actual,
        target=state.get("target_requirements", "")
    )
    
    # 判断是否达到目标
    target_hardness = extract_target_hardness(state.get("target_requirements", ""))
    target_achieved = actual.get("hardness", 0) >= target_hardness
    
    experiment_analysis = {
        "comparison": comparison,
        "analysis_report": analysis_content,
        "success_level": success_level,
        "target_achieved": target_achieved
    }
    
    logger.info(f"[实验结果分析] 完成 - 成功等级: {success_level}")
    
    return {
        "experiment_analysis": experiment_analysis,
        "current_step": "analysis_complete",
        "workflow_status": "analyzed"
    }


def decide_next_iteration_node(state: CoatingWorkflowState) -> Dict:
    """
    决策下一步迭代
    基于实验结果决定：完成 | 继续当前方向 | 尝试其他方案
    """
    logger.info(f"[迭代决策] 任务 {state['task_id']}")
    
    analysis = state.get("experiment_analysis", {})
    iteration_count = state.get("iteration_count", 0) + 1
    
    # 决策逻辑
    if analysis.get("target_achieved", False):
        next_action = "complete"
        next_step = "result_summary"
        reason = "已达到目标性能"
    elif analysis.get("success_level") in ["excellent", "good"]:
        next_action = "continue_current"
        next_step = "performance_improvement_prediction"
        reason = "当前方向效果良好，继续优化"
    elif iteration_count >= 5:
        next_action = "complete"
        next_step = "result_summary"
        reason = "达到最大迭代次数"
    else:
        next_action = "try_other"
        next_step = "p1_composition_optimization"
        reason = "当前方向效果不佳，尝试其他优化方案"
    
    logger.info(f"[迭代决策] 决定: {next_action} - {reason}")
    
    return {
        "next_action": next_action,
        "next_step": next_step,
        "decision_reason": reason,
        "iteration_count": iteration_count,
        "workflow_status": "iteration_decided"
    }


def await_plan_confirmation_node(state: CoatingWorkflowState) -> Dict:
    """
    等待用户确认或调整优化方案细节（可选节点）
    """
    logger.info(f"[等待确认] 任务 {state['task_id']}")
    
    return {
        "workflow_status": "awaiting_plan_confirmation",
        "optimization_plan": state.get("selected_optimization_plan", {}),
        "predicted_improvement": state.get("performance_improvement", {}),
        "optimized_parameters": state.get("optimized_parameters", {}),
        "editable_params": True,  # 允许用户微调参数
        "current_step": "awaiting_confirmation"
    }


# ==================== 辅助函数（从experiment_nodes.py整合） ====================

def apply_optimization_to_params(
    current_composition: Dict,
    current_process: Dict,
    current_structure: Dict,
    optimization_plan: Dict
) -> Dict:
    """应用优化方案到参数"""
    optimized = {
        "composition": current_composition.copy(),
        "process_params": current_process.copy(),
        "structure_design": current_structure.copy()
    }
    
    # 根据优化类型应用变更
    opt_type = optimization_plan.get("type", "")
    changes = optimization_plan.get("changes", {})
    
    if "P1" in opt_type or "成分" in opt_type:
        optimized["composition"].update(changes.get("composition", {}))
    elif "P2" in opt_type or "结构" in opt_type:
        optimized["structure_design"].update(changes.get("structure", {}))
    elif "P3" in opt_type or "工艺" in opt_type:
        optimized["process_params"].update(changes.get("process", {}))
    
    return optimized


def calculate_prediction_deviation(predicted: Dict, actual: Dict) -> Dict:
    """计算预测偏差"""
    pred_hardness = predicted.get("predicted_hardness", 0)
    actual_hardness = actual.get("hardness", 0)
    confidence_range = predicted.get("uncertainty", {}).get("hardness_range", [pred_hardness, pred_hardness])
    
    deviation = actual_hardness - pred_hardness
    deviation_pct = (deviation / pred_hardness * 100) if pred_hardness > 0 else 0
    within_confidence = confidence_range[0] <= actual_hardness <= confidence_range[1]
    
    return {
        "hardness": {
            "predicted": pred_hardness,
            "actual": actual_hardness,
            "deviation": deviation,
            "deviation_percentage": deviation_pct,
            "within_confidence": within_confidence
        }
    }


def evaluate_experiment_success(predicted: Dict, actual: Dict, target: str) -> str:
    """评估实验成功等级"""
    deviation_pct = abs(calculate_prediction_deviation(predicted, actual)["hardness"]["deviation_percentage"])
    target_hardness = extract_target_hardness(target)
    actual_hardness = actual.get("hardness", 0)
    
    achieved_target = actual_hardness >= target_hardness
    
    if deviation_pct < 5:
        accuracy = "excellent"
    elif deviation_pct < 10:
        accuracy = "good"
    elif deviation_pct < 20:
        accuracy = "acceptable"
    else:
        accuracy = "poor"
    
    if achieved_target and accuracy in ["excellent", "good"]:
        return "excellent"
    elif achieved_target:
        return "good"
    elif accuracy in ["excellent", "good"]:
        return "acceptable"
    else:
        return "poor"


def extract_target_hardness(target_requirements: str) -> float:
    """从目标需求中提取硬度目标"""
    import re
    match = re.search(r'(\d+\.?\d*)\s*GPa', target_requirements)
    if match:
        return float(match.group(1))
    return 30.0  # 默认目标


def determine_next_step_recommendation(success_level: str, target_achieved: bool) -> str:
    """决定下一步建议"""
    if target_achieved:
        return "目标已达成，建议结束迭代并生成最终报告"
    elif success_level in ["excellent", "good"]:
        return "当前优化方向有效，建议继续当前方向进行参数微调"
    else:
        return "当前方向效果不佳，建议尝试其他优化方案（P1/P2/P3）"


def generate_experiment_procedure(plan: Dict, params: Dict) -> list:
    """生成实验步骤"""
    procedure = [
        {
            "step": 1,
            "title": "设备准备",
            "details": [
                "检查真空系统漏率<5×10⁻⁴ Pa",
                "清洁靶材表面",
                "安装基片到旋转夹具"
            ],
            "duration": "30分钟"
        },
        {
            "step": 2,
            "title": "基片预处理",
            "details": [
                "Ar离子轰击清洗（偏压-800V，15分钟）",
                "升温至沉积温度"
            ],
            "duration": "30分钟"
        },
        {
            "step": 3,
            "title": "涂层沉积",
            "details": [
                f"设置靶功率: {params.get('process_params', {}).get('target_power', 'TBD')} W",
                f"调整偏压: {params.get('process_params', {}).get('bias_voltage', 'TBD')} V",
                f"气体流量: N₂ {params.get('process_params', {}).get('n2_flow', 'TBD')} sccm, "
                f"Ar {params.get('process_params', {}).get('ar_flow', 'TBD')} sccm",
                f"沉积时间: 根据目标厚度 {params.get('structure_design', {}).get('total_thickness', 3)} μm"
            ],
            "duration": "2-4小时"
        },
        {
            "step": 4,
            "title": "后处理",
            "details": [
                "缓慢降温至室温（<10℃/min）",
                "取出样品"
            ],
            "duration": "1小时"
        }
    ]
    
    return procedure
