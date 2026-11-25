from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor, StackingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA = Path("D:/baicuoiki/data")

df = pd.read_csv(
    DATA / "rooms_clean_normalized.csv",
    encoding="utf-8-sig"
)

df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["area"] = pd.to_numeric(df["area"], errors="coerce")

df = df.dropna(subset=["id", "price", "area", "district"])
df = df[(df["price"] > 0) & (df["area"] > 0)]
df = df.sort_values("id").reset_index(drop=True)

if len(df) < 5:
    raise ValueError("Can it nhat 5 phong de chay thu nghiem.")

X = df[["area", "district"]]
y = df["price"].to_numpy(dtype=float)

def make_preprocessor():
    return ColumnTransformer(
        transformers=[
            ("area", StandardScaler(), ["area"]),
            (
                "district",
                OneHotEncoder(handle_unknown="ignore"),
                ["district"]
            )
        ]
    )

def make_knn():
    return Pipeline([
        ("preprocess", make_preprocessor()),
        ("model", KNeighborsRegressor(n_neighbors=3))
    ])

def make_rf():
    return Pipeline([
        ("preprocess", make_preprocessor()),
        ("model", RandomForestRegressor(
            n_estimators=100,
            max_depth=4,
            random_state=42,
            n_jobs=-1
        ))
    ])

def make_stacking():
    return StackingRegressor(
        estimators=[
            ("knn", make_knn()),
            ("rf", make_rf())
        ],
        final_estimator=Ridge(alpha=10.0),
        cv=3,
        n_jobs=1
    )

predictions = []

for train_idx, test_idx in LeaveOneOut().split(X):
    model = make_stacking()

    model.fit(
        X.iloc[train_idx],
        y[train_idx]
    )

    predicted = float(
        model.predict(X.iloc[test_idx])[0]
    )

    i = int(test_idx[0])

    predictions.append({
        "id": int(df.iloc[i]["id"]),
        "actual": float(y[i]),
        "predicted": predicted,
        "absolute_error": abs(float(y[i]) - predicted)
    })

result = pd.DataFrame(predictions)

mae = mean_absolute_error(result["actual"], result["predicted"])
rmse = np.sqrt(
    mean_squared_error(result["actual"], result["predicted"])
)
r2 = r2_score(result["actual"], result["predicted"])

result.to_csv(
    DATA / "danh_gia_stacking_buoc86.csv",
    index=False,
    encoding="utf-8-sig"
)

summary = pd.DataFrame([{
    "model": "Stacking_Ensemble",
    "MAE": mae,
    "RMSE": rmse,
    "R2": r2
}])

summary.to_csv(
    DATA / "chi_so_stacking_buoc86.csv",
    index=False,
    encoding="utf-8-sig"
)

print("HOAN THANH BUOC 86.20")
print("Phuong phap: Nested Stacking + LOOCV")
print("So phong:", len(df))

print("\nKET QUA:")
print("MAE: {:,.0f} VND".format(mae))
print("RMSE: {:,.0f} VND".format(rmse))
print("R2: {:.4f}".format(r2))

print("\nCHI TIET:")
print(result.round(2).to_string(index=False))

print("\nDA TAO:")
print("1. danh_gia_stacking_buoc86.csv")
print("2. chi_so_stacking_buoc86.csv")

print("\nLUU Y:")
print("Ket qua chi minh hoa ky thuat voi 7 phong.")
print("Khong su dung de ket luan mo hinh tot nhat.")
