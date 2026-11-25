import os
import time
import requests
import psycopg2
from psycopg2.extras import Json

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
]

def get_osm_data(latitude, longitude, radius):
    query = f"""
    [out:json][timeout:45];
    (
      nwr(around:{radius},{latitude},{longitude})["highway"="bus_stop"];
      nwr(around:{radius},{latitude},{longitude})["amenity"~"^(school|university|hospital)$"];
      nwr(around:{radius},{latitude},{longitude})["leisure"="park"];
    );
    out center;
    """

    errors = []

    for server in OVERPASS_SERVERS:
        try:
            print("Dang thu:", server)

            response = requests.post(
                server,
                data={"data": query},
                timeout=75,
                headers={"User-Agent": "Tronhanh123-Student-Project/1.0"},
            )

            if response.status_code in (429, 502, 503, 504):
                errors.append(f"{server}: HTTP {response.status_code}")
                time.sleep(3)
                continue

            response.raise_for_status()
            return response.json().get("elements", [])

        except (requests.RequestException, ValueError) as exc:
            errors.append(f"{server}: {exc}")

    raise RuntimeError(
        "Khong lay duoc du lieu OSM. " + "; ".join(errors)
    )


def update_pois_around_room(latitude, longitude, radius=1500):
    latitude = float(latitude)
    longitude = float(longitude)

    elements = get_osm_data(latitude, longitude, radius)

    connection = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "tronhanh123"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )

    inserted = 0

    try:
        with connection:
            with connection.cursor() as cursor:
                for element in elements:
                    tags = element.get("tags", {})

                    lat = element.get("lat")
                    lon = element.get("lon")

                    if lat is None or lon is None:
                        center = element.get("center", {})
                        lat = center.get("lat")
                        lon = center.get("lon")

                    if lat is None or lon is None:
                        continue

                    if tags.get("highway") == "bus_stop":
                        category = "bus_stop"
                    elif tags.get("amenity") == "school":
                        category = "school"
                    elif tags.get("amenity") == "university":
                        category = "university"
                    elif tags.get("amenity") == "hospital":
                        category = "hospital"
                    elif tags.get("leisure") == "park":
                        category = "park"
                    else:
                        continue

                    cursor.execute(
                        """
                        INSERT INTO osm_pois (
                            osm_type, osm_id, name,
                            category, subcategory,
                            tags, geom, updated_at
                        )
                        SELECT
                            %s, %s, %s, %s, %s, %s,
                            ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                            NOW()
                        WHERE NOT EXISTS (
                            SELECT 1
                            FROM osm_pois
                            WHERE osm_type = %s AND osm_id = %s
                        )
                        """,
                        (
                            element["type"],
                            element["id"],
                            tags.get("name", "Chưa có tên"),
                            category,
                            category,
                            Json(tags),
                            lon,
                            lat,
                            element["type"],
                            element["id"],
                        ),
                    )

                    inserted += cursor.rowcount

        return {
            "success": True,
            "downloaded": len(elements),
            "inserted": inserted,
        }

    finally:
        connection.close()
