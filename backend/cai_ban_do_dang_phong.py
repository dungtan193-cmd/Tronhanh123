from pathlib import Path
from datetime import datetime
import re
import shutil

ROOT = Path(r"D:\baicuoiki")
SRC = ROOT / "frontend" / "src"
COMPONENTS = SRC / "components"

COMPONENTS.mkdir(parents=True, exist_ok=True)

component_path = COMPONENTS / "BanDoChonViTri.jsx"

component_code = r'''
import { useEffect, useRef, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  useMap,
  useMapEvents
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const HANOI = [21.0285, 105.8542];

const markerIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});

function MapController({ position }) {
  const map = useMap();

  useEffect(() => {
    if (position) {
      map.flyTo(
        [position.latitude, position.longitude],
        17,
        { duration: 1.2 }
      );
    }
  }, [map, position?.latitude, position?.longitude]);

  return null;
}

function Pin({ position, onChange }) {
  useMapEvents({
    click(e) {
      onChange({
        latitude: e.latlng.lat,
        longitude: e.latlng.lng
      });
    }
  });

  if (!position) return null;

  return (
    <Marker
      position={[position.latitude, position.longitude]}
      icon={markerIcon}
      draggable
      eventHandlers={{
        dragend(e) {
          const p = e.target.getLatLng();

          onChange({
            latitude: p.lat,
            longitude: p.lng
          });
        }
      }}
    />
  );
}

export default function BanDoChonViTri({
  address = "",
  value = null,
  onChange
}) {
  const [position, setPosition] = useState(value);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const requestId = useRef(0);

  useEffect(() => {
    setPosition(value);
  }, [value?.latitude, value?.longitude]);

  useEffect(() => {
    requestId.current += 1;
    setResults([]);
    setMessage("");
  }, [address]);

  function choosePosition(point) {
    const selected = {
      latitude: Number(point.latitude),
      longitude: Number(point.longitude)
    };

    setPosition(selected);
    setResults([]);
    setMessage("Đã chọn vị trí. Bạn có thể kéo ghim để chỉnh lại.");
    onChange?.(selected);
  }

  async function searchAddress() {
    const q = address.trim();

    if (!q) {
      setMessage("Vui lòng nhập địa chỉ.");
      return;
    }

    const current = ++requestId.current;

    setLoading(true);
    setResults([]);
    setMessage("");

    try {
      const params = new URLSearchParams({
        q,
        format: "jsonv2",
        limit: "5",
        countrycodes: "vn"
      });

      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?${params}`
      );

      if (!response.ok) {
        throw new Error("Không thể tìm địa chỉ.");
      }

      const data = await response.json();

      if (current !== requestId.current) return;

      if (!data.length) {
        setMessage("Không tìm thấy địa chỉ. Hãy nhập thêm quận và thành phố.");
        return;
      }

      const locations = data.map(item => ({
        name: item.display_name,
        latitude: Number(item.lat),
        longitude: Number(item.lon)
      }));

      setResults(locations);

      // Chỉ di chuyển bản đồ, chưa lưu ghim chính thức
      setPosition({
        latitude: locations[0].latitude,
        longitude: locations[0].longitude
      });

      setMessage("Đã tìm thấy. Hãy chọn kết quả phù hợp.");
    } catch (error) {
      if (current === requestId.current) {
        setMessage(error.message);
      }
    } finally {
      if (current === requestId.current) {
        setLoading(false);
      }
    }
  }

  return (
    <div style={{ marginTop: 14 }}>
      <button
        type="button"
        onClick={searchAddress}
        disabled={loading}
        style={{
          background: "#2563eb",
          color: "#fff",
          padding: "10px 16px",
          border: "none",
          borderRadius: 8,
          cursor: "pointer"
        }}
      >
        {loading ? "Đang tìm..." : "🔍 Tìm địa chỉ trên bản đồ"}
      </button>

      {message && <p>{message}</p>}

      {results.map((item, index) => (
        <button
          key={index}
          type="button"
          onClick={() => choosePosition(item)}
          style={{
            display: "block",
            width: "100%",
            textAlign: "left",
            padding: 10,
            marginTop: 6,
            border: "1px solid #ddd",
            borderRadius: 6,
            background: "#f8fafc",
            cursor: "pointer"
          }}
        >
          {item.name}
        </button>
      ))}

      <div style={{ marginTop: 12 }}>
        <MapContainer
          center={
            position
              ? [position.latitude, position.longitude]
              : HANOI
          }
          zoom={position ? 16 : 12}
          style={{
            height: 380,
            width: "100%",
            borderRadius: 12
          }}
        >
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapController position={position} />

          <Pin
            position={position}
            onChange={choosePosition}
          />
        </MapContainer>
      </div>

      {position && (
        <p>
          Vĩ độ: {position.latitude.toFixed(6)}
          {" | "}
          Kinh độ: {position.longitude.toFixed(6)}
        </p>
      )}
    </div>
  );
}
'''

component_path.write_text(component_code, encoding="utf-8")

print("DA TAO:", component_path)

# Tim form dang phong hien co
candidates = []

for path in SRC.rglob("*"):
    if path.suffix not in (".jsx", ".tsx"):
        continue

    if path == component_path:
        continue

    text = path.read_text(
        encoding="utf-8-sig",
        errors="replace"
    )

    lower = text.lower()

    score = 0

    if "đăng phòng" in lower or "đăng tin" in lower:
        score += 3

    if "formdata" in lower:
        score += 2

    if "address" in lower:
        score += 2

    if "latitude" in lower or "longitude" in lower:
        score += 1

    if "room" in path.name.lower():
        score += 1

    if score >= 5:
        candidates.append((score, path))

candidates.sort(key=lambda x: -x[0])

print("\n===== FILE FORM TIM THAY =====")

for score, path in candidates:
    print(score, path.relative_to(ROOT))

if len(candidates) != 1:
    print("\nCHUA TU DONG SUA FORM:")
    print("Can xac dinh chinh xac file de tranh pha code cu.")
    print("Component ban do da duoc tao.")
    raise SystemExit(0)

form_path = candidates[0][1]

print("\nFILE FORM:", form_path.relative_to(ROOT))

# Khong sua JSX bang regex khi chua biet cau truc state,
# vi co the lam hong form dang phong hien tai.
print("Can kiem tra cau truc JSX truoc khi noi state va submit.")
print("Khong co file cu nao bi ghi de.")
