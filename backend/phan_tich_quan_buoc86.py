from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

df = pd.read_csv(DATA / "rooms_clean_normalized.csv", encoding="utf-8-sig")
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["district"] = df["district"].fillna("Khong xac dinh").astype(str).str.strip()
df.loc[df["district"] == "", "district"] = "Khong xac dinh"
df = df.dropna(subset=["price"])

if df.empty:
    raise ValueError("Khong co du lieu de phan tich")

summary = (
    df.groupby("district", as_index=False)
    .agg(
        so_phong=("price", "size"),
        gia_trung_binh=("price", "mean"),
        gia_thap_nhat=("price", "min"),
        gia_cao_nhat=("price", "max")
    )
    .sort_values("so_phong", ascending=False)
)

summary.to_csv(
    DATA / "thong_ke_theo_quan.csv",
    index=False,
    encoding="utf-8-sig"
)

print("THONG KE THEO QUAN/HUYEN:")
print(summary.to_string(index=False))

# Bieu do gia trung binh theo quan
plt.figure(figsize=(10, 6))
plt.barh(
    summary["district"],
    summary["gia_trung_binh"] / 1_000_000
)
plt.xlabel("Gia thue trung binh (trieu VND)")
plt.ylabel("Quan / huyen")
plt.title("Gia thue trung binh theo khu vuc")
plt.tight_layout()
plt.savefig(DATA / "gia_trung_binh_theo_quan.png", dpi=150)
plt.close()

# Treemap: dien tich moi o ty le voi so phong
try:
    import squarify
except ImportError:
    raise SystemExit(
        "Thieu squarify. Chay: python -m pip install squarify"
    )

plt.figure(figsize=(11, 7))
labels = [
    f"{row.district}\n{row.so_phong} phong"
    for row in summary.itertuples()
]

squarify.plot(
    sizes=summary["so_phong"].tolist(),
    label=labels,
    alpha=0.8,
    pad=True,
    text_kwargs={"fontsize": 10}
)
plt.axis("off")
plt.title("Treemap - So luong phong theo quan/huyen")
plt.tight_layout()
plt.savefig(DATA / "treemap_phong_theo_quan.png", dpi=150)
plt.close()

print("\nHOAN THANH BUOC 86.7")
print("1. thong_ke_theo_quan.csv")
print("2. gia_trung_binh_theo_quan.png")
print("3. treemap_phong_theo_quan.png")

