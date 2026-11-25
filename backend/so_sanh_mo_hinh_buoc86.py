from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path("D:/baicuoiki/data")

knn = pd.read_csv(DATA / "danh_gia_knn_buoc86.csv")
rooms = pd.read_csv(
    DATA / "rooms_clean_normalized.csv",
    encoding="utf-8-sig"
)

rooms["price"] = pd.to_numeric(rooms["price"], errors="coerce")
rooms = rooms.dropna(subset=["price"])
rooms = rooms[rooms["price"] > 0]

knn["id"] = pd.to_numeric(knn["id"])
rooms["id"] = pd.to_numeric(rooms["id"])

actual_by_id = rooms.set_index("id")["price"]

# Baseline LOOCV: trung binh gia cua tat ca phong tru phong dang kiem tra
baseline_predictions = []

for room_id in knn["id"]:
    train = rooms[rooms["id"] != room_id]
    baseline_predictions.append(float(train["price"].mean()))

knn["baseline_predicted"] = baseline_predictions

def metrics(actual, predicted):
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))

    ss_res = np.sum((actual - predicted) ** 2)
    ss_tot = np.sum((actual - actual.mean()) ** 2)

    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan

    return mae, rmse, r2

y = knn["actual"].to_numpy()

knn_scores = metrics(y, knn["predicted"])
baseline_scores = metrics(y, knn["baseline_predicted"])

comparison = pd.DataFrame([
    {
        "model": "KNN",
        "MAE": knn_scores[0],
        "RMSE": knn_scores[1],
        "R2": knn_scores[2]
    },
    {
        "model": "Baseline_Mean",
        "MAE": baseline_scores[0],
        "RMSE": baseline_scores[1],
        "R2": baseline_scores[2]
    }
])

output = DATA / "so_sanh_mo_hinh_buoc86.csv"
comparison.to_csv(output, index=False, encoding="utf-8-sig")

print("HOAN THANH BUOC 86.13")
print("\nSO SANH MO HINH:")
print(comparison.to_string(index=False))

print("\nDa luu:", output)
print("Luu y: Chi co 7 mau, ket qua mang tinh thu nghiem.")
