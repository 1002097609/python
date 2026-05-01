"""
数据库连接与初始化模块

本模块负责营销素材拆解与裂变系统的数据库连接配置和初始化。
主要功能：
  - 从环境变量读取 MySQL 连接配置
  - 创建 SQLAlchemy 引擎和会话工厂
  - 提供 get_db() 依赖注入函数（FastAPI 中使用）
  - 提供 init_db() 函数自动创建数据库和建表
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# 加载 .env 文件中的环境变量（DB_HOST、DB_PORT 等配置）
load_dotenv()

# ==================== 从环境变量读取数据库连接配置 ====================
# 若环境变量未设置，则使用默认值（适用于本地开发环境）
DB_HOST = os.getenv("DB_HOST", "localhost")       # 数据库主机地址
DB_PORT = os.getenv("DB_PORT", "3306")             # 数据库端口，MySQL 默认 3306
DB_USER = os.getenv("DB_USER", "root")             # 数据库用户名
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")     # 数据库密码
DB_NAME = os.getenv("DB_NAME", "material_system")  # 数据库名称

# 组装 MySQL 连接 URL，使用 pymysql 驱动，字符集设为 utf8mb4 支持 emoji
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# 创建 SQLAlchemy 引擎
# echo=True 表示在控制台输出 SQL 语句（调试用，生产环境建议关闭）
# pool_pre_ping=True 表示连接池在使用前先检测连接是否存活，防止连接断开导致报错
engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)

# 创建会话工厂
# autocommit=False 表示不自动提交，需手动调用 commit()
# autoflush=False 表示不会在每次查询前自动刷新变更
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明式基类，所有 ORM 模型类都继承自此类
Base = declarative_base()


def get_db():
    """
    数据库会话生成器（FastAPI 依赖注入使用）。

    使用 yield 确保请求结束后自动关闭会话，防止连接泄漏。
    典型的 FastAPI 依赖注入用法：db: Session = Depends(get_db)

    Yields:
        sqlalchemy.orm.Session: 数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # 请求处理完成后确保释放数据库连接


def init_db():
    """
    初始化数据库：创建数据库（若不存在）并创建所有表。

    步骤：
      1. 连接到 MySQL 服务器（不指定数据库），执行 CREATE DATABASE IF NOT EXISTS
      2. 使用模型基类 Base 的元数据在目标数据库中创建所有已注册的表

    注意：此函数在应用启动时调用一次即可，重复调用不会删除已有数据。
    """
    # 第一步：连接到 MySQL 服务器（不指定具体数据库），用于创建数据库本身
    temp_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/?charset=utf8mb4"
    temp_engine = create_engine(temp_url, echo=False)  # 临时引擎，关闭 SQL 输出
    with temp_engine.connect() as conn:
        # 创建数据库，使用 utf8mb4 字符集和 utf8mb4_unicode_ci 排序规则（支持中文和 emoji）
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    temp_engine.dispose()  # 释放临时引擎的连接池

    # 第二步：在已存在的数据库中，根据所有已注册 ORM 模型创建对应的表
    Base.metadata.create_all(bind=engine)
