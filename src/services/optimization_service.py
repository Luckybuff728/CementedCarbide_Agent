"""
优化建议服务 - 消除P1/P2/P3节点的代码重复
"""
from typing import Dict, List, Any, Optional
from enum import Enum
import logging
import re
from ..llm import get_llm_service, MATERIAL_EXPERT_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """优化类型枚举"""
    P1_COMPOSITION = "P1_成分优化"
    P2_STRUCTURE = "P2_结构优化"
    P3_PROCESS = "P3_工艺优化"


class OptimizationService:
    """优化建议生成服务"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
        logger.info("[优化服务] 初始化完成 - 使用统一优化方法")
        
    def generate_optimization_suggestion(
        self,
        optimization_type: OptimizationType,
        state: Dict[str, Any],
        stream_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        统一的优化建议生成方法 - 简化版，只返回原始内容
        
        Args:
            optimization_type: 优化类型
            state: 工作流状态
            stream_callback: 流式输出回调
            
        Returns:
            优化建议结果（统一结构字典）
        """
        logger.info(f"[{optimization_type.value}] 开始生成优化建议")
        
        # 获取上下文信息
        current_performance = state.get("performance_prediction", {})
        target_requirements = state.get("target_requirements", "")
        composition = state.get("coating_composition", {})
        params = state.get("process_params", {})
        structure = state.get("structure_design", {})
        
        # 生成提示词
        prompt = self._create_optimization_prompt(
            optimization_type,
            composition,
            params,
            structure,
            current_performance,
            target_requirements
        )
        
        # LLM流式生成
        try:
            logger.info(f"[{optimization_type.value}] 开始LLM流式生成...")
            
            def _callback(chunk_content):
                if stream_callback:
                    stream_callback(optimization_type.name.lower(), chunk_content)
            
            content = self.llm_service.generate_stream(
                prompt=prompt,
                stream_callback=_callback
            )
            
            logger.info(f"[{optimization_type.value}] 建议生成完成，长度: {len(content)}")
            
            data = {
                "content": content
            }
            
            return {
                "status": "success",
                "data": data,
                "message": f"{optimization_type.value}建议生成完成",
                "error": None,
                "meta": {
                    "optimization_type": optimization_type.name
                }
            }
            
        except Exception as e:
            logger.error(f"[{optimization_type.value}] 生成失败: {str(e)}")
            return {
                "status": "error",
                "data": {},
                "message": f"{optimization_type.value}建议生成失败，请稍后重试",
                "error": {
                    "type": "llm_error",
                    "details": str(e)
                },
                "meta": {
                    "optimization_type": optimization_type.name
                }
            }
    
    def _create_optimization_prompt(
        self,
        optimization_type: OptimizationType,
        composition: Dict,
        params: Dict,
        structure: Dict,
        current_performance: Dict,
        target_requirements: Any
    ) -> str:
        """创建优化提示词，包含完整的输入参数"""
        
        # 构建完整的当前参数信息
        import json
        
        # 构建成分信息
        composition_str = f"Al {composition.get('al_content', 0):.1f} at.%, Ti {composition.get('ti_content', 0):.1f} at.%, N {composition.get('n_content', 0):.1f} at.%"
        if composition.get('other_elements'):
            other_elems = ', '.join([f"{e.get('name', '')} {e.get('content', 0):.1f} at.%" for e in composition.get('other_elements', [])])
            composition_str += f", 其他元素: {other_elems}"
        
        # 构建工艺参数信息
        process_str = f"""工艺类型: {params.get('process_type', 'N/A')}
- 沉积温度: {params.get('deposition_temperature', 0)} ℃
- 沉积气压: {params.get('deposition_pressure', 0)} Pa
- 偏压: {params.get('bias_voltage', 0)} V
- N₂流量: {params.get('n2_flow', 0)} sccm"""
        if params.get('other_gases'):
            other_gases = ', '.join([f"{g.get('type', '')} {g.get('flow', 0)} sccm" for g in params.get('other_gases', [])])
            process_str += f"\n- 其他气体: {other_gases}"
        
        # 构建结构设计信息
        structure_str = f"结构类型: {structure.get('structure_type', '单层')}"
        if structure.get('structure_type') == 'multi' and structure.get('layers'):
            layers_info = '; '.join([f"第{i+1}层({l.get('type', '')}, {l.get('thickness', 0)}μm)" for i, l in enumerate(structure.get('layers', []))])
            structure_str += f" - {layers_info}"
        else:
            structure_str += f", 总厚度: {structure.get('total_thickness', 0)} μm"
        
        # 构建性能需求信息
        target_str = "N/A"
        if isinstance(target_requirements, dict):
            target_parts = []
            if target_requirements.get('substrate_material'):
                target_parts.append(f"基材: {target_requirements.get('substrate_material')}")
            if target_requirements.get('working_temperature'):
                target_parts.append(f"工作温度: {target_requirements.get('working_temperature')}°C")
            if target_requirements.get('application_scenario'):
                target_parts.append(f"应用: {target_requirements.get('application_scenario')}")
            target_str = ', '.join(target_parts) if target_parts else "N/A"
        elif isinstance(target_requirements, str):
            target_str = target_requirements
        
        base_info = f"""
## 当前完整参数

### 1. 涂层成分配比
{composition_str}

### 2. 工艺参数
{process_str}

### 3. 结构设计
{structure_str}

### 4. 当前性能预测
- 预测纳米硬度: {current_performance.get('hardness', 0)} GPa
- 弹性模量: {current_performance.get('elastic_modulus', 0)} GPa
- 磨损率: {current_performance.get('wear_rate', 0)} mm³/(N·m)
- 结合力: {current_performance.get('adhesion_strength', 0)} N

### 5. 目标需求
{target_str}

---

## 优化任务
请基于上述完整参数，生成**1个**最优的{optimization_type.value}方案。

**严格按照以下格式输出**（使用统一的Markdown格式）：

## 方案名称 
[例如：高Al/微Si掺杂提升抗氧化与硬度]

### 方案概述
[用1-2句话概括优化思路和目标]

### 具体调整内容
- **调整项1**: [具体数值/参数] → [目标数值/参数]（变化量）
- **调整项2**: [具体数值/参数] → [目标数值/参数]（变化量）
- **调整项3**: [具体数值/参数] → [目标数值/参数]（变化量）
[根据优化类型列出3-5个关键调整项]

### 科学原理
[2-3段文字，解释为什么这样调整能提升性能，需要包含材料学/工艺学依据]

### 预期效果
- **硬度提升**: 预计提高XX%或X GPa
- **其他性能**: [列出其他预期改善的性能指标]
- **综合评价**: [整体性能提升预期]

### 实施注意事项
- [关键注意点1]
- [关键注意点2]
- [关键注意点3]

要求：
- 100字
- **必须严格遵循上述Markdown格式结构**
- 紧密结合当前参数数据进行分析
- 提供具有材料学依据的优化方案
- 数值要具体、可操作
- 只需1个综合最优方案，不要生成多个方案
"""
        
        if optimization_type == OptimizationType.P1_COMPOSITION:
            return f"""
作为AlTiN涂层材料专家，请基于以下完整数据生成**成分优化**建议：

{base_info}

### 优化方向建议
1. **Al/Ti比例调整**：影响硬度、韧性、氧化温度的平衡
2. **微量元素添加**：Cr提升氧化性能，Si细化晶粒，Y改善韧性
3. **N含量优化**：影响化学计量比和相结构
4. **元素协同效应**：考虑多元素间的相互作用

请结合当前成分配比（{composition_str}），给出具有材料学依据的优化方案。
"""
        
        elif optimization_type == OptimizationType.P2_STRUCTURE:
            return f"""
作为涂层结构设计专家，请基于以下完整数据生成**结构优化**建议：

{base_info}

### 优化方向建议
1. **多层/纳米复合结构**：通过界面阻止裂纹扩展，提升韧性
2. **梯度结构设计**：底层高韧性，表层高硬度，优化应力分布
3. **调制周期优化**：纳米多层的超硬效应（最优周期3-10nm）
4. **总厚度控制**：平衡硬度与结合力，避免过厚导致应力失效

请结合当前结构设计（{structure_str}），给出具有材料学依据的优化方案。
"""
        
        elif optimization_type == OptimizationType.P3_PROCESS:
            return f"""
作为PVD工艺专家，请基于以下完整数据生成**工艺优化**建议：

{base_info}

### 优化方向建议
1. **沉积温度调整**：影响晶粒尺寸、残余应力和结合力
2. **偏压功率优化**：控制离子轰击能量，影响致密度和应力
3. **气体流量配比**：N₂/Ar比例影响成分和微观结构
4. **沉积气压控制**：影响粒子平均自由程和沉积速率
5. **多步工艺**：如变温沉积、脉冲偏压等先进工艺

请结合当前工艺参数（温度{params.get('deposition_temperature', 0)}°C，气压{params.get('deposition_pressure', 0)}Pa等），给出具有工艺学依据的优化方案。
"""
        
        return base_info
