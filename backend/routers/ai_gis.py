from fastapi import APIRouter, HTTPException
from database.connection import ket_noi_db

router = APIRouter(prefix="/api/ai/gis", tags=["AI GIS"])

SQL_FEATURES = """
SELECT
    r.id AS room_id,
    r.district,
    r.area,
    r.price,
    r.latitude,
    r.longitude,
    (
        SELECT ROUND(
            MIN(
                ST_Distance(
                    ST_SetSRID(
                        ST_MakePoint(r.longitude, r.latitude),
                        4326
                    )::geography,
                    p.geom::geography
                )
            )::numeric,
            1
        )
        FROM public.osm_pois p
        WHERE p.category = 'university'
    ) AS nearest_university_m,
    (
        SELECT COUNT(*)::integer
        FROM public.osm_pois p
        WHERE p.category = 'bus_stop'
        AND ST_DWithin(
            ST_SetSRID(
                ST_MakePoint(r.longitude, r.latitude),
                4326
            )::geography,
            p.geom::geography,
            1000
        )
    ) AS bus_stops_1km,
    (
        SELECT COUNT(*)::integer
        FROM public.osm_pois p
        WHERE p.category = 'school'
        AND ST_DWithin(
            ST_SetSRID(
                ST_MakePoint(r.longitude, r.latitude),
                4326
            )::geography,
            p.geom::geography,
            1000
        )
    ) AS schools_1km,
    (
        SELECT COUNT(*)::integer
        FROM public.osm_pois p
        WHERE p.category = 'hospital'
        AND ST_DWithin(
            ST_SetSRID(
                ST_MakePoint(r.longitude, r.latitude),
                4326
            )::geography,
            p.geom::geography,
            1000
        )
    ) AS hospitals_1km,
    (
        SELECT COUNT(*)::integer
        FROM public.osm_pois p
        WHERE p.category = 'park'
        AND ST_DWithin(
            ST_SetSRID(
                ST_MakePoint(r.longitude, r.latitude),
                4326
            )::geography,
            p.geom::geography,
            1000
        )
    ) AS parks_1km
FROM public.rooms r
WHERE r.status = 'da_duyet'
  AND r.price > 0
  AND r.area > 0
  AND r.latitude BETWEEN -90 AND 90
  AND r.longitude BETWEEN -180 AND 180
ORDER BY r.id;
"""


@router.get("/features")
def get_gis_features():
    conn = ket_noi_db()

    if conn is None:
        raise HTTPException(
            status_code=503,
            detail="Không thể kết nối PostgreSQL."
        )

    try:
        with conn.cursor() as cursor:
            cursor.execute(SQL_FEATURES)
            columns = [col[0] for col in cursor.description]
            records = cursor.fetchall()

        rooms = []

        for record in records:
            item = dict(zip(columns, record))

            for key in [
                "area",
                "price",
                "latitude",
                "longitude",
                "nearest_university_m",
            ]:
                if item[key] is not None:
                    item[key] = float(item[key])

            rooms.append(item)

        return {
            "status": "ready",
            "source": "PostgreSQL + PostGIS + OpenStreetMap",
            "radius_m": 1000,
            "total_rooms": len(rooms),
            "minimum_training_rooms": 30,
            "can_train_gis_model": len(rooms) >= 30,
            "rooms": rooms,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Không thể tính đặc trưng GIS."
        ) from exc

    finally:
        conn.close()
