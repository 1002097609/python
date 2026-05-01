"""
备选启动脚本 — 从 backend 目录下运行

用法: cd backend && python run.py

与 server.py 的区别：
- server.py 从项目根目录运行，手动配置路径
- run.py 从 backend 目录运行，自动推导路径，使用 subprocess 启动 uvicorn

流程：
1. 初始化数据库
2. 设置 PYTHONPATH 环境变量
3. 通过 subprocess 启动 uvicorn（生产推荐方式）
"""
import subprocess
import sys
import os

# ============================================================
# 路径推导
# ============================================================
# 获取当前文件（run.py）的绝对路径，即 backend/ 目录
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# Step 1: 初始化数据库
# ============================================================
# 将 backend 目录加入模块搜索路径，使 from database import 生效
sys.path.insert(0, BACKEND_DIR)
from database import init_db

# 创建数据库和所有数据表（如果不存在）
init_db()
print("[OK] 数据库初始化完成")

# ============================================================
# Step 2: 准备环境变量
# ============================================================
# 将 backend 目录加入 PYTHONPATH，确保 uvicron 能找到 main:app
env = os.environ.copy()
env["PYTHONPATH"] = BACKEND_DIR + os.pathsep + env.get("PYTHONPATH", "")

# ============================================================
# Step 3: 启动 uvicorn 服务器
# ============================================================
# 使用 subprocess.run 而非 uvicorn.run()，这是生产环境推荐的做法
# - cwd: 设置工作目录为 backend/，确保相对路径正确
# - env: 传入修改后的环境变量
print("[START] FastAPI: http://localhost:8000")
print("[DOCS] Swagger: http://localhost:8000/docs")
subprocess.run(
    [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
    cwd=BACKEND_DIR,
    env=env,
)
