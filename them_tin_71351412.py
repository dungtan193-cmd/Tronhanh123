import csv
from pathlib import Path

path = Path("du_lieu_phong_thuc_te.csv")

columns = [
    "title", "district", "address", "price", "area",
    "latitude", "longitude", "source_url",
    "verification_method", "verification_note"
]

url = "https://muaban.net/bat-dong-san/cho-thue-nha-tro-phong-tro-quan-dong-da-ha-noi/cho-thue-tap-the-tang-1-dh-thuy-loi-id71351412"

row = {
    "title": "Cho thuê tập thể tầng 1, ĐH Thuỷ Lợi",
    "district": "Đống Đa",
    "address": "Khu vực Đại học Thuỷ Lợi, Đống Đa, Hà Nội",
    "price": "8500000",
    "area": "60",
    "latitude": "",
    "longitude": "",
    "source_url": url,
    "verification_method": "",
    "verification_note": "Chưa xác minh địa chỉ và tọa độ chính xác"
}

existing = []

if path.exists():
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        existing = list(csv.DictReader(f))

if any(r.get("source_url") == url for r in existing):
    print("Tin đã tồn tại trong CSV.")
else:
    existing.append(row)

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(existing)

    print("Đã thêm tin vào CSV chờ xác minh.")
