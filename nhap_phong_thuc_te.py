import csv
import math
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from database.connection import ket_noi_db

CSV_FILE = Path("du_lieu_phong_thuc_te.csv")

# Phạm vi kiểm tra sơ bộ quanh Hà Nội.
# Đây KHÔNG phải ranh giới hành chính chính xác.
LAT_MIN, LAT_MAX = 20.0, 22.0
LON_MIN, LON_MAX = 104.5, 107.0

REQUIRED = [
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

VALID_METHODS = {
    "listing_pin",
    "exact_address",
    "manual_verified",
}

def clean_text(value):
    return unicodedata.normalize(
        "NFC", str(value or "").strip()
    )

def normalized_key(value):
    value = clean_text(value).casefold()
    value = re.sub(r"\s+", " ", value)
    return value

def normalize_url(value):
    value = clean_text(value)
    parsed = urlparse(value)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("source_url phải là URL http/https hợp lệ")

    host = parsed.netloc.lower()

    # Bỏ các tham số theo dõi phổ biến.
    query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not k.lower().startswith("utm_")
        and k.lower() not in ("fbclid", "gclid")
    ]

    return urlunparse((
        parsed.scheme.lower(),
        host,
        parsed.path.rstrip("/") or "/",
        "",
        urlencode(query),
        "",
    ))

def parse_number(value, field):
    value = clean_text(value)

    if not value:
        raise ValueError(f"Thiếu {field}")

    try:
        result = float(value)
    except ValueError:
        raise ValueError(f"{field} không phải số hợp lệ")

    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{field} phải lớn hơn 0")

    return result

def parse_coordinate(value, field):
    value = clean_text(value)

    if not value:
        return None

    try:
        result = float(value)
    except ValueError:
        raise ValueError(f"{field} không hợp lệ")

    if not math.isfinite(result):
        raise ValueError(f"{field} không hữu hạn")

    return result

def validate_row(row, line_number):
    data = {
        key: clean_text(row.get(key))
        for key in REQUIRED
    }

    for field in ("title", "district", "address", "source_url"):
        if not data[field]:
            raise ValueError(f"Thiếu {field}")

    price = parse_number(data["price"], "price")
    area = parse_number(data["area"], "area")

    latitude = parse_coordinate(data["latitude"], "latitude")
    longitude = parse_coordinate(data["longitude"], "longitude")

    if (latitude is None) != (longitude is None):
        raise ValueError(
            "Phải nhập cả latitude và longitude, hoặc để trống cả hai"
        )

    if latitude is not None:
        if not (LAT_MIN <= latitude <= LAT_MAX):
            raise ValueError("latitude ngoài phạm vi kiểm tra Hà Nội")

        if not (LON_MIN <= longitude <= LON_MAX):
            raise ValueError("longitude ngoài phạm vi kiểm tra Hà Nội")

    source_url = normalize_url(data["source_url"])

    method = data["verification_method"].lower()
    note = data["verification_note"]

    if method and method not in VALID_METHODS:
        raise ValueError(
            "verification_method chỉ nhận: "
            + ", ".join(sorted(VALID_METHODS))
        )

    # Không tự động xác minh chỉ vì người dùng nhập tọa độ.
    # Phải có phương pháp và ghi chú về nguồn bằng chứng.
    verified = bool(
        latitude is not None
        and method in VALID_METHODS
        and len(note) >= 10
    )

    return {
        "line": line_number,
        "title": data["title"],
        "district": data["district"],
        "address": data["address"],
        "price": price,
        "area": area,
        "latitude": latitude,
        "longitude": longitude,
        "source_url": source_url,
        "verification_method": method or None,
        "verification_note": note or None,
        "location_verified": verified,
    }

