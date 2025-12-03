"""
LLM智能参数验证服务 - 统一验证所有输入参数
"""
from typing import Dict, List, Any, Tuple
import json
from loguru import logger
from ..llm import get_llm_service, MATERIAL_EXPERT_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

class ValidationService:
    """基于LLM的涂层参数智能验证服务（统一验证）"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
        logger.info("[参数验证服务] 初始化完成 - 使用LLM统一验证模式")
    
    def validate_all_parameters(
        self, 
        composition: Dict[str, Any], 
        process_params: Dict[str, Any],
        structure_design: Dict[str, Any],
        target_requirements: Dict[str, Any],
        stream_callback=None
    ) -> Dict[str, Any]:
        """简化的参数验证 - 基础检查 + LLM分析
        
        Args:
            composition: 成分字典
            process_params: 工艺参数字典
            structure_design: 结构设计字典
            target_requirements: 性能需求字典
            stream_callback: 流式输出回调函数
            
        Returns:
            验证结果字典: {
                "input_validated": bool,
                "validation_content": str,
                "validation_errors": list
            }
        """
        logger.info("[参数验证] 开始简化验证流程")
        
        # 1. 基础参数检查
        basic_errors = self._basic_parameter_check(composition, process_params, structure_design)
        
        # 如果基础检查失败，直接返回
        if basic_errors:
            logger.warning(f"[参数验证] 基础检查失败: {basic_errors}")
            return {
                "input_validated": False,
                "validation_content": f"参数基础检查失败:\n" + "\n".join(f"- {error}" for error in basic_errors),
                "validation_errors": basic_errors
            }
        
        # 2. 构建参数描述（保持不变）
        comp_text = self._format_composition(composition)
        process_text = self._format_process_params(process_params)
        structure_text = self._format_structure_design(structure_design)
        target_text = self._format_target_requirements(target_requirements)
        
        # 3. LLM分析
        prompt = f"""
作为PVD涂层材料专家，请快速检查以下涂层配方参数是否有明显错误：

**成分配比：** {comp_text}
**工艺参数：** {process_text}
**结构设计：** {structure_text}
**性能需求：** {target_text}

**验证原则：**
- 只要没有明显的技术错误，就应该通过验证
- 参数在合理范围内即可，不需要完美匹配
- 重点检查是否有致命性问题（如温度过高、成分不合理等）

