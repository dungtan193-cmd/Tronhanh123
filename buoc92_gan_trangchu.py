from pathlib import Path
import shutil

path = Path("frontend/src/App.jsx")
backup = Path("frontend/src/App_before_step92.jsx.bak")

content = path.read_text(encoding="utf-8-sig")

shutil.copy2(path, backup)

# 1. Import component
import_line = "import RentPricePredictor from './RentPricePredictor'"

if import_line not in content:
    anchor = "import DashboardAI from './DashboardAI'"

    if anchor not in content:
        raise RuntimeError("Không tìm thấy import DashboardAI.")

    content = content.replace(
        anchor,
        anchor + "\n" + import_line,
        1
    )

# 2. Chèn ngay phía trên bộ lọc và danh sách phòng
component = "<RentPricePredictor />"

if component not in content:
    anchor = '<div className="content-layout">'

    if content.count(anchor) != 1:
        raise RuntimeError(
            f"Tìm thấy {content.count(anchor)} vị trí content-layout. "
            "Dừng để tránh chèn sai."
        )

    content = content.replace(
        anchor,
        """{/* BUOC_92_AI_DU_DOAN_GIA */}
        <RentPricePredictor />

        """ + anchor,
        1
    )

path.write_text(content, encoding="utf-8")

print("THANH CONG: Da gan AI du doan gia vao trang chu.")
print("Backup:", backup)
print("So component:", content.count(component))
