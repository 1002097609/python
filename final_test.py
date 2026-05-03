import json, urllib.request, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

data = json.dumps({
    "title": "零食带货：办公室必备的低卡零食清单",
    "content": "打工人必看！这5款低卡零食让我一个月瘦了8斤。第一款是魔芋爽，0脂肪0蔗糖，嘴巴寂寞时来一包完全没负担。第二款是鸡胸肉干，蛋白质超高，比薯片好吃还不容易胖。",
    "platform": "抖音",
    "category": ""
}).encode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:8081/api/dismantle/ai-analyze",
    data=data,
    headers={"Content-Type": "application/json; charset=utf8"},
    method="POST"
)

print("Sending request...")
start = time.time()
try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        elapsed = time.time() - start
        result = json.loads(resp.read().decode("utf-8"))
    print(f"Response time: {elapsed:.1f}s")
    meta = result.get("_meta", {})
    fallback = meta.get("_fallback", False)
    print(f"Engine: {'RULE FALLBACK' if fallback else 'LongCat AI'}")
    print(f"L1 Topic: {result.get('l1_topic')}")
except Exception as e:
    elapsed = time.time() - start
    print(f"ERROR after {elapsed:.1f}s: {e}")
