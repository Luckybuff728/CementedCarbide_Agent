"""
TopMat Agent 主运行脚本
"""
import os
import sys
import asyncio
import multiprocessing
from pathlib import Path
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_streamlit():
    """运行Streamlit应用"""
    import streamlit.web.cli as stcli
    import sys
    
    sys.argv = [
        "streamlit",
        "run",
        "streamlit_app.py",
        "--server.port", os.getenv("STREAMLIT_PORT", "8501"),
        "--server.address", "localhost",
        "--theme.base", "light",
        "--theme.primaryColor", "#4CAF50"
    ]
    sys.exit(stcli.main())


def run_fastapi():
    """运行FastAPI服务"""
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=os.getenv("SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVER_PORT", "8000")),
        reload=True,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )


def check_environment():
    """检查环境配置"""
    required_vars = ["DASHSCOPE_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"缺少必需的环境变量: {', '.join(missing_vars)}")
        logger.info("请复制 .env.example 到 .env 并填写相关配置")
        return False
    
    return True


def main():
    """主函数"""
    print("""
    ╔══════════════════════════════════════════╗
    ║     TopMat Agent - 涂层优化专家系统      ║
    ╚══════════════════════════════════════════╝
    """)
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 选择运行模式
    print("请选择运行模式:")
    print("1. 完整模式 (Streamlit + FastAPI)")
    print("2. 仅Streamlit前端")
    print("3. 仅FastAPI后端")
    print("4. 运行测试")
    print("5. 退出")
    
    choice = input("\n请输入选项 (1-5): ").strip()
    
    if choice == "1":
        # 完整模式
        logger.info("启动完整模式...")
        
        # 创建进程
        fastapi_process = multiprocessing.Process(target=run_fastapi)
        streamlit_process = multiprocessing.Process(target=run_streamlit)
        
        try:
            # 启动进程
            fastapi_process.start()
            logger.info("FastAPI服务已启动: http://localhost:8000")
            
            # 等待FastAPI启动
            import time
            time.sleep(2)
            
            streamlit_process.start()
            logger.info("Streamlit应用已启动: http://localhost:8501")
            
            print("\n服务已启动:")
            print("- Streamlit UI: http://localhost:8501")
            print("- FastAPI Docs: http://localhost:8000/docs")
            print("\n按 Ctrl+C 停止所有服务...")
            
            # 等待进程结束
            fastapi_process.join()
            streamlit_process.join()
            
        except KeyboardInterrupt:
            logger.info("正在停止服务...")
            fastapi_process.terminate()
            streamlit_process.terminate()
            fastapi_process.join()
            streamlit_process.join()
            logger.info("服务已停止")
    
    elif choice == "2":
        # 仅Streamlit
        logger.info("启动Streamlit前端...")
        run_streamlit()
    
    elif choice == "3":
        # 仅FastAPI
        logger.info("启动FastAPI后端...")
        run_fastapi()
    
    elif choice == "4":
        # 运行测试
        logger.info("运行测试...")
        import pytest
        pytest.main(["tests/", "-v", "--tb=short"])
    
    elif choice == "5":
        print("再见!")
        sys.exit(0)
    
    else:
        print("无效的选项，请重新运行")
        sys.exit(1)


def demo_mode():
    """演示模式 - 快速展示系统功能"""
    logger.info("进入演示模式...")
    
    from src.graph.workflow import CoatingWorkflowManager
    
    # 创建工作流管理器
    manager = CoatingWorkflowManager(use_memory=True)
    
    # 准备演示数据
    demo_input = {
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
        "target_requirements": "高速切削刀具涂层，需要高硬度(>30GPa)和良好的抗氧化性(>850℃)"
    }
    
    print("\n演示输入参数:")
    print(f"涂层成分: Al={demo_input['composition']['al_content']}%, "
          f"Ti={demo_input['composition']['ti_content']}%, "
          f"N={demo_input['composition']['n_content']}%")
    print(f"工艺参数: 偏压={demo_input['process_params']['bias_voltage']}V, "
          f"温度={demo_input['process_params']['deposition_temperature']}℃")
    print(f"目标需求: {demo_input['target_requirements']}")
    
    # 运行演示
    async def run_demo():
        task_id = "DEMO_001"
        print(f"\n开始任务: {task_id}")
        
        # 执行工作流
        print("\n执行中...")
        async for update in manager.stream_task(task_id, demo_input):
            if isinstance(update, tuple):
                mode, data = update
                print(f"[{mode}] 收到更新")
            else:
                print(f"收到更新: {type(update).__name__}")
        
        # 获取最终状态
        state = manager.get_task_state(task_id)
        
        print("\n任务完成!")
        print(f"最终状态: {state.get('workflow_status', 'unknown')}")
        
        if state.get('performance_prediction'):
            print("\n预测性能:")
            pred = state['performance_prediction']
            print(f"- 硬度: {pred.get('hardness', 'N/A')} GPa")
            print(f"- 结合力: {pred.get('adhesion_level', 'N/A')}")
            print(f"- 置信度: {pred.get('confidence_score', 0)*100:.1f}%")
        
        if state.get('optimization_suggestions'):
            print("\n优化建议:")
            for opt_type, suggestions in state['optimization_suggestions'].items():
                if suggestions:
                    print(f"- {opt_type}: {len(suggestions)} 个方案")
    
    # 运行异步函数
    asyncio.run(run_demo())
    
    print("\n演示完成!")


if __name__ == "__main__":
    # 检查是否是演示模式
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_mode()
    else:
        main()
