"""
涂层服务 - 核心业务逻辑
"""
from typing import Dict, List, Any, Optional
import json
from loguru import logger
import time
from datetime import datetime
from .validation_service import ValidationService
from .optimization_service import OptimizationService, OptimizationType
from .topphi_service import TopPhiService
from .ml_prediction_service import MLPredictionService
from .historical_data_service import HistoricalDataService



class CoatingService:
    """涂层优化核心服务"""
    
    def __init__(self):
        self.validation_service = ValidationService()
        self.optimization_service = OptimizationService()
        # ✅ 拆分后的独立服务
        self.topphi_service = TopPhiService()
        self.ml_service = MLPredictionService()
        self.historical_service = HistoricalDataService()
    
    def _wrap_success(self, data: Dict[str, Any], message: str = "", meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """统一封装成功结果 - 提供status/data/message/meta结构"""
        return {
            "status": "success",
            "data": data,
            "message": message,
            "error": None,
            "meta": meta or {}
        }
    
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
        
        # 使用简化的验证函数
        validation_result = self.validation_service.validate_all_parameters(
            composition, params, structure, target_requirements, stream_callback
        )
        
        # 归一化成分数据
        normalized_composition = self.validation_service.normalize_composition(composition)
        
        # 构建简化的结果（作为业务数据部分）
        result = {
            "input_validated": validation_result["input_validated"],
            "validation_errors": validation_result["validation_errors"],
            "validation_content": validation_result["validation_content"],
            # 保存到state供后续节点使用
            "coating_composition": normalized_composition,
            "process_params": params,
            "structure_design": structure,
            "target_requirements": target_requirements,
            "current_step": "validation_complete",
            "next_step": "performance_prediction" if validation_result["input_validated"] else "error",
            "workflow_status": "validated" if validation_result["input_validated"] else "validation_failed"
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
        logger.debug(f"[完整参数JSON记录-不带单位]\n{json.dumps(full_params_json, ensure_ascii=False, indent=2)}")
        logger.debug(f"[完整参数JSON记录-带单位]\n{json.dumps(formatted_params, ensure_ascii=False, indent=2)}")
        
        if not validation_result["input_validated"]:
            logger.error(f"验证错误: {validation_result['validation_errors']}")
        
        # 使用统一封装格式返回
        return self._wrap_success(result, message="输入参数验证完成")
    
    def simulate_topphi(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        TopPhi模拟 - 调用独立的TopPhiService
        """
        logger.info(f"[TopPhi模拟] 任务 {state['task_id']} 开始")
        
        composition = state.get("coating_composition", {})
        params = state.get("process_params", {})
        
        # ✅ 使用拆分后的TopPhiService
        topphi_result = self.topphi_service.simulate_deposition(composition, params)
        
        data = {
            "topphi_simulation": topphi_result,
            "current_step": "topphi_complete"
        }
        
        return self._wrap_success(data, message="[TopPhi模拟] 完成")
    
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
        
        # 构建统一的性能预测视图，便于前端和后续节点使用
        # 统一为4个核心性能指标：硬度、弹性模量、磨损率、结合力
        performance_prediction = {
            "hardness": ml_prediction.get("hardness"),
            "elastic_modulus": ml_prediction.get("elastic_modulus"),
            "wear_rate": ml_prediction.get("wear_rate"),
            "adhesion_strength": ml_prediction.get("adhesion_strength"),
            "model_confidence": ml_prediction.get("model_confidence"),
        }
        
        data = {
            "ml_prediction": ml_prediction,
            "performance_prediction": performance_prediction,
            "current_step": "ml_complete"
        }
        
        return self._wrap_success(data, message="[ML模型预测] 完成")
    
    def compare_historical_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        历史数据比对 - 调用独立的HistoricalDataService
        """
        logger.info(f"[历史数据比对] 任务 {state['task_id']} 开始")
        
        composition = state.get("coating_composition", {})
        params = state.get("process_params", {})
        
        # ✅ 使用拆分后的HistoricalDataService
        historical_comparison = self.historical_service.retrieve_similar_cases(composition, params)
        
        data = {
            "historical_comparison": historical_comparison,
            "current_step": "historical_complete"
        }
        
        return self._wrap_success(data, message="[历史数据比对] 完成")
    
    def integrate_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        根因分析 - 整合预测结果，使用LLM生成根因分析
        
        流式输出通过contextvars自动发送到前端，无需传递callback
        """
        
        topphi = state.get("topphi_simulation", {})
        ml_pred = state.get("ml_prediction", {})
        historical = state.get("historical_comparison", {})
        
        # 生成根因分析（使用LLM，自动流式输出）
        composition = state.get("coating_composition", {})
        params = state.get("process_params", {})
        
        root_cause_analysis = self._generate_llm_root_cause_analysis(
            state, composition, params, ml_pred, topphi, historical
        )
        
        # 从LLM分析文本中提取关键信息
        analysis_summary = self._extract_analysis_summary(root_cause_analysis)
        
        logger.info(f"[根因分析] 提取的摘要: {analysis_summary.get('summary', '')[:100]}")
        logger.info(f"[根因分析] 关键发现数量: {len(analysis_summary.get('key_findings', []))}")
        
        # 直接返回结构化的根因分析结果（作为业务数据）
        integrated = {
            "summary": analysis_summary.get("summary", ""),
            "key_findings": analysis_summary.get("key_findings", []),
            "recommendations": analysis_summary.get("recommendations", []),
            "root_cause_analysis": root_cause_analysis,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"[根因分析] 返回结果类型: {type(integrated)}, 键: {list(integrated.keys())}")
        logger.info(f"[根因分析] 分析完成")
        
        data = {
            "integrated_analysis": integrated
        }
        
        return self._wrap_success(data, message="[根因分析] 完成")
    
    def generate_p1_optimization(self, state: Dict[str, Any], stream_callback=None) -> Dict[str, Any]:
        """生成P1成分优化建议"""
        result = self.optimization_service.generate_optimization_suggestion(
            OptimizationType.P1_COMPOSITION,
            state,
            stream_callback
        )
        return result
    
    def generate_p2_optimization(self, state: Dict[str, Any], stream_callback=None) -> Dict[str, Any]:
        """生成P2结构优化建议"""
        result = self.optimization_service.generate_optimization_suggestion(
            OptimizationType.P2_STRUCTURE,
            state,
            stream_callback
        )
        return result
    
    def generate_p3_optimization(self, state: Dict[str, Any], stream_callback=None) -> Dict[str, Any]:
        """生成P3工艺优化建议"""
        result = self.optimization_service.generate_optimization_suggestion(
            OptimizationType.P3_PROCESS,
            state,
            stream_callback
        )
        return result
    
    def _generate_llm_root_cause_analysis(
        self, state: Dict, composition: Dict, params: Dict, ml_pred: Dict, topphi: Dict, historical: Dict
    ) -> str:
        """
        使用LLM生成根因分析
        
        流式输出通过generate_agent_stream自动发送到前端（使用contextvars）
        """
        
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
- 预测纳米硬度: {ml_pred.get('hardness', 0)} GPa
- 弹性模量: {ml_pred.get('elastic_modulus', 0)} GPa
- 磨损率: {ml_pred.get('wear_rate', 0)} mm³/Nm
- 结合力: {ml_pred.get('adhesion_strength', 0)} N
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

**分析任务**：请基于上述数据进行根因分析，回答：

1. **成分与性能关系**（2条）
   - 当前Al/Ti/N比例对硅度和耐磨性的影响
   - 成分配比的优缺点

2. **工艺参数影响**（2条）
   - 温度/偏压对涂层结构的影响
   - 气体流量对成分控制的作用

3. **性能预测与历史对比**（1条）
   - ML预测结果与历史数据的对比分析

4. **综合评价**（1条）
   - 当前配方整体评价和主要改进方向

**要求**：
- 简洁明了，不超过100字
- 引用具体数值
- 专业语言，清晰表述
- 重点突出影响性能的关键因素
- 用中文输出，使用Markdown格式
"""
# - 简洁明了，不超过100字

        # 使用统一的generate_agent_stream进行流式生成（自动通过contextvars发送到前端）
        try:
            from ..llm import get_llm_service, MATERIAL_EXPERT_PROMPT
            
            llm_service = get_llm_service()
            content = llm_service.generate_agent_stream(
                node="analyst",  # 使用analyst节点，流式输出到前端
                prompt=prompt,
                system_prompt=MATERIAL_EXPERT_PROMPT
            )
            
            logger.info(f"[根因分析] 生成完成，长度: {len(content)}")
            return content
            
        except Exception as e:
            logger.error(f"[根因分析] LLM生成失败: {e}")
            raise RuntimeError(f"根因分析失败: {e}")
    
    def generate_optimization_summary(self, state: Dict[str, Any], stream_callback=None) -> Dict[str, Any]:
        """使用LLM生成优化方案综合建议
        
        Args:
            state: 工作流状态，包含P1/P2/P3的完整分析内容
            stream_callback: 流式输出回调函数
            
        Returns:
            综合建议文本
        """
        from ..llm import get_llm_service, MATERIAL_EXPERT_PROMPT
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

**请提供简短的综合建议并突出推荐方案：**

1. 简要对比三个方案的主要特点
2. **明确推荐具体方案**（P1/P2/P3）及核心理由
3. 提示关键注意事项

**格式要求：**
- 使用醒目的Markdown格式
- **推荐方案**必须使用以下格式高亮显示：
  ```markdown
  > ### 推荐方案：P[X] - [方案名称]
  > **推荐理由**：[一句话说明为什么推荐]
  ```
- 简洁明了，不超过100字
"""
        
        # 使用LLM服务生成
        llm_service = get_llm_service()
        
        try:
            def _callback(content):
                if stream_callback:
                    stream_callback('optimization_summary', content)
            
            comprehensive_content = llm_service.generate_stream(
                prompt=prompt,
                stream_callback=_callback
            )
            
            logger.info(f"[优化汇总] LLM生成完成，长度: {len(comprehensive_content)}")
            data = {
                "comprehensive_recommendation": comprehensive_content
            }
            return {
                "status": "success",
                "data": data,
                "message": "[优化汇总] 完成",
                "error": None,
                "meta": {}
            }
            
        except Exception as e:
            logger.error(f"[优化汇总] LLM生成失败: {str(e)}", exc_info=True)
            error_msg = "❌ **优化汇总生成失败**\n\n请稍后重试。"
            if stream_callback:
                stream_callback("optimization_summary", error_msg)
            raise RuntimeError(f"优化汇总生成失败: {e}")
    
    def _extract_analysis_summary(self, analysis_text: str) -> Dict[str, Any]:
        """
        提取根因分析摘要，匹配提示词设计的4个部分：
        1. 成分与性能关系（2条）
        2. 工艺参数影响（2条）
        3. 性能预测与历史对比（1条）
        4. 综合评价（1条）
        """
        if not analysis_text:
            return {"summary": "", "key_findings": [], "recommendations": []}
        
        lines = analysis_text.split('\n')
        summary = ""
        key_findings = []
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 识别章节标题
            if "成分与性能" in line or "成分配比" in line or (line.startswith("1.") and "成分" in line):
                current_section = "composition"
                continue
            elif "工艺参数" in line or (line.startswith("2.") and "工艺" in line):
                current_section = "process"
                continue
            elif "性能预测" in line or "历史对比" in line or line.startswith("3."):
                current_section = "performance"
                continue
            elif "综合评价" in line or (line.startswith("4.") and "综合" in line):
                current_section = "summary"
                continue
            
            # 跳过标题行
            if line.startswith("#") or line.startswith("**"):
                continue
            
            # 清理行内容
            clean_line = line.lstrip("-*•·").strip()
            if len(clean_line) < 10:
                continue
            
            # 提取关键发现（成分/工艺/性能部分）
            if current_section in ["composition", "process", "performance"]:
                # 限制每条长度，截取到句号或逗号
                if len(clean_line) > 80:
                    # 找到第一个句号或逗号截断
                    for sep in ["。", "，", "；"]:
                        pos = clean_line.find(sep)
                        if 20 < pos < 80:
                            clean_line = clean_line[:pos+1]
                            break
                    else:
                        clean_line = clean_line[:80] + "..."
                key_findings.append(clean_line)
            
            # 提取综合评价（只取第一句有意义的话）
            elif current_section == "summary" and not summary:
                # 去掉Markdown格式
                clean_line = clean_line.replace("**", "").replace("*", "")
                if len(clean_line) > 20:
                    # 限制长度
                    if len(clean_line) > 100:
                        pos = clean_line.find("。")
                        if 20 < pos < 100:
                            clean_line = clean_line[:pos+1]
                        else:
                            clean_line = clean_line[:100] + "..."
                    summary = clean_line
        
        # Fallback: 如果没找到综合评价，从最后几行找
        if not summary:
            for line in reversed(lines[-10:]):
                clean_line = line.strip().lstrip("-*•·").replace("**", "")
                if len(clean_line) > 30 and not clean_line.startswith("#"):
                    if any(kw in clean_line for kw in ["配方", "建议", "优化", "综合", "整体"]):
                        summary = clean_line[:100]
                        break
        
        # 最终Fallback
        if not summary:
            summary = "当前配方分析完成，请查看关键发现了解详情。"
        
        logger.info(f"[提取摘要] 综合评价: {summary[:50]}...")
        logger.info(f"[提取摘要] 关键发现: {len(key_findings)} 条")
        
        return {
            "summary": summary,
            "key_findings": key_findings[:4],  # 最多4条
            "recommendations": []
        }
