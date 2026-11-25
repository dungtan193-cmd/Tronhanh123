BEGIN;

CREATE TABLE IF NOT EXISTS room_seed_batches (
    room_id INTEGER PRIMARY KEY REFERENCES rooms(id) ON DELETE CASCADE,
    batch_code TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

WITH university_locations(name, district, address_area, lat, lon) AS (
    VALUES
    ('Đại học Bách khoa Hà Nội', 'Hai Bà Trưng', 'Tạ Quang Bửu', 21.0055::float8, 105.8435::float8),
    ('Đại học Kinh tế Quốc dân', 'Hai Bà Trưng', 'Trần Đại Nghĩa', 20.9995, 105.8455),
    ('Đại học Thủy lợi', 'Đống Đa', 'Tây Sơn', 21.0075, 105.8245),
    ('Đại học Y Hà Nội', 'Đống Đa', 'Tôn Thất Tùng', 20.9975, 105.8275),
    ('Đại học Sư phạm Hà Nội', 'Cầu Giấy', 'Xuân Thủy', 21.0375, 105.7845),
    ('Đại học Quốc gia Hà Nội', 'Cầu Giấy', 'Xuân Thủy', 21.0385, 105.7815),
    ('Đại học Công nghiệp Hà Nội', 'Bắc Từ Liêm', 'Cầu Diễn', 21.0545, 105.7355),
    ('Học viện Công nghệ Bưu chính Viễn thông', 'Hà Đông', 'Trần Phú', 20.9805, 105.7885),
    ('Học viện Nông nghiệp Việt Nam', 'Gia Lâm', 'Trâu Quỳ', 21.0065, 105.9365),
    ('Đại học Thương mại', 'Cầu Giấy', 'Hồ Tùng Mậu', 21.0365, 105.7755)
),
numbered AS (
    SELECT
        row_number() OVER (ORDER BY name)::int AS school_no,
        name,
        district,
        address_area,
        lat,
        lon
    FROM university_locations
),
generated AS (
    SELECT
        n.school_no,
        g.room_no,
        n.name,
        n.district,
        n.address_area,
        n.lat + CASE WHEN g.room_no = 1 THEN 0.0015 ELSE -0.0018 END AS latitude,
        n.lon + CASE WHEN g.room_no = 1 THEN 0.0012 ELSE -0.0015 END AS longitude,
        (1800000 + ((n.school_no * 317 + g.room_no * 593) % 38) * 100000)::numeric(12,2) AS price,
        (16 + ((n.school_no * 7 + g.room_no * 11) % 20))::numeric(8,2) AS area
    FROM numbered n
    CROSS JOIN generate_series(1, 2) AS g(room_no)
),
inserted AS (
    INSERT INTO rooms (
        user_id,
        title,
        address,
        district,
        price,
        area,
        description,
        image,
        status,
        latitude,
        longitude
    )
    SELECT
        5,
        'Phòng trọ gần ' || name || ' - căn ' || room_no,
        'Khu vực ' || address_area || ', ' || district || ', Hà Nội',
        district,
        price,
        area,
        'Phòng khép kín, có khu vệ sinh riêng, phù hợp sinh viên và người đi làm. Liên hệ để cập nhật thông tin.',
        NULL,
        'da_duyet',
        latitude,
        longitude
    FROM generated
    RETURNING id
)
INSERT INTO room_seed_batches (room_id, batch_code)
SELECT id, 'HN_UNIVERSITY_20_20261122'
FROM inserted;

COMMIT;

SELECT
    r.id,
    r.title,
    r.district,
    r.price,
    r.area,
    r.latitude,
    r.longitude
FROM rooms r
JOIN room_seed_batches b ON b.room_id = r.id
WHERE b.batch_code = 'HN_UNIVERSITY_20_20261122'
ORDER BY r.id;
