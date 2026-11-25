from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path("D:/baicuoiki/data")

df = pd.read_csv(
    DATA / "danh_gia_knn_buoc86.csv",
    encoding="utf-8-sig"
)

def evaluate(data):
    actual = data["actual"].to_numpy(dtype=float)
    predicted = data["predicted"].to_numpy(dtype=float)

    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))

    ss_res = np.sum((actual - predicted) ** 2)
    ss_tot = np.sum((actual - actual.mean()) ** 2)

    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan

    return {
        "so_phong": len(data),
        "MAE": round(float(mae), 2),
        "RMSE": round(float(rmse), 2),
        "R2": round(float(r2), 4)
    }

all_rooms = evaluate(df)

# Chi tinh sai so tren 6 du doan da co.
# Khong huan luyen lai mo hinh.
without_id3 = evaluate(df[df["id"] != 3])

result = pd.DataFrame([
    {"truong_hop": "Day_du_7_phong", **all_rooms},
    {"truong_hop": "Bo_ket_qua_ID3", **without_id3}
])

output = DATA / "phan_tich_do_nhay_knn_buoc86.csv"
result.to_csv(output, index=False, encoding="utf-8-sig")

print("HOAN THANH BUOC 86.14")
print(result.to_string(index=False))
print("\nDa luu:", output)

print("\nLUU Y:")
print("Day la phan tich do nhay cua cac du doan da co.")
print("Khong phai ket qua huan luyen lai KNN voi 6 phong.")
