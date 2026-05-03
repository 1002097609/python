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
        raw = resp.read().decode("utf-8")
        result = json.loads(raw)

    # Print raw JSON to see exact content
    print("=== RAW JSON ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    meta = result.get("_meta", {})
    is_fallback = meta.get("_fallback", False)
    print(f"\n是否降级(规则引擎): {is_fallback}")
    if is_fallback:
        print("⚠️  使用的是规则引擎（LongCat API 未生效）")
    else:
        print("✅ 使用的是 LongCat AI 大模型")

except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"ERROR: {e}")
