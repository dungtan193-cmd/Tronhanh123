import requests

BASE = "http://localhost:8000"

endpoints = {
    "GIS": "/api/ai/gis/features",
    "Dashboard": "/api/analytics/live/dashboard",
    "AI": "/api/ai/live/status",
}

print("\n=== KIEM TRA HE THONG TU DONG ===")

for name, path in endpoints.items():
    try:
        response = requests.get(BASE + path, timeout=30)
        print(f"\n{name}: HTTP {response.status_code}")

        if response.ok:
            data = response.json()

            if name == "GIS":
                print("So phong GIS:", data.get("total_rooms"))
                print("So phong trong danh sach:", len(data.get("rooms", [])))

            elif name == "Dashboard":
                print("Cac truong du lieu:", list(data.keys()))
                print("So phong:", len(data.get("rooms", [])))

            elif name == "AI":
                print("Trang thai:", data.get("status"))
                print("Du lieu moi nhat:", data.get("is_current"))
                print("Cap nhat luc:", data.get("updated_at"))
        else:
            print("Loi:", response.text[:300])

    except Exception as exc:
        print("Khong ket noi duoc:", exc)

print("\n=== KET THUC KIEM TRA ===")
