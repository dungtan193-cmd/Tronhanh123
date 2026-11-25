from fastapi import APIRouter, HTTPException, Query
from database.connection import ket_noi_db

router = APIRouter(
    prefix="/api/ai/gis/research",
    tags=["AI GIS Research"]
)

SQL = """
SELECT
    r.id AS room_id,
    r.title,
    r.district,
    r.address,
    r.price,
    r.area,
    r.latitude,
    r.longitude,
    r.source_url,
    r.location_verified,

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
            )::numeric, 1
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

FROM public.ai_real_room_dataset r
WHERE r.location_verified = TRUE
  AND r.latitude BETWEEN 20 AND 22
  AND r.longitude BETWEEN 104.5 AND 107
  AND r.price > 0
  AND r.area > 0
ORDER BY r.id
"""

@router.get("/features")
def research_features(
    limit: int = Query(default=1000, ge=1, le=10000)
):
    conn = ket_noi_db()

    if conn is None:
        raise HTTPException(
            status_code=503,
            detail="Không kết nối được PostgreSQL"
        )

    try:
        with conn.cursor() as cursor:
            cursor.execute(SQL + " LIMIT %s", (limit,))
            columns = [col[0] for col in cursor.description]
            records = cursor.fetchall()

        rooms = []

        for record in records:
            item = dict(zip(columns, record))

            for field in (
                "price",
                "area",
                "latitude",
                "longitude",
                "nearest_university_m",
            ):
                if item[field] is not None:
                    item[field] = float(item[field])

            rooms.append(item)

        return {
            "status": "ready",
            "source": "Verified research dataset + PostGIS + OSM",
            "radius_m": 1000,
            "total_rooms": len(rooms),
            "minimum_training_rooms": 30,
            "can_train_gis_model": len(rooms) >= 30,
            "rooms": rooms,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Không thể tính đặc trưng GIS nghiên cứu"
        ) from exc

    finally:
        conn.close()
