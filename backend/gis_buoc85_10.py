# -*- coding: utf-8 -*-
"""Tronhanh123 GIS API (Bước 85.6). Đọc dữ liệu PostGIS, không ghi DB.
Trong backend/main.py: from backend.gis_buoc85_6 import router as gis_router
                    app.include_router(gis_router)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import json
import math
from database.connection import ket_noi_db

router = APIRouter(prefix='/api/gis', tags=['GIS - OpenStreetMap / PostGIS'])
CATEGORIES = ('university', 'hospital', 'bus_stop', 'park', 'school')


def query_db(sql, args=()):
    conn = ket_noi_db()
    if conn is None:
        raise HTTPException(503, 'Không kết nối được PostgreSQL')
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(sql, args)
        names = [c[0] for c in cursor.description]
        return [dict(zip(names, row)) for row in cursor.fetchall()]
    except HTTPException:
        raise
    except Exception as exc:
        # Không trả chi tiết SQL/DB cho client.
        raise HTTPException(503, 'Không truy vấn được dữ liệu GIS; kiểm tra PostGIS và các view Bước 85.4') from exc
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()


@router.get('/health')
def gis_health():
    rows = query_db('SELECT PostGIS_Version() AS version, (SELECT COUNT(*) FROM public.osm_pois) AS poi_count, (SELECT COUNT(*) FROM public.v_room_geo) AS rooms_with_coordinates')
    return {'status': 'success', 'data': rows[0]}


@router.get('/categories')
def categories():
    rows = query_db('SELECT category, COUNT(*)::integer AS count FROM public.osm_pois GROUP BY category ORDER BY category')
    return {'status': 'success', 'data': rows, 'source': 'OpenStreetMap contributors (ODbL)'}


@router.get('/rooms/{room_id}/summary')
def room_summary(room_id: int):
    if room_id < 1:
        raise HTTPException(422, 'ID phòng không hợp lệ')
    rows = query_db('''
        SELECT r.room_id, r.title, r.latitude, r.longitude,
               u.poi_id AS nearest_university_id, u.university_name,
               u.distance_m AS nearest_university_distance_m,
               a.total_pois_1km, a.universities_1km, a.hospitals_1km,
               a.bus_stops_1km, a.parks_1km, a.schools_1km
        FROM public.v_room_geo r
        JOIN public.v_room_nearest_university u ON u.room_id=r.room_id
        JOIN public.v_room_amenities_1km a ON a.room_id=r.room_id
        WHERE r.room_id=%s
    ''', (room_id,))
    if not rows:
        raise HTTPException(404, 'Không tìm thấy phòng đã duyệt có tọa độ hợp lệ')
    return {'status': 'success', 'data': rows[0], 'distance_note': 'Khoảng cách đường chim bay, không phải thời gian đi lại', 'source': 'OpenStreetMap contributors (ODbL)'}


@router.get('/rooms/{room_id}/nearby')
def room_nearby(room_id: int, radius_m: int = Query(1000, ge=100, le=5000),
                category: str | None = Query(None), limit: int = Query(100, ge=1, le=500)):
    if room_id < 1:
        raise HTTPException(422, 'ID phòng không hợp lệ')
    if category is not None and category not in CATEGORIES:
        raise HTTPException(422, 'Loại POI không hợp lệ')
    room = query_db('SELECT room_id FROM public.v_room_geo WHERE room_id=%s', (room_id,))
    if not room:
        raise HTTPException(404, 'Không tìm thấy phòng đã duyệt có tọa độ hợp lệ')
    rows = query_db('''
        SELECT p.id, p.osm_type, p.osm_id, p.name, p.category, p.subcategory,
               ST_Y(p.geom)::float AS latitude, ST_X(p.geom)::float AS longitude,
               ROUND(ST_Distance(r.geom::geography, p.geom::geography)::numeric,1) AS distance_m
        FROM public.v_room_geo r JOIN public.osm_pois p
          ON ST_DWithin(r.geom::geography, p.geom::geography, %s)
        WHERE r.room_id=%s AND (%s::text IS NULL OR p.category=%s)
        ORDER BY distance_m, p.id LIMIT %s
    ''', (radius_m, room_id, category, category, limit))
    return {'status': 'success', 'room_id': room_id, 'radius_m': radius_m,
            'count_returned': len(rows), 'data': rows, 'source': 'OpenStreetMap contributors (ODbL)'}


@router.get('/pois')
def pois(south: float = Query(..., ge=-90, le=90), west: float = Query(..., ge=-180, le=180),
         north: float = Query(..., ge=-90, le=90), east: float = Query(..., ge=-180, le=180),
         category: str | None = None, limit: int = Query(300, ge=1, le=1000)):
    if south >= north or west >= east:
        raise HTTPException(422, 'Bounding box không hợp lệ; cần south < north và west < east')
    if category is not None and category not in CATEGORIES:
        raise HTTPException(422, 'Loại POI không hợp lệ')
    rows = query_db('''
        SELECT id, osm_type, osm_id, name, category,
               ST_Y(geom)::float AS latitude, ST_X(geom)::float AS longitude
        FROM public.osm_pois
        WHERE geom && ST_MakeEnvelope(%s,%s,%s,%s,4326)
          AND (%s::text IS NULL OR category=%s)
        ORDER BY id LIMIT %s
    ''', (west, south, east, north, category, category, limit))
    return {'status': 'success', 'count_returned': len(rows), 'data': rows,
            'source': 'OpenStreetMap contributors (ODbL)'}


# BUOC 85.10: Loc phong theo da giac bang PostGIS (chi doc).
class PolygonRequest(BaseModel):
    # Toa do theo thu tu Leaflet: [latitude, longitude].
    vertices: list[list[float]] = Field(..., min_length=3, max_length=100)


@router.post('/rooms/within-polygon')
def rooms_within_polygon(body: PolygonRequest):
    vertices = body.vertices
    for point in vertices:
        if len(point) != 2 or not all(math.isfinite(x) for x in point):
            raise HTTPException(422, 'Moi dinh phai co 2 toa do hop le [latitude, longitude]')
        lat, lng = point
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise HTTPException(422, 'Toa do dinh nam ngoai pham vi hop le')
    if len(set((lat, lng) for lat, lng in vertices)) < 3:
        raise HTTPException(422, 'Can it nhat 3 dinh khac nhau')
    # GeoJSON va PostGIS su dung [longitude, latitude].
    ring = [[lng, lat] for lat, lng in vertices]
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    polygon_json = json.dumps({'type': 'Polygon', 'coordinates': [ring]})
    # ST_IsValid tranh da giac tu cat, ST_Covers bao gom diem tren canh.
    validation = query_db('''
        SELECT ST_IsValid(g) AS valid,
               ST_Area(g::geography) AS area_m2
        FROM (SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s),4326) AS g) AS t
    ''', (polygon_json,))[0]
    if not validation['valid'] or validation['area_m2'] <= 0:
        raise HTTPException(422, 'Da giac khong hop le (co the tu cat nhau hoac dien tich bang 0)')
    rows = query_db('''
        SELECT r.room_id AS id
        FROM public.v_room_geo AS r
        WHERE ST_Covers(ST_SetSRID(ST_GeomFromGeoJSON(%s),4326), r.geom)
        ORDER BY r.room_id
    ''', (polygon_json,))
    return {
        'status': 'success', 'data': rows, 'total': len(rows),
        'method': 'PostGIS ST_Covers',
        'note': 'Chi lay phong da duyet co toa do; bao gom phong nam tren canh da giac'
    }
