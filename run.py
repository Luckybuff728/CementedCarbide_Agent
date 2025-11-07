"""
TopMat Agent 主运行脚本
简化版本 - 直接启动FastAPI服务
"""
import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_fastapi(reload=True):
    """运行FastAPI服务
    
    Args:
        reload: 是否启用热重载（开发模式）
    """
    import uvicorn
    
    # 从环境变量读取配置
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"启动FastAPI服务: {host}:{port}")
    logger.info(f"热重载模式: {'开启' if reload else '关闭'}")
    logger.info(f"日志级别: {log_level}")
    
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level
    )

def check_environment():
    """检查环境配置
    
    Returns:
        bool: 环境配置是否完整
    """
    required_vars = ["DASHSCOPE_API_KEY"]
    missing_vars = []
    
    logger.info("检查环境配置...")
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            # 隐藏敏感信息
            value = os.getenv(var)
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            logger.info(f"✓ {var}: {masked_value}")
    
    if missing_vars:
        logger.error(f"✗ 缺少必需的环境变量: {', '.join(missing_vars)}")
        logger.info("请复制 .env.example 到 .env 并填写相关配置")
        return False
    
    # 检查可选配置
    optional_vars = ["SERVER_HOST", "SERVER_PORT", "LOG_LEVEL", "DATABASE_URL"]
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✓ {var}: {value}")
        else:
            logger.debug(f"- {var}: 使用默认值")
    
    logger.info("环境配置检查完成 ✓")
    return True

def print_banner():
    """打印启动横幅"""
    print("""
    ╔══════════════════════════════════════════╗
    ║     TopMat Agent - 涂层优化专家系统      ║
    ║              v1.0.1                      ║
    ╚══════════════════════════════════════════╝
    """)

def main():
    """主函数
    
    支持命令行参数:
        --no-reload: 禁用热重载（生产模式）
        --test: 运行测试
    """
    print_banner()
    
    # 检查环境
    if not check_environment():
        logger.error("环境配置不完整，退出")
        sys.exit(1)
    
    # 解析命令行参数
    if "--test" in sys.argv:
        # 运行测试模式
        logger.info("运行测试套件...")
        try:
            import pytest
            sys.exit(pytest.main(["tests/", "-v", "--tb=short"]))
        except ImportError:
            logger.error("pytest未安装，请运行: pip install pytest")
            sys.exit(1)
    
    # 检查是否禁用热重载
    reload = "--no-reload" not in sys.argv
    
    # 启动FastAPI服务
    logger.info("提示: 前端服务请在frontend目录运行 'npm run dev'")
    logger.info("="*50)
    
    try:
        run_fastapi(reload=reload)
    except KeyboardInterrupt:
        logger.info("\n收到中断信号，正在关闭服务...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"服务启动失败: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
