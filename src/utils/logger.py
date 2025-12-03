"""
统一日志配置模块
使用 loguru 替代标准 logging，并拦截标准 logging 的日志输出。
"""
import logging
import sys
import os
from pathlib import Path
from loguru import logger

class InterceptHandler(logging.Handler):
    """
    拦截标准 logging 日志并转发到 loguru
    """
    def emit(self, record):
        # 获取对应的 Loguru 日志级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 查找调用者
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """
    配置统一日志
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径（可选）
    """
    # 移除 loguru 默认的 handler
    logger.remove()
    
    # 1. 配置控制台输出
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 2. 配置从标准 logging 拦截
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # 设置一些第三方库的日志级别，避免太啰嗦
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    
    # 3. 配置文件输出（如果提供）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            str(log_path),
            rotation="10 MB",    # 每个文件 10MB
            retention="10 days", # 保留 10 天
            compression="zip",   # 压缩旧日志
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            encoding="utf-8"
        )
        
    logger.info(f"日志系统初始化完成，级别: {log_level}")

# 导出 logger 实例
__all__ = ["setup_logging", "logger"]
