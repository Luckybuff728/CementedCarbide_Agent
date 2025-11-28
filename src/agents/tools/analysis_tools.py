"""
分析工具 - 性能预测和根因分析相关的原子工具

功能：
1. TopPhi 第一性原理模拟
2. ML 性能预测
3. 历史数据对比
4. 综合根因分析

更新说明 (v2.1)：
- 使用 ToolRuntime 从状态自动获取参数
- 工具无需 LLM 传递复杂参数，减少错误
"""
from typing import Dict, Any
from langchain.tools import tool, ToolRuntime
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


# ==================== Pydantic Schema 定义（保留供参考） ====================
# 注：这些 Schema 不再用于工具参数，因为工具现在从 ToolRuntime 获取状态

class TopPhiSimulationInput(BaseModel):
    """TopPhi 模拟输入参数（仅供参考）"""
    al_content: float = Field(..., description="Al含量 (at.%)")
    ti_content: float = Field(..., description="Ti含量 (at.%)")
    n_content: float = Field(..., description="N含量 (at.%)")
    deposition_temperature: float = Field(..., description="沉积温度 (°C)")
    deposition_pressure: float = Field(default=0.5, description="沉积气压 (Pa)")


# ==================== 工具定义（使用 ToolRuntime） ====================

@tool
def simulate_topphi_tool(runtime: ToolRuntime) -> Dict[str, Any]:
    """
    调用 TopPhi 第一性原理模拟引擎。
    
    自动从当前状态获取成分和工艺参数。
    如需修改参数，请先调用 update_coating_composition 或 update_process_params。
    
    预测涂层的微观结构特性：
    - 晶粒尺寸
    - 择优取向
    - 残余应力
    - 晶格常数
    
    Returns:
        微观结构预测结果
    """
    # 从状态获取参数
    state = runtime.state
    composition = state.get("coating_composition", {})
    process_params = state.get("process_params", {})
    
    al_content = composition.get("al_content", 0) or 0
    ti_content = composition.get("ti_content", 0) or 0
    n_content = composition.get("n_content", 0) or 0
    deposition_temperature = process_params.get("deposition_temperature", 450) or 450
    deposition_pressure = process_params.get("deposition_pressure", 0.5) or 0.5
    
    logger.info(f"[TopPhi] 模拟开始: Al={al_content}%, Ti={ti_content}%, N={n_content}%, T={deposition_temperature}°C")
    
    # 检查是否有必要参数
    if al_content == 0 and ti_content == 0 and n_content == 0:
        return {"error": "未提供涂层成分数据，无法进行 TopPhi 模拟"}
    
    # 调用 TopPhi 服务
    try:
        from ...services.topphi_service import TopPhiService
        service = TopPhiService()
        
        comp_data = {
            "al_content": al_content,
            "ti_content": ti_content,
            "n_content": n_content
        }
        proc_data = {
            "deposition_temperature": deposition_temperature,
            "deposition_pressure": deposition_pressure
        }
        
        result = service.simulate_deposition(comp_data, proc_data)
        logger.info(f"[TopPhi] 模拟完成: 晶粒尺寸={result.get('grain_size_nm', 'N/A')}nm")
        
        return result
        
    except Exception as e:
        logger.error(f"[TopPhi] 模拟失败: {e}")
        return {"error": str(e)}


@tool
def predict_ml_performance_tool(runtime: ToolRuntime) -> Dict[str, Any]:
    """
    使用机器学习模型预测涂层宏观性能。
    
    自动从当前状态获取成分、工艺参数和结构设计。
    如需修改参数，请先调用 update_coating_composition 或 update_process_params。
    
    预测指标：
    - 纳米硬度 (GPa)
    - 弹性模量 (GPa)
    - 磨损率 (mm³/Nm)
    - 结合力 (N)
    
    Returns:
        性能预测结果，包含预测值和置信度
    """
    # 从状态获取参数
    state = runtime.state
    composition = state.get("coating_composition", {})
    process_params = state.get("process_params", {})
    structure_design = state.get("structure_design", {})
    
    al_content = composition.get("al_content", 0) or 0
    ti_content = composition.get("ti_content", 0) or 0
    
    logger.info(f"[ML预测] 开始性能预测: Al={al_content}%, Ti={ti_content}%")
    
    # 检查是否有必要参数
    if al_content == 0 and ti_content == 0:
        return {"error": "未提供涂层成分数据，无法进行 ML 预测"}
    
    try:
        from ...services.ml_prediction_service import MLPredictionService
        service = MLPredictionService()
        
        result = service.predict_performance(
            composition, 
            process_params, 
            structure_design or {}
        )
        
        logger.info(f"[ML预测] 完成: 硬度={result.get('hardness', 'N/A')} GPa")
        
        return {
            "hardness": result.get("hardness"),
            "elastic_modulus": result.get("elastic_modulus"),
            "wear_rate": result.get("wear_rate"),
            "adhesion_strength": result.get("adhesion_strength"),
            "model_confidence": result.get("model_confidence", 0.85),
            "prediction_source": "ML_Model_v2"
        }
        
    except Exception as e:
        logger.error(f"[ML预测] 失败: {e}")
        return {"error": str(e)}


