"""
FastAPI 应用主入口模块

职责：
- 创建 FastAPI 应用实例
- 注册全局中间件（CORS 跨域支持）
- 挂载所有 API 路由
- 应用启动时自动初始化数据库

启动时调用 init_db() 确保数据库和所有表已创建。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .routes import api_router

# ============================================================
# 创建 FastAPI 应用实例
# ============================================================
app = FastAPI(
    title="素材拆解与裂变系统",
    description="营销素材拆解、骨架管理与裂变引擎",
    version="0.1.0",
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
# 挂载 API 路由
# ============================================================
# api_router 统一挂载在 /api 前缀下，各子路由再分别挂载各自的端点
# 例如：/api/material/、/api/dismantle/、/api/option/ 等
app.include_router(api_router)


# ============================================================
# 应用启动事件
# ============================================================
@app.on_event("startup")
def on_startup():
    """
    应用启动回调函数

    在 FastAPI 启动完成、开始接收请求之前执行：
    - 连接到 MySQL 数据库
    - 如果数据库不存在则自动创建
    - 如果数据表不存在则自动建表（SQLAlchemy create_all）

    这保证了应用每次启动时数据库结构都是最新的。
    """
    init_db()


# ============================================================
# 根路径健康检查
# ============================================================
@app.get("/")
def root():
    """
    根路径 — 服务健康检查端点

    Returns:
        dict: 包含系统名称和 API 文档地址的欢迎信息
    """
    return {"message": "素材拆解与裂变系统 API", "docs": "/docs"}
