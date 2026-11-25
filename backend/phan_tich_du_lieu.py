from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

input_file = DATA_DIR / "rooms_raw.csv"
output_file = DATA_DIR / "rooms_clean.csv"

if not input_file.exists():
    raise FileNotFoundError(f"Khong tim thay: {input_file}")

df = pd.read_csv(input_file, encoding="utf-8-sig")

print("So dong ban dau:", len(df))

for col in ["price", "area", "latitude", "longitude"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["district"] = df["district"].fillna("Khong xac dinh").str.strip()

df = df.drop_duplicates(subset=["id"])
df = df.dropna(subset=["price", "area"])
df = df[
    df["area"].between(5, 300)
    & df["price"].between(100000, 100000000)
].copy()

df["price_per_m2"] = df["price"] / df["area"]

df.to_csv(output_file, index=False, encoding="utf-8-sig")

print("So dong sau lam sach:", len(df))
print("Gia trung binh:", round(df["price"].mean()))
print("Dien tich trung binh:", round(df["area"].mean(), 2))

plt.figure(figsize=(8, 5))
plt.hist(df["price"] / 1_000_000, bins=min(5, len(df)), edgecolor="black")
plt.title("Phan bo gia thue phong tro")
plt.xlabel("Gia thue (trieu VND)")
plt.ylabel("So phong")
plt.tight_layout()
plt.savefig(DATA_DIR / "bieu_do_gia_thue.png", dpi=150)
plt.close()

print("DA HOAN THANH!")
print("File du lieu:", output_file)
print("Bieu do:", DATA_DIR / "bieu_do_gia_thue.png")
