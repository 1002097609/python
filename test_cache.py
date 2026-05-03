import json, urllib.request, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

data = json.dumps({
    "title": "测试缓存的素材",
    "content": "这是一款非常好用的护肤产品，推荐给大家！",
    "platform": "抖音",
    "category": ""
}).encode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:8081/api/dismantle/ai-analyze",
    data=data,
    headers={"Content-Type": "application/json; charset=utf8"},
    method="POST"
)

# First call
print("=== 第一次调用 ===")
t1 = time.time()
with urllib.request.urlopen(req, timeout=120) as resp:
    result1 = json.loads(resp.read().decode("utf-8"))
print(f"耗时: {time.time()-t1:.1f}s, 主题: {result1.get('l1_topic')}")

# Second call (should hit cache)
print("\n=== 第二次调用（应命中缓存）===")
t2 = time.time()
with urllib.request.urlopen(req, timeout=120) as resp:
    result2 = json.loads(resp.read().decode("utf-8"))
print(f"耗时: {time.time()-t2:.1f}s, 主题: {result2.get('l1_topic')}")

if result1.get('l1_topic') == result2.get('l1_topic'):
    print("\n✅ 缓存命中，结果一致")
else:
    print("\n❌ 缓存未命中，结果不一致")
