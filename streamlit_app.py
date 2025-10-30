"""
TopMat Agent Streamlit前端应用 - 流式单页面版本
"""
import streamlit as st
import asyncio
import uuid
import json
import time
from datetime import datetime
import pandas as pd
from src.graph.workflow import CoatingWorkflowManager
from src.models.coating_models import (
    CoatingComposition, 
    ProcessParameters,
    StructureDesign,
    TargetRequirements
)

# 页面配置
st.set_page_config(
    page_title="TopMat Agent - 涂层优化专家",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化session state
if "workflow_manager" not in st.session_state:
    st.session_state.workflow_manager = CoatingWorkflowManager(use_memory=True)
if "current_task_id" not in st.session_state:
    st.session_state.current_task_id = None
if "task_history" not in st.session_state:
    st.session_state.task_history = []
if "workflow_outputs" not in st.session_state:
    st.session_state.workflow_outputs = []
if "current_node" not in st.session_state:
    st.session_state.current_node = None
if "processing" not in st.session_state:
    st.session_state.processing = False
if "selected_optimization" not in st.session_state:
    st.session_state.selected_optimization = None


def main():
    """主应用函数"""
    # 标题和描述
    st.title("🔬 TopMat Agent - 硬质合金涂层优化专家")
    st.markdown("**专注于硬质合金涂层组分开发、结构设计和工艺优化**")
    st.markdown("---")
    
    # 侧边栏
    with st.sidebar:
        st.header("📋 任务管理")
        
        # 当前任务状态
        if st.session_state.current_task_id:
            st.subheader("当前任务")
            st.success(f"任务ID: {st.session_state.current_task_id}")
            if st.session_state.current_node:
                st.info(f"🔄 正在处理: {st.session_state.current_node}")
        
        # 任务历史
        if st.session_state.task_history:
            st.subheader("历史任务")
            for task in st.session_state.task_history[-5:]:
                with st.expander(f"🔹 {task['id'][:15]}..."):
                    st.text(f"状态: {task['status']}")
                    st.text(f"创建时间: {task['created_at'].strftime('%H:%M:%S')}")
        
        # 重置按钮
        if st.button("🔄 开始新任务"):
            reset_session()
            st.rerun()
    
    # 主界面 - 单页面流式显示
    render_main_interface()


def render_main_interface():
    """渲染主界面 - 单页面流式显示"""
    # 输入表单区域
    if not st.session_state.processing:
        render_input_form()
    
    # 工作流输出区域
    if st.session_state.workflow_outputs:
        st.markdown("---")
        st.header("🔄 优化过程")
        render_workflow_outputs()
    
    # 底部状态栏
    if st.session_state.processing:
        render_status_bar()


def render_input_form():
    """渲染输入表单"""
    st.subheader("📝 涂层参数输入")
    
    # 创建输入表单
    with st.form("coating_input_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 1️⃣ 涂层成分")
            al_content = st.number_input(
                "Al含量(%)", 
                min_value=0.0, 
                max_value=100.0, 
                value=30.0,
                step=0.1
            )
            ti_content = st.number_input(
                "Ti含量(%)",
                min_value=0.0,
                max_value=100.0,
                value=25.0,
                step=0.1
            )
            n_content = st.number_input(
                "N含量(%)",
                min_value=0.0,
                max_value=100.0,
                value=45.0,
                step=0.1
            )
            
            # X元素（可选）
            use_x_element = st.checkbox("添加X元素")
            if use_x_element:
                x_element = st.selectbox(
                    "X元素类型",
                    ["Cr", "Si", "B", "C", "Y", "Nb"]
                )
                x_content = st.number_input(
                    f"{x_element}含量(%)",
                    min_value=0.0,
                    max_value=20.0,
                    value=0.0,
                    step=0.1
                )
            else:
                x_element = None
                x_content = 0.0
        
        with col2:
            st.markdown("#### 2️⃣ 工艺参数")
            deposition_pressure = st.number_input(
                "沉积气压(Pa)",
                min_value=0.1,
                max_value=5.0,
                value=0.6,
                step=0.1
            )
            
            col2_1, col2_2, col2_3 = st.columns(3)
            with col2_1:
                n2_flow = st.number_input(
                    "N₂流量(sccm)",
                    min_value=0,
                    max_value=500,
                    value=210,
                    step=10
                )
            with col2_2:
                ar_flow = st.number_input(
                    "Ar流量(sccm)",
                    min_value=0,
                    max_value=500,
                    value=280,
                    step=10
                )
            with col2_3:
                kr_flow = st.number_input(
                    "Kr流量(sccm)",
                    min_value=0,
                    max_value=500,
                    value=200,
                    step=10
                )
            
            bias_voltage = st.number_input(
                "偏压(V)",
                min_value=0,
                max_value=200,
                value=90,
                step=5
            )
            deposition_temperature = st.number_input(
                "沉积温度(℃)",
                min_value=400,
                max_value=800,
                value=550,
                step=10
            )
        
        st.markdown("#### 3️⃣ 涂层结构设计")
        col3_1, col3_2 = st.columns(2)
        with col3_1:
            total_thickness = st.number_input(
                "总厚度(μm)",
                min_value=0.1,
                max_value=20.0,
                value=3.0,
                step=0.1
            )
        with col3_2:
            layer_type = st.selectbox(
                "结构类型",
                ["单层", "多层", "梯度"]
            )
        
        st.markdown("#### 4️⃣ 目标性能需求")
        application_scenario = st.text_area(
            "应用场景描述",
            value="高速切削刀具涂层，需要高硬度和良好的抗氧化性",
            height=100
        )
        
        col4_1, col4_2 = st.columns(2)
        with col4_1:
            hardness_req = st.number_input(
                "硬度要求(GPa)",
                min_value=20.0,
                max_value=50.0,
                value=30.0,
                step=0.5
            )
        with col4_2:
            adhesion_req = st.selectbox(
                "结合力要求",
                ["HF1", "HF2", "HF3", "HF4"]
            )
        
        # 提交按钮
        submitted = st.form_submit_button("🚀 提交并开始优化", type="primary", use_container_width=True)
        
        if submitted:
            # 验证成分总和
            total_composition = al_content + ti_content + n_content + x_content
            if total_composition > 100.1:  # 允许0.1的误差
                st.error(f"❌ 成分总和({total_composition:.1f}%)超过100%，请调整！")
            else:
                # 准备输入数据
                input_data = {
                    "composition": {
                        "al_content": al_content,
                        "ti_content": ti_content,
                        "n_content": n_content,
                        "x_element": x_element,
                        "x_content": x_content
                    },
                    "process_params": {
                        "deposition_pressure": deposition_pressure,
                        "n2_flow": n2_flow,
                        "ar_flow": ar_flow,
                        "kr_flow": kr_flow,
                        "bias_voltage": bias_voltage,
                        "deposition_temperature": deposition_temperature
                    },
                    "structure_design": {
                        "total_thickness": total_thickness,
                        "layer_type": layer_type,
                        "layers": []
                    },
                    "target_requirements": application_scenario
                }
                
                # 创建新任务
                task_id = f"TASK_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                st.session_state.current_task_id = task_id
                st.session_state.processing = True
                st.session_state.workflow_outputs = []
                st.session_state.selected_optimization = None
                
                # 添加到历史
                st.session_state.task_history.append({
                    "id": task_id,
                    "status": "processing",
                    "created_at": datetime.now()
                })
                
                # 启动异步工作流处理
                asyncio.run(process_workflow(task_id, input_data))
                st.rerun()


async def process_workflow(task_id: str, input_data: dict):
    """异步处理工作流"""
    try:
        st.session_state.current_node = "输入验证"
        
        # 流式执行工作流
        async for chunk in st.session_state.workflow_manager.stream_task(
            task_id=task_id,
            input_data=input_data,
            thread_id=task_id
        ):
            # 处理工作流输出
            if chunk:
                st.session_state.workflow_outputs.append(chunk)
                # 更新当前节点
                if isinstance(chunk, dict) and len(chunk) > 0:
                    node_name = list(chunk.keys())[0]
                    st.session_state.current_node = get_node_display_name(node_name)
        
        st.session_state.processing = False
        st.session_state.current_node = None
        
    except Exception as e:
        st.session_state.workflow_outputs.append({
            "error": {
                "type": "error",
                "message": f"处理出错: {str(e)}"
            }
        })
        st.session_state.processing = False
        st.session_state.current_node = None


def render_workflow_outputs():
    """渲染工作流输出"""
    for idx, output in enumerate(st.session_state.workflow_outputs):
        if isinstance(output, dict):
            # 根据输出类型渲染不同内容
            node_name = list(output.keys())[0] if output else "unknown"
            node_data = output.get(node_name, {})
            
            # 输入验证节点
            if node_name == "input_validation":
                render_validation_output(node_data)
            
            # 性能预测节点
            elif node_name == "performance_prediction":
                render_prediction_output(node_data)
            
            # 优化建议节点
            elif node_name == "optimization_suggestion":
                render_optimization_output(node_data)
            
            # 等待用户选择
            elif node_name == "await_user_selection":
                render_selection_interface(node_data)
            
            # 结果汇总
            elif node_name == "result_summary":
                render_summary_output(node_data)
            
            # 错误处理
            elif node_name == "error":
                render_error_output(node_data)


def render_validation_output(data: dict):
    """渲染验证输出"""
    with st.container():
        st.markdown("### ✅ 输入验证")
        if data.get("input_validated", False):
            st.success("✓ 输入参数验证通过")
        else:
            st.error("✗ 输入参数验证失败")
            for error in data.get("validation_errors", []):
                st.warning(f"⚠️ {error}")


def render_prediction_output(data: dict):
    """渲染性能预测输出"""
    with st.container():
        st.markdown("### 🔮 性能预测")
        
        # 预测结果
        prediction = data.get("performance_prediction", {})
        if prediction:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                hardness = prediction.get('hardness')
                st.metric("硬度", f"{hardness:.1f} GPa" if hardness is not None else "N/A")
            with col2:
                st.metric("结合力", prediction.get('adhesion_level', 'N/A'))
            with col3:
                wear_rate = prediction.get('wear_rate')
                st.metric("磨损率", f"{wear_rate:.2e}" if wear_rate is not None else "N/A")
            with col4:
                oxidation_temp = prediction.get('oxidation_temperature')
                st.metric("抗氧化温度", f"{oxidation_temp}℃" if oxidation_temp is not None else "N/A")
            
            # 结构预测
            deposition_structure = prediction.get("deposition_structure", {})
            if deposition_structure:
                st.markdown("**微观结构预测**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"晶粒尺寸: {deposition_structure.get('grain_size', 'N/A')}")
                with col2:
                    st.info(f"择优取向: {deposition_structure.get('preferred_orientation', 'N/A')}")
                with col3:
                    st.info(f"残余应力: {deposition_structure.get('residual_stress', 'N/A')}")
        
        # 历史数据对比
        historical = data.get("historical_comparison", [])
        if historical:
            st.markdown("**📈 历史数据对比**")
            comparison_df = pd.DataFrame(historical)
            st.dataframe(comparison_df, hide_index=True, use_container_width=True)
        
        # 根因分析 - 流式显示
        root_cause = data.get("root_cause_analysis", "")
        if root_cause:
            st.markdown("**🔍 根因分析**")
            # 创建一个容器用于流式显示
            analysis_container = st.empty()
            if isinstance(root_cause, str):
                # 模拟流式显示效果
                analysis_container.markdown(root_cause)
            else:
                analysis_container.markdown(str(root_cause))


def render_optimization_output(data: dict):
    """渲染优化建议输出 - 三个建议并行流式显示"""
    with st.container():
        st.markdown("### 💡 优化建议")
        
        suggestions = data.get("optimization_suggestions", {})
        if suggestions:
            # 三列并行显示
            col1, col2, col3 = st.columns(3)
            
            # P1 - 成分优化
            with col1:
                render_suggestion_card("P1", "🧪 成分优化", suggestions.get("P1", []))
            
            # P2 - 结构优化
            with col2:
                render_suggestion_card("P2", "🏗️ 结构优化", suggestions.get("P2", []))
            
            # P3 - 工艺优化
            with col3:
                render_suggestion_card("P3", "⚙️ 工艺优化", suggestions.get("P3", []))


def render_suggestion_card(opt_id: str, title: str, suggestions: list):
    """渲染单个优化建议卡片"""
    st.markdown(f"#### {title}")
    
    if not suggestions:
        st.info("暂无建议")
        return
    
    for idx, sugg in enumerate(suggestions):
        with st.expander(f"方案 {idx+1}", expanded=True):
            # 流式显示建议内容
            desc = sugg.get("description", "")
            st.write(f"**方案**: {desc}")
            
            if "expected_hardness_increase" in sugg:
                st.success(f"预期硬度提升: +{sugg['expected_hardness_increase']} GPa")
            
            st.info(f"实施难度: {sugg.get('implementation_difficulty', '未知')}")
            st.text(f"优先级: {sugg.get('priority', 'N/A')}")
            
            # 选择按钮
            if st.button(f"选择此方案", key=f"select_{opt_id}_{idx}"):
                st.session_state.selected_optimization = {
                    "type": opt_id,
                    "index": idx,
                    "data": sugg
                }
                st.success(f"✓ 已选择 {title} - 方案{idx+1}")
                st.rerun()


def render_selection_interface(data: dict):
    """渲染用户选择界面"""
    with st.container():
        st.markdown("### 🎯 请选择优化方案")
        
        if st.session_state.selected_optimization:
            selected = st.session_state.selected_optimization
            st.success(f"✓ 您已选择: {selected['type']} - 方案{selected['index']+1}")
            
            if st.button("➡️ 继续优化流程", type="primary"):
                # 更新工作流状态
                st.session_state.workflow_manager.update_task_selection(
                    st.session_state.current_task_id,
                    selected['data']
                )
                st.session_state.processing = True
                # 继续工作流
                asyncio.run(continue_workflow())
                st.rerun()
        else:
            st.info("请从上方三个优化方案中选择一个")


def render_summary_output(data: dict):
    """渲染结果汇总输出"""
    with st.container():
        st.markdown("### 📊 结果汇总")
        st.success("🎉 优化任务完成！")
        
        # 性能对比
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**性能提升对比**")
            initial = data.get("initial_performance", {})
            final = data.get("final_performance", {})
            
            comparison_df = pd.DataFrame({
                "指标": ["硬度(GPa)", "结合力", "磨损率"],
                "初始值": [
                    f"{initial.get('hardness', 0):.1f}",
                    initial.get('adhesion_level', 'N/A'),
                    f"{initial.get('wear_rate', 0):.2e}"
                ],
                "优化后": [
                    f"{final.get('hardness', 0):.1f}",
                    final.get('adhesion_level', 'N/A'),
                    f"{final.get('wear_rate', 0):.2e}"
                ]
            })
            st.dataframe(comparison_df, hide_index=True, use_container_width=True)
        
        with col2:
            st.markdown("**目标达成情况**")
            iterations = data.get("total_iterations", 0)
            st.metric("迭代次数", f"{iterations}次", "效率优秀" if iterations < 5 else "")
        
        # 关键改进点
        improvements = data.get("key_improvements", "")
        if improvements:
            st.markdown("**🔑 关键改进点**")
            st.markdown(improvements)


def render_error_output(data: dict):
    """渲染错误输出"""
    with st.container():
        st.error(f"❌ 错误: {data.get('message', '未知错误')}")


def render_status_bar():
    """渲染底部状态栏"""
    st.markdown("---")
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.session_state.current_node:
                st.info(f"⏳ 正在处理: {st.session_state.current_node}")
        with col2:
            st.spinner("处理中...")


def get_node_display_name(node_name: str) -> str:
    """获取节点显示名称"""
    name_map = {
        "input_validation": "输入验证",
        "performance_prediction": "性能预测",
        "optimization_suggestion": "生成优化建议",
        "await_user_selection": "等待用户选择",
        "iteration_planning": "迭代规划",
        "result_summary": "结果汇总"
    }
    return name_map.get(node_name, node_name)


async def continue_workflow():
    """继续工作流执行"""
    try:
        # 继续执行工作流
        async for chunk in st.session_state.workflow_manager.stream_task(
            task_id=st.session_state.current_task_id
        ):
            if chunk:
                st.session_state.workflow_outputs.append(chunk)
                if isinstance(chunk, dict) and len(chunk) > 0:
                    node_name = list(chunk.keys())[0]
                    st.session_state.current_node = get_node_display_name(node_name)
        
        st.session_state.processing = False
        st.session_state.current_node = None
    except Exception as e:
        st.session_state.workflow_outputs.append({
            "error": {"message": f"继续处理出错: {str(e)}"}
        })
        st.session_state.processing = False


def reset_session():
    """重置会话状态"""
    st.session_state.current_task_id = None
    st.session_state.workflow_outputs = []
    st.session_state.current_node = None
    st.session_state.processing = False
    st.session_state.selected_optimization = None


if __name__ == "__main__":
    main()
# streamlit run streamlit_app.py --server.port 8501