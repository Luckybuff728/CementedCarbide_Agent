"""
涂层上下文中间件 - 动态注入涂层参数到系统消息

功能：
- 在模型调用前，根据当前状态动态构建上下文
- 将涂层成分、工艺参数、结构设计、性能需求等信息注入系统消息
- 完整支持前端表单的所有数据结构

数据结构参考（与前端表单一致）：
- coating_composition: {al_content, ti_content, n_content, other_elements[{name, content}]}
- process_params: {process_type, deposition_temperature, deposition_pressure, bias_voltage, n2_flow, other_gases[{type, flow}]}
- structure_design: {structure_type, total_thickness, layers[{type, thickness}]}
- target_requirements: {substrate_material, adhesion_strength, elastic_modulus, working_temperature, cutting_speed, application_scenario}
"""
import json
from typing import Any, Dict, List, Optional, Callable
from loguru import logger
from langchain.agents.middleware import (
    AgentMiddleware, 
    ModelRequest, 
    ModelResponse,
    AgentState,
)
from langchain_core.messages import SystemMessage


# ==================== 数据格式化辅助函数 ====================

def _format_composition(comp: Dict[str, Any]) -> str:
    """
    格式化成分数据
    
    Args:
        comp: 成分字典 {al_content, ti_content, n_content, other_elements}
    
    Returns:
        格式化的成分描述字符串
    """
    if not comp:
        return ""
    
    parts = []
    
    # 主要成分
    al = comp.get('al_content', 0) or 0
    ti = comp.get('ti_content', 0) or 0
    n = comp.get('n_content', 0) or 0
    
    if al > 0 or ti > 0 or n > 0:
        parts.append(f"Al {al:.1f}%, Ti {ti:.1f}%, N {n:.1f}%")
    
    # 其他元素
    other_elements = comp.get('other_elements', [])
    if other_elements:
        others = [f"{e.get('name', '?')} {e.get('content', 0):.1f}%" 
                  for e in other_elements if e.get('name')]
        if others:
            parts.append(f"其他: {', '.join(others)}")
    
    return " | ".join(parts) if parts else ""


def _format_process_params(proc: Dict[str, Any]) -> str:
    """
    格式化工艺参数
    
    Args:
        proc: 工艺参数字典 {process_type, deposition_temperature, ...}
    
    Returns:
        格式化的工艺参数描述字符串
    """
    if not proc:
        return ""
    
    parts = []
    
    # 工艺类型
    process_types = {
        "magnetron_sputtering": "磁控溅射",
        "cvd": "CVD",
        "arc_ion_plating": "电弧离子镀",
        "pecvd": "PECVD",
    }
    ptype = proc.get('process_type', '')
    if ptype:
        parts.append(process_types.get(ptype, ptype))
    
    # 主要参数
    temp = proc.get('deposition_temperature', 0)
    pressure = proc.get('deposition_pressure', 0)
    bias = proc.get('bias_voltage', 0)
    n2_flow = proc.get('n2_flow', 0)
    
    params = []
    if temp: params.append(f"{temp}°C")
    if pressure: params.append(f"{pressure}Pa")
    if bias: params.append(f"偏压{bias}V")
    if n2_flow: params.append(f"N₂ {n2_flow}sccm")
    
    if params:
        parts.append(", ".join(params))
    
    # 其他气体
    other_gases = proc.get('other_gases', [])
    if other_gases:
        gases = [f"{g.get('type', '?')} {g.get('flow', 0)}sccm" 
                 for g in other_gases if g.get('type')]
        if gases:
            parts.append(f"其他气体: {', '.join(gases)}")
    
    return " | ".join(parts) if parts else ""


def _format_structure(struct: Dict[str, Any]) -> str:
    """
    格式化结构设计
    
    Args:
        struct: 结构设计字典 {structure_type, total_thickness, layers}
    
    Returns:
        格式化的结构描述字符串
    """
    if not struct:
        return ""
    
    parts = []
    
    struct_type = struct.get('structure_type', 'single')
    
    if struct_type == 'multi':
        # 多层结构
        layers = struct.get('layers', [])
        if layers:
            layer_desc = " → ".join([
                f"{l.get('type', '?')} {l.get('thickness', 0):.2f}μm" 
                for l in layers if l.get('type')
            ])
            total = sum(l.get('thickness', 0) for l in layers)
            parts.append(f"多层结构: {layer_desc}")
            parts.append(f"总厚度: {total:.2f}μm")
        else:
            parts.append("多层结构（待定义）")
    else:
        # 单层结构
        thickness = struct.get('total_thickness', 0)
        parts.append(f"单层结构: {thickness:.1f}μm")
    
    return " | ".join(parts) if parts else ""


