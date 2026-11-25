from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler

ROOT = Path("D:/baicuoiki")
DATA = ROOT / "data"

df = pd.read_csv(
    DATA / "rooms_ai_gis_advanced.csv",
    encoding="utf-8-sig"
)

features = [
    "price_per_m2",
    "area",
    "nearest_university_m",
    "universities_1km",
    "hospitals_1km",
    "bus_stops_1km",
    "parks_1km",
    "schools_1km"
]

for col in features + ["price"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(
    subset=["price", "area", "price_per_m2"]
).copy()

df = df[
    (df["price"] > 0) &
    (df["area"] > 0)
].copy()

df["is_generated"] = (
    df["is_generated"]
    .astype(str)
    .str.lower()
    .isin(["true", "t", "1"])
)

X = SimpleImputer(
    strategy="median"
).fit_transform(df[features])

X = RobustScaler().fit_transform(X)

model = IsolationForest(
    n_estimators=200,
    contamination=0.10,
    random_state=42,
    n_jobs=-1
)

df["anomaly_prediction"] = model.fit_predict(X)
df["anomaly_score"] = model.decision_function(X)

df["is_anomaly"] = (
    df["anomaly_prediction"] == -1
)

# Canh bao gia thap theo trung vi toan bo du lieu
median_price_m2 = df["price_per_m2"].median()

df["low_price_warning"] = (
    df["price_per_m2"] < median_price_m2 * 0.5
)

# Chi gan nhan can kiem tra, khong ket luan lua dao
df["needs_review"] = (
    df["is_anomaly"] |
    df["low_price_warning"]
)

output = DATA / "isolation_forest_gis_nang_cao.csv"

df.to_csv(
    output,
    index=False,
    encoding="utf-8-sig"
)

print("===== ISOLATION FOREST GIS =====")
print("Tong so phong:", len(df))
print("Phong bat thuong:", int(df["is_anomaly"].sum()))
print("Canh bao gia thap:", int(df["low_price_warning"].sum()))
print("Can kiem tra:", int(df["needs_review"].sum()))

print("\n===== DANH SACH CAN KIEM TRA =====")

cols = [
    "id",
    "title",
    "district",
    "price",
    "area",
    "price_per_m2",
    "anomaly_score",
    "is_generated",
    "needs_review"
]

print(
    df[df["needs_review"]][cols]
    .sort_values("anomaly_score")
    .to_string(index=False)
)

print("\nDA LUU:")
print(output)

print("\nLUU Y:")
print("Bat thuong khong dong nghia voi lua dao.")
print("Du lieu tu tao chi dung kiem thu thuat toan.")
