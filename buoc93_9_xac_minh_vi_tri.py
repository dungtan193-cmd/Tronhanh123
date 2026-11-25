import webbrowser
from urllib.parse import quote

from database.connection import ket_noi_db

def main():
    conn = ket_noi_db()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, district, address
                FROM ai_real_room_dataset
                WHERE location_verified = FALSE
                ORDER BY id
            """)

            rooms = cursor.fetchall()

        if not rooms:
            print("Khong co phong can xac minh.")
            return

        print("\n=== DANH SACH PHONG CAN XAC MINH ===")

        for room in rooms:
            room_id, title, district, address = room

            print("\nID:", room_id)
            print("Tieu de:", title)
            print("Quan:", district)
            print("Dia chi:", address)

            query = quote(f"{address}, {district}, Ha Noi")

            url = (
                "https://www.openstreetmap.org/search"
                f"?query={query}"
            )

            print("Ban do:", url)

            answer = input(
                "\nMo ban do de kiem tra? (y/n): "
            ).strip().lower()

            if answer == "y":
                webbrowser.open(url)

    finally:
        conn.close()

if __name__ == "__main__":
    main()
