"""
效果数据 API 测试（tests/test_effect.py）

覆盖：
  - 录入效果数据
  - 查询效果数据
  - 更新效果数据
  - 删除效果数据
  - 自动推导衍生指标
  - 效果闭环（更新裂变实际效果和骨架统计）
"""

import pytest
from fastapi.testclient import TestClient


class TestCreateEffect:
    """测试录入效果数据"""

    def test_create_effect_success(self, client: TestClient, sample_fission):
        """正常录入"""
        resp = client.post("/api/effect/", json={
            "fission_id": sample_fission.id,
            "material_id": sample_fission.source_material_id,
            "platform": "抖音",
            "impressions": 10000,
            "clicks": 300,
            "conversions": 45,
            "cost": 500.0,
            "revenue": 1200.0,
            "stat_date": "2026-05-01",
        })
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["fission_id"] == sample_fission.id
        assert data["roi"] is not None  # 自动计算

    def test_create_effect_auto_calculate(self, client: TestClient, sample_fission):
        """自动推导衍生指标"""
        resp = client.post("/api/effect/", json={
            "fission_id": sample_fission.id,
            "impressions": 1000,
            "clicks": 100,
            "conversions": 10,
            "cost": 200.0,
            "revenue": 800.0,
            "stat_date": "2026-05-02",
        })
        data = resp.json()["data"]
        # CTR = 100/1000*100 = 10.0
        assert data["ctr"] == 10.0
        # CVR = 10/100*100 = 10.0
        assert data["cvr"] == 10.0
        # ROI = 800/200 = 4.0
        assert data["roi"] == 4.0
        # CPA = 200/10 = 20.0
        assert data["cpa"] == 20.0

    def test_create_effect_no_fission_or_material(self, client: TestClient):
        """必须关联 fission_id 或 material_id"""
        resp = client.post("/api/effect/", json={
            "cost": 100.0,
        })
        assert resp.json()["code"] == 400


class TestGetEffect:
    """测试查询效果数据"""

    def test_get_fission_effects(self, client: TestClient, sample_fission, sample_effect):
        """查询裂变关联的效果数据"""
        resp = client.get(f"/api/effect/fission/{sample_fission.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1

    def test_get_effect_detail(self, client: TestClient, sample_effect):
        """查询单条效果数据"""
        resp = client.get(f"/api/effect/{sample_effect.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == sample_effect.id

    def test_get_effect_not_found(self, client: TestClient):
        """不存在的效果数据"""
        resp = client.get("/api/effect/99999")
        assert resp.json()["code"] == 404


class TestUpdateEffect:
    """测试更新效果数据"""

    def test_update_effect_success(self, client: TestClient, sample_effect):
        """正常更新"""
        resp = client.put(f"/api/effect/{sample_effect.id}", json={
            "cost": 600.0,
            "revenue": 1500.0,
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["cost"] == 600.0

    def test_update_effect_not_found(self, client: TestClient):
        """更新不存在的数据"""
        resp = client.put("/api/effect/99999", json={"cost": 100.0})
        assert resp.json()["code"] == 404


class TestDeleteEffect:
    """测试删除效果数据"""

    def test_delete_effect_success(self, client: TestClient, sample_fission):
        """正常删除"""
        # 先创建一条
        create_resp = client.post("/api/effect/", json={
            "fission_id": sample_fission.id,
            "cost": 100.0,
            "revenue": 200.0,
            "stat_date": "2026-05-03",
        })
        effect_id = create_resp.json()["data"]["id"]

        # 删除
        resp = client.delete(f"/api/effect/{effect_id}")
        assert resp.status_code == 204

    def test_delete_effect_not_found(self, client: TestClient):
        """删除不存在的数据"""
        resp = client.delete("/api/effect/99999")
        assert resp.json()["code"] == 404