def read_csv():
    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy {CSV_FILE.resolve()}"
        )

    with CSV_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        missing = [
            field for field in REQUIRED
            if field not in (reader.fieldnames or [])
        ]

        if missing:
            raise ValueError(
                "CSV thiếu các cột: " + ", ".join(missing)
            )

        valid = []
        invalid = []
        seen_urls = set()
        seen_listings = set()

        for line_number, row in enumerate(reader, start=2):
            try:
                item = validate_row(row, line_number)

                url_key = item["source_url"]
                listing_key = (
                    normalized_key(item["address"]),
                    normalized_key(item["title"]),
                    round(item["area"], 2),
                )

                if url_key in seen_urls:
                    raise ValueError("Trùng source_url trong CSV")

                if listing_key in seen_listings:
                    raise ValueError("Trùng phòng trong CSV")

                seen_urls.add(url_key)
                seen_listings.add(listing_key)
                valid.append(item)

            except Exception as error:
                invalid.append({
                    "line": line_number,
                    "error": str(error),
                })

    return valid, invalid

def ensure_table(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_real_room_dataset (
                id BIGSERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                district VARCHAR(100) NOT NULL,
                address TEXT NOT NULL,
                price NUMERIC(14,2) NOT NULL CHECK (price > 0),
                area NUMERIC(10,2) NOT NULL CHECK (area > 0),
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                source_url TEXT NOT NULL,
                collected_at TIMESTAMPTZ DEFAULT NOW(),
                location_verified BOOLEAN NOT NULL DEFAULT FALSE,
                verification_method TEXT,
                verification_note TEXT,
                CONSTRAINT valid_latitude CHECK (
                    latitude IS NULL OR latitude BETWEEN -90 AND 90
                ),
                CONSTRAINT valid_longitude CHECK (
                    longitude IS NULL OR longitude BETWEEN -180 AND 180
                )
            )
        """)

def existing_keys(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT source_url, address, title, area
            FROM ai_real_room_dataset
        """)
        rows = cursor.fetchall()

    urls = set()
    listings = set()

    for url, address, title, area in rows:
        try:
            urls.add(normalize_url(url))
        except ValueError:
            urls.add(clean_text(url))

        listings.add((
            normalized_key(address),
            normalized_key(title),
            round(float(area), 2),
        ))

    return urls, listings

def main():
    apply_changes = "--apply" in sys.argv

    valid, invalid = read_csv()

    print("\n=== KIEM TRA CSV ===")
    print("Ban ghi hop le:", len(valid))
    print("Ban ghi loi:", len(invalid))
    print(
        "Co toa do va khai bao bang chung:",
        sum(item["location_verified"] for item in valid),
    )

    for item in invalid[:30]:
        print(
            f"Dong {item['line']}: {item['error']}"
        )

    if invalid:
        print("\nCó dòng lỗi. Hãy sửa CSV trước khi nhập.")
        return

    if not valid:
        print("\nCSV chưa có phòng. Không có gì để nhập.")
        return

    conn = ket_noi_db()

    if conn is None:
        raise RuntimeError("Không kết nối được PostgreSQL")

    try:
        ensure_table(conn)

        urls, listings = existing_keys(conn)

        new_items = []
        duplicates = []

        for item in valid:
            listing_key = (
                normalized_key(item["address"]),
                normalized_key(item["title"]),
                round(item["area"], 2),
            )

            if (
                item["source_url"] in urls
                or listing_key in listings
            ):
                duplicates.append(item)
            else:
                new_items.append(item)
                urls.add(item["source_url"])
                listings.add(listing_key)

        print("\n=== KIEM TRA DATABASE ===")
        print("Phong moi:", len(new_items))
        print("Phong da ton tai:", len(duplicates))

        if not apply_changes:
            conn.rollback()
            print("\nCHE DO XEM TRUOC: Chua ghi vao database.")
            print(
                "Neu du lieu dung, chay: "
                "python nhap_phong_thuc_te.py --apply"
            )
            return

        with conn.cursor() as cursor:
            for item in new_items:
                cursor.execute("""
                    INSERT INTO ai_real_room_dataset (
                        title,
                        district,
                        address,
                        price,
                        area,
                        latitude,
                        longitude,
                        source_url,
                        location_verified,
                        verification_method,
                        verification_note
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s
                    )
                """, (
                    item["title"],
                    item["district"],
                    item["address"],
                    item["price"],
                    item["area"],
                    item["latitude"],
                    item["longitude"],
                    item["source_url"],
                    item["location_verified"],
                    item["verification_method"],
                    item["verification_note"],
                ))

        conn.commit()
        print("\nDA NHAP:", len(new_items), "phong")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    main()
