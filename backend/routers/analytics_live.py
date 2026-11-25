from fastapi import APIRouter, HTTPException
from database.connection import ket_noi_db

router = APIRouter(
    prefix="/api/analytics/live",
    tags=["Live Analytics"]
)


@router.get("/dashboard")
def dashboard_truc_tiep():
    conn = ket_noi_db()

    if conn is None:
        raise HTTPException(
            status_code=503,
            detail="Không kết nối được PostgreSQL"
        )

    cursor = None

    try:
        cursor = conn.cursor()

        # Chỉ phân tích phòng đã được duyệt.
        cursor.execute("""
            SELECT
                id,
                title,
                address,
                COALESCE(NULLIF(TRIM(district), ''), 'Chưa xác định'),
                price,
                area,
                latitude,
                longitude,
                created_at
            FROM rooms
            WHERE status = 'da_duyet'
              AND price > 0
              AND area > 0
            ORDER BY id
        """)

        rows = cursor.fetchall()

        rooms = []

        for row in rows:
            price = float(row[4])
            area = float(row[5])

            rooms.append({
                "id": row[0],
                "title": row[1],
                "address": row[2],
                "district": row[3],
                "price": price,
                "area": area,
                "price_per_m2": round(price / area, 2),
                "latitude": row[6],
                "longitude": row[7],
                "created_at": (
                    row[8].isoformat()
                    if row[8] is not None else None
                )
            })

        if not rooms:
            return {
                "total_rooms": 0,
                "average_price": 0,
                "min_price": 0,
                "max_price": 0,
                "district_count": 0,
                "district_stats": [],
                "rooms": [],
                "source": "postgresql",
                "live": True
            }

        prices = [r["price"] for r in rooms]

        district_map = {}

        for room in rooms:
            district = room["district"]

            if district not in district_map:
                district_map[district] = {
                    "district": district,
                    "count": 0,
                    "total_price": 0
                }

            district_map[district]["count"] += 1
            district_map[district]["total_price"] += room["price"]

        district_stats = []

        for item in district_map.values():
            district_stats.append({
                "district": item["district"],
                "count": item["count"],
                "average_price": round(
                    item["total_price"] / item["count"], 2
                )
            })

        district_stats.sort(
            key=lambda item: (-item["count"], item["district"])
        )

        return {
            "total_rooms": len(rooms),
            "average_price": round(
                sum(prices) / len(prices), 2
            ),
            "min_price": min(prices),
            "max_price": max(prices),
            "district_count": len(district_stats),
            "district_stats": district_stats,
            "rooms": rooms,
            "source": "postgresql",
            "live": True
        }

    except Exception as e:
        print("Loi Live Analytics:", repr(e))
        raise HTTPException(
            status_code=500,
            detail="Không thể tính thống kê từ database"
        )

    finally:
        if cursor is not None:
            cursor.close()
        conn.close()