def _format_target_requirements(target: Any) -> str:
    """
    格式化性能需求
    
    Args:
        target: 性能需求，可以是字典或字符串
    
    Returns:
        格式化的性能需求描述字符串
    """
    if not target:
        return ""
    
    # 如果是字符串，直接返回
    if isinstance(target, str):
        return target
    
    # 如果是字典，格式化
    if isinstance(target, dict):
        parts = []
        
        # 基体材料
        substrate = target.get('substrate_material', '')
        if substrate:
            parts.append(f"基体: {substrate}")
        
        # 性能参数
        params = []
        if target.get('adhesion_strength'):
            params.append(f"结合力≥{target['adhesion_strength']}N")
        if target.get('elastic_modulus'):
            params.append(f"弹性模量≥{target['elastic_modulus']}GPa")
        if target.get('working_temperature'):
            params.append(f"工作温度≤{target['working_temperature']}°C")
        if target.get('cutting_speed'):
            params.append(f"切削速度≥{target['cutting_speed']}m/min")
        
        if params:
            parts.append(", ".join(params))
        
        # 应用场景
        scenario = target.get('application_scenario', '')
        if scenario:
            parts.append(f"应用: {scenario}")
        
        return " | ".join(parts) if parts else ""
    
    return str(target)


class CoatingContextMiddleware(AgentMiddleware):
    """
    涂层上下文中间件
    
    根据专家类型动态构建并注入上下文到系统消息。
    替代原有的 _build_expert_context 函数。
    
    Args:
        expert_name: 专家类型 ("Validator" / "Analyst" / "Optimizer" / "Experimenter")
    """
    
    def __init__(self, expert_name: str):
        """
        初始化中间件
        
        Args:
            expert_name: 专家名称，决定上下文构建策略
        """
        super().__init__()
        self.expert_name = expert_name
        
        # 上下文构建策略映射
        self._context_builders: Dict[str, Callable] = {
            "Validator": self._build_validator_context,
            "Analyst": self._build_analyst_context,
            "Optimizer": self._build_optimizer_context,
            "Experimenter": self._build_experimenter_context,
        }
    
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """
        在模型调用前注入涂层上下文（同步版本）
        
        Args:
            request: 模型请求，包含状态、消息、系统消息等
            handler: 实际的模型调用处理器
        
        Returns:
            模型响应
        """
        # 注入上下文
        modified_request = self._inject_context(request)
        return handler(modified_request)
    
    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """
        在模型调用前注入涂层上下文（异步版本）
        
        Args:
            request: 模型请求，包含状态、消息、系统消息等
            handler: 实际的模型调用处理器
        
        Returns:
            模型响应
        """
        # 注入上下文
        modified_request = self._inject_context(request)
        # 异步调用 handler
        result = handler(modified_request)
        # 如果 handler 返回的是协程，等待它
        if hasattr(result, '__await__'):
            return await result
        return result
    
    def _inject_context(self, request: ModelRequest) -> ModelRequest:
        """
        注入上下文到请求中（共享逻辑）
        
        Args:
            request: 原始模型请求
        
        Returns:
            修改后的模型请求
        """
        state = request.state
        
        # 根据专家类型构建上下文
        builder = self._context_builders.get(self.expert_name)
        if builder:
            context = builder(state)
            if context:
                # 将上下文追加到系统消息
                new_content = list(request.system_message.content_blocks) + [
                    {"type": "text", "text": f"\n\n{context}"}
                ]
                new_system_message = SystemMessage(content=new_content)
                logger.debug(f"[{self.expert_name}] 注入上下文: {len(context)} 字符")
                return request.override(system_message=new_system_message)
        
        return request
    
    def _build_validator_context(self, state: Dict[str, Any]) -> str:
        """
        构建验证专家的上下文
        
        包含完整的涂层参数信息，供验证工具使用。
        """
        parts = ["【待验证参数】"]
        
        comp = state.get("coating_composition", {})
        proc = state.get("process_params", {})
        struct = state.get("structure_design", {})
        target = state.get("target_requirements")
        
        # 成分配比（使用格式化函数）
        comp_str = _format_composition(comp)
        if comp_str:
            parts.append(f"- 成分: {comp_str}")
        
        # 工艺参数（使用格式化函数）
        proc_str = _format_process_params(proc)
        if proc_str:
            parts.append(f"- 工艺: {proc_str}")
        
        # 结构设计（使用格式化函数，支持多层结构）
        struct_str = _format_structure(struct)
        if struct_str:
            parts.append(f"- 结构: {struct_str}")
        
        # 性能需求（使用格式化函数，支持完整字段）
        target_str = _format_target_requirements(target)
        if target_str:
            parts.append(f"- 目标: {target_str}")
        
        return "\n".join(parts) if len(parts) > 1 else ""
    
    def _build_analyst_context(self, state: Dict[str, Any]) -> str:
        """
        构建分析专家的上下文
        
        提供当前涂层配方摘要和性能目标。
        """
        parts = []
        
        # 验证状态
        if state.get("validation_passed"):
            parts.append("✅ 参数验证已通过")
        
        comp = state.get("coating_composition", {})
        proc = state.get("process_params", {})
        struct = state.get("structure_design", {})
        target = state.get("target_requirements")
        
        # 当前配方摘要
        comp_str = _format_composition(comp)
        proc_str = _format_process_params(proc)
        struct_str = _format_structure(struct)
        
        if comp_str or proc_str:
            parts.append("【当前配方】")
            if comp_str:
                parts.append(f"  成分: {comp_str}")
            if proc_str:
                parts.append(f"  工艺: {proc_str}")
            if struct_str:
                parts.append(f"  结构: {struct_str}")
        
        # 目标需求
        target_str = _format_target_requirements(target)
        if target_str:
            parts.append(f"【目标】{target_str}")
        
        # 工具使用提示
        parts.append("\n⚠️ 根据用户请求精准选择工具，避免不必要的调用。")
        
        return "\n".join(parts) if parts else ""
    
    def _build_optimizer_context(self, state: Dict[str, Any]) -> str:
        """
        构建优化专家的上下文
        
        提供当前配方、预测结果和目标，供优化方案生成使用。
        """
        parts = ["【优化背景】"]
        
        comp = state.get("coating_composition", {})
        proc = state.get("process_params", {})
        struct = state.get("structure_design", {})
        target = state.get("target_requirements")
        ml_pred = state.get("ml_prediction", {})
        
        # 当前配方（使用格式化函数）
        comp_str = _format_composition(comp)
        if comp_str:
            parts.append(f"- 成分: {comp_str}")
        
        proc_str = _format_process_params(proc)
        if proc_str:
            parts.append(f"- 工艺: {proc_str}")
        
        struct_str = _format_structure(struct)
        if struct_str:
            parts.append(f"- 结构: {struct_str}")
        
        # 性能预测结果
        if ml_pred:
            pred_parts = []
            if ml_pred.get('hardness'):
                pred_parts.append(f"硬度 {ml_pred['hardness']} GPa")
            if ml_pred.get('adhesion_strength'):
                pred_parts.append(f"结合力 {ml_pred['adhesion_strength']} N")
            if ml_pred.get('elastic_modulus'):
                pred_parts.append(f"弹性模量 {ml_pred['elastic_modulus']} GPa")
            if ml_pred.get('friction_coefficient'):
                pred_parts.append(f"摩擦系数 {ml_pred['friction_coefficient']}")
            if pred_parts:
                parts.append(f"- 预测性能: {', '.join(pred_parts)}")
        
        # 目标需求（使用格式化函数）
        target_str = _format_target_requirements(target)
        if target_str:
            parts.append(f"- 用户目标: {target_str}")
        
        return "\n".join(parts) if len(parts) > 1 else ""
    
    def _build_experimenter_context(self, state: Dict[str, Any]) -> str:
        """
        构建实验专家的上下文
        
        提供选择的优化方案和当前配方信息。
        """
        parts = []
        
        selected_opt = state.get('selected_optimization')
        comp = state.get("coating_composition", {})
        proc = state.get("process_params", {})
        struct = state.get("structure_design", {})
        
        if selected_opt:
            parts.append(f"【任务】执行 {selected_opt} 优化方案")
            
            # 完整参数（使用格式化函数）
            comp_str = _format_composition(comp)
            if comp_str:
                parts.append(f"  成分: {comp_str}")
            
            proc_str = _format_process_params(proc)
            if proc_str:
                parts.append(f"  工艺: {proc_str}")
            
            struct_str = _format_structure(struct)
            if struct_str:
                parts.append(f"  结构: {struct_str}")
        else:
            parts.append("【等待】用户选择优化方案或提交实验数据")
        
        return "\n".join(parts) if parts else ""


def create_context_middleware(expert_name: str) -> CoatingContextMiddleware:
    """
    创建涂层上下文中间件的便捷函数
    
    Args:
        expert_name: 专家名称
    
    Returns:
        配置好的中间件实例
    """
    return CoatingContextMiddleware(expert_name=expert_name)
