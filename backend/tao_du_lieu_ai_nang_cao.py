from pathlib import Path
import subprocess
import io
import pandas as pd

ROOT = Path("D:/baicuoiki")
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

query = """
COPY (
    SELECT
        r.id,
        r.title,
        r.address,
        r.district,
        r.price,
        r.area,
        r.latitude,
        r.longitude,
        r.created_at,
        CASE
            WHEN b.room_id IS NOT NULL THEN TRUE
            ELSE FALSE
        END AS is_generated
    FROM rooms r
    LEFT JOIN room_seed_batches b
        ON b.room_id = r.id
        AND b.batch_code = 'HN_UNIVERSITY_20_20261122'
    WHERE r.status = 'da_duyet'
      AND r.latitude IS NOT NULL
      AND r.longitude IS NOT NULL
      AND r.price > 0
      AND r.area > 0
    ORDER BY r.id
) TO STDOUT WITH CSV HEADER
"""

result = subprocess.run(
    [
        "docker", "exec", "-i",
        "postgres_db",
        "psql",
        "-X",
        "-q",
        "-v", "ON_ERROR_STOP=1",
        "-U", "postgres",
        "-d", "tronhanh123",
        "-c", query
    ],
    capture_output=True
)

if result.returncode != 0:
    print(result.stderr.decode("utf-8", errors="replace"))
    raise SystemExit("Khong the doc PostgreSQL")

df = pd.read_csv(
    io.BytesIO(result.stdout),
    encoding="utf-8"
)

for col in ["price", "area", "latitude", "longitude"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(
    subset=["price", "area", "latitude", "longitude"]
)

df = df[
    (df["price"] > 0) &
    (df["area"] > 0)
].copy()

df["price_per_m2"] = df["price"] / df["area"]

# Danh dau du lieu tu tao, khong dung de danh gia thuc te
df["is_generated"] = (
    df["is_generated"]
    .astype(str)
    .str.lower()
    .isin(["true", "t", "1"])
)

output = DATA / "rooms_ai_advanced.csv"

df.to_csv(
    output,
    index=False,
    encoding="utf-8-sig"
)

print("===== DU LIEU AI NANG CAO =====")
print("Tong so phong:", len(df))
print("Phong tu tao:", int(df["is_generated"].sum()))
print("Phong con lai:", int((~df["is_generated"]).sum()))
print("So cot:", len(df.columns))
print("File:", output)

print("\n===== CAC COT =====")
print(df.columns.tolist())

print("\n===== 5 PHONG DAU =====")
print(
    df[
        ["id", "district", "price", "area",
         "price_per_m2", "is_generated"]
    ].head().to_string(index=False)
)
