from pathlib import Path
import shutil

path = Path("frontend/src/DashboardAI.jsx")
backup = Path("frontend/src/DashboardAI_before_step90.jsx.bak")

content = path.read_text(encoding="utf-8-sig")
shutil.copy2(path, backup)

import_line = "import ModelComparisonCharts from './ModelComparisonCharts'"

if import_line not in content:
    content = import_line + "\n" + content

anchor = """                        <p style={{ color: '#b45309' }}>
                          Kết quả chỉ mang tính thử nghiệm, chưa đủ cơ sở
                          để định giá phòng trọ thực tế.
                        </p>"""

chart = """                        <ModelComparisonCharts
                          models={aiData.training?.models}
                        />

"""

if anchor not in content:
    raise RuntimeError(
        "Không tìm thấy vị trí thêm biểu đồ. "
        "File DashboardAI.jsx chưa đúng cấu trúc dự kiến."
    )

if "<ModelComparisonCharts" not in content:
    content = content.replace(anchor, chart + anchor, 1)

path.write_text(content, encoding="utf-8")

print("Đã tích hợp biểu đồ đánh giá AI.")
print("File sao lưu:", backup)
