from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

DATA = Path("D:/baicuoiki/data")

iqr = pd.read_csv(
    DATA / "bao_cao_bat_thuong_buoc86.csv",
    encoding="utf-8-sig"
)

iso = pd.read_csv(
    DATA / "isolation_forest_buoc86.csv",
    encoding="utf-8-sig"
)

result = iqr[
    ["id", "price", "area", "price_per_m2", "is_outlier_iqr"]
].merge(
    iso[["id", "anomaly_score", "is_anomaly"]],
    on="id",
    how="inner",
    validate="one_to_one"
)

result["dong_thuan"] = (
    result["is_outlier_iqr"] == result["is_anomaly"]
)

result = result.sort_values("id")

output = DATA / "so_sanh_iqr_isolation_forest.csv"
result.to_csv(output, index=False, encoding="utf-8-sig")

print("HOAN THANH BUOC 86.16")
print("Tong so phong:", len(result))
print("IQR danh dau:", int(result["is_outlier_iqr"].sum()))
print("Isolation Forest danh dau:", int(result["is_anomaly"].sum()))
print("So phong hai phuong phap dong thuan:", int(result["dong_thuan"].sum()))

print("\nCHI TIET:")
print(
    result[
        ["id", "price", "is_outlier_iqr", "is_anomaly", "dong_thuan"]
    ].to_string(index=False)
)

colors = [
    "tomato" if value else "steelblue"
    for value in result["is_anomaly"]
]

plt.figure(figsize=(9, 5))
plt.bar(
    result["id"].astype(str),
    result["price_per_m2"],
    color=colors
)

plt.xlabel("ID phong")
plt.ylabel("Gia thue / m2 (VND)")
plt.title("Phat hien bat thuong bang IQR va Isolation Forest")
plt.grid(axis="y", alpha=0.25)

plt.tight_layout()

chart = DATA / "so_sanh_bat_thuong_buoc86.png"
plt.savefig(chart, dpi=160)
plt.close()

print("\nDa luu:", output)
print("Bieu do:", chart)
