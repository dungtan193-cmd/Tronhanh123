-- TRONHANH123 | BUOC 85.4 - NEN TANG GIS POSTGIS
-- An toan: khong xoa/sua bang rooms, users hoac du lieu hien co.
-- Chay trong database tronhanh123, PostgreSQL 16 + PostGIS 3.4.
BEGIN;
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS public.osm_pois (
    id BIGSERIAL PRIMARY KEY,
    osm_type VARCHAR(12) NOT NULL CHECK (osm_type IN ('node', 'way', 'relation')),
    osm_id BIGINT NOT NULL,
    name TEXT,
    category VARCHAR(40) NOT NULL,
    subcategory TEXT,
    tags JSONB NOT NULL DEFAULT '{}'::jsonb,
    geom geometry(Point, 4326) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT osm_pois_osm_unique UNIQUE (osm_type, osm_id),
    CONSTRAINT osm_pois_category_nonempty CHECK (length(btrim(category)) > 0)
);
CREATE INDEX IF NOT EXISTS idx_osm_pois_geom ON public.osm_pois USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_osm_pois_category ON public.osm_pois (category);

-- View nay chi lay phong da duyet va toa do hop le; khong thay doi bang rooms.
CREATE OR REPLACE VIEW public.v_room_geo AS
SELECT r.id AS room_id, r.title, r.address, r.district,
       r.price, r.area, r.latitude, r.longitude,
       ST_SetSRID(ST_MakePoint(r.longitude, r.latitude), 4326)::geometry(Point,4326) AS geom
FROM public.rooms AS r
WHERE r.status = 'da_duyet'
  AND r.latitude IS NOT NULL AND r.longitude IS NOT NULL
  AND r.latitude BETWEEN -90 AND 90
  AND r.longitude BETWEEN -180 AND 180
  AND NOT (r.latitude = 0 AND r.longitude = 0);

-- Khoang cach met theo geography (khong tinh theo do vi do).
-- Quy uoc category='university' cho truong dai hoc.
CREATE OR REPLACE VIEW public.v_room_nearest_university AS
SELECT r.room_id, r.title, r.district,
       p.id AS poi_id, p.name AS university_name,
       ROUND(p.distance_m::numeric, 1) AS distance_m
FROM public.v_room_geo AS r
LEFT JOIN LATERAL (
    SELECT o.id, o.name,
           ST_Distance(r.geom::geography, o.geom::geography) AS distance_m
    FROM public.osm_pois AS o
    WHERE o.category = 'university'
    ORDER BY ST_Distance(r.geom::geography, o.geom::geography), o.id
    LIMIT 1
) AS p ON TRUE;

-- Dem POI trong ban kinh 1000 met, theo tung phong.
-- Co the bo sung category moi khi nhap OSM; dem tat ca POI da nhap.
CREATE OR REPLACE VIEW public.v_room_amenities_1km AS
SELECT r.room_id, r.title, r.district,
       COUNT(p.id)::integer AS total_pois_1km,
       COUNT(p.id) FILTER (WHERE p.category = 'university')::integer AS universities_1km,
       COUNT(p.id) FILTER (WHERE p.category = 'hospital')::integer AS hospitals_1km,
       COUNT(p.id) FILTER (WHERE p.category = 'bus_stop')::integer AS bus_stops_1km,
       COUNT(p.id) FILTER (WHERE p.category = 'park')::integer AS parks_1km,
       COUNT(p.id) FILTER (WHERE p.category = 'school')::integer AS schools_1km
FROM public.v_room_geo AS r
LEFT JOIN public.osm_pois AS p
  ON ST_DWithin(r.geom::geography, p.geom::geography, 1000)
GROUP BY r.room_id, r.title, r.district;

COMMIT;

-- KIEM TRA (chi doc):
SELECT PostGIS_Version() AS postgis_version;
SELECT COUNT(*) AS approved_rooms_with_valid_coordinates FROM public.v_room_geo;
SELECT COUNT(*) AS osm_pois_imported FROM public.osm_pois;
SELECT * FROM public.v_room_nearest_university ORDER BY room_id LIMIT 5;
SELECT * FROM public.v_room_amenities_1km ORDER BY room_id LIMIT 5;
-- Luu y: Neu chua nhap POI, khoang cach truong gan nhat la NULL, so POI la 0.
