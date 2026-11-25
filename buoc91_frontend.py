from pathlib import Path
import shutil

path = Path("frontend/src/DashboardAI.jsx")
backup = Path("frontend/src/DashboardAI_before_step91.jsx.bak")

content = path.read_text(encoding="utf-8-sig")
shutil.copy2(path, backup)

import_line = "import PredictionComparisonCharts from './PredictionComparisonCharts'"

if import_line not in content:
    content = import_line + "\n" + content

anchor = """                        <ModelComparisonCharts
                          models={aiData.training?.models}
                        />"""

new = anchor + """

                        <PredictionComparisonCharts
                          models={aiData.training?.models}
                        />"""

if "<PredictionComparisonCharts" not in content:
    if anchor not in content:
        raise RuntimeError(
            "Không tìm thấy biểu đồ Bước 90 trong DashboardAI.jsx."
        )
    content = content.replace(anchor, new, 1)

path.write_text(content, encoding="utf-8")

print("Da them bieu do so sanh gia thuc te va du doan.")
print("Backup:", backup)
