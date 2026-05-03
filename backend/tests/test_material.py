"""
素材管理 API 测试（tests/test_material.py）

覆盖：
  - 创建素材
  - 查询素材列表（分页、筛选）
  - 查询单个素材
  - 更新素材
  - 删除素材
  - 批量更新状态
"""

import pytest
from fastapi.testclient import TestClient


class TestCreateMaterial:
    """测试创建素材"""

    def test_create_material_success(self, client: TestClient):
        """正常创建素材"""
        resp = client.post("/api/material/", json={
            "title": "测试素材",
            "content": "测试内容",
            "platform": "抖音",
            "category": "护肤",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["code"] == 201
        assert data["data"]["title"] == "测试素材"
        assert data["data"]["platform"] == "抖音"
        assert data["data"]["status"] == 0

    def test_create_material_minimal(self, client: TestClient):
        """只传必填字段"""
        resp = client.post("/api/material/", json={
            "title": "最小素材",
            "content": "内容",
        })
        assert resp.status_code == 201
        assert resp.json()["data"]["title"] == "最小素材"

    def test_create_material_missing_title(self, client: TestClient):
        """缺少 title 应返回 422"""
        resp = client.post("/api/material/", json={
            "content": "没有标题",
        })
        assert resp.status_code == 422


class TestListMaterials:
    """测试查询素材列表"""

    def test_list_materials_empty(self, client: TestClient):
        """空列表"""
        resp = client.get("/api/material/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_materials_with_data(self, client: TestClient, sample_material):
        """有数据时的列表"""
        resp = client.get("/api/material/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_list_materials_filter_platform(self, client: TestClient, sample_material):
        """按平台筛选"""
        resp = client.get("/api/material/?platform=抖音")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["platform"] == "抖音"

    def test_list_materials_filter_category(self, client: TestClient, sample_material):
        """按品类筛选"""
        resp = client.get("/api/material/?category=护肤")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1

    def test_list_materials_keyword_search(self, client: TestClient, sample_material):
        """关键词搜索"""
        resp = client.get("/api/material/?keyword=护肤")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1

    def test_list_materials_pagination(self, client: TestClient, sample_material):
        """分页参数"""
        resp = client.get("/api/material/?page=1&page_size=5")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["page"] == 1
        assert data["page_size"] == 5


class TestGetMaterial:
    """测试查询单个素材"""

    def test_get_material_success(self, client: TestClient, sample_material):
        """正常查询"""
        resp = client.get(f"/api/material/{sample_material.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == sample_material.id
        assert data["title"] == "测试护肤素材"

    def test_get_material_not_found(self, client: TestClient):
        """不存在的素材"""
        resp = client.get("/api/material/99999")
        assert resp.status_code == 200  # 统一响应格式，HTTP 200 但 code=404
        assert resp.json()["code"] == 404


class TestUpdateMaterial:
    """测试更新素材"""

    def test_update_material_success(self, client: TestClient, sample_material):
        """正常更新"""
        resp = client.put(f"/api/material/{sample_material.id}", json={
            "title": "更新后的标题",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "更新后的标题"

    def test_update_material_not_found(self, client: TestClient):
        """更新不存在的素材"""
        resp = client.put("/api/material/99999", json={"title": "不存在"})
        assert resp.json()["code"] == 404


class TestDeleteMaterial:
    """测试删除素材"""

    def test_delete_material_success(self, client: TestClient):
        """正常删除"""
        # 先创建一个素材
        create_resp = client.post("/api/material/", json={
            "title": "待删除素材",
            "content": "内容",
        })
        material_id = create_resp.json()["data"]["id"]

        # 删除
        resp = client.delete(f"/api/material/{material_id}")
        assert resp.status_code == 204

        # 确认已删除
        get_resp = client.get(f"/api/material/{material_id}")
        assert get_resp.json()["code"] == 404

    def test_delete_material_not_found(self, client: TestClient):
        """删除不存在的素材"""
        resp = client.delete("/api/material/99999")
        assert resp.json()["code"] == 404


class TestBatchUpdateStatus:
    """测试批量更新状态"""

    def test_batch_update_success(self, client: TestClient):
        """正常批量更新"""
        # 创建两个素材
        ids = []
        for i in range(2):
            resp = client.post("/api/material/", json={
                "title": f"批量素材{i}",
                "content": "内容",
            })
            ids.append(resp.json()["data"]["id"])

        resp = client.put("/api/material/batch/status", json={
            "ids": ids,
            "status": 1,
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["updated"] == 2

    def test_batch_update_empty_ids(self, client: TestClient):
        """空 ids 应返回 422"""
        resp = client.put("/api/material/batch/status", json={
            "ids": [],
            "status": 1,
        })
        assert resp.json()["code"] == 422

    def test_batch_update_invalid_status(self, client: TestClient):
        """无效 status 应返回 422"""
        resp = client.put("/api/material/batch/status", json={
            "ids": [1],
            "status": 99,
        })
        assert resp.json()["code"] == 422
