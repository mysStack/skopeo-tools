"""
Skopeo API服务主入口
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import skopeo_router
from utils.logger import setup_logger

# 创建应用实例
app = FastAPI(
    title="Skopeo API",
    description="使用skopeo进行镜像操作的API服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(skopeo_router, prefix="/api")

# 设置日志
logger = setup_logger(__name__)

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("Skopeo API 服务器启动")

    # 检查skopeo是否可用
    from utils.skopeo_utils import check_skopeo_availability
    is_skopeo_available = await check_skopeo_availability()
    if not is_skopeo_available:
        logger.warning("Skopeo不可用，某些功能可能无法正常工作")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=settings.PORT, reload=True, log_level="debug")
