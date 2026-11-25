from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

DATA = Path("D:/baicuoiki/data")

comparison = pd.read_csv(
    DATA / "so_sanh_mo_hinh_buoc86.csv",
    encoding="utf-8-sig"
)

rf = pd.read_csv(
    DATA / "chi_so_random_forest_buoc86.csv",
    encoding="utf-8-sig"
)

result = pd.concat(
    [comparison, rf],
    ignore_index=True
)

result = result[["model", "MAE", "RMSE", "R2"]]

output = DATA / "so_sanh_3_mo_hinh_buoc86.csv"
result.to_csv(output, index=False, encoding="utf-8-sig")

print("HOAN THANH BUOC 86.18")
print(result.to_string(index=False))

# Bieu do so sanh MAE va RMSE
chart_data = result.set_index("model")[["MAE", "RMSE"]] / 1_000_000

ax = chart_data.plot(
    kind="bar",
    figsize=(10, 6),
    rot=0
)

ax.set_title("So sanh sai so cac mo hinh du doan gia thue")
ax.set_xlabel("Mo hinh")
ax.set_ylabel("Sai so (trieu VND)")
ax.grid(axis="y", alpha=0.25)

plt.tight_layout()

chart = DATA / "so_sanh_3_mo_hinh_buoc86.png"
plt.savefig(chart, dpi=160)
plt.close()

print("\nDa luu:")
print("1. so_sanh_3_mo_hinh_buoc86.csv")
print("2. so_sanh_3_mo_hinh_buoc86.png")
