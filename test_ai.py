import json, urllib.request, urllib.error

data = json.dumps({
    "title": "测试护肤精华种草",
    "content": "姐妹们！这款精华真的太好用了，连续用了28天，皮肤状态明显改善。成分党必看，5%烟酰胺浓度刚刚好，敏感肌也能用。质地清爽不油腻，吸收超快。对比了市面上10款同类产品，这款性价比排第一！回购了3次，闭眼入不会错。",
    "platform": "抖音",
    "category": ""
}).encode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:8081/api/dismantle/ai-analyze",
    data=data,
    headers={"Content-Type": "application/json; charset=utf8"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    print("=== AI 拆解结果 ===")
    print(f"L1 主题: {result.get('l1_topic')}")
    print(f"L1 核心卖点: {result.get('l1_core_point')}")
    print(f"L2 策略: {', '.join(result.get('l2_strategy', []))}")
    print(f"L2 情绪: {result.get('l2_emotion')}")
    print("L3 结构:")
    for s in result.get("l3_structure", []):
        print(f"  - {s.get('name')} ({s.get('ratio')}%): {s.get('function')}")
    l4 = result.get("l4_elements", {})
    print(f"L4 标题公式: {l4.get('title_formula')}")
    print(f"L4 钩子: {l4.get('hook')}")
    l5 = result.get("l5_expressions", {})
    print(f"L5 金句: {', '.join(l5.get('golden_sentences', []))}")
    meta = result.get("_meta", {})
    print(f"\nMeta: 品类={meta.get('detected_category')}, 结构={meta.get('structure_type')}, 降级={meta.get('_fallback', False)}")

except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"ERROR: {e}")
