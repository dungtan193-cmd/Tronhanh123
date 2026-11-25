from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.ensemble import StackingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor

ROOT = Path("D:/baicuoiki")
DATA = ROOT / "data"

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

df["district"] = df["district"].fillna("Khac").astype(str).str.strip().str.lower()

X = df[features_num + features_cat]
y = df["price"].to_numpy(dtype=float)

if len(df) < 15:
    raise ValueError("Can it nhat 15 phong de thu nghiem Stacking.")

def make_preprocessor():
    return ColumnTransformer([
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
            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            features_cat
        )
    ])

def make_stacking():
    return Pipeline([
        ("preprocess", make_preprocessor()),
        ("model", StackingRegressor(
            estimators=[
                (
                    "xgboost",
                    XGBRegressor(
                        n_estimators=80,
                        max_depth=2,
                        learning_rate=0.05,
                        subsample=0.9,
                        colsample_bytree=0.9,
                        objective="reg:squarederror",
                        random_state=42,
                        n_jobs=1
                    )
                ),
                (
                    "lightgbm",
                    LGBMRegressor(
                        n_estimators=80,
                        max_depth=2,
                        num_leaves=4,
                        min_child_samples=3,
                        learning_rate=0.05,
                        verbosity=-1,
                        random_state=42,
                        n_jobs=1
                    )
                ),
                (
                    "catboost",
                    CatBoostRegressor(
                        iterations=80,
                        depth=2,
                        learning_rate=0.05,
                        loss_function="RMSE",
                        verbose=False,
                        random_seed=42,
                        thread_count=1
                    )
                )
            ],
            final_estimator=Ridge(alpha=10.0),
            cv=3,
            n_jobs=1
        ))
    ])

cv = KFold(n_splits=3, shuffle=True, random_state=42)

print("===== STACKING ENSEMBLE NANG CAO =====")
print("So phong:", len(df))
print("So dac trung:", len(X.columns))
print("Dang danh gia 3-fold CV...")

pred = cross_val_predict(
    make_stacking(),
    X,
    y,
    cv=cv,
    n_jobs=1
)

mae = mean_absolute_error(y, pred)
rmse = np.sqrt(mean_squared_error(y, pred))
r2 = r2_score(y, pred)

pd.DataFrame({
    "id": df["id"].to_numpy(),
    "actual": y,
    "predicted": pred,
    "absolute_error": np.abs(y - pred)
}).to_csv(
    DATA / "danh_gia_stacking_nang_cao.csv",
    index=False,
    encoding="utf-8-sig"
)

pd.DataFrame([{
    "model": "Stacking_XGBoost_LightGBM_CatBoost",
    "n_samples": len(df),
    "MAE": mae,
    "RMSE": rmse,
    "R2": r2,
    "evaluation": "3-fold CV - technical demo"
}]).to_csv(
    DATA / "chi_so_stacking_nang_cao.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n===== KET QUA =====")
print(f"MAE: {mae:,.0f} VND")
print(f"RMSE: {rmse:,.0f} VND")
print(f"R2: {r2:.4f}")

print("\nDa luu:")
print("data/danh_gia_stacking_nang_cao.csv")
print("data/chi_so_stacking_nang_cao.csv")
