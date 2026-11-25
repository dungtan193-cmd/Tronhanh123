from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

INPUT = Path("reports/gis/room_gis_analysis.csv")
OUTPUT = Path("reports/gis/charts")
OUTPUT.mkdir(parents=True, exist_ok=True)

if not INPUT.exists():
    raise FileNotFoundError(f"Khong tim thay: {INPUT}")

df = pd.read_csv(INPUT)

required = [
    "room_id",
    "price",
    "area",
    "nearest_university_m",
    "total_amenities_1km",
]

missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Thieu cot: {missing}")

for col in required:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=required).copy()

if df.empty:
    raise ValueError("Khong co du lieu hop le de ve bieu do")

df = df.sort_values("room_id")
labels = ["Room " + str(int(x)) for x in df["room_id"]]

# 1. Bieu do gia thue
plt.figure(figsize=(10, 5))
plt.bar(labels, df["price"] / 1_000_000)
plt.title("Rental prices by room")
plt.xlabel("Room ID")
plt.ylabel("Price (million VND/month)")
plt.tight_layout()
plt.savefig(OUTPUT / "01_rental_prices.png", dpi=180)
plt.close()

# 2. Khoang cach den dai hoc
plt.figure(figsize=(10, 5))
plt.bar(labels, df["nearest_university_m"])
plt.title("Distance to nearest university")
plt.xlabel("Room ID")
plt.ylabel("Distance (meters)")
plt.tight_layout()
plt.savefig(OUTPUT / "02_university_distance.png", dpi=180)
plt.close()

# 3. So tien ich trong 1km
plt.figure(figsize=(10, 5))
plt.bar(labels, df["total_amenities_1km"])
plt.title("Nearby amenities within 1 km")
plt.xlabel("Room ID")
plt.ylabel("Amenity count")
plt.tight_layout()
plt.savefig(OUTPUT / "03_amenities.png", dpi=180)
plt.close()

# 4. Moi quan he khoang cach va gia thue
plt.figure(figsize=(9, 6))

normal = df[df["price"] >= 1_000_000]
review = df[df["price"] < 1_000_000]

plt.scatter(
    normal["nearest_university_m"],
    normal["price"] / 1_000_000,
    label="Other rooms",
    s=75,
)

if not review.empty:
    plt.scatter(
        review["nearest_university_m"],
        review["price"] / 1_000_000,
        label="Price needs review",
        marker="x",
        s=110,
    )

for _, row in df.iterrows():
    plt.annotate(
        str(int(row["room_id"])),
        (
            row["nearest_university_m"],
            row["price"] / 1_000_000,
        ),
        xytext=(5, 5),
        textcoords="offset points",
    )

plt.title("University distance vs rental price")
plt.xlabel("Distance (meters)")
plt.ylabel("Price (million VND/month)")
plt.legend()
plt.tight_layout()
plt.savefig(OUTPUT / "04_distance_vs_price.png", dpi=180)
plt.close()

print("\n=== BUOC 93.14 HOAN THANH ===")
print("So phong:", len(df))
print("Da tao 4 bieu do:")
for file in sorted(OUTPUT.glob("*.png")):
    print(" -", file)

print("\nLuu y: 7 phong chi phu hop phan tich mo ta.")
print("Khong su dung de ket luan quan he nhan qua.")
