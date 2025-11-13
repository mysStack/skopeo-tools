"""
应用配置模块
"""
import os
from typing import Optional

class Settings:
    """应用设置类"""

    # 服务器配置
    PORT: int = int(os.getenv("PORT", "8080"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Skopeo配置
    SKOPEO_TIMEOUT: int = int(os.getenv("SKOPEO_TIMEOUT", "120"))  # 默认120秒超时
    SKOPEO_PATH: str = os.getenv("SKOPEO_PATH", "skopeo")  # skopeo命令路径

    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")

    # 临时文件配置
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp/skopeo-tools")

    def __init__(self):
        # 确保临时目录存在
        os.makedirs(self.TEMP_DIR, exist_ok=True)

# 创建全局设置实例
settings = Settings()
