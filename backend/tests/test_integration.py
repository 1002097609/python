"""
集成测试（tests/test_integration.py）

覆盖核心业务流的端到端测试：
  素材 → 拆解 → 提取骨架 → 裂变 → 效果回写 → 骨架统计更新
"""

import pytest
from fastapi.testclient import TestClient


class TestFullBusinessFlow:
    """完整业务流程测试：素材 → 拆解 → 骨架 → 裂变 → 效果回写"""

    def test_complete_flow(self, client: TestClient, sample_option):
        """
        端到端业务流程：
        1. 创建素材
        2. 创建拆解记录
        3. 从拆解提取骨架
        4. 使用骨架执行裂变
        5. 录入裂变效果数据
        6. 验证骨架统计更新
        7. 查询骨架效果聚合
        """
        # Step 1: 创建素材
        material_resp = client.post("/api/material/", json={
            "title": "集成测试素材",
            "content": "这是一款非常好用的零食推荐视频",
            "platform": "抖音",
            "category": "零食",
        })
        assert material_resp.status_code == 201
        material_id = material_resp.json()["data"]["id"]

        # Step 2: 创建拆解记录
        dismantle_resp = client.post("/api/dismantle/", json={
            "material_id": material_id,
            "l1_topic": "零食推荐",
            "l1_core_point": "好吃不贵",
            "l2_strategy": ["反差对比"],
            "l2_emotion": "轻松幽默",
            "l3_structure": [
                {"name": "开头", "function": "痛点共鸣", "ratio": 0.2},
                {"name": "测评", "function": "产品展示", "ratio": 0.6},
                {"name": "结尾", "function": "行动号召", "ratio": 0.2},
            ],
            "l4_elements": {"hook": "提问式", "title_formula": "数字+效果"},
        })
        assert dismantle_resp.status_code == 201
        dismantle_id = dismantle_resp.json()["data"]["id"]

        # Step 3: 提取骨架
        skeleton_resp = client.post(f"/api/skeleton/from-dismantle/{dismantle_id}")
        assert skeleton_resp.status_code == 201
        skeleton_id = skeleton_resp.json()["data"]["id"]
        assert skeleton_resp.json()["data"]["skeleton_type"] == "测评对比型"

        # Step 4: 执行裂变
        fission_resp = client.post("/api/fission/", json={
            "skeleton_id": skeleton_id,
            "source_material_id": material_id,
            "fission_mode": "replace_leaf",
            "new_topic": "办公室减压零食",
            "new_category": "零食",
        })
        assert fission_resp.status_code == 201
        fission_id = fission_resp.json()["data"]["fission_id"]
        assert fission_resp.json()["data"]["predicted_ctr"] is not None
        assert fission_resp.json()["data"]["predicted_roi"] is not None

        # Step 5: 录入效果数据
        effect_resp = client.post("/api/effect/", json={
            "fission_id": fission_id,
            "material_id": material_id,
            "platform": "抖音",
            "impressions": 20000,
            "clicks": 600,
            "conversions": 90,
            "cost": 1000.0,
            "revenue": 3000.0,
            "stat_date": "2026-05-01",
        })
        assert effect_resp.status_code == 201
        effect_data = effect_resp.json()["data"]
        # 验证自动计算的 ROI
        assert effect_data["roi"] == 3.0

        # Step 6: 验证骨架统计已更新
        skeleton_get = client.get(f"/api/skeleton/{skeleton_id}")
        skeleton_data = skeleton_get.json()["data"]
        assert skeleton_data["usage_count"] == 1
        # avg_roi/avg_ctr 通过效果数据回写自动更新，具体值取决于加权计算

        # Step 7: 查询骨架效果聚合
        effects_resp = client.get(f"/api/skeleton/{skeleton_id}/effects")
        assert effects_resp.status_code == 200
        effects_data = effects_resp.json()["data"]
        assert len(effects_data["trend"]) >= 1
        assert len(effects_data["fissions"]) >= 1
        # 验证裂变记录的效果汇总
        fission_effect = effects_data["fissions"][0]
        assert fission_effect["effect_summary"] is not None
        assert fission_effect["effect_summary"]["roi"] == 3.0


class TestMaterialDeleteCascade:
    """测试素材删除的级联效果"""

    def test_delete_material_cascade(self, client: TestClient, sample_option):
        """删除素材应级联删除拆解、骨架、裂变、效果数据"""
        # 创建素材
        material_resp = client.post("/api/material/", json={
            "title": "级联删除测试",
            "content": "内容",
            "platform": "抖音",
            "category": "护肤",
        })
        material_id = material_resp.json()["data"]["id"]

        # 拆解
        dismantle_resp = client.post("/api/dismantle/", json={
            "material_id": material_id,
            "l1_topic": "测试",
        })
        dismantle_id = dismantle_resp.json()["data"]["id"]

        # 提取骨架
        skeleton_resp = client.post(f"/api/skeleton/from-dismantle/{dismantle_id}")
        skeleton_id = skeleton_resp.json()["data"]["id"]

        # 裂变
        fission_resp = client.post("/api/fission/", json={
            "skeleton_id": skeleton_id,
            "fission_mode": "replace_leaf",
            "new_topic": "测试裂变",
        })
        fission_id = fission_resp.json()["data"]["fission_id"]

        # 录入效果
        client.post("/api/effect/", json={
            "fission_id": fission_id,
            "cost": 500.0,
            "revenue": 1000.0,
            "stat_date": "2026-05-01",
        })

        # 删除素材
        delete_resp = client.delete(f"/api/material/{material_id}")
        assert delete_resp.status_code == 204

        # 验证素材已删除
        get_resp = client.get(f"/api/material/{material_id}")
        assert get_resp.json()["code"] == 404

        # 验证骨架已级联删除
        skeleton_get = client.get(f"/api/skeleton/{skeleton_id}")
        assert skeleton_get.json()["code"] == 404


class TestFissionStatusFlow:
    """测试裂变状态流转完整流程"""

    def test_fission_status_complete_flow(self, client: TestClient, sample_skeleton):
        """完整状态流转：草稿→待审核→已采用→已投放"""
        # 创建裂变
        fission_resp = client.post("/api/fission/", json={
            "skeleton_id": sample_skeleton.id,
            "fission_mode": "replace_leaf",
            "new_topic": "状态流转测试",
        })
        fission_id = fission_resp.json()["data"]["fission_id"]
        # 验证初始状态为草稿(0)
        detail_resp = client.get(f"/api/fission/{fission_id}")
        assert detail_resp.json()["data"]["output_status"] == 0

        # 0→1
        r1 = client.put(f"/api/fission/{fission_id}/status?status=1")
        assert r1.status_code == 200
        assert r1.json()["data"]["output_status"] == 1

        # 1→2
        r2 = client.put(f"/api/fission/{fission_id}/status?status=2")
        assert r2.status_code == 200
        assert r2.json()["data"]["output_status"] == 2

        # 2→3
        r3 = client.put(f"/api/fission/{fission_id}/status?status=3")
        assert r3.status_code == 200
        assert r3.json()["data"]["output_status"] == 3

        # 3 为终态，不能再变更
        r4 = client.put(f"/api/fission/{fission_id}/status?status=3")
        assert r4.json()["code"] == 400  # 状态未变化


class TestHealthEndpoint:
    """测试健康检查端点"""

    def test_health_check(self, client: TestClient):
        """健康检查返回正常"""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 200
        assert data["data"]["status"] == "healthy"

    def test_root_endpoint(self, client: TestClient):
        """根路径返回服务信息"""
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
