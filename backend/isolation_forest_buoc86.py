from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

DATA = Path("D:/baicuoiki/data")

df = pd.read_csv(
    DATA / "rooms_clean_normalized.csv",
    encoding="utf-8-sig"
)

df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["area"] = pd.to_numeric(df["area"], errors="coerce")

df = df.dropna(subset=["price", "area"]).copy()
df = df[(df["price"] > 0) & (df["area"] > 0)].copy()

df["price_per_m2"] = df["price"] / df["area"]

# Dung gia, dien tich va don gia/m2
features = ["price", "area", "price_per_m2"]

X = df[features].to_numpy(dtype=float)
X_scaled = StandardScaler().fit_transform(X)

model = IsolationForest(
    n_estimators=200,
    contamination=0.2,
    random_state=42
)

df["isolation_prediction"] = model.fit_predict(X_scaled)
df["anomaly_score"] = model.decision_function(X_scaled)

df["is_anomaly"] = df["isolation_prediction"] == -1

output = DATA / "isolation_forest_buoc86.csv"

df.to_csv(
    output,
    index=False,
    encoding="utf-8-sig"
)

print("HOAN THANH BUOC 86.15")
print("Tong so phong:", len(df))
print("So phong bi danh dau:", int(df["is_anomaly"].sum()))

print("\nKET QUA:")
print(
    df[
        ["id", "price", "area", "price_per_m2",
         "anomaly_score", "is_anomaly"]
    ].sort_values("anomaly_score").to_string(index=False)
)

print("\nDa luu:", output)
print("LUU Y: Ket qua chi mang tinh thu nghiem voi 7 mau.")
