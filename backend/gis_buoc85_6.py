
# -*- coding: utf-8 -*-
"""
Tronhanh123 GIS API - Buoc 85.10

Giu nguyen 5 API GIS cu.
Bo sung loc phong tro trong Polygon bang PostGIS ST_Covers.

Trong backend/main.py:
    from backend.gis_buoc85_6 import router as gis_router
    app.include_router(gis_router)
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from database.connection import ket_noi_db

router = APIRouter(
    prefix="/api/gis",
    tags=["GIS - OpenStreetMap / PostGIS"]
)

CATEGORIES = (
    "university",
    "hospital",
    "bus_stop",
    "park",
    "school"
)


# ============================================================
# DATABASE
# ============================================================

def query_db(sql, args=()):
    conn = ket_noi_db()

    if conn is None:
        raise HTTPException(
            status_code=503,
            detail="Không kết nối được PostgreSQL"
        )

    cursor = None

    try:
        cursor = conn.cursor()
        cursor.execute(sql, args)

        names = [c[0] for c in cursor.description]

        return [
            dict(zip(names, row))
            for row in cursor.fetchall()
        ]

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Không truy vấn được dữ liệu GIS; "
                "kiểm tra PostGIS và các view."
            )
        ) from exc

    finally:
        if cursor is not None:
            cursor.close()

        conn.close()


# ============================================================
# 1. GIS HEALTH
# ============================================================

@router.get("/health")
def gis_health():
    rows = query_db("""
        SELECT
            PostGIS_Version() AS version,

            (
                SELECT COUNT(*)
                FROM public.osm_pois
            ) AS poi_count,

            (
                SELECT COUNT(*)
                FROM public.v_room_geo
            ) AS rooms_with_coordinates
    """)

    return {
        "status": "success",
        "data": rows[0]
    }


# ============================================================
# 2. CATEGORIES
# ============================================================

@router.get("/categories")
def categories():
    rows = query_db("""
        SELECT
            category,
            COUNT(*)::integer AS count
        FROM public.osm_pois
        GROUP BY category
        ORDER BY category
    """)

    return {
        "status": "success",
        "data": rows,
        "source": "OpenStreetMap contributors (ODbL)"
    }


# ============================================================
# 3. ROOM SUMMARY
# ============================================================

@router.get("/rooms/{room_id}/summary")
def room_summary(room_id: int):

    if room_id < 1:
        raise HTTPException(
            status_code=422,
            detail="ID phòng không hợp lệ"
        )

    rows = query_db("""
        SELECT
            r.room_id,
            r.title,
            r.latitude,
            r.longitude,

            u.poi_id AS nearest_university_id,
            u.university_name,
            u.distance_m AS nearest_university_distance_m,

            a.total_pois_1km,
            a.universities_1km,
            a.hospitals_1km,
            a.bus_stops_1km,
            a.parks_1km,
            a.schools_1km

        FROM public.v_room_geo r

        JOIN public.v_room_nearest_university u
            ON u.room_id = r.room_id

        JOIN public.v_room_amenities_1km a
            ON a.room_id = r.room_id

        WHERE r.room_id = %s
    """, (room_id,))

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=(
                "Không tìm thấy phòng đã duyệt "
                "có tọa độ hợp lệ"
            )
        )

    return {
        "status": "success",
        "data": rows[0],
        "distance_note": (
            "Khoảng cách đường chim bay, "
            "không phải thời gian đi lại"
        ),
        "source": "OpenStreetMap contributors (ODbL)"
    }


# ============================================================
# 4. NEARBY POIS
# ============================================================

@router.get("/rooms/{room_id}/nearby")
def room_nearby(
    room_id: int,
    radius_m: int = Query(1000, ge=100, le=5000),
    category: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500)
):

    if room_id < 1:
        raise HTTPException(
            status_code=422,
            detail="ID phòng không hợp lệ"
        )

    if category is not None and category not in CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail="Loại POI không hợp lệ"
        )

    room = query_db("""
        SELECT room_id
        FROM public.v_room_geo
        WHERE room_id = %s
    """, (room_id,))

    if not room:
        raise HTTPException(
            status_code=404,
            detail=(
                "Không tìm thấy phòng đã duyệt "
                "có tọa độ hợp lệ"
            )
        )

    rows = query_db("""
        SELECT
            p.id,
            p.osm_type,
            p.osm_id,
            p.name,
            p.category,
            p.subcategory,

            ST_Y(p.geom)::float AS latitude,
            ST_X(p.geom)::float AS longitude,

            ROUND(
                ST_Distance(
                    r.geom::geography,
                    p.geom::geography
                )::numeric,
                1
            ) AS distance_m

        FROM public.v_room_geo r

        JOIN public.osm_pois p
            ON ST_DWithin(
                r.geom::geography,
                p.geom::geography,
                %s
            )

        WHERE r.room_id = %s

          AND (
              %s::text IS NULL
              OR p.category = %s
          )

        ORDER BY distance_m, p.id

        LIMIT %s
    """, (
        radius_m,
        room_id,
        category,
        category,
        limit
    ))

    return {
        "status": "success",
        "room_id": room_id,
        "radius_m": radius_m,
        "count_returned": len(rows),
        "data": rows,
        "source": "OpenStreetMap contributors (ODbL)"
    }


# ============================================================
# 5. POIS TRONG BOUNDING BOX
# ============================================================

@router.get("/pois")
def pois(
    south: float = Query(..., ge=-90, le=90),
    west: float = Query(..., ge=-180, le=180),
    north: float = Query(..., ge=-90, le=90),
    east: float = Query(..., ge=-180, le=180),
    category: str | None = None,
    limit: int = Query(300, ge=1, le=1000)
):

    if south >= north or west >= east:
        raise HTTPException(
            status_code=422,
            detail=(
                "Bounding box không hợp lệ; "
                "cần south < north và west < east"
            )
        )

    if category is not None and category not in CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail="Loại POI không hợp lệ"
        )

    rows = query_db("""
        SELECT
            id,
            osm_type,
            osm_id,
            name,
            category,

            ST_Y(geom)::float AS latitude,
            ST_X(geom)::float AS longitude

        FROM public.osm_pois

        WHERE geom && ST_MakeEnvelope(
            %s, %s, %s, %s, 4326
        )

        AND (
            %s::text IS NULL
            OR category = %s
        )

        ORDER BY id

        LIMIT %s
    """, (
        west,
        south,
        east,
        north,
        category,
        category,
        limit
    ))

    return {
        "status": "success",
        "count_returned": len(rows),
        "data": rows,
        "source": "OpenStreetMap contributors (ODbL)"
    }


# ============================================================
# 6. POLYGON - POSTGIS ST_COVERS
# ============================================================

class PolygonRequest(BaseModel):
    # Moi diem co dang:
    # [longitude, latitude]
    #
    # Vi du:
    # [
    #     [105.80, 21.00],
    #     [105.82, 21.00],
    #     [105.82, 21.02]
    # ]

    coordinates: list[list[float]] = Field(
        ...,
        min_length=3,
        max_length=100
    )


@router.post("/rooms/within-polygon")
def rooms_within_polygon(payload: PolygonRequest):

    coordinates = payload.coordinates

    if len(coordinates) < 3:
        raise HTTPException(
            status_code=422,
            detail="Polygon cần ít nhất 3 đỉnh"
        )

    # Kiem tra toa do va tao danh sach dinh
    points = []

    for point in coordinates:

        if len(point) != 2:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Mỗi đỉnh phải có dạng "
                    "[longitude, latitude]"
                )
            )

        longitude, latitude = point

        if not (-180 <= longitude <= 180):
            raise HTTPException(
                status_code=422,
                detail="Kinh độ không hợp lệ"
            )

        if not (-90 <= latitude <= 90):
            raise HTTPException(
                status_code=422,
                detail="Vĩ độ không hợp lệ"
            )

        points.append(
            (longitude, latitude)
        )

    # Dong polygon neu diem dau va cuoi khac nhau
    if points[0] != points[-1]:
        points.append(points[0])

    if len(set(points[:-1])) < 3:
        raise HTTPException(
            status_code=422,
            detail="Polygon phải có ít nhất 3 đỉnh khác nhau"
        )

    # Tao WKT an toan tu toa do da kiem tra
    polygon_wkt = "POLYGON((" + ", ".join(
        f"{lon} {lat}"
        for lon, lat in points
    ) + "))"

    # Kiem tra polygon hop le
    validation = query_db("""
        SELECT
            ST_IsValid(
                ST_GeomFromText(%s, 4326)
            ) AS is_valid,

            ST_IsValidReason(
                ST_GeomFromText(%s, 4326)
            ) AS reason
    """, (
        polygon_wkt,
        polygon_wkt
    ))

    if not validation[0]["is_valid"]:
        raise HTTPException(
            status_code=422,
            detail=(
                "Polygon không hợp lệ: "
                + str(validation[0]["reason"])
            )
        )

    # Loc phong bang PostGIS
    #
    # ST_Covers:
    # - Lay phong nam trong polygon
    # - Bao gom phong tren ranh gioi polygon
    #
    # v_room_geo:
    # - Chi gom phong co toa do hop le
    # - Su dung geom SRID 4326

    rows = query_db("""
        SELECT
            r.room_id AS id,
            r.title,
            r.latitude,
            r.longitude

        FROM public.v_room_geo r

        WHERE ST_Covers(
            ST_GeomFromText(%s, 4326),
            r.geom
        )

        ORDER BY r.room_id DESC
    """, (polygon_wkt,))

    return {
        "status": "success",
        "method": "PostGIS ST_Covers",
        "count": len(rows),
        "count_returned": len(rows),
        "total": len(rows),
        "data": rows,
        "message": (
            f"Tìm thấy {len(rows)} phòng "
            "nằm trong vùng Polygon"
        )
    }