@tool
def compare_historical_tool(runtime: ToolRuntime) -> Dict[str, Any]:
    """
    检索并对比历史相似案例。
    
    自动从当前状态获取成分和工艺参数，
    从数据库中查找相似的涂层配方，提供成功案例的性能数据作为参考。
    
    Returns:
        相似案例列表，包含性能数据和相似度
    """
    # 从状态获取参数
    state = runtime.state
    composition = state.get("coating_composition", {})
    process_params = state.get("process_params", {})
    
    al_content = composition.get("al_content", 0) or 0
    ti_content = composition.get("ti_content", 0) or 0
    n_content = composition.get("n_content", 0) or 0
    process_type = process_params.get("process_type", "magnetron_sputtering")
    
    logger.info(f"[历史对比] 检索相似案例: Al={al_content}%, Ti={ti_content}%")
    
    # 检查是否有必要参数
    if al_content == 0 and ti_content == 0:
        return {"error": "未提供涂层成分数据，无法检索历史案例", "total_cases": 0, "similar_cases": []}
    
    try:
        from ...services.historical_data_service import HistoricalDataService
        service = HistoricalDataService()
        
        comp_data = {
            "al_content": al_content,
            "ti_content": ti_content,
            "n_content": n_content
        }
        proc_data = {"process_type": process_type}
        
        result = service.retrieve_similar_cases(comp_data, proc_data)
        
        total_cases = result.get("total_cases", 0)
        logger.info(f"[历史对比] 找到 {total_cases} 个相似案例")
        
        return result
        
    except Exception as e:
        logger.error(f"[历史对比] 失败: {e}")
        return {"error": str(e), "total_cases": 0, "similar_cases": []}


@tool
def analyze_root_cause_tool(runtime: ToolRuntime) -> Dict[str, Any]:
    """
    综合分析性能预测结果，进行根因分析。
    
    自动从当前状态获取所有必要数据，包括成分、工艺、结构、模拟结果等。
    
    分析内容：
    - 成分与性能的关系
    - 工艺参数的影响
    - 与目标需求的差距
    - 主要瓶颈和改进方向
    
    使用LLM进行智能分析，生成专家级见解。
    
    Returns:
        根因分析结果，包含关键发现和建议
    """
    # 从状态获取所有必要数据
    state = runtime.state
    composition = state.get("coating_composition", {})
    process_params = state.get("process_params", {})
    structure_design = state.get("structure_design", {})
    topphi_result = state.get("topphi_simulation", {})
    ml_prediction = state.get("ml_prediction", {})
    target_requirements = state.get("target_requirements", {})
    
    logger.info("[根因分析] 开始综合分析")
    logger.info(f"[根因分析] structure_design={structure_design}")
    
    try:
        from ...services.coating_service import CoatingService
        service = CoatingService()
        
        analysis_state = {
            "task_id": "root_cause_analysis",
            "coating_composition": composition,
            "process_params": process_params,
            "structure_design": structure_design or {},
            "topphi_simulation": topphi_result or {},
            "ml_prediction": ml_prediction or {},
            "target_requirements": target_requirements or {},
            "historical_comparison": state.get("historical_comparison", {})
        }
        
        result = service.integrate_analysis(analysis_state)
        
        if result.get("status") == "success":
            analysis = result.get("data", {}).get("integrated_analysis", {})
            logger.info(f"[根因分析] 完成: {len(analysis.get('key_findings', []))} 个关键发现")
            return analysis
        else:
            return {"error": result.get("message", "分析失败")}
        
    except Exception as e:
        logger.error(f"[根因分析] 失败: {e}")
        return {"error": str(e)}
