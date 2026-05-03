"""
FastAPI 应用主入口模块

职责：
- 创建 FastAPI 应用实例
- 注册全局中间件（CORS 跨域支持）
- 挂载所有 API 路由
- 全局异常处理器
- 健康检查端点
- 优雅启停（lifespan）
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .database import init_db, engine
from .routes import api_router
from .response import success, BusinessException

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理：
    - 启动时：初始化数据库
    - 关闭时：释放数据库连接池
    """
    logger.info("Application starting up...")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("Application shutting down...")
    engine.dispose()
    logger.info("Database connections released")


# ============================================================
# 创建 FastAPI 应用实例
# ============================================================
app = FastAPI(
    title="素材拆解与裂变系统",
    description="营销素材拆解、骨架管理与裂变引擎",
    version="0.1.0",
    lifespan=lifespan,
)

# ============================================================
# 注册全局中间件
# ============================================================
# 启用 CORS 跨域支持，允许前端（Vite 开发服务器）访问后端 API
# 生产环境中应收紧 allow_origins 配置，此处为开发便利设置为 "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 允许所有域名跨域（开发模式）
    allow_credentials=True,       # 允许携带 Cookie
    allow_methods=["*"],          # 允许所有 HTTP 方法
    allow_headers=["*"],          # 允许所有请求头
)


# ============================================================
# 全局异常处理器
# ============================================================
@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    """处理业务异常，返回统一格式的错误响应"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """兜底异常处理器，捕获所有未处理的异常，避免直接暴露堆栈信息"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "data": None},
    )


# ============================================================
# 挂载 API 路由
# ============================================================
# api_router 统一挂载在 /api 前缀下，各子路由再分别挂载各自的端点
# 例如：/api/material/、/api/dismantle/、/api/option/ 等
app.include_router(api_router)


# ============================================================
# 健康检查端点
# ============================================================
@app.get("/")
def root():
    """
    根路径 — 服务健康检查端点

    Returns:
        dict: 包含系统名称和 API 文档地址的欢迎信息
    """
    return success({"message": "素材拆解与裂变系统 API", "docs": "/docs"})


@app.get("/health")
def health_check():
    """
    健康检查端点 — 供负载均衡器 / K8s 存活探针使用

    Returns:
        dict: 服务状态信息
    """
    return success({"status": "healthy", "service": "material-system"})
