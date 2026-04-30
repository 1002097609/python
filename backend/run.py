"""启动脚本 — 在 backend 目录下运行: python run.py"""
import subprocess
import sys
import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# 先初始化数据库
sys.path.insert(0, BACKEND_DIR)
from database import init_db
init_db()
print("[OK] 数据库初始化完成")

# 用正确的环境变量启动 uvicorn
env = os.environ.copy()
env["PYTHONPATH"] = BACKEND_DIR + os.pathsep + env.get("PYTHONPATH", "")

print("[START] FastAPI: http://localhost:8000")
print("[DOCS] Swagger: http://localhost:8000/docs")
subprocess.run(
    [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
    cwd=BACKEND_DIR,
    env=env,
)
