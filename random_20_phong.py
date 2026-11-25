import random
import subprocess

random.seed(20261122)

# 20 tiêu đề và địa chỉ đa dạng quanh các khu đại học Hà Nội
rooms = [
    ("Trọ giá rẻ khu Bách Khoa", "Ngõ 40 Tạ Quang Bửu", "Hai Bà Trưng"),
    ("Phòng trọ khép kín phố Lê Thanh Nghị", "Ngõ 75 Lê Thanh Nghị", "Hai Bà Trưng"),
    ("Phòng trọ sinh viên gần Kinh tế Quốc dân", "Ngõ 91 Trần Đại Nghĩa", "Hai Bà Trưng"),
    ("Trọ giá tốt khu Minh Khai", "Ngõ 254 Minh Khai", "Hai Bà Trưng"),
    ("Phòng trọ gần Đại học Thủy lợi", "Ngõ 95 Chùa Bộc", "Đống Đa"),
    ("Trọ sinh viên khu Tây Sơn", "Ngõ 167 Tây Sơn", "Đống Đa"),
    ("Phòng trọ khép kín Tôn Thất Tùng", "Ngõ 43 Tôn Thất Tùng", "Đống Đa"),
    ("Trọ giá rẻ gần Đại học Y Hà Nội", "Ngõ 1 Phương Mai", "Đống Đa"),
    ("Phòng trọ sinh viên Cầu Giấy", "Ngõ 255 Cầu Giấy", "Cầu Giấy"),
    ("Trọ khép kín khu Xuân Thủy", "Ngõ 181 Xuân Thủy", "Cầu Giấy"),
    ("Phòng trọ giá tốt Mai Dịch", "Ngõ 20 Hồ Tùng Mậu", "Cầu Giấy"),
    ("Trọ sinh viên gần Đại học Thương mại", "Ngõ 136 Hồ Tùng Mậu", "Cầu Giấy"),
    ("Phòng trọ khép kín Cầu Diễn", "Ngõ 120 Cầu Diễn", "Bắc Từ Liêm"),
    ("Trọ giá rẻ khu Nhổn", "Ngõ 67 Nhổn", "Bắc Từ Liêm"),
    ("Phòng trọ sinh viên Phú Diễn", "Ngõ 58 Phú Diễn", "Bắc Từ Liêm"),
    ("Trọ khép kín gần Đại học Công nghiệp", "Ngõ 32 Cầu Diễn", "Bắc Từ Liêm"),
    ("Phòng trọ giá rẻ Hà Đông", "Ngõ 45 Trần Phú", "Hà Đông"),
    ("Trọ sinh viên khu Văn Quán", "Ngõ 19 Nguyễn Khuyến", "Hà Đông"),
    ("Phòng trọ gần Học viện Nông nghiệp", "Ngõ 56 Trâu Quỳ", "Gia Lâm"),
    ("Trọ khép kín khu Trâu Quỳ", "Ngõ 18 Ngô Xuân Quảng", "Gia Lâm"),
]

random.shuffle(rooms)

def quote(value):
    return "'" + value.replace("'", "''") + "'"

batch = "HN_UNIVERSITY_20_20261122"

sql = [
    "BEGIN;",
    "SET client_encoding = 'UTF8';"
]

for index, (title, address, district) in enumerate(rooms):
    full_address = f"{address}, {district}, Hà Nội"

    sql.append(f"""
UPDATE rooms
SET
    title = {quote(title)},
    address = {quote(full_address)},
    district = {quote(district)}
WHERE id = (
    SELECT r.id
    FROM rooms r
    JOIN room_seed_batches b ON b.room_id = r.id
    WHERE b.batch_code = {quote(batch)}
    ORDER BY r.id
    OFFSET {index} LIMIT 1
);
""")

sql.append("COMMIT;")

result = subprocess.run(
    [
        "docker", "exec", "-i",
        "postgres_db",
        "psql",
        "-v", "ON_ERROR_STOP=1",
        "-U", "postgres",
        "-d", "tronhanh123"
    ],
    input="\n".join(sql).encode("utf-8"),
    capture_output=True
)

print(result.stdout.decode("utf-8", errors="replace"))
print(result.stderr.decode("utf-8", errors="replace"))

if result.returncode != 0:
    raise SystemExit("CAP NHAT THAT BAI")

print("DA DOI TEN VA DIA CHI CHO 20 PHONG")
