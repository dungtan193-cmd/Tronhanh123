# -*- coding: utf-8 -*-
"""Tronhanh123 - Buoc 85.5 offline: import POI from a local .osm.pbf/.osm file.
Usage: python nhap_poi_tu_file_osm.py "D:\\du_lieu\\vietnam-latest.osm.pbf"
Dependency: python -m pip install osmium
Only upserts public.osm_pois. Never modifies rooms/users.
OSM data: © OpenStreetMap contributors, ODbL.
"""
import csv
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

CONTAINER = os.getenv('TRONHANH_DB_CONTAINER', 'postgres_db')
DATABASE = os.getenv('TRONHANH_DB_NAME', 'tronhanh123')
DB_USER = os.getenv('TRONHANH_DB_USER', 'postgres')
BATCH_SIZE = 1000


def sql(query):
    p = subprocess.run(['docker','exec',CONTAINER,'psql','-X','-U',DB_USER,'-d',DATABASE,
                        '-At','-v','ON_ERROR_STOP=1','-c',query],capture_output=True,text=True,
                       encoding='utf-8',errors='replace')
    if p.returncode: raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout.strip()


def classify(tags):
    a = tags.get('amenity', '')
    if a in ('university','college'): return ('university',a)
    if a in ('hospital','clinic'): return ('hospital',a)
    if a == 'school': return ('school',a)
    if tags.get('highway') == 'bus_stop' or a == 'bus_station' or (tags.get('public_transport') == 'platform' and tags.get('bus') == 'yes'):
        return ('bus_stop', tags.get('highway') or a or 'platform')
    if tags.get('leisure') == 'park': return ('park','park')
    return None


def insert_batch(rows):
    if not rows: return
    with tempfile.TemporaryDirectory(prefix='osm85_') as folder:
        local = Path(folder)/'poi.csv'
        with local.open('w',newline='',encoding='utf-8') as f: csv.writer(f).writerows(rows)
        remote = '/tmp/tronhanh85_poi_offline.csv'
        cp = subprocess.run(['docker','cp',str(local),f'{CONTAINER}:{remote}'],capture_output=True,text=True)
        if cp.returncode: raise RuntimeError(cp.stderr)
        statement = r'''
\set ON_ERROR_STOP on
BEGIN;
CREATE TEMP TABLE poi_import_stage(osm_type text,osm_id bigint,name text,category text,subcategory text,tags_json text,lon double precision,lat double precision) ON COMMIT DROP;
\copy poi_import_stage FROM '/tmp/tronhanh85_poi_offline.csv' WITH (FORMAT csv, ENCODING 'UTF8');
INSERT INTO public.osm_pois(osm_type,osm_id,name,category,subcategory,tags,geom,updated_at)
SELECT osm_type,osm_id,NULLIF(name,''),category,subcategory,tags_json::jsonb,ST_SetSRID(ST_MakePoint(lon,lat),4326),NOW()
FROM poi_import_stage
ON CONFLICT (osm_type,osm_id) DO UPDATE SET name=EXCLUDED.name,category=EXCLUDED.category,subcategory=EXCLUDED.subcategory,tags=EXCLUDED.tags,geom=EXCLUDED.geom,updated_at=NOW();
COMMIT;
'''
        p = subprocess.run(['docker','exec','-i',CONTAINER,'psql','-X','-U',DB_USER,'-d',DATABASE,'-v','ON_ERROR_STOP=1'],
                           input=statement,capture_output=True,text=True,encoding='utf-8',errors='replace')
        if p.returncode: raise RuntimeError(p.stderr.strip() or p.stdout.strip())


