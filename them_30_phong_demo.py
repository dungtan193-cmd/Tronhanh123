from database.connection import ket_noi_db

rooms = [
    ("Cầu Giấy", "Dịch Vọng Hậu", 3200000, 22),
    ("Cầu Giấy", "Mai Dịch", 2800000, 20),
    ("Cầu Giấy", "Quan Hoa", 3500000, 25),
    ("Cầu Giấy", "Nghĩa Tân", 3000000, 21),
    ("Cầu Giấy", "Trung Hòa", 4500000, 30),

    ("Đống Đa", "Chùa Láng", 3300000, 23),
    ("Đống Đa", "Khâm Thiên", 2700000, 19),
    ("Đống Đa", "Thái Hà", 4200000, 28),
    ("Đống Đa", "Phương Mai", 3100000, 22),
    ("Đống Đa", "Láng Hạ", 4000000, 27),

    ("Thanh Xuân", "Triều Khúc", 2200000, 18),
    ("Thanh Xuân", "Nguyễn Trãi", 2900000, 22),
    ("Thanh Xuân", "Khương Đình", 2500000, 20),
    ("Thanh Xuân", "Nhân Chính", 3800000, 27),
    ("Thanh Xuân", "Hạ Đình", 2600000, 21),

    ("Hai Bà Trưng", "Bạch Mai", 3000000, 22),
    ("Hai Bà Trưng", "Minh Khai", 3200000, 24),
    ("Hai Bà Trưng", "Trương Định", 2600000, 20),
    ("Hai Bà Trưng", "Đại La", 2800000, 21),
    ("Hai Bà Trưng", "Thanh Nhàn", 3500000, 25),

    ("Nam Từ Liêm", "Mỹ Đình", 3500000, 25),
    ("Nam Từ Liêm", "Phú Đô", 2700000, 21),
    ("Nam Từ Liêm", "Mễ Trì", 3800000, 28),
    ("Nam Từ Liêm", "Trung Văn", 3000000, 23),
    ("Nam Từ Liêm", "Đình Thôn", 3300000, 24),

    ("Bắc Từ Liêm", "Cổ Nhuế", 2400000, 20),
    ("Bắc Từ Liêm", "Đông Ngạc", 2200000, 19),
    ("Bắc Từ Liêm", "Xuân Đỉnh", 2800000, 23),
    ("Bắc Từ Liêm", "Phú Diễn", 2500000, 21),
    ("Bắc Từ Liêm", "Minh Khai", 2300000, 20),
]

conn = ket_noi_db()

if conn is None:
    raise RuntimeError("Không kết nối được PostgreSQL")

try:
    cur = conn.cursor()

    cur.execute("""
        SELECT id
        FROM users
        WHERE role = 'quan_tri'
        ORDER BY id
        LIMIT 1
    """)

    admin = cur.fetchone()

    if not admin:
        raise RuntimeError("Không tìm thấy tài khoản admin")

    admin_id = admin[0]
    inserted = 0
    skipped = 0

    for index, (district, area_name, price, area) in enumerate(rooms, 1):
        title = f"[DEMO-AI-89-{index:02d}] Phòng trọ {area_name}, {district}"

        cur.execute(
            "SELECT id FROM rooms WHERE title = %s LIMIT 1",
            (title,)
        )

        if cur.fetchone():
            skipped += 1
            continue

        address = f"{area_name}, {district}, Hà Nội"

        description = (
            "Dữ liệu giả lập phục vụ kiểm thử đồ án Tronhanh123. "
            "Không phải tin cho thuê thực tế."
        )

        cur.execute("""
            INSERT INTO rooms (
                user_id,
                title,
                address,
                district,
                price,
                area,
                description,
                status,
                created_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                'da_duyet', NOW()
            )
        """, (
            admin_id,
            title,
            address,
            district,
            price,
            area,
            description
        ))

        inserted += 1

    conn.commit()

    print("Them moi:", inserted)
    print("Bo qua vi da ton tai:", skipped)

    cur.execute("""
        SELECT COUNT(*)
        FROM rooms
        WHERE status = 'da_duyet'
          AND price > 0
          AND area > 0
    """)

    print("Tong phong hop le:", cur.fetchone()[0])

    cur.close()

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
