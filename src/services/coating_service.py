"""
涂层服务 - 核心业务逻辑
"""
from typing import Dict, List, Any, Optional
import logging
import json
import time
from .validation_service import ValidationService
from .optimization_service import OptimizationService, OptimizationType
from .topphi_service import TopPhiService
from .ml_prediction_service import MLPredictionService
from .historical_data_service import HistoricalDataService

logger = logging.getLogger(__name__)


class CoatingService:
    """涂层优化核心服务"""
    
    def __init__(self):
        self.validation_service = ValidationService()
        self.optimization_service = OptimizationService()
        # ✅ 拆分后的独立服务
        self.topphi_service = TopPhiService()
        self.ml_service = MLPredictionService()
        self.historical_service = HistoricalDataService()
    
    def validate_input(self, state: Dict[str, Any], stream_callback=None) -> Dict[str, Any]:
        """
        验证输入参数
        
        Args:
            state: 工作流状态
            stream_callback: 流式输出回调函数
            
        Returns:
            验证结果
        """
        logger.info(f"开始验证任务 {state['task_id']} 的输入参数")
        
        # 获取所有输入参数
        composition = state.get("coating_composition", {})
        params = state.get("process_params", {})
        structure = state.get("structure_design", {})
        target_requirements = state.get("target_requirements", {})
        
        # 使用统一验证函数（支持流式输出）
        all_errors, validation_analysis = self.validation_service.validate_all_parameters(
            composition, params, structure, target_requirements, stream_callback
        )
        
        # 归一化成分数据
        normalized_composition = self.validation_service.normalize_composition(composition)
        
        # 预处理数据（供前端显示使用）
        preprocessed_data = {
            "coating_composition": normalized_composition,  # 使用归一化后的成分
            "process_params": params,
            "structure_design": structure,
            "target_requirements": target_requirements
        }
        
        # 构建结果（包含原始参数、验证后的数据和LLM分析内容）
        result = {
            "input_validated": len(all_errors) == 0,
            "validation_errors": all_errors,
            "validation_analysis": validation_analysis,  # LLM流式分析内容
            "preprocessed_data": preprocessed_data,  # 供前端显示
            # 保存到state供后续节点使用
            "coating_composition": normalized_composition,
            "process_params": params,
            "structure_design": structure,
            "target_requirements": target_requirements,
            "current_step": "validation_complete",
            "next_step": "performance_prediction" if len(all_errors) == 0 else "error",
            "workflow_status": "validated" if len(all_errors) == 0 else "validation_failed"
        }
        
        # 记录完整的JSON参数（带单位）
        import json
        from ..utils.data_formatter import format_full_parameters_with_units
        
        # 原始数据（不带单位）
        full_params_json = {
            "coating_composition": normalized_composition,
            "process_params": params,
            "structure_design": structure,
            "target_requirements": target_requirements
        }
        
        # 带单位的数据（供日志记录）
        formatted_params = format_full_parameters_with_units(
            normalized_composition, params, structure, target_requirements
        )
        
        logger.info(f"[参数验证完成] 验证结果: {result['input_validated']}")
        logger.info(f"[完整参数JSON记录-不带单位]\n{json.dumps(full_params_json, ensure_ascii=False, indent=2)}")
        logger.info(f"[完整参数JSON记录-带单位]\n{json.dumps(formatted_params, ensure_ascii=False, indent=2)}")
        
        if all_errors:
            logger.error(f"验证错误: {all_errors}")
        
        return result
    
    def simulate_topphi(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        TopPhi模拟 - 调用独立的TopPhiService
        """
        logger.info(f"[TopPhi模拟] 任务 {state['task_id']} 开始")
        
        composition = state.get("coating_composition", {})
        params = state.get("process_params", {})
        
        # ✅ 使用拆分后的TopPhiService
        topphi_result = self.topphi_service.simulate_deposition(composition, params)
        
        return {
            "topphi_simulation": topphi_result,
            "current_step": "topphi_complete"
        }
    
    def predict_ml_performance(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        ML模型预测 - 调用独立的MLPredictionService
        """
        logger.info(f"[ML模型预测] 任务 {state['task_id']} 开始")
        
        composition = state.get("coating_composition", {})
        params = state.get("process_params", {})
        structure = state.get("structure_design", {})
        
        # ✅ 使用拆分后的MLPredictionService
        ml_prediction = self.ml_service.predict_performance(composition, params, structure)
        
        return {
            "ml_prediction": ml_prediction,
            "current_step": "ml_complete"
        }
    
    def compare_historical_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        历史数据比对 - 调用独立的HistoricalDataService
        """
        logger.info(f"[历史数据比对] 任务 {state['task_id']} 开始")
        
        composition = state.get("coating_composition", {})
        params = state.get("process_params", {})
        
        # ✅ 使用拆分后的HistoricalDataService
        historical_comparison = self.historical_service.retrieve_similar_cases(composition, params)
        
        return {
            "historical_comparison": historical_comparison,
            "current_step": "historical_complete"
        }
    
    def integrate_analysis(self, state: Dict[str, Any], stream_callback=None) -> Dict[str, Any]:
        """
        根因分析 - 整合预测结果，使用LLM生成根因分析
        """
        
        topphi = state.get("topphi_simulation", {})
        ml_pred = state.get("ml_prediction", {})
        historical = state.get("historical_comparison", {})
        
        # 生成根因分析（使用LLM）
        composition = state.get("coating_composition", {})
        params = state.get("process_params", {})
        
        root_cause_analysis = self._generate_llm_root_cause_analysis(
            state, composition, params, ml_pred, topphi, historical, stream_callback
        )
        
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
        
        # 构建综合分析报告
        integrated_analysis = {
            "root_cause_analysis": root_cause_analysis,
            "performance_summary": {
                "predicted_hardness": performance_prediction["hardness"],
                "confidence": performance_prediction["confidence_score"],
                "key_findings": self._extract_key_findings(ml_pred, topphi, historical)
            },
            "recommendation": self._generate_recommendation(performance_prediction, historical)
        }
        
        logger.info(f"[根因分析] 分析完成")
        
        return {
            "performance_prediction": performance_prediction,
            "integrated_analysis": integrated_analysis,  # 新增：结构化的综合分析
            "prediction_confidence": performance_prediction["confidence_score"],
            "current_step": "prediction_complete"
        }
    
    def generate_p1_optimization(self, state: Dict[str, Any], stream_callback=None) -> Dict[str, Any]:
        """生成P1成分优化建议"""
        result = self.optimization_service.generate_optimization_suggestion(
            OptimizationType.P1_COMPOSITION,
            state,
            stream_callback
        )
        return {
            "p1_suggestions": result["suggestions"],
            "p1_content": result["content"]
        }
    
    def generate_p2_optimization(self, state: Dict[str, Any], stream_callback=None) -> Dict[str, Any]:
        """生成P2结构优化建议"""
        result = self.optimization_service.generate_optimization_suggestion(
            OptimizationType.P2_STRUCTURE,
            state,
            stream_callback
        )
        return {
            "p2_suggestions": result["suggestions"],
            "p2_content": result["content"]
        }
    
    def generate_p3_optimization(self, state: Dict[str, Any], stream_callback=None) -> Dict[str, Any]:
        """生成P3工艺优化建议"""
        result = self.optimization_service.generate_optimization_suggestion(
            OptimizationType.P3_PROCESS,
            state,
            stream_callback
        )
        return {
            "p3_suggestions": result["suggestions"],
            "p3_content": result["content"]
        }
    
    def _generate_llm_root_cause_analysis(
        self, state: Dict, composition: Dict, params: Dict, ml_pred: Dict, topphi: Dict, historical: Dict, stream_callback=None
    ) -> str:
        """使用LLM生成根因分析"""
        
        logger.info(f"[根因分析] 开始LLM流式生成...")
        
        # 获取结构设计和性能需求
        structure = state.get('structure_design', {})
        target_requirements = state.get('target_requirements', {})
        
        # 构建其他元素显示
        other_elements_str = '无'
        if composition.get('other_elements'):
            other_elements_str = ', '.join([f"{e.get('name', '')} {e.get('content', 0)} at.%" for e in composition.get('other_elements')])
        
        # 构建其他气体显示
        other_gases_str = '无'
        if params.get('other_gases'):
            other_gases_str = ', '.join([f"{g.get('type', '')} {g.get('flow', 0)} sccm" for g in params.get('other_gases')])
        
        # 构建结构设计显示
        structure_str = f"{structure.get('structure_type', '单层')}"
        if structure.get('structure_type') == 'multi' and structure.get('layers'):
            layers_str = '; '.join([f"第{i+1}层({l.get('type', '')}, {l.get('thickness', 0)}μm)" for i, l in enumerate(structure.get('layers', []))])
            structure_str += f" - {layers_str}"
        else:
            structure_str += f" - 总厚度: {structure.get('total_thickness', 0)} μm"
        
        # 构建完整的分析提示词
        prompt = f"""
作为涂层材料专家，请基于以下完整数据进行深入的根因分析：

## 1. 涂层成分配比
- Al含量: {composition.get('al_content', 0)}%
- Ti含量: {composition.get('ti_content', 0)}%
- N含量: {composition.get('n_content', 0)}%
- 其他元素: {other_elements_str}

## 2. 工艺参数
- 工艺类型: {params.get('process_type', 'N/A')}
- 沉积温度: {params.get('deposition_temperature', 0)}°C
- 沉积气压: {params.get('deposition_pressure', 0)} Pa
- 偏压: {params.get('bias_voltage', 0)} V
- N₂流量: {params.get('n2_flow', 0)} sccm
- 其他气体: {other_gases_str}

## 3. 结构设计
{structure_str}

## 4. TopPhi微观结构预测
- 晶粒尺寸: {topphi.get('grain_size_nm', 0)} nm
- 择优取向: {topphi.get('preferred_orientation', 'N/A')}
- 残余应力: {topphi.get('residual_stress_gpa', 0)} GPa
- 晶格常数: {topphi.get('lattice_constant', 'N/A')} Å

## 5. ML性能预测
- 预测硬度: {ml_pred.get('hardness_gpa', 0)} GPa
- 杨氏模量: {ml_pred.get('elastic_modulus_gpa', 0)} GPa
- 泊松比: {ml_pred.get('poisson_ratio', 0)}
- 结合力等级: {ml_pred.get('adhesion_level', 'N/A')}
- 氧化温度: {ml_pred.get('oxidation_temp_c', 0)}°C
- 预测置信度: {(ml_pred.get('model_confidence', 0) * 100):.1f}%

## 6. 历史案例对比
- 相似案例数: {historical.get('total_cases', 0)} 个
- 最高硬度记录: {historical.get('highest_hardness', 0)} GPa
- 平均相似度: {(historical.get('average_similarity', 0) * 100):.1f}%

## 7. 性能需求
- 基材材料: {target_requirements.get('substrate_material', 'N/A')}
- 目标结合力: {target_requirements.get('adhesion_strength', 0)} N
- 弹性模量: {target_requirements.get('elastic_modulus', 0)} GPa
- 工作温度: {target_requirements.get('working_temperature', 0)}°C
- 切削速度: {target_requirements.get('cutting_speed', 0)} m/min
- 应用场景: {target_requirements.get('application_scenario', 'N/A')}

---

**分析任务：**
请结合上述所有数据，进行系统的根因分析，回答以下问题：

1. **成分配比分析**（2-3条）
   - Al/Ti/N比例如何影响晶体结构和性能？
   - 当前成分配比的优势和不足是什么？

2. **工艺参数影响**（2-3条）
   - 沉积温度、偏压等关键工艺参数如何影响涂层质量？
   - 气体流量配比对成分和结构的影响？

3. **微观结构与性能关系**（1-2条）
   - 晶粒尺寸、取向、应力如何决定宏观性能？

4. **历史案例对比洞察**（1-2条）
   - 与历史成功/失败案例的关键差异是什么？
   - 可以从历史数据中获得什么启示？

5. **综合评价与建议**（1条）
   - 当前配方的整体评价和主要改进方向

要求：
- 每条分析要具体引用上述数据中的数值
- 使用专业术语，但表述清晰易懂
- 重点突出影响性能的关键因素
- 用中文输出，使用Markdown格式
"""
# - 简洁明了，不超过100字

        # LLM流式生成
        content = ""
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            from ..llm.llm_config import MATERIAL_EXPERT_PROMPT
            
            # 使用流式生成
            for chunk in self.optimization_service.llm.stream([
                SystemMessage(content=MATERIAL_EXPERT_PROMPT),
                HumanMessage(content=prompt)
            ]):
                if hasattr(chunk, 'content') and chunk.content:
                    content += chunk.content
                    # 发送流式输出
                    if stream_callback:
                        stream_callback("integrated_analysis", chunk.content)
            
            logger.info(f"[根因分析] 生成完成，长度: {len(content)}")
            return content
            
        except Exception as e:
            logger.error(f"[根因分析] LLM生成失败: {e}")
            if stream_callback:
                stream_callback("integrated_analysis", f"\n❌ **分析过程出错**: {str(e)}\n")
            # 降级到简单分析
            return self._simple_root_cause_analysis(composition, params, ml_pred)
    
    def _simple_root_cause_analysis(self, composition: Dict, params: Dict, prediction: Dict) -> str:
        """简单的根因分析（降级方案）"""
        analysis = []
        
        # 成分分析
        al_content = composition.get("al_content", 0)
        ti_content = composition.get("ti_content", 0)
        
        if al_content > 35:
            analysis.append("**成分优势**：高Al含量（{:.1f}%）有助于形成稳定的Al₂O₃氧化层，显著提高硬度和抗氧化性能。".format(al_content))
        elif al_content > 30:
            analysis.append("**成分特点**：Al含量（{:.1f}%）适中，有利于平衡硬度和韧性。".format(al_content))
        
        if ti_content > 25:
            analysis.append("**结构稳定**：Ti含量（{:.1f}%）促进形成稳定的fcc-TiAlN结构，提供良好的基础性能。".format(ti_content))
        
        # 工艺分析  
        bias_voltage = params.get("bias_voltage", 0)
        if bias_voltage > 80:
            analysis.append("**工艺优化**：高偏压（{:.0f}V）促进离子轰击，增强涂层致密化和界面结合力。".format(bias_voltage))
        
        deposition_temp = params.get("deposition_temperature", 0)
        if deposition_temp > 500:
            analysis.append("**温度控制**：适宜的沉积温度（{:.0f}°C）有利于晶粒细化和应力释放。".format(deposition_temp))
        
        # 性能预测
        hardness = prediction.get("hardness_gpa", 0)
        analysis.append("**预测结果**：当前参数组合预计硬度为{:.1f} GPa，属于{}性能水平。".format(
            hardness, "优秀" if hardness > 30 else "良好" if hardness > 25 else "中等"
        ))
        
        return "\n\n".join(analysis) if analysis else "性能主要由成分和工艺共同决定。"
    
    def _extract_key_findings(self, ml_pred: Dict, topphi: Dict, historical: Dict) -> list:
        """提取关键发现"""
        findings = []
        
        hardness = ml_pred.get("hardness_gpa", 0)
        if hardness > 30:
            findings.append(f"硬度预测达到{hardness:.1f} GPa，超过目标要求")
        elif hardness > 25:
            findings.append(f"硬度预测为{hardness:.1f} GPa，满足基本要求")
        else:
            findings.append(f"硬度预测仅{hardness:.1f} GPa，需要优化")
        
        grain_size = topphi.get("grain_size_nm", 0)
        if grain_size < 10:
            findings.append(f"纳米晶粒结构({grain_size:.1f} nm)有助于强化")
        
        avg_similarity = historical.get("average_similarity", 0)
        if avg_similarity > 0.8:
            findings.append(f"历史案例相似度高({avg_similarity:.2f})，预测可靠")
        
        return findings
    
    def _generate_recommendation(self, performance: Dict, historical: Dict) -> str:
        """生成优化建议"""
        hardness = performance.get("hardness", 0)
        confidence = performance.get("confidence_score", 0)
        highest_historical = historical.get("highest_hardness", 0)
        
        if hardness >= highest_historical:
            return "当前参数配置已达到历史最优水平，建议进入实验验证阶段。"
        elif hardness > 28:
            return f"性能预测良好，但仍有提升空间（历史最高{highest_historical:.1f} GPa）。建议优化成分配比或工艺参数。"
        else:
            return "预测性能未达预期，强烈建议参考优化方案进行调整。"
    
    def generate_optimization_summary(self, state: Dict[str, Any], stream_callback=None) -> str:
        """使用LLM生成优化方案综合建议
        
        Args:
            state: 工作流状态，包含P1/P2/P3的完整分析内容
            stream_callback: 流式输出回调函数
            
        Returns:
            综合建议文本
        """
        from ..llm.llm_config import get_material_expert_llm, MATERIAL_EXPERT_PROMPT
        from langchain_core.messages import SystemMessage, HumanMessage
        
        logger.info("[优化汇总] 开始LLM生成综合建议...")
        
        # 获取三个方案的完整内容
        p1_content = state.get("p1_content", "")
        p2_content = state.get("p2_content", "")
        p3_content = state.get("p3_content", "")
        
        # 构建简短建议提示词
        prompt = f"""
作为涂层材料专家，现在需要对以下三个优化方案给出简短的综合建议：

## P1 - 成分优化方案
{p1_content[:] if p1_content else "暂无P1方案"}...

## P2 - 结构优化方案
{p2_content[:] if p2_content else "暂无P2方案"}...

## P3 - 工艺优化方案
{p3_content[:] if p3_content else "暂无P3方案"}...

---

**请提供简短的综合建议（2-3句话）：**

1. 简要对比三个方案的主要特点
2. 给出推荐的方案选择建议及理由
3. 提示关键注意事项

**要求：**
- 简洁明了，不超过150字
- 重点突出推荐方案
- 不要使用Markdown格式，只输出纯文本
"""
        
        # 使用LLM流式生成
        llm = get_material_expert_llm()
        comprehensive_content = ""
        
        try:
            for chunk in llm.stream([
                SystemMessage(content=MATERIAL_EXPERT_PROMPT),
                HumanMessage(content=prompt)
            ]):
                if hasattr(chunk, 'content') and chunk.content:
                    comprehensive_content += chunk.content
                    if stream_callback:
                        stream_callback('optimization_summary', chunk.content)
            
            logger.info(f"[优化汇总] LLM生成完成，长度: {len(comprehensive_content)}")
            return comprehensive_content
            
        except Exception as e:
            logger.error(f"[优化汇总] LLM生成失败: {str(e)}", exc_info=True)
            # 降级到简单汇总
            return self._generate_simple_summary(p1_content, p2_content, p3_content)
    
    def _generate_simple_summary(self, p1_content: str, p2_content: str, p3_content: str) -> str:
        """生成简单的汇总（降级方案）"""
        recommendations = []
        
        if p1_content:
            recommendations.append("**成分优化方案（P1）**：调整Al/Ti比例，优化合金元素添加")
        
        if p2_content:
            recommendations.append("**结构优化方案（P2）**：考虑多层或梯度结构设计")
        
        if p3_content:
            recommendations.append("**工艺优化方案（P3）**：优化沉积参数，提升涂层质量")
        
        if not recommendations:
            return "系统正在生成优化建议，请稍候..."
        
        return "\n\n".join(recommendations) + "\n\n**建议优先顺序**：建议优先考虑实施难度较低、预期效果明显的方案。可以从P3工艺优化开始，然后尝试P1成分调整，最后考虑P2结构改进。"
