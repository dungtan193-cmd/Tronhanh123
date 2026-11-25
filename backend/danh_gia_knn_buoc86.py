from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path("D:/baicuoiki/data")
df = pd.read_csv(
    DATA / "rooms_clean_normalized.csv",
    encoding="utf-8-sig"
)

df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["area"] = pd.to_numeric(df["area"], errors="coerce")

df = df.dropna(subset=["price", "area", "district"])
df = df[(df["price"] > 0) & (df["area"] > 0)].copy()

df = df.reset_index(drop=True)

if len(df) < 3:
    raise ValueError("Can it nhat 3 phong de danh gia.")

def predict_knn(train, area, district, k=3):
    train = train.copy()

    # Chuan hoa khoang cach dien tich theo tap train
    scale = max(float(train["area"].std(ddof=0)), 1.0)

    area_distance = abs(train["area"] - area) / scale
    district_penalty = (
        train["district"].str.casefold() != district.casefold()
    ).astype(float)

    train["distance"] = area_distance + district_penalty

    neighbors = train.nsmallest(min(k, len(train)), "distance")

    weights = 1.0 / (neighbors["distance"].to_numpy() + 0.1)

    return float(np.average(
        neighbors["price"].to_numpy(),
        weights=weights
    ))

results = []

for i in range(len(df)):
    test = df.iloc[i]
    train = df.drop(index=i)

    prediction = predict_knn(
        train,
        float(test["area"]),
        str(test["district"])
    )

    actual = float(test["price"])

    results.append({
        "id": test["id"],
        "actual": actual,
        "predicted": round(prediction, 2),
        "absolute_error": round(abs(actual - prediction), 2)
    })

result = pd.DataFrame(results)

y_true = result["actual"].to_numpy()
y_pred = result["predicted"].to_numpy()

mae = float(np.mean(np.abs(y_true - y_pred)))
rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

ss_res = float(np.sum((y_true - y_pred) ** 2))
ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))

r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")

output = DATA / "danh_gia_knn_buoc86.csv"
result.to_csv(output, index=False, encoding="utf-8-sig")

print("HOAN THANH BUOC 86.12")
print("Phuong phap: Leave-One-Out Cross-Validation")
print("So phong:", len(df))

print("\nKET QUA:")
print("MAE: {:,.0f} VND".format(mae))
print("RMSE: {:,.0f} VND".format(rmse))
print("R2: {:.4f}".format(r2))

print("\nCHI TIET:")
print(result.to_string(index=False))

print("\nDa luu:", output)
print("LUU Y: Day la mo hinh KNN thu nghiem,")
print("khong phai ket qua danh gia API KNN hien tai.")
