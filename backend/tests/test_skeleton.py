"""
骨架库 API 测试（tests/test_skeleton.py）

覆盖：
  - 创建骨架（从拆解记录提取）
  - 查询骨架列表（分页、筛选、排序）
  - 查询单个骨架
  - 更新骨架
  - 删除骨架
  - 骨架效果聚合数据
"""

import pytest
from fastapi.testclient import TestClient


class TestCreateSkeletonFromDismantle:
    """测试从拆解记录提取骨架"""

    def test_create_from_dismantle_success(self, client: TestClient, sample_dismantle):
        """正常提取骨架"""
        resp = client.post(f"/api/skeleton/from-dismantle/{sample_dismantle.id}")
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] is not None
        assert data["skeleton_type"] == "测评对比型"

    def test_create_from_dismantle_not_found(self, client: TestClient):
        """不存在的拆解记录"""
        resp = client.post("/api/skeleton/from-dismantle/99999")
        assert resp.json()["code"] == 404

    def test_create_from_dismantle_idempotent(self, client: TestClient, sample_material):
        """幂等性：重复提取返回已有骨架"""
        # 创建一个独立的拆解记录
        d_resp = client.post("/api/dismantle/", json={
            "material_id": sample_material.id,
            "l1_topic": "幂等测试",
        })
        dismantle_id = d_resp.json()["data"]["id"]

        # 第一次提取
        resp1 = client.post(f"/api/skeleton/from-dismantle/{dismantle_id}")
        assert resp1.status_code == 201
        skeleton_id = resp1.json()["data"]["id"]

        # 第二次（已有关联骨架，应返回已有骨架，不重复创建）
        resp2 = client.post(f"/api/skeleton/from-dismantle/{dismantle_id}")
        assert resp2.status_code in (200, 201)  # 取决于会话是否共享
        # 返回的骨架ID应与第一次相同（data中可能是id或skeleton_id）
        resp2_data = resp2.json()["data"]
        resp2_sk_id = resp2_data.get("id") or resp2_data.get("skeleton_id")
        assert resp2_sk_id == skeleton_id


class TestListSkeletons:
    """测试查询骨架列表"""

    def test_list_skeletons_empty(self, client: TestClient):
        """空列表"""
        resp = client.get("/api/skeleton/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_skeletons_with_data(self, client: TestClient, sample_skeleton):
        """有数据"""
        resp = client.get("/api/skeleton/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1

    def test_list_skeletons_filter_platform(self, client: TestClient, sample_skeleton):
        """按平台筛选"""
        resp = client.get("/api/skeleton/?platform=抖音")
        data = resp.json()["data"]
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["platform"] == "抖音"

    def test_list_skeletons_sort_by_roi(self, client: TestClient, sample_skeleton):
        """按 ROI 排序"""
        resp = client.get("/api/skeleton/?sort_by=avg_roi")
        assert resp.status_code == 200

    def test_list_skeletons_pagination(self, client: TestClient, sample_skeleton):
        """分页"""
        resp = client.get("/api/skeleton/?page=1&page_size=10")
        data = resp.json()["data"]
        assert data["page"] == 1
        assert data["page_size"] == 10


class TestGetSkeleton:
    """测试查询单个骨架"""

    def test_get_skeleton_success(self, client: TestClient, sample_skeleton):
        """正常查询"""
        resp = client.get(f"/api/skeleton/{sample_skeleton.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == sample_skeleton.id
        assert data["name"] == "测评对比型 — 护肤品推荐"

    def test_get_skeleton_not_found(self, client: TestClient):
        """不存在的骨架"""
        resp = client.get("/api/skeleton/99999")
        assert resp.json()["code"] == 404


class TestUpdateSkeleton:
    """测试更新骨架"""

    def test_update_skeleton_success(self, client: TestClient, sample_skeleton):
        """正常更新"""
        resp = client.put(f"/api/skeleton/{sample_skeleton.id}", json={
            "name": "更新后的骨架名称",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "更新后的骨架名称"

    def test_update_skeleton_not_found(self, client: TestClient):
        """更新不存在的骨架"""
        resp = client.put("/api/skeleton/99999", json={"name": "不存在"})
        assert resp.json()["code"] == 404


class TestDeleteSkeleton:
    """测试删除骨架"""

    def test_delete_skeleton_success(self, client: TestClient, sample_dismantle):
        """正常删除"""
        # 先创建一个骨架
        create_resp = client.post(f"/api/skeleton/from-dismantle/{sample_dismantle.id}")
        skeleton_id = create_resp.json()["data"]["id"]

        # 删除
        resp = client.delete(f"/api/skeleton/{skeleton_id}")
        assert resp.status_code == 204

        # 确认已删除
        get_resp = client.get(f"/api/skeleton/{skeleton_id}")
        assert get_resp.json()["code"] == 404


class TestSkeletonEffects:
    """测试骨架效果聚合数据"""

    def test_get_skeleton_effects_empty(self, client: TestClient, sample_skeleton):
        """无裂变数据时的效果"""
        resp = client.get(f"/api/skeleton/{sample_skeleton.id}/effects")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["trend"] == []
        assert data["fissions"] == []

    def test_get_skeleton_effects_with_data(self, client: TestClient, sample_skeleton, sample_effect):
        """有裂变+效果数据"""
        resp = client.get(f"/api/skeleton/{sample_skeleton.id}/effects")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["trend"]) >= 1
        assert len(data["fissions"]) >= 1
        # 验证趋势数据字段
        trend = data["trend"][0]
        assert "date" in trend
        assert "avg_roi" in trend
        assert "avg_ctr" in trend
        assert "total_cost" in trend
        assert "total_revenue" in trend

    def test_get_skeleton_effects_not_found(self, client: TestClient):
        """不存在的骨架"""
        resp = client.get("/api/skeleton/99999/effects")
        assert resp.json()["code"] == 404
