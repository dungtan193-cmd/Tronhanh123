from pathlib import Path
from datetime import datetime
import ast
import re

path = Path("backend/main.py")
source = path.read_text(encoding="utf-8-sig")

marker = "# ===== BUOC 93.23: AUTO AI LIFESPAN ====="

if marker in source:
    print("Buoc 93.23 da duoc tich hop.")
    raise SystemExit(0)

ai_path = Path("backend/routers/ai_live.py")
ai_source = ai_path.read_text(encoding="utf-8-sig")

if not all(
    name in ai_source
    for name in ("def start_auto_ai_refresh(", "def stop_auto_ai_refresh(")
):
    raise SystemExit(
        "Chua co ham auto AI trong ai_live.py. "
        "Can hoan thanh buoc 93.22 truoc."
    )

# Kiem tra cau truc Python truoc khi sua.
ast.parse(source)

if re.search(r"\blifespan\s*=", source):
    raise SystemExit(
        "FastAPI da co lifespan. "
        "Chua sua file de tranh ghi de co che cu."
    )

if re.search(r"@app\.on_event\s*\(", source):
    raise SystemExit(
        "Phat hien startup/shutdown event cu. "
        "Chua sua file de tranh xung dot."
    )

pattern = r"\bapp\s*=\s*FastAPI\s*\("
match = re.search(pattern, source)

if not match:
    raise SystemExit("Khong tim thay app = FastAPI(...).")

backup = path.with_name(
    "main.backup_93_23_" +
    datetime.now().strftime("%Y%m%d_%H%M%S") +
    ".py"
)

addition = '''
# ===== BUOC 93.23: AUTO AI LIFESPAN =====
from contextlib import asynccontextmanager
from backend.routers.ai_live import (
    start_auto_ai_refresh,
    stop_auto_ai_refresh,
)

@asynccontextmanager
async def tronhanh_lifespan(app: FastAPI):
    start_auto_ai_refresh()
    try:
        yield
    finally:
        stop_auto_ai_refresh()


'''

updated = (
    source[:match.start()]
    + addition
    + source[match.start():]
)

updated = re.sub(
    r"\bapp\s*=\s*FastAPI\s*\(",
    "app = FastAPI(\n    lifespan=tronhanh_lifespan,",
    updated,
    count=1,
)

ast.parse(updated)

backup.write_text(source, encoding="utf-8")
path.write_text(updated, encoding="utf-8")

print("=== BUOC 93.23 HOAN THANH ===")
print("Da sao luu:", backup)
print("Da ket noi auto AI vao FastAPI lifespan.")
print("AI se kiem tra du lieu dinh ky khi backend dang chay.")
