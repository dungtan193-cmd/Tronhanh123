from pathlib import Path
import shutil

path = Path("backend/main.py")
content = path.read_text(encoding="utf-8-sig")

shutil.copy2(path, "backend/main_before_step93.py.bak")

import_line = "from backend.routers.ai_gis import router as ai_gis_router"
include_line = "app.include_router(ai_gis_router)"

if import_line not in content:
    content = import_line + "\n" + content

if include_line not in content:
    content += "\n" + include_line + "\n"

path.write_text(content, encoding="utf-8")

print("Da dang ky API GIS AI.")
