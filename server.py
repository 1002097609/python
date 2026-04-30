"""
开发服务器入口
用法: python server.py
"""
import sys
import os

# 将项目根目录加入 path，使 backend 包可导入
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from backend.database import init_db
from backend.main import app
import uvicorn

if __name__ == "__main__":
    print("[INIT] 初始化数据库...")
    init_db()
    print("[OK] 数据库就绪")
    print("[START] 启动 FastAPI: http://localhost:8001")
    print("[DOCS] Swagger 文档:  http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)