def main():
    if len(sys.argv)!=2:
        print('Cach dung: python nhap_poi_tu_file_osm.py "D:\\du_lieu\\vietnam-latest.osm.pbf"')
        return 2
    source=Path(sys.argv[1]).expanduser().resolve()
    if not source.is_file():
        print('Khong tim thay file:',source)
        return 2
    if not (source.name.lower().endswith('.osm.pbf') or source.suffix.lower()=='.osm'):
        print('Chi ho tro file .osm.pbf hoac .osm (XML).')
        return 2
    try: import osmium
    except ImportError:
        print('Chua co thu vien osmium. Chay: python -m pip install osmium')
        return 2
    print('PostGIS:',sql('SELECT PostGIS_Version();'))
    points=[]
    for line in sql('SELECT latitude || chr(44) || longitude FROM public.v_room_geo').splitlines():
        if ',' in line:
            lat,lon=map(float,line.split(','))
            if math.isfinite(lat) and math.isfinite(lon): points.append((lat,lon))
    if not points: raise RuntimeError('Khong co phong da duyet co toa do hop le.')
    # Match the previous importer's coverage: ~3 km around room coordinate bounds.
    lat_min=min(x for x,y in points)-3/111
    lat_max=max(x for x,y in points)+3/111
    lon_pad=3/(111*max(.2,math.cos(math.radians(sum(x for x,y in points)/len(points)))))
    lon_min=min(y for x,y in points)-lon_pad
    lon_max=max(y for x,y in points)+lon_pad
    print(f'{len(points)} phong co toa do. Pham vi: {lat_min:.5f},{lon_min:.5f} -> {lat_max:.5f},{lon_max:.5f}')
    print('Dang doc file OSM; file PBF lon co the mat vai phut...')

    class Importer(osmium.SimpleHandler):
        def __init__(self):
            super().__init__()
            self.batch=[]
            self.total=0
            self.skipped_ways=0
            self.relations=0
        def add(self,kind,obj,lat,lon,tags):
            if not (lat_min<=lat<=lat_max and lon_min<=lon<=lon_max): return
            cat=classify(tags)
            if cat is None:return
            self.batch.append((kind,int(obj.id),tags.get('name',''),cat[0],cat[1],json.dumps(tags,ensure_ascii=False),lon,lat))
            if len(self.batch)>=BATCH_SIZE:self.flush()
        def flush(self):
            if self.batch:
                insert_batch(self.batch)
                self.total+=len(self.batch)
                print(f'  Da nhap/cap nhat {self.total} POI...',flush=True)
                self.batch.clear()
        def node(self,obj):
            tags=dict(obj.tags)
            if classify(tags) is None:return
            if obj.location.valid(): self.add('node',obj,obj.location.lat,obj.location.lon,tags)
        def way(self,obj):
            tags=dict(obj.tags)
            if classify(tags) is None:return
            coords=[]
            for n in obj.nodes:
                if n.location.valid():coords.append((n.location.lat,n.location.lon))
            if coords:
                self.add('way',obj,sum(x for x,y in coords)/len(coords),sum(y for x,y in coords)/len(coords),tags)
            else:self.skipped_ways+=1
        def relation(self,obj):
            if classify(dict(obj.tags)) is not None:self.relations+=1

    h=Importer()
    # locations=True resolves way node coordinates from the input PBF/XML.
    h.apply_file(str(source),locations=True)
    h.flush()
    print('\nHOAN THANH:',h.total,'POI duoc doc va nhap/cap nhat.')
    if h.relations:
        print('Luu y:',h.relations,'relation co tag phu hop chua duoc nhap (chua tinh tam polygon relation).')
    if h.skipped_ways: print('Way thieu toa do:',h.skipped_ways)
    print('\nPOI theo loai:\n'+sql("SELECT category || ': ' || COUNT(*) FROM public.osm_pois GROUP BY category ORDER BY category"))
    print('\nKhoang cach truong gan nhat (5 phong):\n'+sql("SELECT room_id || ': ' || COALESCE(university_name,'chua co du lieu') || ' / ' || COALESCE(distance_m::text,'NULL') || ' m' FROM public.v_room_nearest_university ORDER BY room_id LIMIT 5"))
    print('\nPOI trong 1 km (5 phong):\n'+sql("SELECT room_id || ': ' || total_pois_1km FROM public.v_room_amenities_1km ORDER BY room_id LIMIT 5"))
    print('Nguon du lieu: OpenStreetMap contributors (ODbL).')
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except KeyboardInterrupt:
        print('\nDa dung; POI da nhap theo batch van duoc giu. Chay lai de tiep tuc.',file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print('LOI:',e,file=sys.stderr)
        sys.exit(1)
