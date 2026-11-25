import requests
import time

BASE = "http://localhost:8000"

print("=== BUOC 93.26: KIEM TRA AI TU DONG ===")

print("\n1. Kiem tra backend")
try:
    r = requests.get(BASE + "/api/health", timeout=10)
    r.raise_for_status()
    print("Backend:", r.status_code)
except Exception as exc:
    raise SystemExit(f"Backend chua san sang: {exc}")

print("\n2. Kiem tra AI")
r = requests.get(BASE + "/api/ai/live/status", timeout=30)
r.raise_for_status()
data = r.json()

print("Trang thai:", data.get("status"))
print("Du lieu hien hanh:", data.get("is_current"))
print("So phong AI:", data.get("total_rooms_in_database"))
print("Lan cap nhat:", data.get("updated_at"))

print("\n3. Kiem tra GIS")
r = requests.get(BASE + "/api/ai/gis/features", timeout=30)
r.raise_for_status()
gis = r.json()

print("So phong GIS:", gis.get("total_rooms"))
print("Du dieu kien huan luyen GIS:", gis.get("can_train_gis_model"))

print("\n4. Ket luan")

if data.get("status") == "ready" and data.get("is_current"):
    print("PASS: AI co ket qua hien hanh.")
else:
    print("WAIT: AI chua co ket qua hien hanh.")

print("Luu y: Can kiem thu sau thay doi du lieu de xac nhan auto refresh.")
print("\n=== HOAN THANH ===")
