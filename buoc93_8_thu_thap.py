import csv
import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

INPUT_FILE = Path("danh_sach_url_phong.txt")
OUTPUT_FILE = Path("du_lieu_phong_thuc_te.csv")
REVIEW_FILE = Path("reports/ai_gis/thu_thap_can_kiem_tra.csv")

COLUMNS = [
    "title", "district", "address", "price", "area",
    "latitude", "longitude", "source_url",
    "verification_method", "verification_note"
]

HEADERS = {
    "User-Agent": "Tronhanh123Research/1.0 (manual public-page review)"
}


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def find_jsonld(soup):
    results = []

    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or script.get_text())
        except (ValueError, TypeError):
            continue

        def walk(obj):
            if isinstance(obj, list):
                for item in obj:
                    walk(item)
            elif isinstance(obj, dict):
                results.append(obj)
                if "@graph" in obj:
                    walk(obj["@graph"])

        walk(data)

    return results


def extract_page(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20,
        allow_redirects=True,
    )
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()

    if "text/html" not in content_type:
        raise ValueError("URL không trả về trang HTML")

    soup = BeautifulSoup(response.text, "html.parser")

    title = ""
    address = ""
    price = ""
    area = ""

    og_title = soup.select_one('meta[property="og:title"]')

    if og_title:
        title = clean(og_title.get("content"))

    if not title and soup.title:
        title = clean(soup.title.get_text())

    for item in find_jsonld(soup):
        if not title:
            title = clean(item.get("name"))

        location = item.get("address")

        if isinstance(location, dict):
            address = address or clean(
                location.get("streetAddress")
            )
        elif isinstance(location, str):
            address = address or clean(location)

        offers = item.get("offers")

        if isinstance(offers, dict):
            raw_price = offers.get("price")
            currency = clean(offers.get("priceCurrency")).upper()

            if raw_price is not None and currency in ("VND", ""):
                price = clean(raw_price)

        floor_size = item.get("floorSize")

        if isinstance(floor_size, dict):
            unit = clean(floor_size.get("unitCode")).upper()
            value = floor_size.get("value")

            if value is not None and unit in ("MTK", "M2", ""):
                area = clean(value)

    return {
        "title": title,
        "district": "",
        "address": address,
        "price": price,
        "area": area,
        "latitude": "",
        "longitude": "",
        "source_url": response.url,
        "verification_method": "",
        "verification_note": "",
    }


def main():
    REVIEW_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not INPUT_FILE.exists():
        INPUT_FILE.write_text(
            "# Mỗi dòng là một URL tin đăng công khai\n",
            encoding="utf-8",
        )
        print("Đã tạo:", INPUT_FILE)
        print("Hãy thêm URL tin đăng rồi chạy lại.")
        return

    urls = [
        line.strip()
        for line in INPUT_FILE.read_text(
            encoding="utf-8-sig"
        ).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

    if not urls:
        print("Chưa có URL trong:", INPUT_FILE)
        return

    existing = []

    if OUTPUT_FILE.exists():
        with OUTPUT_FILE.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            reader = csv.DictReader(file)

            if reader.fieldnames != COLUMNS:
                raise ValueError(
                    "CSV hiện có không đúng cấu trúc. "
                    "Không ghi đè dữ liệu."
                )

            existing = list(reader)

    known_urls = {
        clean(row.get("source_url"))
        for row in existing
    }

    collected = []
    review = []

    for index, url in enumerate(dict.fromkeys(urls), start=1):
        print(f"[{index}/{len(urls)}] {url}")

        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            review.append({
                "source_url": url,
                "error": "URL không hợp lệ",
            })
            continue

        if url in known_urls:
            print("  Đã có trong CSV, bỏ qua.")
            continue

        try:
            row = extract_page(url)

            if row["source_url"] in known_urls:
                continue

            collected.append(row)
            known_urls.add(row["source_url"])

            print("  Đã lấy:", row["title"][:80])

        except Exception as exc:
            review.append({
                "source_url": url,
                "error": str(exc),
            })
            print("  Không lấy được:", exc)

        time.sleep(2)

    if collected:
        with OUTPUT_FILE.open(
            "a",
            encoding="utf-8-sig" if not OUTPUT_FILE.exists() else "utf-8",
            newline="",
        ) as file:
            writer = csv.DictWriter(file, fieldnames=COLUMNS)

            if not existing and file.tell() == 0:
                writer.writeheader()

            writer.writerows(collected)

    if review:
        with REVIEW_FILE.open(
            "w", encoding="utf-8-sig", newline=""
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=["source_url", "error"],
            )
            writer.writeheader()
            writer.writerows(review)

    print("\n=== KẾT QUẢ ===")
    print("Tin mới trích xuất:", len(collected))
    print("URL cần kiểm tra:", len(review))
    print("CSV:", OUTPUT_FILE)
    print("Báo cáo lỗi:", REVIEW_FILE)


if __name__ == "__main__":
    main()
