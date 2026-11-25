from pathlib import Path
import pandas as pd
import numpy as np

DATA = Path("D:/baicuoiki/data")
df = pd.read_csv(DATA / "rooms_clean_normalized.csv", encoding="utf-8-sig")

df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["area"] = pd.to_numeric(df["area"], errors="coerce")

df = df.dropna(subset=["price", "area"])
df = df[(df["price"] > 0) & (df["area"] > 0)].copy()

df["price_per_m2"] = df["price"] / df["area"]

q1 = df["price_per_m2"].quantile(0.25)
q3 = df["price_per_m2"].quantile(0.75)
iqr = q3 - q1

lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr

df["is_outlier_iqr"] = (
    (df["price_per_m2"] < lower) |
    (df["price_per_m2"] > upper)
)

output = DATA / "bao_cao_bat_thuong_buoc86.csv"
df.to_csv(output, index=False, encoding="utf-8-sig")

print("HOAN THANH BUOC 86.11")
print("Tong so phong:", len(df))
print("So phong bi danh dau:", int(df["is_outlier_iqr"].sum()))

print("\nCAC PHONG CAN KIEM TRA:")
cols = ["id", "title", "price", "area", "price_per_m2"]

print(
    df.loc[df["is_outlier_iqr"], cols].to_string(index=False)
)

print("\nDa luu:", output)
