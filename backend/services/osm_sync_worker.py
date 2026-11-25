import json
import logging
import threading
import time
from datetime import datetime, timedelta, timezone

import requests
from psycopg2.extras import Json

log = logging.getLogger("tronhanh123.osm")

SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

_worker_started = False
_worker_lock = threading.Lock()


def create_queue_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS osm_sync_jobs (
                room_id INTEGER PRIMARY KEY
                    REFERENCES rooms(id) ON DELETE CASCADE,
                status TEXT NOT NULL DEFAULT 'pending',
                attempts INTEGER NOT NULL DEFAULT 0,
                next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                last_error TEXT,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
    conn.commit()


def enqueue_room(conn, room_id):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO osm_sync_jobs (
                room_id, status, attempts, next_attempt_at
            )
            VALUES (%s, 'pending', 0, NOW())
            ON CONFLICT (room_id) DO UPDATE
            SET status = 'pending',
                attempts = 0,
                next_attempt_at = NOW(),
                last_error = NULL,
                updated_at = NOW()
        """, (room_id,))
    conn.commit()


def fetch_pois(lat, lon, radius=1500):
    query = f"""
    [out:json][timeout:30];
    (
      nwr(around:{radius},{lat},{lon})["highway"="bus_stop"];
      nwr(around:{radius},{lat},{lon})["amenity"~"^(school|university|hospital)$"];
      nwr(around:{radius},{lat},{lon})["leisure"="park"];
    );
    out center;
    """

    errors = []

    for server in SERVERS:
        try:
            response = requests.post(
                server,
                data={"data": query},
                headers={
                    "User-Agent": "Tronhanh123-StudentProject/1.0"
                },
                timeout=(10, 45),
            )
            response.raise_for_status()
            return response.json().get("elements", [])
        except (requests.RequestException, ValueError) as exc:
            errors.append(f"{server}: {exc}")

    raise RuntimeError("; ".join(errors)[:1000])


def save_pois(conn, elements):
    inserted = 0

    with conn.cursor() as cur:
        for element in elements:
            tags = element.get("tags", {})
            lat = element.get("lat")
            lon = element.get("lon")

            if lat is None or lon is None:
                center = element.get("center") or {}
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

            cur.execute("""
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
            """, (
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
            ))

            inserted += cur.rowcount

    conn.commit()
    return inserted


def worker_loop(connect_db):
    while True:
        conn = None
        try:
            conn = connect_db()
            if conn is None:
                time.sleep(30)
                continue

            create_queue_table(conn)

            with conn.cursor() as cur:
                cur.execute("""
                    SELECT j.room_id, r.latitude, r.longitude,
                           j.attempts
                    FROM osm_sync_jobs j
                    JOIN rooms r ON r.id = j.room_id
                    WHERE j.status = 'pending'
                      AND j.next_attempt_at <= NOW()
                      AND r.status = 'da_duyet'
                      AND r.latitude IS NOT NULL
                      AND r.longitude IS NOT NULL
                    ORDER BY j.next_attempt_at
                    LIMIT 1
                """)
                job = cur.fetchone()

            if not job:
                time.sleep(30)
                continue

            room_id, lat, lon, attempts = job

            try:
                elements = fetch_pois(lat, lon)
                count = save_pois(conn, elements)

                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE osm_sync_jobs
                        SET status = 'done',
                            attempts = attempts + 1,
                            last_error = NULL,
                            updated_at = NOW()
                        WHERE room_id = %s
                    """, (room_id,))
                conn.commit()

                log.info(
                    "OSM room=%s downloaded=%s inserted=%s",
                    room_id, len(elements), count
                )

            except Exception as exc:
                conn.rollback()

                delay_minutes = min(
                    30 * (2 ** min(attempts, 4)),
                    480
                )

                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE osm_sync_jobs
                        SET attempts = attempts + 1,
                            next_attempt_at =
                                NOW() + (%s * INTERVAL '1 minute'),
                            last_error = %s,
                            updated_at = NOW()
                        WHERE room_id = %s
                    """, (
                        delay_minutes,
                        str(exc)[:1000],
                        room_id,
                    ))
                conn.commit()
                log.warning("OSM room=%s: %s", room_id, exc)

            time.sleep(10)

        except Exception:
            log.exception("OSM worker error")
            if conn:
                conn.rollback()
            time.sleep(30)
        finally:
            if conn:
                conn.close()


def start_worker(connect_db):
    global _worker_started

    with _worker_lock:
        if _worker_started:
            return

        _worker_started = True
        threading.Thread(
            target=worker_loop,
            args=(connect_db,),
            daemon=True,
            name="osm-sync-worker",
        ).start()
