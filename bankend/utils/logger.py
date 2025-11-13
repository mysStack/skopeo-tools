"""
日志工具模块
"""
import logging
import os
from typing import Optional

def setup_logger(name: str, log_file: Optional[str] = None, level: str = "INFO") -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径，如果不指定则输出到控制台
        level: 日志级别

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 清除可能存在的处理器
    logger.handlers.clear()

    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 如果指定了日志文件，添加文件处理器
    if log_file:
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        # 否则添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
