"""
分析工具 - 性能预测和根因分析相关的原子工具

功能：
1. TopPhi 第一性原理模拟
2. ML 性能预测
3. 历史数据对比
4. 综合根因分析
"""
from typing import Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


# ==================== Pydantic Schema 定义 ====================

class TopPhiSimulationInput(BaseModel):
    """TopPhi 模拟输入参数"""
    al_content: float = Field(..., description="Al含量 (at.%)")
    ti_content: float = Field(..., description="Ti含量 (at.%)")
    n_content: float = Field(..., description="N含量 (at.%)")
    deposition_temperature: float = Field(..., description="沉积温度 (°C)")
    deposition_pressure: float = Field(default=0.5, description="沉积气压 (Pa)")


class MLPredictionInput(BaseModel):
    """ML性能预测输入参数"""
    composition: Dict[str, Any] = Field(..., description="涂层成分配比")
    process_params: Dict[str, Any] = Field(..., description="工艺参数")
    structure_design: Dict[str, Any] = Field(default_factory=dict, description="结构设计")


class HistoricalCompareInput(BaseModel):
    """历史数据对比输入"""
    al_content: float = Field(..., description="Al含量 (at.%)")
    ti_content: float = Field(..., description="Ti含量 (at.%)")
    n_content: float = Field(..., description="N含量 (at.%)")
    process_type: str = Field(default="magnetron_sputtering", description="工艺类型")


class RootCauseInput(BaseModel):
    """根因分析输入"""
    composition: Dict[str, Any] = Field(..., description="涂层成分")
    process_params: Dict[str, Any] = Field(..., description="工艺参数")
    structure_design: Dict[str, Any] = Field(default_factory=dict, description="结构设计")
    topphi_result: Dict[str, Any] = Field(..., description="TopPhi模拟结果")
    ml_prediction: Dict[str, Any] = Field(..., description="ML预测结果")
    target_requirements: Dict[str, Any] = Field(default_factory=dict, description="目标需求")


# ==================== 工具定义 ====================

@tool(args_schema=TopPhiSimulationInput)
def simulate_topphi_tool(
    al_content: float,
    ti_content: float,
    n_content: float,
    deposition_temperature: float,
    deposition_pressure: float = 0.5
) -> Dict[str, Any]:
    """
    调用 TopPhi 第一性原理模拟引擎。
    
    预测涂层的微观结构特性：
    - 晶粒尺寸
    - 择优取向
    - 残余应力
    - 晶格常数
    
    这是最准确但最耗时的预测方法。
    
    Returns:
        微观结构预测结果
    """
    logger.info(f"[TopPhi] 模拟开始: Al={al_content}%, Ti={ti_content}%, N={n_content}%")
    
    # 调用 TopPhi 服务
    try:
        from ...services.topphi_service import TopPhiService
        service = TopPhiService()
        
        composition = {
            "al_content": al_content,
            "ti_content": ti_content,
            "n_content": n_content
        }
        process_params = {
            "deposition_temperature": deposition_temperature,
            "deposition_pressure": deposition_pressure
        }
        
        result = service.simulate_deposition(composition, process_params)
        logger.info(f"[TopPhi] 模拟完成: 晶粒尺寸={result.get('grain_size_nm', 'N/A')}nm")
        
        return result
        
    except Exception as e:
        logger.error(f"[TopPhi] 模拟失败: {e}")
        return {"error": str(e)}


@tool(args_schema=MLPredictionInput)
def predict_ml_performance_tool(
    composition: Dict[str, Any],
    process_params: Dict[str, Any],
    structure_design: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    使用机器学习模型预测涂层宏观性能。
    
    预测指标：
    - 纳米硬度 (GPa)
    - 弹性模量 (GPa)
    - 磨损率 (mm³/Nm)
    - 结合力 (N)
    
    速度快，适合快速评估和优化迭代。
    
    Returns:
        性能预测结果，包含预测值和置信度
    """
    logger.info("[ML预测] 开始性能预测")
    
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


@tool(args_schema=HistoricalCompareInput)
def compare_historical_tool(
    al_content: float,
    ti_content: float,
    n_content: float,
    process_type: str = "magnetron_sputtering"
) -> Dict[str, Any]:
    """
    检索并对比历史相似案例。
    
    从数据库中查找成分和工艺相似的涂层配方，
    提供成功案例的性能数据作为参考。
    
    Returns:
        相似案例列表，包含性能数据和相似度
    """
    logger.info(f"[历史对比] 检索相似案例: Al={al_content}%, Ti={ti_content}%")
    
    try:
        from ...services.historical_data_service import HistoricalDataService
        service = HistoricalDataService()
        
        composition = {
            "al_content": al_content,
            "ti_content": ti_content,
            "n_content": n_content
        }
        process_params = {"process_type": process_type}
        
        result = service.retrieve_similar_cases(composition, process_params)
        
        total_cases = result.get("total_cases", 0)
        logger.info(f"[历史对比] 找到 {total_cases} 个相似案例")
        
        return result
        
    except Exception as e:
        logger.error(f"[历史对比] 失败: {e}")
        return {"error": str(e), "total_cases": 0, "similar_cases": []}


@tool(args_schema=RootCauseInput)
def analyze_root_cause_tool(
    composition: Dict[str, Any],
    process_params: Dict[str, Any],
    structure_design: Dict[str, Any] = None,
    topphi_result: Dict[str, Any] = None,
    ml_prediction: Dict[str, Any] = None,
    target_requirements: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    综合分析性能预测结果，进行根因分析。
    
    分析内容：
    - 成分与性能的关系
    - 工艺参数的影响
    - 与目标需求的差距
    - 主要瓶颈和改进方向
    
    使用LLM进行智能分析，生成专家级见解。
    
    Returns:
        根因分析结果，包含关键发现和建议
    """
    logger.info("[根因分析] 开始综合分析")
    logger.info(f"[根因分析] structure_design={structure_design}")
    
    try:
        from ...services.coating_service import CoatingService
        service = CoatingService()
        
        state = {
            "task_id": "root_cause_analysis",
            "coating_composition": composition,
            "process_params": process_params,
            "structure_design": structure_design or {},
            "topphi_simulation": topphi_result or {},
            "ml_prediction": ml_prediction or {},
            "target_requirements": target_requirements or {},
            "historical_comparison": {}
        }
        
        result = service.integrate_analysis(state)
        
        if result.get("status") == "success":
            analysis = result.get("data", {}).get("integrated_analysis", {})
            logger.info(f"[根因分析] 完成: {len(analysis.get('key_findings', []))} 个关键发现")
            return analysis
        else:
            return {"error": result.get("message", "分析失败")}
        
    except Exception as e:
        logger.error(f"[根因分析] 失败: {e}")
        return {"error": str(e)}
