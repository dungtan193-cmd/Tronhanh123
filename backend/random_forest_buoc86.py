from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA = Path("D:/baicuoiki/data")

df = pd.read_csv(
    DATA / "rooms_clean_normalized.csv",
    encoding="utf-8-sig"
)

df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["area"] = pd.to_numeric(df["area"], errors="coerce")

df = df.dropna(subset=["id", "price", "area", "district"])
df = df[(df["price"] > 0) & (df["area"] > 0)].copy()
df = df.sort_values("id").reset_index(drop=True)

if len(df) < 3:
    raise ValueError("Can it nhat 3 phong de danh gia.")

predictions = []

for i in range(len(df)):
    train = df.drop(index=i)
    test = df.iloc[[i]]

    # One-hot encoding: chi hoc danh sach quan tu tap train
    X_train = pd.get_dummies(
        train[["area", "district"]],
        columns=["district"],
        dtype=float
    )

    X_test = pd.get_dummies(
        test[["area", "district"]],
        columns=["district"],
        dtype=float
    )

    X_test = X_test.reindex(
        columns=X_train.columns,
        fill_value=0
    )

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=4,
        min_samples_leaf=1,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, train["price"])

    predicted = float(model.predict(X_test)[0])

    predictions.append({
        "id": int(test["id"].iloc[0]),
        "actual": float(test["price"].iloc[0]),
        "predicted": predicted,
        "absolute_error": abs(
            float(test["price"].iloc[0]) - predicted
        )
    })

result = pd.DataFrame(predictions)

y_true = result["actual"].to_numpy()
y_pred = result["predicted"].to_numpy()

mae = mean_absolute_error(y_true, y_pred)
rmse = np.sqrt(mean_squared_error(y_true, y_pred))
r2 = r2_score(y_true, y_pred)

result.to_csv(
    DATA / "danh_gia_random_forest_buoc86.csv",
    index=False,
    encoding="utf-8-sig"
)

summary = pd.DataFrame([{
    "model": "Random_Forest",
    "MAE": mae,
    "RMSE": rmse,
    "R2": r2
}])

summary.to_csv(
    DATA / "chi_so_random_forest_buoc86.csv",
    index=False,
    encoding="utf-8-sig"
)

print("HOAN THANH BUOC 86.17")
print("Phuong phap: LOOCV")
print("So phong:", len(df))

print("\nKET QUA RANDOM FOREST:")
print("MAE: {:,.0f} VND".format(mae))
print("RMSE: {:,.0f} VND".format(rmse))
print("R2: {:.4f}".format(r2))

print("\nCHI TIET:")
print(result.round(2).to_string(index=False))

print("\nDa luu:")
print("1. danh_gia_random_forest_buoc86.csv")
print("2. chi_so_random_forest_buoc86.csv")

print("\nLUU Y: Chi co 7 mau, ket qua mang tinh thu nghiem.")
