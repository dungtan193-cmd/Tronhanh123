import csv
from pathlib import Path

path = Path("du_lieu_phong_thuc_te.csv")

columns = [
    "title",
    "district",
    "address",
    "price",
    "area",
    "latitude",
    "longitude",
    "source_url",
    "verification_method",
    "verification_note",
]

if path.exists():
    print("File da ton tai, khong ghi de:", path)
else:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(columns)

    print("Da tao:", path)
