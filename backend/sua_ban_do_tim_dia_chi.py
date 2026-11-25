from pathlib import Path
from datetime import datetime
import shutil
import re

ROOT = Path(r"D:\baicuoiki")
APP = ROOT / "frontend" / "src" / "App.jsx"
MAP = ROOT / "frontend" / "src" / "components" / "BanDoChonViTri.jsx"

source = APP.read_text(encoding="utf-8-sig")

# 1. Kiem tra component moi
if not MAP.exists():
    raise SystemExit("LOI: Khong tim thay component ban do moi.")

map_code = MAP.read_text(encoding="utf-8-sig")

if "function searchAddress()" not in map_code:
    raise SystemExit("LOI: Component moi chua co chuc nang tim dia chi.")

# 2. Doi ten component cu, tranh trung ten
old_definition = re.compile(
    r"\bfunction\s+BanDoChonViTri\s*\("
)

if old_definition.search(source):
    source, count = old_definition.subn(
        "function BanDoChonViTriCu(",
        source,
        count=1
    )
    print("Da doi ten component ban do cu.")
elif "function BanDoChonViTriCu(" in source:
    print("Component cu da duoc doi ten.")
else:
    raise SystemExit("Khong tim thay component ban do cu.")

# 3. Import component moi
import_line = (
    'import BanDoChonViTri '
    'from "./components/BanDoChonViTri";'
)

if import_line not in source:
    source = import_line + "\n" + source

# 4. Chuyen form SUA PHONG sang component moi
edit_pattern = re.compile(
    r'<BanDoChonViTri\s+'
    r'latitude=\{editForm\.latitude\}\s+'
    r'longitude=\{editForm\.longitude\}\s+'
    r'onChange=\{\(lat,\s*lng\)\s*=>\s*'
    r'setEditForm\(\(prev\)\s*=>\s*'
    r'\(\{\s*\.\.\.prev,\s*latitude:\s*lat,\s*'
    r'longitude:\s*lng\s*\}\)\)\}\s*/>',
    re.MULTILINE
)

edit_replacement = """<BanDoChonViTri
                  address={editForm.address || ""}
                  value={
                    editForm.latitude != null &&
                    editForm.longitude != null &&
                    editForm.latitude !== "" &&
                    editForm.longitude !== ""
                      ? {
                          latitude: Number(editForm.latitude),
                          longitude: Number(editForm.longitude),
                        }
                      : null
                  }
                  onChange={({ latitude, longitude }) =>
                    setEditForm((prev) => ({
                      ...prev,
                      latitude,
                      longitude,
                    }))
                  }
                />"""

source, edit_count = edit_pattern.subn(
    lambda _: edit_replacement,
    source
)

# 5. Kiem tra form DANG PHONG
if "address={formDangTin.address}" not in source:
    raise SystemExit(
        "LOI: Form dang phong chua duoc ket noi dia chi."
    )

# 6. Sao luu va ghi file
backup = APP.with_name(
    "App.backup_map_search_" +
    datetime.now().strftime("%Y%m%d_%H%M%S") +
    ".jsx"
)

shutil.copy2(APP, backup)
APP.write_text(source, encoding="utf-8")

print("\n===== HOAN THANH =====")
print("Backup:", backup)
print("Da import component ban do moi.")
print("Da sua form sua phong:", edit_count)
print("Form dang phong: DA KET NOI")
print("File:", APP)
