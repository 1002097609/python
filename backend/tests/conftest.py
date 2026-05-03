"""
测试固件模块（tests/conftest.py）

提供 pytest 测试所需的共享固件（fixtures），包括：
  - 内存 SQLite 测试数据库
  - FastAPI TestClient
  - 预置的测试数据（素材、拆解、骨架、裂变、效果数据）
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.database import Base
from backend.main import app
from backend.database import get_db
from datetime import date
from backend.models.material import Material
from backend.models.dismantle import Dismantle
from backend.models.skeleton import Skeleton
from backend.models.fission import Fission
from backend.models.effect_data import EffectData
from backend.models.option import Option
from backend.models.tag import Tag, MaterialTag


# ============================================================
# 测试数据库（内存 SQLite）
# ============================================================
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """创建所有测试表（整个测试会话只执行一次）"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    每个测试函数独立的数据库会话。
    使用嵌套事务实现回滚，确保测试间数据隔离。
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    """
    FastAPI TestClient，覆盖 get_db 依赖以使用测试数据库。
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ============================================================
# 基础数据固件
# ============================================================

@pytest.fixture
def sample_option(db):
    """创建测试用选项数据"""
    options = [
        Option(group_key="platform", label="抖音", value="douyin", sort_order=1),
        Option(group_key="platform", label="快手", value="kuaishou", sort_order=2),
        Option(group_key="category", label="护肤", value="skincare", sort_order=1),
        Option(group_key="category", label="零食", value="snack", sort_order=2),
        Option(group_key="style", label="轻松幽默", value="humorous", sort_order=1),
        Option(group_key="fission_mode", label="换叶子|🍃|效果保留85%", value="replace_leaf", sort_order=1),
        Option(group_key="fission_mode", label="换枝杈|🌿|效果保留65%", value="replace_branch", sort_order=2),
        Option(group_key="fission_mode", label="换表达|🎨|效果保留70%", value="replace_style", sort_order=3),
    ]
    for opt in options:
        db.add(opt)
    db.commit()
    return options


@pytest.fixture
def sample_material(db, sample_option):
    """创建测试用素材"""
    material = Material(
        title="测试护肤素材",
        content="这是一款非常好用的护肤产品推荐视频脚本",
        platform="抖音",
        category="护肤",
        media_type="video",
        status=0,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@pytest.fixture
def sample_dismantle(db, sample_material):
    """创建测试用拆解记录"""
    dismantle = Dismantle(
        material_id=sample_material.id,
        l1_topic="护肤品推荐",
        l1_core_point="好皮肤靠对的产品",
        l2_strategy=["反差对比", "痛点切入"],
        l2_emotion="轻松幽默",
        l3_structure=[
            {"name": "开头", "function": "痛点共鸣", "ratio": 0.2},
            {"name": "测评", "function": "产品展示", "ratio": 0.5},
            {"name": "结尾", "function": "行动号召", "ratio": 0.3},
        ],
        l3_summary="开头共鸣→测评展示→结尾号召",
        l4_elements={
            "hook": "提问式",
            "title_formula": "数字+效果",
            "transition": "自然过渡",
        },
        l5_expressions={
            "title": "这款护肤品真的好用",
            "script": "今天给大家分享一款我最近爱用的护肤品",
        },
    )
    db.add(dismantle)
    db.commit()
    db.refresh(dismantle)
    # 更新素材状态
    sample_material.status = 1
    db.commit()
    return dismantle


@pytest.fixture
def sample_skeleton(db, sample_material, sample_dismantle):
    """创建测试用骨架"""
    skeleton = Skeleton(
        name="测评对比型 — 护肤品推荐",
        skeleton_type="测评对比型",
        source_material_id=sample_material.id,
        strategy_desc="轻松幽默+反差对比",
        structure_json=[
            {"name": "开头", "function": "痛点共鸣", "ratio": 0.2},
            {"name": "测评", "function": "产品展示", "ratio": 0.5},
            {"name": "结尾", "function": "行动号召", "ratio": 0.3},
        ],
        elements_json={
            "hook": "提问式",
            "title_formula": "数字+效果",
        },
        style_tags=["轻松幽默", "快节奏"],
        platform="抖音",
        usage_count=0,
    )
    db.add(skeleton)
    db.commit()
    db.refresh(skeleton)

    # 关联拆解记录
    sample_dismantle.skeleton_id = skeleton.id
    db.commit()

    return skeleton


@pytest.fixture
def sample_fission(db, sample_skeleton):
    """创建测试用裂变记录"""
    fission = Fission(
        skeleton_id=sample_skeleton.id,
        source_material_id=sample_skeleton.source_material_id,
        fission_mode="replace_leaf",
        new_topic="办公室减压零食推荐",
        new_category="零食",
        new_platform="抖音",
        replacement_json={},
        output_title="办公室减压零食推荐",
        output_content="工作累了？试试这些好吃的零食...",
        output_status=0,
        predicted_ctr="1.1%-1.4%",
        predicted_roi="1.4x-1.9x",
    )
    db.add(fission)
    db.commit()
    db.refresh(fission)

    # 更新骨架使用次数
    sample_skeleton.usage_count = 1
    db.commit()

    return fission


@pytest.fixture
def sample_effect(db, sample_fission):
    """创建测试用效果数据"""
    effect = EffectData(
        fission_id=sample_fission.id,
        material_id=sample_fission.source_material_id,
        platform="抖音",
        impressions=10000,
        clicks=330,
        ctr=3.3,
        conversions=50,
        cvr=15.15,
        cost=500.0,
        revenue=1200.0,
        roi=2.4,
        cpa=10.0,
        stat_date=date(2026, 4, 30),
    )
    db.add(effect)
    db.commit()
    db.refresh(effect)
    return effect
