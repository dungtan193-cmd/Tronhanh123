import subprocess

BATCH = "HN_UNIVERSITY_20_20261122"

schools = [
    ("Đại học Bách khoa Hà Nội", "Tạ Quang Bửu", "Hai Bà Trưng"),
    ("Đại học Kinh tế Quốc dân", "Trần Đại Nghĩa", "Hai Bà Trưng"),
    ("Đại học Thủy lợi", "Tây Sơn", "Đống Đa"),
    ("Đại học Y Hà Nội", "Tôn Thất Tùng", "Đống Đa"),
    ("Đại học Sư phạm Hà Nội", "Xuân Thủy", "Cầu Giấy"),
    ("Đại học Quốc gia Hà Nội", "Xuân Thủy", "Cầu Giấy"),
    ("Đại học Công nghiệp Hà Nội", "Cầu Diễn", "Bắc Từ Liêm"),
    ("Học viện Công nghệ Bưu chính Viễn thông", "Trần Phú", "Hà Đông"),
    ("Học viện Nông nghiệp Việt Nam", "Trâu Quỳ", "Gia Lâm"),
    ("Đại học Thương mại", "Hồ Tùng Mậu", "Cầu Giấy"),
]

def quote(value):
    return "'" + value.replace("'", "''") + "'"

sql = [
    "BEGIN;",
    "SET client_encoding = 'UTF8';"
]

for name, street, district in schools:
    for number in (1, 2):
        title = f"Phòng trọ gần {name} - căn {number}"
        address = f"Khu vực {street}, {district}, Hà Nội"
        description = (
            "Phòng trọ gần khu vực trường đại học, "
            "phù hợp sinh viên và người đi làm. "
            "Liên hệ để biết thêm thông tin."
        )

        sql.append(f"""
UPDATE rooms
SET
    title = {quote(title)},
    address = {quote(address)},
    district = {quote(district)},
    description = {quote(description)}
WHERE id = (
    SELECT r.id
    FROM rooms r
    JOIN room_seed_batches b ON b.room_id = r.id
    WHERE b.batch_code = {quote(BATCH)}
      AND r.title LIKE {quote('%căn ' + str(number))}
    ORDER BY r.id
    LIMIT 1 OFFSET 0
);
""")

# Sửa theo thứ tự ID của đúng 20 phòng trong batch.
sql = ["BEGIN;", "SET client_encoding = 'UTF8';"]

for i, (name, street, district) in enumerate(schools):
    for number in (1, 2):
        position = i * 2 + number - 1

        title = f"Phòng trọ gần {name} - căn {number}"
        address = f"Khu vực {street}, {district}, Hà Nội"
        description = (
            "Phòng trọ gần trường đại học, phù hợp sinh viên "
            "và người đi làm. Liên hệ để biết thêm thông tin."
        )

        sql.append(f"""
UPDATE rooms
SET
    title = {quote(title)},
    address = {quote(address)},
    district = {quote(district)},
    description = {quote(description)}
WHERE id = (
    SELECT r.id
    FROM rooms r
    JOIN room_seed_batches b ON b.room_id = r.id
    WHERE b.batch_code = {quote(BATCH)}
    ORDER BY r.id
    OFFSET {position} LIMIT 1
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
    raise SystemExit("Sửa dữ liệu thất bại.")

print("ĐÃ SỬA TIẾNG VIỆT CHO 20 PHÒNG.")

