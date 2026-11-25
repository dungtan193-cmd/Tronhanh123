from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
df = pd.read_csv(DATA / "rooms_clean.csv", encoding="utf-8-sig")

df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["area"] = pd.to_numeric(df["area"], errors="coerce")
df["price_per_m2"] = df["price"] / df["area"]
df = df.dropna(subset=["price", "area", "price_per_m2"])

if df.empty:
    raise ValueError("Khong co du lieu hop le")

# 1. BOXPLOT
plt.figure(figsize=(8, 5))
plt.boxplot(df["price"] / 1_000_000)
plt.title("Boxplot - Gia thue phong tro")
plt.ylabel("Gia thue (trieu VND)")
plt.tight_layout()
plt.savefig(DATA / "boxplot_gia_thue.png", dpi=150)
plt.close()

# 2. VIOLIN PLOT
plt.figure(figsize=(8, 5))
plt.violinplot(df["price"] / 1_000_000, showmeans=True, showmedians=True)
plt.title("Violin Plot - Gia thue phong tro")
plt.ylabel("Gia thue (trieu VND)")
plt.tight_layout()
plt.savefig(DATA / "violin_gia_thue.png", dpi=150)
plt.close()

# 3. HEATMAP TUONG QUAN
columns = ["price", "area", "price_per_m2"]
corr = df[columns].corr()

fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)

ax.set_xticks(range(len(columns)))
ax.set_yticks(range(len(columns)))
ax.set_xticklabels(columns)
ax.set_yticklabels(columns)

for i in range(len(columns)):
    for j in range(len(columns)):
        value = corr.iloc[i, j]
        label = f"{value:.2f}" if pd.notna(value) else "N/A"
        ax.text(j, i, label, ha="center", va="center")

fig.colorbar(im, ax=ax)
ax.set_title("Heatmap - Tuong quan du lieu")
plt.tight_layout()
plt.savefig(DATA / "heatmap_tuong_quan.png", dpi=150)
plt.close()

print("HOAN THANH BUOC 86.6")
print("1. boxplot_gia_thue.png")
print("2. violin_gia_thue.png")
print("3. heatmap_tuong_quan.png")
