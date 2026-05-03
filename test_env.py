import os, sys
sys.path.insert(0, r"D:\claude_demo\demo2\demo")

# Simulate what happens at import time
# First database loads dotenv
from backend.database import engine  # This triggers load_dotenv()
print(f"After database import, ANTHROPIC_AUTH_TOKEN = {os.getenv('ANTHROPIC_AUTH_TOKEN', 'NOT_SET')[:10]}...")

# Now import ai_dismantle
from backend.services.ai_dismantle import LONGCAT_API_KEY, LONGCAT_BASE_URL, LONGCAT_MODEL
print(f"LONGCAT_API_KEY = {LONGCAT_API_KEY[:10] if LONGCAT_API_KEY else 'EMPTY'}...")
print(f"LONGCAT_BASE_URL = {LONGCAT_BASE_URL}")
print(f"LONGCAT_MODEL = {LONGCAT_MODEL}")
