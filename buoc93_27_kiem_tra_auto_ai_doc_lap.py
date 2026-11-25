import subprocess
import sys
import time
from pathlib import Path

print("=== BUOC 93.27: KIEM TRA AUTO AI DOC LAP ===")

code = r"""
import time
from fastapi.testclient import TestClient
from backend.main import app
from backend.routers.ai_live import state, lock

with TestClient(app) as client:
    print("FastAPI lifespan started", flush=True)

    for i in range(12):
        with lock:
            status = state["status"]
            updated_at = state["updated_at"]
            error = state["error"]

        print(
            f"Lan {i+1}: status={status}, "
            f"updated_at={updated_at}, error={error}",
            flush=True
        )

        if status == "ready":
            print("PASS: AI tu chay khong can goi API status", flush=True)
            break

        if status == "error":
            print("FAIL: AI gap loi", flush=True)
            break

        time.sleep(5)
    else:
        print("TIMEOUT: AI chua hoan thanh sau 60 giay", flush=True)
"""

try:
    result = subprocess.run(
        [sys.executable, "-c", code],
        timeout=90,
        check=False
    )
    print("Exit code:", result.returncode)

except subprocess.TimeoutExpired:
    print("TIMEOUT: Qua trinh kiem tra vuot 90 giay.")

print("=== KET THUC ===")
