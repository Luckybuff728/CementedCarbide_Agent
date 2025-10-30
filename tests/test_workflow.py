"""
工作流测试用例
"""
import pytest
import asyncio
from src.graph.workflow import CoatingWorkflowManager
from src.graph.state import CoatingWorkflowState
from src.models.coating_models import (
    CoatingComposition,
    ProcessParameters,
    StructureDesign,
    TargetRequirements
)


@pytest.fixture
def workflow_manager():
    """创建工作流管理器fixture"""
    return CoatingWorkflowManager(use_memory=False)


@pytest.fixture
def sample_input_data():
    """创建示例输入数据"""
    return {
        "composition": {
            "al_content": 30.0,
            "ti_content": 25.0,
            "n_content": 45.0,
            "x_element": None,
            "x_content": 0.0
        },
        "process_params": {
            "deposition_pressure": 0.6,
            "n2_flow": 210,
            "ar_flow": 280,
            "kr_flow": 200,
            "bias_voltage": 90,
            "deposition_temperature": 550
        },
        "structure_design": {
            "total_thickness": 3.0,
            "layers": []
        },
        "target_requirements": "高速切削刀具涂层，需要高硬度和良好的抗氧化性"
    }


@pytest.mark.asyncio
async def test_workflow_initialization(workflow_manager):
    """测试工作流初始化"""
    assert workflow_manager is not None
    assert workflow_manager.workflow is not None
    assert len(workflow_manager.active_tasks) == 0


@pytest.mark.asyncio
async def test_start_task(workflow_manager, sample_input_data):
    """测试启动任务"""
    task_id = "TEST_001"
    
    # 启动任务
    result = await workflow_manager.start_task(
        task_id=task_id,
        input_data=sample_input_data,
        thread_id="THREAD_TEST"
    )
    
    # 验证结果
    assert result is not None
    assert result.get("task_id") == task_id
    assert result.get("workflow_status") in ["validated", "error", "predicted"]
    
    # 检查任务是否被记录
    assert task_id in workflow_manager.active_tasks


@pytest.mark.asyncio
async def test_input_validation_success(workflow_manager, sample_input_data):
    """测试输入验证成功的情况"""
    task_id = "TEST_VALIDATION_SUCCESS"
    
    result = await workflow_manager.start_task(
        task_id=task_id,
        input_data=sample_input_data
    )
    
    # 验证应该通过
    assert result.get("input_validated") is True
    assert len(result.get("validation_errors", [])) == 0


@pytest.mark.asyncio
async def test_input_validation_failure(workflow_manager):
    """测试输入验证失败的情况"""
    # 创建无效输入（成分总和超过100%）
    invalid_input = {
        "composition": {
            "al_content": 50.0,
            "ti_content": 40.0,
            "n_content": 30.0,
            "x_element": None,
            "x_content": 0.0
        },
        "process_params": {
            "deposition_pressure": 0.6,
            "n2_flow": 210,
            "ar_flow": 280,
            "kr_flow": 200,
            "bias_voltage": 90,
            "deposition_temperature": 550
        },
        "structure_design": {
            "total_thickness": 3.0,
            "layers": []
        },
        "target_requirements": "测试需求"
    }
    
    task_id = "TEST_VALIDATION_FAIL"
    result = await workflow_manager.start_task(
        task_id=task_id,
        input_data=invalid_input
    )
    
    # 验证应该失败
    assert result.get("input_validated") is False
    assert len(result.get("validation_errors", [])) > 0


@pytest.mark.asyncio
async def test_stream_task(workflow_manager, sample_input_data):
    """测试流式执行任务"""
    task_id = "TEST_STREAM"
    updates = []
    
    # 收集所有流式更新
    async for chunk in workflow_manager.stream_task(
        task_id=task_id,
        input_data=sample_input_data
    ):
        updates.append(chunk)
    
    # 验证有更新产生
    assert len(updates) > 0
    
    # 检查更新类型
    update_types = [type(u) for u in updates]
    assert all(isinstance(u, (dict, tuple)) for u in updates)


@pytest.mark.asyncio
async def test_user_selection_update(workflow_manager, sample_input_data):
    """测试用户选择更新"""
    task_id = "TEST_SELECTION"
    
    # 先启动任务
    await workflow_manager.start_task(
        task_id=task_id,
        input_data=sample_input_data
    )
    
    # 更新用户选择
    selection = {
        "type": "P1",
        "description": "增加Al含量至35%",
        "expected_improvement": 2.5
    }
    
    workflow_manager.update_task_selection(task_id, selection)
    
    # 验证选择已更新
    state = workflow_manager.get_task_state(task_id)
    assert state["selected_optimization_type"] == "P1"
    assert state["selected_optimization_plan"] == selection


@pytest.mark.asyncio
async def test_add_experimental_results(workflow_manager, sample_input_data):
    """测试添加实验结果"""
    task_id = "TEST_RESULTS"
    
    # 启动任务
    await workflow_manager.start_task(
        task_id=task_id,
        input_data=sample_input_data
    )
    
    # 添加实验结果
    results = {
        "actual_hardness": 29.5,
        "sem_quality": "良好",
        "adhesion_level": "HF1"
    }
    
    workflow_manager.add_experimental_results(task_id, results)
    
    # 验证结果已添加
    state = workflow_manager.get_task_state(task_id)
    assert state["experimental_results"] == results


@pytest.mark.asyncio
async def test_get_nonexistent_task(workflow_manager):
    """测试获取不存在的任务"""
    with pytest.raises(ValueError):
        workflow_manager.get_task_state("NONEXISTENT_TASK")


@pytest.mark.asyncio
async def test_composition_normalization():
    """测试成分归一化"""
    from src.graph.nodes import normalize_composition
    
    composition = {
        "al_content": 30,
        "ti_content": 20,
        "n_content": 40
    }
    
    normalized = normalize_composition(composition)
    total = sum(normalized.values())
    
    # 归一化后总和应该是100
    assert abs(total - 100.0) < 0.1


def test_coating_models():
    """测试涂层模型"""
    # 测试成分模型
    composition = CoatingComposition(
        al_content=30.0,
        ti_content=25.0,
        n_content=45.0
    )
    assert composition.al_content == 30.0
    
    # 测试工艺参数模型
    params = ProcessParameters()
    assert params.deposition_pressure == 0.6
    assert params.bias_voltage == 90
    
    # 测试结构设计模型
    structure = StructureDesign(
        total_thickness=3.0,
        layers=[]
    )
    assert structure.total_thickness == 3.0
    
    # 测试成分验证（总和超过100%应该报错）
    with pytest.raises(ValueError):
        invalid_comp = CoatingComposition(
            al_content=50.0,
            ti_content=40.0,
            n_content=30.0
        )


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
