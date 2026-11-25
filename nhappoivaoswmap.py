# -*- coding: utf-8 -*-
"""Tronhanh123 - Buoc 85.5 (sua timeout): nhap POI OSM theo o nho, co resume.
Chi INSERT/UPDATE public.osm_pois; khong sua rooms, users.
Chay: python nhappoivaoswmap.py
Dung Ctrl+C de tam dung, chay lai de tiep tuc.
"""
import csv
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

CONTAINER = os.getenv('TRONHANH_DB_CONTAINER', 'postgres_db')
DATABASE = os.getenv('TRONHANH_DB_NAME', 'tronhanh123')
DB_USER = os.getenv('TRONHANH_DB_USER', 'postgres')
TILE_SIZE = float(os.getenv('OSM_TILE_SIZE', '0.025'))
HTTP_TIMEOUT = int(os.getenv('OSM_HTTP_TIMEOUT', '35'))
CACHE = Path(__file__).resolve().parent / 'osm_cache_buoc85'
ENDPOINTS = [
    'https://overpass.private.coffee/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
    'https://overpass-api.de/api/interpreter',
]


def docker_sql(sql):
    p = subprocess.run(['docker', 'exec', CONTAINER, 'psql', '-X', '-U', DB_USER,
                        '-d', DATABASE, '-At', '-v', 'ON_ERROR_STOP=1', '-c', sql],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout.strip()


def bbox_from_rooms():
    result = docker_sql('SELECT latitude || \',\' || longitude FROM public.v_room_geo')
    points = []
    for line in result.splitlines():
        if ',' not in line:
            continue
        lat, lon = map(float, line.split(','))
        if math.isfinite(lat) and math.isfinite(lon):
            points.append((lat, lon))
    if not points:
        raise RuntimeError('Khong co phong da duyet co toa do hop le.')
    lats, lons = zip(*points)
    padding_lat = 3 / 111
    padding_lon = 3 / (111 * max(.2, math.cos(math.radians(sum(lats) / len(lats)))))
    box = (min(lats)-padding_lat, min(lons)-padding_lon,
           max(lats)+padding_lat, max(lons)+padding_lon)
    if box[2]-box[0] > .8 or box[3]-box[1] > .8:
        raise RuntimeError('Pham vi qua rong; can chia khu vuc.')
    return box, len(points)


def tiles(bbox):
    south, west, north, east = bbox
    lat_steps = math.ceil((north-south)/TILE_SIZE)
    lon_steps = math.ceil((east-west)/TILE_SIZE)
    for i in range(lat_steps):
        for j in range(lon_steps):
            yield (south+i*TILE_SIZE, west+j*TILE_SIZE,
                   min(north, south+(i+1)*TILE_SIZE),
                   min(east, west+(j+1)*TILE_SIZE))


def query_for(box):
    s, w, n, e = box
    bbox = f'{s:.6f},{w:.6f},{n:.6f},{e:.6f}'
    return ('[out:json][timeout:30];('
            f'nwr["amenity"~"^(university|college|hospital|clinic|school|bus_station)$"]({bbox});'
            f'nwr["highway"="bus_stop"]({bbox});'
            f'nwr["leisure"="park"]({bbox});'
            f'nwr["public_transport"="platform"]["bus"="yes"]({bbox});'
            ');out center tags;')


def fetch(query, index):
    body = urllib.parse.urlencode({'data': query}).encode('utf-8')
    # Xoay endpoint giua cac o, tranh don tai len mot server.
    servers = ENDPOINTS[index % len(ENDPOINTS):] + ENDPOINTS[:index % len(ENDPOINTS)]
    errors = []
    for endpoint in servers:
        try:
            request = urllib.request.Request(endpoint, data=body, headers={
                'User-Agent': 'Tronhanh123-student-GIS-project/1.1 (OSM POI import)',
                'Content-Type': 'application/x-www-form-urlencoded',
            })
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
                payload = json.load(response)
            if not isinstance(payload.get('elements'), list):
                raise ValueError('Phan hoi khong co elements')
            return payload['elements']
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            errors.append(f'{endpoint}: {str(exc)[:100]}')
            print('    Server khong phan hoi:', errors[-1], flush=True)
    raise RuntimeError('; '.join(errors))


def classify(tags):
    a = tags.get('amenity', '')
    if a in ('university', 'college'):
        return 'university', a
    if a in ('hospital', 'clinic'):
        return 'hospital', a
    if a == 'school':
        return 'school', a
    if tags.get('highway') == 'bus_stop' or a == 'bus_station' or (tags.get('public_transport') == 'platform' and tags.get('bus') == 'yes'):
        return 'bus_stop', tags.get('highway') or a or 'platform'
    if tags.get('leisure') == 'park':
        return 'park', 'park'
    return None


def parse(elements):
    found = {}
    for item in elements:
        tags = item.get('tags') or {}
        category = classify(tags)
        kind = item.get('type')
        if not category or kind not in ('node', 'way', 'relation'):
            continue
        point = item.get('center') or item
        lat, lon = point.get('lat'), point.get('lon')
        if not isinstance(lat, (float, int)) or not isinstance(lon, (float, int)):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        key = (kind, int(item['id']))
        found[key] = (kind, key[1], tags.get('name', ''), category[0], category[1],
                      json.dumps(tags, ensure_ascii=False), lon, lat)
    return list(found.values())


def import_rows(rows):
    if not rows:
        return
    with tempfile.TemporaryDirectory(prefix='tronhanh85_') as folder:
        csv_path = Path(folder) / 'poi.csv'
        with csv_path.open('w', encoding='utf-8', newline='') as handle:
            csv.writer(handle).writerows(rows)
        remote = '/tmp/tronhanh85_poi_import.csv'
        p = subprocess.run(['docker', 'cp', str(csv_path), f'{CONTAINER}:{remote}'],
                           capture_output=True, text=True)
        if p.returncode:
            raise RuntimeError(p.stderr)
        sql = r'''\set ON_ERROR_STOP on
BEGIN;
CREATE TEMP TABLE poi_import_stage (
 osm_type text, osm_id bigint, name text, category text,
 subcategory text, tags_json text, lon double precision, lat double precision
) ON COMMIT DROP;
\copy poi_import_stage FROM '/tmp/tronhanh85_poi_import.csv' WITH (FORMAT csv, ENCODING 'UTF8');
INSERT INTO public.osm_pois(osm_type,osm_id,name,category,subcategory,tags,geom,updated_at)
SELECT osm_type,osm_id,NULLIF(name,''),category,subcategory,
       tags_json::jsonb, ST_SetSRID(ST_MakePoint(lon,lat),4326),NOW()
FROM poi_import_stage
ON CONFLICT (osm_type,osm_id) DO UPDATE SET
 name=EXCLUDED.name, category=EXCLUDED.category,
 subcategory=EXCLUDED.subcategory, tags=EXCLUDED.tags,
 geom=EXCLUDED.geom, updated_at=NOW();
COMMIT;
'''
        p = subprocess.run(['docker', 'exec', '-i', CONTAINER, 'psql', '-X',
                            '-v', 'ON_ERROR_STOP=1', '-U', DB_USER, '-d', DATABASE],
                           input=sql, capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
        if p.returncode:
            raise RuntimeError('Khong nhap duoc POI: ' + p.stderr + p.stdout)


def main():
    print('=== TRONHANH123 - BUOC 85.5: OSM CHIA O / TU DONG TIEP TUC ===', flush=True)
    print('Chi ghi public.osm_pois, khong sua rooms/users.', flush=True)
    print('PostGIS:', docker_sql('SELECT PostGIS_Version();'), flush=True)
    box, rooms = bbox_from_rooms()
    all_tiles = list(tiles(box))
    CACHE.mkdir(parents=True, exist_ok=True)
    print(f'{rooms} phong co toa do; {len(all_tiles)} o nho; cache: {CACHE}', flush=True)
    success, failed, total_rows = 0, 0, 0
    for i, tile in enumerate(all_tiles, 1):
        cache_file = CACHE / ('tile_' + '_'.join(f'{x:.6f}' for x in tile) + '.json')
        try:
            if cache_file.exists():
                elements = json.loads(cache_file.read_text(encoding='utf-8'))
                source = 'cache'
            else:
                print(f'[{i}/{len(all_tiles)}] Dang tai OSM...', flush=True)
                elements = fetch(query_for(tile), i)
                # Chi luu cache sau khi phan hoi hop le.
                cache_file.write_text(json.dumps(elements, ensure_ascii=False), encoding='utf-8')
                source = 'OSM'
            rows = parse(elements)
            import_rows(rows)
            success += 1
            total_rows += len(rows)
            print(f'[{i}/{len(all_tiles)}] OK ({source}), {len(rows)} POI; tong luot nhap: {total_rows}', flush=True)
            if source == 'OSM':
                time.sleep(1.5)
        except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
            failed += 1
            print(f'[{i}/{len(all_tiles)}] BO QUA O NAY: {exc}', flush=True)
    print('\nPOI THEO LOAI:', flush=True)
    print(docker_sql('SELECT category || chr(9) || COUNT(*) FROM public.osm_pois GROUP BY category ORDER BY category;'), flush=True)
    print('\nKHOANG CACH TRUONG DAI HOC (5 PHONG):', flush=True)
    print(docker_sql("SELECT room_id || chr(9) || COALESCE(university_name,'chua co') || chr(9) || COALESCE(distance_m::text,'NULL') FROM public.v_room_nearest_university ORDER BY room_id LIMIT 5;"), flush=True)
    print('\nTIEN ICH TRONG 1 KM (5 PHONG):', flush=True)
    print(docker_sql('SELECT room_id || chr(9) || total_pois_1km FROM public.v_room_amenities_1km ORDER BY room_id LIMIT 5;'), flush=True)
    print(f'\nKET QUA: {success}/{len(all_tiles)} o thanh cong; {failed} o loi.', flush=True)
    if failed:
        print('Co o chua tai duoc. Chay lai lenh de thu lai; o thanh cong da luu cache.', flush=True)
        sys.exit(2)
    print('HOAN THANH. Du lieu: OpenStreetMap contributors (ODbL).', flush=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nDa tam dung. Chay lai de tiep tuc tu cache.', flush=True)
        sys.exit(130)
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        print('LOI:', exc, file=sys.stderr)
        sys.exit(1)
