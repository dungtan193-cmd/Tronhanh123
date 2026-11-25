import requests
import pandas as pd
from pathlib import Path

API = "http://localhost:8000/api/ai/gis/features"
OUTPUT = Path("reports/gis")
OUTPUT.mkdir(parents=True, exist_ok=True)

response = requests.get(API, timeout=60)
response.raise_for_status()

data = response.json()
df = pd.DataFrame(data.get("rooms", []))

if df.empty:
    raise RuntimeError("API GIS khong co du lieu")

columns = [
    "room_id",
    "district",
    "area",
    "price",
    "nearest_university_m",
    "bus_stops_1km",
    "schools_1km",
    "hospitals_1km",
    "parks_1km",
]

missing = [c for c in columns if c not in df.columns]
if missing:
    raise RuntimeError("Thieu cot: " + ", ".join(missing))

df = df[columns].copy()

df["price_per_m2"] = (
    df["price"].astype(float)
    / df["area"].astype(float)
)

df["total_amenities_1km"] = (
    df["bus_stops_1km"]
    + df["schools_1km"]
    + df["hospitals_1km"]
    + df["parks_1km"]
)

df["price_needs_review"] = df["price"] < 1000000

output_file = OUTPUT / "room_gis_analysis.csv"
df.to_csv(output_file, index=False, encoding="utf-8-sig")

print("\n=== PHAN TICH GIS ===")
print("So phong:", len(df))
print("Gia trung binh:", round(df["price"].mean()))
print(
    "Khoang cach DH trung binh:",
    round(df["nearest_university_m"].mean(), 1),
    "m"
)
print(
    "Tien ich trung binh trong 1km:",
    round(df["total_amenities_1km"].mean(), 1)
)

print("\n=== PHONG CAN KIEM TRA GIA ===")
print(
    df.loc[
        df["price_needs_review"],
        ["room_id", "price", "area"]
    ].to_string(index=False)
)

print("\nDa xuat:", output_file)
