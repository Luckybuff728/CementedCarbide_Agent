"""
TopMat Agent Docker环境运行脚本
无需用户交互，直接启动FastAPI服务
"""
import os
import sys
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


def run_fastapi():
    """运行FastAPI服务"""
    import uvicorn
    
    logger.info("=" * 50)
    logger.info("TopMat Agent - 后端服务启动中...")
    logger.info("=" * 50)
    logger.info(f"服务地址: http://0.0.0.0:8000")
    logger.info(f"API文档: http://0.0.0.0:8000/docs")
    logger.info("=" * 50)
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",  # Docker环境需要监听所有接口
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    try:
        run_fastapi()
    except KeyboardInterrupt:
        logger.info("\n后端服务已停止")
        sys.exit(0)
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}", exc_info=True)
        sys.exit(1)
