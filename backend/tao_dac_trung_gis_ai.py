from pathlib import Path
import subprocess
import io
import pandas as pd

ROOT = Path("D:/baicuoiki")
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)

query = r"""
COPY (
    WITH room_points AS (
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
            (b.room_id IS NOT NULL) AS is_generated,
            ST_SetSRID(
                ST_MakePoint(r.longitude, r.latitude),
                4326
            )::geography AS room_geog
        FROM rooms r
        LEFT JOIN room_seed_batches b
            ON b.room_id = r.id
            AND b.batch_code = 'HN_UNIVERSITY_20_20261122'
        WHERE r.status = 'da_duyet'
          AND r.latitude BETWEEN -90 AND 90
          AND r.longitude BETWEEN -180 AND 180
          AND r.price > 0
          AND r.area > 0
    )
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
        r.is_generated,
        ROUND((r.price / r.area)::numeric, 2) AS price_per_m2,
        ROUND(u.distance_m::numeric, 2) AS nearest_university_m,
        COALESCE(p.universities_1km, 0) AS universities_1km,
        COALESCE(p.hospitals_1km, 0) AS hospitals_1km,
        COALESCE(p.bus_stops_1km, 0) AS bus_stops_1km,
        COALESCE(p.parks_1km, 0) AS parks_1km,
        COALESCE(p.schools_1km, 0) AS schools_1km,
        COALESCE(p.total_pois_1km, 0) AS total_pois_1km
    FROM room_points r
    LEFT JOIN LATERAL (
        SELECT
            ST_Distance(
                r.room_geog,
                o.geom::geography
            ) AS distance_m
        FROM osm_pois o
        WHERE o.category = 'university'
        ORDER BY r.room_geog <-> o.geom::geography
        LIMIT 1
    ) u ON TRUE
    LEFT JOIN LATERAL (
        SELECT
            COUNT(*) FILTER (
                WHERE o.category = 'university'
            ) AS universities_1km,
            COUNT(*) FILTER (
                WHERE o.category = 'hospital'
            ) AS hospitals_1km,
            COUNT(*) FILTER (
                WHERE o.category = 'bus_stop'
            ) AS bus_stops_1km,
            COUNT(*) FILTER (
                WHERE o.category = 'park'
            ) AS parks_1km,
            COUNT(*) FILTER (
                WHERE o.category = 'school'
            ) AS schools_1km,
            COUNT(*) AS total_pois_1km
        FROM osm_pois o
        WHERE ST_DWithin(
            r.room_geog,
            o.geom::geography,
            1000
        )
    ) p ON TRUE
    ORDER BY r.id
) TO STDOUT WITH CSV HEADER
"""

result = subprocess.run(
    [
        "docker", "exec", "-i",
        "postgres_db",
        "psql",
        "-X", "-q",
        "-v", "ON_ERROR_STOP=1",
        "-U", "postgres",
        "-d", "tronhanh123",
        "-c", query
    ],
    capture_output=True
)

if result.returncode != 0:
    print(result.stderr.decode("utf-8", errors="replace"))
    raise SystemExit("LOI TRUY VAN POSTGIS")

df = pd.read_csv(
    io.BytesIO(result.stdout),
    encoding="utf-8"
)

numeric_cols = [
    "price", "area", "latitude", "longitude",
    "price_per_m2", "nearest_university_m",
    "universities_1km", "hospitals_1km",
    "bus_stops_1km", "parks_1km",
    "schools_1km", "total_pois_1km"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["is_generated"] = (
    df["is_generated"]
    .astype(str)
    .str.lower()
    .isin(["true", "t", "1"])
)

output = DATA / "rooms_ai_gis_advanced.csv"

df.to_csv(
    output,
    index=False,
    encoding="utf-8-sig"
)

print("\n===== HOAN THANH BUOC 94.8 =====")
print("Tong so phong:", len(df))
print("Phong tu tao:", int(df["is_generated"].sum()))
print("Phong con lai:", int((~df["is_generated"]).sum()))
print("So POI trong database: 2054")
print("File:", output)

print("\n===== DU LIEU GIS =====")
print(
    df[
        [
            "id",
            "district",
            "nearest_university_m",
            "universities_1km",
            "hospitals_1km",
            "bus_stops_1km",
            "parks_1km",
            "schools_1km"
        ]
    ].head(10).to_string(index=False)
)

print("\n===== GIA TRI THIEU =====")
print(df[numeric_cols].isna().sum().to_string())
