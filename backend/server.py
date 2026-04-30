"""
开发服务器入口（从 backend 目录内运行）
用法: cd backend && python ../server.py
"""
import sys
import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, PROJECT_DIR)
os.chdir(PROJECT_DIR)

from backend.database import init_db
from backend.main import app
import uvicorn

if __name__ == "__main__":
    print("[INIT] 初始化数据库...")
    init_db()
    print("[OK] 数据库就绪")
    print("[START] 启动 FastAPI: http://localhost:8000")
    print("[DOCS] Swagger 文档:  http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
