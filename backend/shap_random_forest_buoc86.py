from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import shap

from sklearn.ensemble import RandomForestRegressor

DATA = Path("D:/baicuoiki/data")

df = pd.read_csv(
    DATA / "rooms_clean_normalized.csv",
    encoding="utf-8-sig"
)

df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["area"] = pd.to_numeric(df["area"], errors="coerce")

df = df.dropna(
    subset=["id", "price", "area", "district"]
).copy()

df = df[
    (df["price"] > 0) &
    (df["area"] > 0)
].copy()

df = df.sort_values("id").reset_index(drop=True)

if len(df) < 3:
    raise ValueError("Can it nhat 3 phong de phan tich.")

X = pd.get_dummies(
    df[["area", "district"]],
    columns=["district"],
    dtype=float
)

y = df["price"]

model = RandomForestRegressor(
    n_estimators=200,
    max_depth=4,
    min_samples_leaf=1,
    random_state=42,
    n_jobs=-1
)

model.fit(X, y)

explainer = shap.TreeExplainer(model)
shap_values = explainer(X)

values = np.asarray(shap_values.values)

if values.ndim != 2:
    raise ValueError(
        "SHAP values khong dung dinh dang mong doi."
    )

# Tong hop muc do anh huong trung binh
importance = pd.DataFrame({
    "feature": X.columns,
    "mean_abs_shap": np.abs(values).mean(axis=0)
})

importance = importance.sort_values(
    "mean_abs_shap",
    ascending=False
)

importance.to_csv(
    DATA / "shap_feature_importance_buoc86.csv",
    index=False,
    encoding="utf-8-sig"
)

# Bieu do 1: SHAP Summary Bar
plt.figure()

shap.summary_plot(
    values,
    X,
    plot_type="bar",
    show=False
)

plt.title("SHAP - Muc do anh huong cua dac trung")
plt.tight_layout()

plt.savefig(
    DATA / "shap_summary_bar_buoc86.png",
    dpi=160,
    bbox_inches="tight"
)

plt.close("all")

# Bieu do 2: SHAP Beeswarm
shap.summary_plot(
    values,
    X,
    show=False
)

plt.title("SHAP - Phan bo tac dong cua dac trung")
plt.tight_layout()

plt.savefig(
    DATA / "shap_beeswarm_buoc86.png",
    dpi=160,
    bbox_inches="tight"
)

plt.close("all")

print("HOAN THANH BUOC 86.19")
print("So phong:", len(df))
print("So dac trung:", X.shape[1])

print("\nMUC DO DONG GOP CUA CAC DAC TRUNG:")
print(importance.to_string(index=False))

print("\nDA TAO:")
print("1. shap_feature_importance_buoc86.csv")
print("2. shap_summary_bar_buoc86.png")
print("3. shap_beeswarm_buoc86.png")

print("\nLUU Y:")
print("SHAP chi giai thich mo hinh tren 7 mau.")
print("Khong suy ra quan he nhan qua.")
