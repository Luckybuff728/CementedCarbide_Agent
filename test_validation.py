"""
测试input_validation节点的问题
"""
import sys
sys.path.append('d:/Agent/TopMat_Agent_1.0')

from src.graph.nodes import input_validation_node

# 模拟前端发送的数据
test_state = {
    "task_id": "TEST_001",
    "coating_composition": {
        "al_content": 30.0,
        "ti_content": 25.0,
        "n_content": 45.0,
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
        "layer_type": "单层",
        "layers": []
    },
    "target_requirements": "应用场景: 高速切削刀具涂层，需要高硬度和良好的抗氧化性, 硬度要求: 30.0GPa, 结合力要求: HF1"
}

print("=== 测试输入验证节点 ===")
print(f"输入数据: {test_state}")
print()

result = input_validation_node(test_state)

print("=== 验证结果 ===")
print(f"input_validated: {result.get('input_validated')}")
print(f"validation_errors: {result.get('validation_errors')}")
print(f"workflow_status: {result.get('workflow_status')}")
print()

if not result.get('input_validated'):
    print("❌ 验证失败！")
    print("错误信息:")
    for error in result.get('validation_errors', []):
        print(f"  - {error}")
else:
    print("✅ 验证通过！")
