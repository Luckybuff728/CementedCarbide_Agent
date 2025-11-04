"""
LLM智能参数验证服务 - 统一验证所有输入参数
"""
from typing import Dict, List, Any, Tuple
import logging
import json
from ..llm.llm_config import get_material_expert_llm, MATERIAL_EXPERT_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

class ValidationService:
    """基于LLM的涂层参数智能验证服务（统一验证）"""
    
    def __init__(self):
        self.llm = get_material_expert_llm()
        logger.info("[参数验证服务] 初始化完成 - 使用LLM统一验证模式")
    
    def validate_all_parameters(
        self, 
        composition: Dict[str, Any], 
        process_params: Dict[str, Any],
        structure_design: Dict[str, Any],
        target_requirements: Dict[str, Any],
        stream_callback=None
    ) -> Tuple[List[str], str]:
        """统一验证所有输入参数（支持流式输出）
        
        Args:
            composition: 成分字典
            process_params: 工艺参数字典
            structure_design: 结构设计字典
            target_requirements: 性能需求字典
            stream_callback: 流式输出回调函数
            
        Returns:
            (errors, analysis_content): 验证错误列表和完整分析内容
        """
        # 记录完整JSON
        full_params = {
            "成分配比": composition,
            "工艺参数": process_params,
            "结构设计": structure_design,
            "性能需求": target_requirements
        }
        logger.info(f"[参数验证] 完整输入参数JSON:\n{json.dumps(full_params, ensure_ascii=False, indent=2)}")
        
        # 构建友好的参数描述（带单位）
        comp_text = f"Al {composition.get('al_content', 0):.1f}%, Ti {composition.get('ti_content', 0):.1f}%, N {composition.get('n_content', 0):.1f}%"
        if composition.get('other_elements'):
            other_elems = ', '.join([f"{e.get('element', '')} {e.get('content', 0):.1f}%" for e in composition.get('other_elements', [])])
            comp_text += f", {other_elems}"
        
        process_text = f"""工艺类型: {process_params.get('process_type', 'N/A')}
- 沉积温度: {process_params.get('deposition_temperature', 0)}°C
- 沉积气压: {process_params.get('deposition_pressure', 0)} Pa
- 偏压: {process_params.get('bias_voltage', 0)} V
- N₂流量: {process_params.get('n2_flow', 0)} sccm"""
        
        if process_params.get('other_gases'):
            other_gases = ', '.join([f"{g.get('type', '')} {g.get('flow', 0)} sccm" for g in process_params.get('other_gases', [])])
            process_text += f"\n- 其他气体: {other_gases}"
        
        structure_text = f"结构类型: {structure_design.get('structure_type', '单层')}, 总厚度: {structure_design.get('total_thickness', 0)} μm"
        if structure_design.get('structure_type') == 'multi' and structure_design.get('layers'):
            layers_info = '; '.join([f"{l.get('type', '')} {l.get('thickness', 0)}μm" for l in structure_design.get('layers', [])])
            structure_text += f"\n- 层结构: {layers_info}"
        
        target_text = str(target_requirements) if isinstance(target_requirements, str) else json.dumps(target_requirements, ensure_ascii=False)
        
        # 构建简洁的验证提示词
        prompt = f"""
作为PVD涂层材料专家，请快速验证以下涂层配方参数的合理性：

## 待验证参数

**成分配比：** {comp_text}

**工艺参数：**
{process_text}

**结构设计：** {structure_text}

**性能需求：** {target_text}

---

## 验证要求

请简明扼要地分析以下关键点：

1. **成分合理性** - 总成分接近100%？Al/Ti/N比例是否合适？
2. **工艺可行性** - 温度、气压、偏压、气体流量是否匹配？有无工艺风险？
3. **结构设计** - 厚度和层结构是否合理？
4. **性能匹配** - 配方是否可能达到目标要求？

## 验证结论

最后明确给出：
- **✅ 验证通过** - 参数合理，可继续分析
- **❌ 发现问题** - 列出具体问题

**注意：**
- 简洁明了，不超过150字
- 只关注参数合理性，无需深入分析
- 使用简洁专业的语言
- 使用Markdown格式
"""
        
        analysis_content = ""
        try:
            logger.info(f"[参数验证] 开始LLM流式分析...")
            
            # 使用流式生成
            for chunk in self.llm.stream([
                SystemMessage(content=MATERIAL_EXPERT_PROMPT),
                HumanMessage(content=prompt)
            ]):
                if hasattr(chunk, 'content') and chunk.content:
                    analysis_content += chunk.content
                    # 发送流式输出到前端
                    if stream_callback:
                        stream_callback('input_validation', chunk.content)
            
            logger.info(f"[参数验证] LLM分析完成，长度: {len(analysis_content)}字符")
            
            # 解析验证结果
            if "验证通过" in analysis_content or "✅" in analysis_content:
                return ([], analysis_content)
            elif "发现问题" in analysis_content or "❌" in analysis_content:
                # 提取错误信息
                errors = []
                for line in analysis_content.split('\n'):
                    line = line.strip()
                    if line and any(keyword in line for keyword in ["错误", "问题", "不合理", "建议修改", "❌"]):
                        errors.append(line)
                return (errors[:5] if errors else ["参数存在问题，请查看详细分析"], analysis_content)
            else:
                # 默认通过
                return ([], analysis_content)
        
        except Exception as e:
            logger.error(f"[参数验证] LLM验证异常: {str(e)}", exc_info=True)
            error_msg = f"验证服务异常: {str(e)}"
            return ([error_msg], error_msg)

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
