"""
拆解引擎 API 测试（tests/test_dismantle.py）

覆盖：
  - 创建拆解记录
  - 查询拆解记录
  - 更新拆解记录
  - 按素材查询拆解
  - 拆解历史
"""

import pytest
from fastapi.testclient import TestClient


class TestCreateDismantle:
    """测试创建拆解记录"""

    def test_create_dismantle_success(self, client: TestClient, sample_material):
        """正常创建拆解"""
        resp = client.post("/api/dismantle/", json={
            "material_id": sample_material.id,
            "l1_topic": "测试主题",
            "l1_core_point": "核心观点",
            "l2_strategy": ["策略1"],
            "l2_emotion": "轻松幽默",
            "l3_structure": [{"name": "开头", "function": "痛点共鸣", "ratio": 0.3}],
        })
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["l1_topic"] == "测试主题"
        assert data["material_id"] == sample_material.id

    def test_create_dismantle_missing_required(self, client: TestClient, sample_material):
        """缺少必填字段 l1_topic 和 l3_structure"""
        resp = client.post("/api/dismantle/", json={
            "material_id": sample_material.id,
        })
        # Pydantic model_validator 校验失败返回 422
        assert resp.status_code == 422

    def test_create_dismantle_missing_l3_function(self, client: TestClient, sample_material):
        """l3_structure 缺少 function 字段"""
        resp = client.post("/api/dismantle/", json={
            "material_id": sample_material.id,
            "l1_topic": "测试",
            "l3_structure": [{"name": "开头"}],
        })
        assert resp.status_code == 422

    def test_create_dismantle_material_not_found(self, client: TestClient):
        """素材不存在"""
        resp = client.post("/api/dismantle/", json={
            "material_id": 99999,
            "l1_topic": "测试",
            "l3_structure": [{"name": "开头", "function": "引入"}],
        })
        assert resp.json()["code"] == 404

    def test_create_dismantle_updates_material_status(self, client: TestClient, sample_material):
        """创建拆解后素材状态变为已拆解"""
        client.post("/api/dismantle/", json={
            "material_id": sample_material.id,
            "l1_topic": "状态测试",
            "l3_structure": [{"name": "开头", "function": "引入"}],
        })
        material_resp = client.get(f"/api/material/{sample_material.id}")
        assert material_resp.json()["data"]["status"] == 1


class TestGetDismantle:
    """测试查询拆解记录"""

    def test_get_dismantle_success(self, client: TestClient, sample_dismantle):
        """正常查询"""
        resp = client.get(f"/api/dismantle/{sample_dismantle.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["l1_topic"] == "护肤品推荐"

    def test_get_dismantle_not_found(self, client: TestClient):
        """不存在的拆解"""
        resp = client.get("/api/dismantle/99999")
        assert resp.json()["code"] == 404

    def test_get_dismantle_by_material(self, client: TestClient, sample_material, sample_dismantle):
        """按素材 ID 查询拆解"""
        resp = client.get(f"/api/dismantle/by-material/{sample_material.id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["material_id"] == sample_material.id

    def test_get_dismantle_by_material_not_found(self, client: TestClient, sample_material):
        """素材未拆解"""
        # 创建一个没有拆解的素材
        create_resp = client.post("/api/material/", json={
            "title": "未拆解素材",
            "content": "内容",
        })
        material_id = create_resp.json()["data"]["id"]
        resp = client.get(f"/api/dismantle/by-material/{material_id}")
        assert resp.json()["code"] == 404


class TestUpdateDismantle:
    """测试更新拆解记录"""

    def test_update_dismantle_success(self, client: TestClient, sample_dismantle):
        """正常更新"""
        resp = client.put(f"/api/dismantle/{sample_dismantle.id}", json={
            "l1_topic": "更新后的主题",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["l1_topic"] == "更新后的主题"

    def test_update_dismantle_not_found(self, client: TestClient):
        """更新不存在的拆解"""
        resp = client.put("/api/dismantle/99999", json={"l1_topic": "不存在"})
        assert resp.json()["code"] == 404


class TestDismantleHistory:
    """测试拆解历史"""

    def test_get_dismantle_history(self, client: TestClient, sample_material, sample_dismantle):
        """查询拆解历史"""
        resp = client.get(f"/api/dismantle/by-material/{sample_material.id}/history")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
