import requests
import pandas as pd

API = "http://localhost:8000/api/ai/gis/features"

response = requests.get(API, timeout=30)
response.raise_for_status()

data = response.json()
df = pd.DataFrame(data["rooms"])

print("\n=== TONG QUAN ===")
print("So phong GIS:", len(df))
print("So cot:", len(df.columns))

print("\n=== DU LIEU THIEU ===")
print(df.isnull().sum().to_string())

print("\n=== KIEM TRA TOA DO ===")
invalid = df[
    ~df["latitude"].between(20, 22)
    | ~df["longitude"].between(105, 107)
]

print("So phong co toa do ngoai khu vuc kiem tra:", len(invalid))

print("\n=== THONG KE GIS ===")
columns = [
    "nearest_university_m",
    "bus_stops_1km",
    "schools_1km",
    "hospitals_1km",
    "parks_1km",
]

print(df[columns].describe().to_string())

print("\n=== KIEM TRA PHONG TRUNG ===")
print("So room_id trung:", df["room_id"].duplicated().sum())

print("\n=== KET LUAN ===")
if len(df) < 30:
    print("CHUA DU DU LIEU DE HUAN LUYEN GIS AI.")
    print("Giu nguyen mo hinh AI hien tai.")
else:
    print("Da dat nguong so luong toi thieu.")
    print("Van can danh gia chat luong du lieu va cross-validation.")
