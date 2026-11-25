from pathlib import Path
from datetime import datetime

path = Path("frontend/src/DashboardAI.jsx")
source = path.read_text(encoding="utf-8-sig")

if "import LiveGISCharts" in source:
    print("LiveGISCharts da duoc tich hop.")
    raise SystemExit(0)

anchor = "<AdvancedLiveCharts"

if anchor not in source:
    raise SystemExit(
        "Khong tim thay AdvancedLiveCharts. "
        "Chua thay doi Dashboard."
    )

backup = path.with_name(
    "DashboardAI.backup_" +
    datetime.now().strftime("%Y%m%d_%H%M%S") +
    ".jsx"
)

backup.write_text(source, encoding="utf-8")

source = (
    "import LiveGISCharts from './LiveGISCharts'\n"
    + source
)

# Chen GIS ngay truoc component AdvancedLiveCharts.
# LiveGISCharts tu goi API va tu cap nhat du lieu.
source = source.replace(
    anchor,
    "<LiveGISCharts />\n                    " + anchor,
    1
)

path.write_text(source, encoding="utf-8")

print("Da sao luu:", backup)
print("Da them GIS dong vao DashboardAI.jsx")
