"""
项目根目录启动脚本 — 开发服务器入口

用法: 在项目根目录下运行 python server.py

功能：
- 将项目根目录加入 Python 路径，确保 backend 包可正常导入
- 初始化数据库（建库 + 建表）
- 启动 Uvicorn ASGI 服务器，监听 127.0.0.1:8081
"""
import sys
import os

# ============================================================
# 路径配置
# ============================================================
# 将项目根目录插入 Python 模块搜索路径最前面
# 这样可以直接 import backend.xxx，而不需要 cd 到 backend 目录
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

# ============================================================
# 导入依赖
# ============================================================
from backend.database import init_db   # 数据库初始化函数
from backend.main import app           # FastAPI 应用实例
import uvicorn                         # ASGI 服务器

# ============================================================
# 主程序入口
# ============================================================
if __name__ == "__main__":
    # Step 1: 初始化数据库（创建数据库 + 创建所有表）
    print("[INIT] 初始化数据库...")
    init_db()
    print("[OK] 数据库就绪")

    # Step 2: 启动 FastAPI 开发服务器
    # - host: 仅监听本地回环地址，外部网络无法直接访问
    # - port: 8081，避免与常见端口（8080、8000）冲突
    # - reload: 关闭热重载，避免 Windows 上的子进程问题
    print("[START] 启动 FastAPI: http://localhost:8001")
    print("[DOCS] Swagger 文档:  http://localhost:8001/docs")
    uvicorn.run(app, host="127.0.0.1", port=8081, reload=False)
