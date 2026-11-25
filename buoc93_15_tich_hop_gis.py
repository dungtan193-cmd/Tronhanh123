from pathlib import Path
from datetime import datetime
import re

app_path = Path("frontend/src/App.jsx")
gis_path = Path("frontend/src/pages/GISAnalysis.jsx")

if not app_path.exists():
    raise SystemExit("Khong tim thay App.jsx")

if not gis_path.exists():
    raise SystemExit(
        "Chua co GISAnalysis.jsx. "
        "Hay chay lai buoc tao trang GIS truoc."
    )

source = app_path.read_text(encoding="utf-8-sig")

# Khong chen trung neu da tich hop.
if "GISAnalysis" in source:
    print("GISAnalysis da duoc nhac den trong App.jsx.")
    print("Khong tu dong sua de tranh trung lap.")
    raise SystemExit(0)

# Chi ho tro App.jsx co component App mac dinh.
pattern = r"(?m)^function App\s*\(\s*\)\s*\{"
match = re.search(pattern, source)

if not match:
    raise SystemExit(
        "Khong tim thay function App(). "
        "Chua sua file; can kiem tra cau truc App.jsx."
    )

# Sao luu truoc khi sua.
backup = app_path.with_name(
    "App.backup_93_15_" +
    datetime.now().strftime("%Y%m%d_%H%M%S") +
    ".jsx"
)
backup.write_text(source, encoding="utf-8")

# Them import.
source = (
    "import GISAnalysis from './pages/GISAnalysis'\n"
    + source
)

# Chen dieu huong rieng o dau App.
# Khong can cai them react-router-dom.
source = re.sub(
    pattern,
    lambda m: (
        m.group(0)
        + "\n  if (window.location.pathname === '/gis-analysis') {"
        + "\n    return <GISAnalysis />"
        + "\n  }\n"
    ),
    source,
    count=1,
)

app_path.write_text(source, encoding="utf-8")

print("=== BUOC 93.15 ===")
print("Da sao luu:", backup)
print("Da tich hop trang GIS vao App.jsx")
print("Duong dan: http://localhost:5173/gis-analysis")
