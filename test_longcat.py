import os, sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r"D:\claude_demo\demo2\demo")

from backend.database import engine  # trigger load_dotenv
from backend.services.ai_dismantle import _call_longcat, LONGCAT_API_KEY, LONGCAT_BASE_URL, LONGCAT_MODEL

print(f"API Key: {LONGCAT_API_KEY[:10]}...")
print(f"Base URL: {LONGCAT_BASE_URL}")
print(f"Model: {LONGCAT_MODEL}")
print()

result = _call_longcat(
    title="测试护肤精华种草",
    content="姐妹们！这款精华真的太好用了，连续用了28天，皮肤状态明显改善。",
    platform="抖音",
    category=""
)

if result:
    print("LongCat API 调用成功!")
    print(json.dumps(result, ensure_ascii=False, indent=2))
else:
    print("LongCat API 返回 None - 调用失败")
