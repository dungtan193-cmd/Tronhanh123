from pathlib import Path
import shutil
from datetime import datetime

path = Path("backend/main.py")
text = path.read_text(encoding="utf-8-sig")

import_line = (
    "from backend.routers.ai_gis_research "
    "import router as ai_gis_research_router"
)

include_line = "app.include_router(ai_gis_research_router)"

if import_line in text and include_line in text:
    print("Router da duoc dang ky. Khong can sua.")
else:
    if "app = FastAPI(" not in text:
        raise RuntimeError(
            "Khong tim thay app = FastAPI(...). "
            "Can kiem tra main.py truoc khi sua."
        )

    backup = path.with_name(
        "main.py.bak_93_6_" +
        datetime.now().strftime("%Y%m%d_%H%M%S")
    )

    shutil.copy2(path, backup)

    if import_line not in text:
        text = import_line + "\n" + text

    if include_line not in text:
        text += "\n" + include_line + "\n"

    path.write_text(text, encoding="utf-8")
    print("Da dang ky router.")
    print("Backup:", backup)