请简明分析，最后给出：
- **✅ 验证通过** 或 **❌ 发现问题**
- 要求100字以内
"""
        
        try:
            def _callback(content):
                if stream_callback:
                    stream_callback('input_validation', content)
            
            analysis_content = self.llm_service.generate_stream(
                prompt=prompt,
                stream_callback=_callback
            )
            
            # LLM 只用于生成说明文案，不再决定是否通过验证
            llm_warnings = []
            if "❌" in analysis_content and "✅" not in analysis_content:
                llm_warnings.append("LLM分析提示参数可能存在风险（仅供参考，不影响流程）")
            
            return {
                "input_validated": True,
                "validation_content": analysis_content,
                "validation_errors": llm_warnings
            }
            
        except Exception as e:
            logger.error(f"[参数验证] LLM验证异常: {str(e)}")
            # LLM 异常时，保留基础检查结果（已通过），仅作为告警信息返回
            return {
                "input_validated": True,
                "validation_content": f"验证服务异常（已按基础规则通过）: {str(e)}",
                "validation_errors": [f"验证服务异常（仅告警）: {str(e)}"]
            }
    
    def _basic_parameter_check(self, composition, process_params, structure_design) -> List[str]:
        """基础参数检查"""
        errors = []
        
        # 检查成分是否为空
        if not composition:
            errors.append("成分配比不能为空")
        else:
            al = composition.get('al_content', 0) or 0
            ti = composition.get('ti_content', 0) or 0
            n = composition.get('n_content', 0) or 0
            total = al + ti + n
            
            if total < 50:  # 基本的总量检查
                errors.append("主要成分总量过低")
        
        # 检查工艺参数
        if not process_params:
            errors.append("工艺参数不能为空")
        else:
            temp = process_params.get('deposition_temperature', 0) or 0
            if temp <= 0 or temp > 1000:
                errors.append("沉积温度异常")
        
        # 检查结构设计
        if not structure_design:
            errors.append("结构设计不能为空")
        else:
            thickness = structure_design.get('total_thickness', 0) or 0
            if thickness <= 0:
                errors.append("总厚度必须大于0")
        
        return errors
    
    def _format_composition(self, composition) -> str:
        """格式化成分描述"""
        comp_text = f"Al {composition.get('al_content', 0):.1f} at.%, Ti {composition.get('ti_content', 0):.1f} at.%, N {composition.get('n_content', 0):.1f} at.%"
        if composition.get('other_elements'):
            other_elems = ', '.join([f"{e.get('name', '')} {e.get('content', 0):.1f} at.%" for e in composition.get('other_elements', [])])
            comp_text += f", {other_elems}"
        return comp_text
    
    def _format_process_params(self, process_params) -> str:
        """格式化工艺参数描述"""
        process_text = f"工艺类型: {process_params.get('process_type', 'N/A')}, 沉积温度: {process_params.get('deposition_temperature', 0)}°C, 沉积气压: {process_params.get('deposition_pressure', 0)} Pa, 偏压: {process_params.get('bias_voltage', 0)} V, N₂流量: {process_params.get('n2_flow', 0)} sccm"
        
        if process_params.get('other_gases'):
            other_gases = ', '.join([f"{g.get('type', '')} {g.get('flow', 0)} sccm" for g in process_params.get('other_gases', [])])
            process_text += f", 其他气体: {other_gases}"
        
        return process_text
    
    def _format_structure_design(self, structure_design) -> str:
        """格式化结构设计描述"""
        structure_text = f"结构类型: {structure_design.get('structure_type', '单层')}, 总厚度: {structure_design.get('total_thickness', 0)} μm"
        if structure_design.get('structure_type') == 'multi' and structure_design.get('layers'):
            layers_info = '; '.join([f"{l.get('type', '')} {l.get('thickness', 0)}μm" for l in structure_design.get('layers', [])])
            structure_text += f", 层结构: {layers_info}"
        return structure_text
    
    def _format_target_requirements(self, target_requirements) -> str:
        """格式化性能需求描述"""
        return str(target_requirements) if isinstance(target_requirements, str) else json.dumps(target_requirements, ensure_ascii=False)

    def normalize_composition(self, composition: Dict[str, Any]) -> Dict[str, Any]:
        """归一化成分到100%
        
        Args:
            composition: 原始成分字典
            
        Returns:
            归一化后的成分字典
        """
        # 计算总成分
        total = 0
        total += composition.get('al_content', 0) or 0
        total += composition.get('ti_content', 0) or 0
        total += composition.get('n_content', 0) or 0
        
        # 添加其他元素
        for elem in composition.get('other_elements', []):
            total += elem.get('content', 0) or 0
        
        if total == 0 or abs(total - 100) < 0.1:
            logger.info(f"[成分归一化] 无需归一化，总和={total}%")
            return composition.copy()
        
        # 归一化
        normalized = composition.copy()
        factor = 100.0 / total
        
        normalized['al_content'] = (composition.get('al_content', 0) or 0) * factor
        normalized['ti_content'] = (composition.get('ti_content', 0) or 0) * factor
        normalized['n_content'] = (composition.get('n_content', 0) or 0) * factor
        
        # 归一化其他元素
        if composition.get('other_elements'):
            normalized['other_elements'] = [
                {
                    'element': elem.get('element', ''),
                    'content': (elem.get('content', 0) or 0) * factor
                }
                for elem in composition['other_elements']
            ]
        
        logger.info(f"[成分归一化] 原始总和={total:.2f}%, 归一化后总和=100%")
        logger.info(f"[成分归一化] 归一化结果JSON: {json.dumps(normalized, ensure_ascii=False, indent=2)}")
        
        return normalized
