"""
裂变引擎 API 测试（tests/test_fission.py）

覆盖：
  - 执行裂变
  - 查询裂变列表
  - 查询单个裂变
  - 更新裂变状态
  - 删除裂变
  - 裂变统计
"""

import pytest
from fastapi.testclient import TestClient


class TestExecuteFission:
    """测试执行裂变"""

    def test_execute_fission_success(self, client: TestClient, sample_skeleton):
        """正常裂变"""
        resp = client.post("/api/fission/", json={
            "skeleton_id": sample_skeleton.id,
            "fission_mode": "replace_leaf",
            "new_topic": "办公室减压零食推荐",
            "new_category": "零食",
        })
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["output_title"] == "办公室减压零食推荐"
        assert data["output_content"] is not None
        assert data["predicted_ctr_min"] is not None
        assert data["predicted_ctr_max"] is not None
        assert data["predicted_roi_min"] is not None
        assert data["predicted_roi_max"] is not None

    def test_execute_fission_skeleton_not_found(self, client: TestClient):
        """骨架不存在"""
        resp = client.post("/api/fission/", json={
            "skeleton_id": 99999,
            "fission_mode": "replace_leaf",
        })
        assert resp.json()["code"] == 404

    def test_execute_fission_replace_branch(self, client: TestClient, sample_skeleton):
        """换枝杈模式"""
        resp = client.post("/api/fission/", json={
            "skeleton_id": sample_skeleton.id,
            "fission_mode": "replace_branch",
            "new_topic": "新品类测试",
        })
        assert resp.status_code == 201

    def test_execute_fission_replace_style(self, client: TestClient, sample_skeleton):
        """换表达模式"""
        resp = client.post("/api/fission/", json={
            "skeleton_id": sample_skeleton.id,
            "fission_mode": "replace_style",
            "new_topic": "新风格测试",
        })
        assert resp.status_code == 201

    def test_execute_fission_increments_usage(self, client: TestClient, sample_skeleton):
        """裂变后骨架使用次数+1"""
        before = sample_skeleton.usage_count or 0
        client.post("/api/fission/", json={
            "skeleton_id": sample_skeleton.id,
            "fission_mode": "replace_leaf",
            "new_topic": "使用次数测试",
        })
        skeleton_resp = client.get(f"/api/skeleton/{sample_skeleton.id}")
        after = skeleton_resp.json()["data"]["usage_count"]
        assert after == before + 1


class TestListFissions:
    """测试查询裂变列表"""

    def test_list_fissions_empty(self, client: TestClient):
        """空列表"""
        resp = client.get("/api/fission/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["items"] == []

    def test_list_fissions_with_data(self, client: TestClient, sample_fission):
        """有数据"""
        resp = client.get("/api/fission/")
        data = resp.json()["data"]
        assert data["total"] >= 1

    def test_list_fissions_filter_status(self, client: TestClient, sample_fission):
        """按状态筛选"""
        resp = client.get("/api/fission/?output_status=0")
        data = resp.json()["data"]
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["output_status"] == 0

    def test_list_fissions_pagination(self, client: TestClient, sample_fission):
        """分页"""
        resp = client.get("/api/fission/?page=1&page_size=5")
        data = resp.json()["data"]
        assert data["page"] == 1
        assert data["page_size"] == 5


class TestGetFission:
    """测试查询单个裂变"""

    def test_get_fission_success(self, client: TestClient, sample_fission):
        """正常查询"""
        resp = client.get(f"/api/fission/{sample_fission.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == sample_fission.id
        assert data["fission_mode"] == "replace_leaf"

    def test_get_fission_not_found(self, client: TestClient):
        """不存在的裂变"""
        resp = client.get("/api/fission/99999")
        assert resp.json()["code"] == 404


class TestUpdateFissionStatus:
    """测试更新裂变状态"""

    def test_update_status_success(self, client: TestClient, sample_fission):
        """正常推进状态"""
        resp = client.put(f"/api/fission/{sample_fission.id}/status?status=1")
        assert resp.status_code == 200
        assert resp.json()["data"]["output_status"] == 1

    def test_update_status_full_flow(self, client: TestClient, sample_fission):
        """完整状态流转: 0→1→2→3"""
        for target in [1, 2, 3]:
            resp = client.put(f"/api/fission/{sample_fission.id}/status?status={target}")
            assert resp.status_code == 200
            assert resp.json()["data"]["output_status"] == target

    def test_update_status_no_regression(self, client: TestClient, sample_fission):
        """状态不能回退"""
        client.put(f"/api/fission/{sample_fission.id}/status?status=1")
        resp = client.put(f"/api/fission/{sample_fission.id}/status?status=0")
        assert resp.json()["code"] == 400

    def test_update_status_no_skip(self, client: TestClient, sample_fission):
        """不能跳跃状态"""
        resp = client.put(f"/api/fission/{sample_fission.id}/status?status=2")
        assert resp.json()["code"] == 400

    def test_update_status_invalid(self, client: TestClient, sample_fission):
        """无效状态值"""
        resp = client.put(f"/api/fission/{sample_fission.id}/status?status=99")
        assert resp.json()["code"] == 400

    def test_update_status_not_found(self, client: TestClient):
        """不存在的裂变"""
        resp = client.put("/api/fission/99999/status?status=1")
        assert resp.json()["code"] == 404


class TestDeleteFission:
    """测试删除裂变"""

    def test_delete_fission_success(self, client: TestClient, sample_skeleton):
        """正常删除"""
        # 先创建一个裂变
        create_resp = client.post("/api/fission/", json={
            "skeleton_id": sample_skeleton.id,
            "fission_mode": "replace_leaf",
            "new_topic": "待删除裂变",
        })
        fission_id = create_resp.json()["data"]["fission_id"]

        # 删除
        resp = client.delete(f"/api/fission/{fission_id}")
        assert resp.status_code == 204

    def test_delete_fission_not_found(self, client: TestClient):
        """删除不存在的裂变"""
        resp = client.delete("/api/fission/99999")
        assert resp.json()["code"] == 404


class TestFissionStats:
    """测试裂变统计"""

    def test_fission_stats(self, client: TestClient, sample_fission):
        """获取统计"""
        resp = client.get("/api/fission/stats")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total" in data
        assert "draft" in data
        assert data["total"] >= 1
