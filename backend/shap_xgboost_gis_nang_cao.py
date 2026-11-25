from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

ROOT = Path("D:/baicuoiki")
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(
    DATA / "rooms_ai_gis_advanced.csv",
    encoding="utf-8-sig"
)

features_num = [
    "area",
    "latitude",
    "longitude",
    "nearest_university_m",
    "universities_1km",
    "hospitals_1km",
    "bus_stops_1km",
    "parks_1km",
    "schools_1km",
    "total_pois_1km"
]

features_cat = ["district"]

for col in features_num + ["price"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["price", "area"])
df = df[(df["price"] > 0) & (df["area"] > 0)].copy()

df["district"] = (
    df["district"]
    .fillna("Khac")
    .astype(str)
    .str.strip()
    .str.lower()
)

X = df[features_num + features_cat]
y = df["price"].to_numpy(dtype=float)

preprocessor = ColumnTransformer([
    (
        "numeric",
        Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ]),
        features_num
    ),
    (
        "categorical",
        OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False
        ),
        features_cat
    )
])

X_processed = preprocessor.fit_transform(X)
feature_names = preprocessor.get_feature_names_out()

model = XGBRegressor(
    n_estimators=80,
    max_depth=2,
    learning_rate=0.05,
    subsample=0.9,
    colsample_bytree=0.9,
    objective="reg:squarederror",
    random_state=42,
    n_jobs=1
)

model.fit(X_processed, y)

print("===== SHAP XGBOOST =====")
print("So phong:", len(df))
print("So dac trung sau ma hoa:", len(feature_names))

explainer = shap.TreeExplainer(model)
shap_values = explainer(X_processed)

values = np.asarray(shap_values.values)

importance = pd.DataFrame({
    "feature": feature_names,
    "mean_abs_shap": np.abs(values).mean(axis=0)
}).sort_values("mean_abs_shap", ascending=False)

importance.to_csv(
    DATA / "shap_xgboost_gis_importance.csv",
    index=False,
    encoding="utf-8-sig"
)

plt.figure()
shap.summary_plot(
    values,
    X_processed,
    feature_names=feature_names,
    plot_type="bar",
    show=False
)
plt.tight_layout()
plt.savefig(
    DATA / "shap_xgboost_gis_bar.png",
    dpi=180,
    bbox_inches="tight"
)
plt.close("all")

plt.figure()
shap.summary_plot(
    values,
    X_processed,
    feature_names=feature_names,
    show=False
)
plt.tight_layout()
plt.savefig(
    DATA / "shap_xgboost_gis_beeswarm.png",
    dpi=180,
    bbox_inches="tight"
)
plt.close("all")

print("\n===== TOP 10 DAC TRUNG =====")
print(importance.head(10).to_string(index=False))

print("\nDA TAO:")
print("data/shap_xgboost_gis_importance.csv")
print("data/shap_xgboost_gis_bar.png")
print("data/shap_xgboost_gis_beeswarm.png")

print("\nLUU Y:")
print("SHAP nay giai thich XGBoost, khong phai toan bo Stacking.")
print("Du lieu co 20 phong tu tao, chi phuc vu kiem thu ky thuat.")
