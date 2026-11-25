import BanDoChonViTri from "./components/BanDoChonViTri";
import GISAnalysis from './pages/GISAnalysis'

import { useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polygon, Polyline, useMap, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import './App.css'
import DashboardAI from './DashboardAI'
import RentPricePredictor from './RentPricePredictor'

const API = 'http://localhost:8000'

const HA_NOI = [21.0285, 105.8542]
const ESRI_TILES = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}'
const ESRI_ATTRIBUTION = 'Tiles &copy; Esri &mdash; Source: Esri, HERE, Garmin, OpenStreetMap contributors, and the GIS user community'

// Ghim tự vẽ bằng CSS/SVG, không phụ thuộc vào CDN ảnh marker.
const GHIM = L.divIcon({
  className: 'tronhanh-map-pin',
  html: '<span style="display:block;width:24px;height:24px;background:#e11d48;border:3px solid white;border-radius:50% 50% 50% 0;transform:rotate(-45deg);box-shadow:0 2px 8px #0006"></span>',
  iconSize: [30, 34],
  iconAnchor: [15, 30],
})

function SuKienChonViTri({ onChange }) {
  useMapEvents({ click(event) { onChange(event.latlng.lat, event.latlng.lng) } })
  return null
}

const coToaDoHopLe = (phong) => {
  if (phong.latitude === null || phong.latitude === undefined || phong.latitude === '' ||
      phong.longitude === null || phong.longitude === undefined || phong.longitude === '') return false
  const lat = Number(phong.latitude)
  const lng = Number(phong.longitude)
  return Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180
}


// Bản đồ chọn tọa độ cho cả đăng tin và chỉnh sửa tin.
function BanDoChonViTriCu({ latitude, longitude, onChange }) {
  const hasPosition = latitude !== '' && latitude != null && longitude !== '' && longitude != null &&
    Number.isFinite(Number(latitude)) && Number.isFinite(Number(longitude))
  const position = hasPosition ? [Number(latitude), Number(longitude)] : null
  return (
    <div style={{ margin: '12px 0 18px' }}>
      <p style={{ marginBottom: 8, color: '#475569', fontSize: 14 }}>
        Nhấp vào bản đồ để chọn vị trí phòng trọ. Kéo ghim để điều chỉnh.
      </p>
      <MapContainer key={hasPosition ? 'selected' : 'empty'} center={position || HA_NOI}
        zoom={hasPosition ? 15 : 11} scrollWheelZoom style={{ height: 300, width: '100%', borderRadius: 10, zIndex: 0 }}>
        <TileLayer attribution={ESRI_ATTRIBUTION} url={ESRI_TILES} maxZoom={19} />
        <SuKienChonViTri onChange={onChange} />
        {position && <Marker position={position} icon={GHIM} draggable
          eventHandlers={{ dragend: (event) => {
            const point = event.target.getLatLng()
            onChange(point.lat, point.lng)
          } }} />}
      </MapContainer>
      <p style={{ margin: '9px 0', fontSize: 13, color: hasPosition ? '#166534' : '#92400e' }}>
        {hasPosition ? `Đã chọn: ${Number(latitude).toFixed(6)}, ${Number(longitude).toFixed(6)}` : 'Chưa chọn vị trí trên bản đồ.'}
      </p>
    </div>
  )
}

const mediaUrl = (path) => {
  if (!path) return ''
  if (/^https?:\/\//i.test(path)) return path
  return `${API}${path.startsWith('/') ? '' : '/'}${path}`
}

const tien = (value) =>
  Number(value || 0).toLocaleString('vi-VN') + ' VNĐ'

const giaTrieu = (value) =>
  (Number(value || 0) / 1000000).toFixed(1) + ' triệu/tháng'

const styles = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(15,23,42,.72)',
    zIndex: 9999,
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 15,
  },
  modal: {
    background: '#fff',
    color: '#1f2937',
    borderRadius: 14,
    width: 'min(920px, 100%)',
    maxHeight: '94vh',
    overflowY: 'auto',
    padding: 24,
    position: 'relative',
  },
  close: {
    position: 'absolute',
    right: 15,
    top: 12,
    border: 0,
    background: '#f1f5f9',
    borderRadius: '50%',
    width: 35,
    height: 35,
    fontSize: 24,
    cursor: 'pointer',
    zIndex: 2,
  },
  button: {
    border: 0,
    borderRadius: 8,
    padding: '10px 16px',
    background: '#2563eb',
    color: 'white',
    cursor: 'pointer',
  },
  input: {
    width: '100%',
    padding: 11,
    border: '1px solid #d1d5db',
    borderRadius: 7,
    margin: '6px 0 14px',
    boxSizing: 'border-box',
  },
}


// BƯỚC 85.7: Tiện ích GIS từ PostGIS / OpenStreetMap.
const NHAN_POI_GIS = {
  university: '🎓 Đại học', hospital: '🏥 Bệnh viện',
  bus_stop: '🚌 Trạm xe buýt', park: '🌳 Công viên', school: '🏫 Trường học',
}
const MAU_POI_GIS = {
  university: '#2563eb', hospital: '#dc2626', bus_stop: '#ea580c',
  park: '#16a34a', school: '#7c3aed',
}
const dinhDangKhoangCachGIS = (met) => {
  const n = Number(met)
  if (!Number.isFinite(n)) return 'Chưa rõ khoảng cách'
  return n >= 1000 ? `${(n / 1000).toFixed(2)} km` : `${Math.round(n)} m`
}

function DieuHuongBanDoGIS({ diemDuocChon }) {
  const map = useMap()
  useEffect(() => {
    if (!diemDuocChon) return
    const lat = Number(diemDuocChon.latitude)
    const lng = Number(diemDuocChon.longitude)
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return
    map.flyTo([lat, lng], Math.max(map.getZoom(), 17), { duration: 0.7 })
  }, [map, diemDuocChon])
  return null
}

const tenPOIGIS = (poi) => {
  const ten = typeof poi.name === 'string' ? poi.name.trim() : ''
  return ten || `${(NHAN_POI_GIS[poi.category] || '📌 Tiện ích').replace(/^[^\p{L}\p{N}]+/u, '')} (chưa có tên)`
}

function TienIchGIS({ phong }) {
  const [tomTat, setTomTat] = useState(null)
  const [diemGan, setDiemGan] = useState([])
  const [dangTai, setDangTai] = useState(true)
  const [loi, setLoi] = useState('')
  const [loaiLoc, setLoaiLoc] = useState('all')
  const [diemDuocChon, setDiemDuocChon] = useState(null)

  // B??C 93.58: T? c?p nh?t ti?n ?ch sau khi OSM ??ng b?.
  useEffect(() => {
    const controller = new AbortController()
    let dangChay = false

    setDangTai(true)
    setTomTat(null)
    setDiemGan([])
    setLoi('')
    setLoaiLoc('all')
    setDiemDuocChon(null)

    const taiGIS = async () => {
      if (dangChay || controller.signal.aborted) return
      dangChay = true

      try {
        const [resTomTat, resDiemGan] = await Promise.all([
          fetch(`${API}/api/gis/rooms/${phong.id}/summary`, {
            signal: controller.signal,
            cache: 'no-store',
          }),
          fetch(`${API}/api/gis/rooms/${phong.id}/nearby?radius_m=1000&limit=200`, {
            signal: controller.signal,
            cache: 'no-store',
          }),
        ])

        const [jsonTomTat, jsonDiemGan] = await Promise.all([
          resTomTat.json(),
          resDiemGan.json(),
        ])

        if (!resTomTat.ok || jsonTomTat.status !== 'success') {
          throw new Error(
            jsonTomTat.detail || 'Kh?ng t?i ???c th?ng k? GIS.'
          )
        }

        if (!resDiemGan.ok || jsonDiemGan.status !== 'success') {
          throw new Error(
            jsonDiemGan.detail || 'Kh?ng t?i ???c ti?n ?ch g?n ph?ng.'
          )
        }

        if (controller.signal.aborted) return

        setTomTat(jsonTomTat.data)
        setDiemGan(
          Array.isArray(jsonDiemGan.data) ? jsonDiemGan.data : []
        )
        setLoi('')
      } catch (err) {
        if (!controller.signal.aborted) {
          setLoi(String(err.message || 'Kh?ng k?t n?i ???c API GIS.'))
        }
      } finally {
        dangChay = false
        if (!controller.signal.aborted) setDangTai(false)
      }
    }

    taiGIS()

    // L?m m?i m?i 30 gi?y khi chi ti?t ph?ng ?ang m?.
    const intervalId = setInterval(taiGIS, 30000)

    return () => {
      clearInterval(intervalId)
      controller.abort()
    }
  }, [phong.id])

  const toaDoPhong = tomTat && Number.isFinite(Number(tomTat.latitude)) &&
    Number.isFinite(Number(tomTat.longitude))
    ? [Number(tomTat.latitude), Number(tomTat.longitude)] : null
  const danhSachHienThi = loaiLoc === 'all'
    ? diemGan : diemGan.filter((poi) => poi.category === loaiLoc)
  const chonLoaiGIS = (loai) => { setLoaiLoc(loai); setDiemDuocChon(null) }
  const toaDoPOI = danhSachHienThi.filter((poi) =>
    poi.latitude != null && poi.longitude != null &&
    Number.isFinite(Number(poi.latitude)) && Number.isFinite(Number(poi.longitude)))

  return (
    <section className="gis-room-section" aria-label="Tiện ích GIS quanh phòng">
      <style>{`
/* BƯỚC 85.7: GIS trong chi tiết phòng */
.gis-room-section { margin: 24px 0; padding: 18px; border: 1px solid #dbeafe; border-radius: 14px; background: #f8fbff; color: #1e293b; }
.gis-room-section h3 { margin: 0 0 6px; }
.gis-room-subtitle, .gis-room-credit { color: #64748b; font-size: 12px; line-height: 1.5; margin: 6px 0 14px; }
.gis-room-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin: 15px 0; }
.gis-room-stats > div { display: flex; flex-direction: column; align-items: center; gap: 3px; padding: 12px 5px; border: 1px solid #dbeafe; border-radius: 10px; background: white; text-align: center; }
.gis-room-stats strong { font-size: 21px; color: #1d4ed8; }
.gis-room-stats span { font-size: 12px; color: #475569; }
.gis-room-nearest { padding: 12px; background: #eff6ff; border-radius: 8px; line-height: 1.6; }
.gis-room-filter { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin: 14px 0; font-weight: 600; }
.gis-room-filter select { max-width: 100%; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 8px; background: white; color: #1e293b; }
.gis-room-map { border-radius: 12px; overflow: hidden; border: 1px solid #cbd5e1; margin: 12px 0 18px; }
.gis-room-list { max-height: 360px; overflow-y: auto; padding: 10px 12px; background: white; border-radius: 10px; border: 1px solid #e2e8f0; }
.gis-room-list > strong { display: block; margin-bottom: 8px; }
.gis-room-list-item { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; padding: 9px 0; border-top: 1px solid #f1f5f9; font-size: 13px; }
.gis-room-list-item strong { white-space: nowrap; color: #1d4ed8; }
.gis-room-list-item button { background: transparent; border: 0; padding: 0; color: inherit; font: inherit; text-align: left; cursor: pointer; flex: 1; }
.gis-room-list-item button:hover, .gis-room-list-item button:focus-visible { color: #1d4ed8; text-decoration: underline; }
.gis-room-list-item.is-selected { background: #eff6ff; border-radius: 5px; }
.gis-room-message { color: #92400e; background: #fffbeb; padding: 12px; border-radius: 8px; }
@media (max-width: 520px) { .gis-room-section { padding: 12px; } .gis-room-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
`}</style>
      <h3>📍 Tiện ích xung quanh phòng (GIS)</h3>
      <p className="gis-room-subtitle">Dữ liệu OpenStreetMap qua PostGIS · Bán kính 1 km · Khoảng cách đường chim bay</p>
      {dangTai && <p>Đang tải dữ liệu tiện ích gần phòng...</p>}
      {!dangTai && loi && <p className="gis-room-message">{loi}</p>}
      {!dangTai && !loi && tomTat && (
        <>
          <div className="gis-room-stats">
            <div><strong>{tomTat.total_pois_1km ?? 0}</strong><span>Tổng tiện ích</span></div>
            <div><strong>{tomTat.universities_1km ?? 0}</strong><span>Đại học</span></div>
            <div><strong>{tomTat.hospitals_1km ?? 0}</strong><span>Bệnh viện</span></div>
            <div><strong>{tomTat.bus_stops_1km ?? 0}</strong><span>Trạm xe buýt</span></div>
            <div><strong>{tomTat.parks_1km ?? 0}</strong><span>Công viên</span></div>
            <div><strong>{tomTat.schools_1km ?? 0}</strong><span>Trường học</span></div>
          </div>
          <p className="gis-room-nearest"><strong>🎓 Đại học gần nhất:</strong>{' '}
            {tomTat.university_name
              ? `${tomTat.university_name} (${dinhDangKhoangCachGIS(tomTat.nearest_university_distance_m)})`
              : 'Chưa có dữ liệu'}</p>
          <label className="gis-room-filter">Lọc điểm tiện ích:{' '}
            <select value={loaiLoc} onChange={(e) => chonLoaiGIS(e.target.value)}>
              <option value="all">Tất cả ({diemGan.length} điểm hiển thị)</option>
              {Object.entries(NHAN_POI_GIS).map(([key, label]) =>
                <option key={key} value={key}>{label}</option>)}
            </select>
          </label>
          {toaDoPhong && (
            <div className="gis-room-map">
              <MapContainer key={`gis-${phong.id}`} center={toaDoPhong} zoom={15}
                scrollWheelZoom={false} style={{ width: '100%', height: 320 }}>
                <DieuHuongBanDoGIS diemDuocChon={diemDuocChon} />
                <TileLayer url={ESRI_TILES} attribution={ESRI_ATTRIBUTION} />
                <Marker position={toaDoPhong} icon={GHIM}>
                  <Popup><strong>🏠 {phong.title}</strong><div>Vị trí phòng trọ</div></Popup>
                </Marker>
                {toaDoPOI.map((poi) => (
                  <Marker key={poi.id} ref={(marker) => { if (marker && diemDuocChon?.id === poi.id) marker.openPopup() }} position={[Number(poi.latitude), Number(poi.longitude)]}
                    icon={L.divIcon({
                      className: 'gis-poi-pin',
                      html: `<span style="display:block;width:14px;height:14px;border:2px solid white;border-radius:50%;background:${MAU_POI_GIS[poi.category] || '#64748b'};box-shadow:0 1px 5px #0005"></span>`,
                      iconSize: [18, 18], iconAnchor: [9, 9],
                    })}>
                    <Popup><strong>{tenPOIGIS(poi)}</strong>
                      <div>{NHAN_POI_GIS[poi.category] || poi.category}</div>
                      <div>Cách phòng {dinhDangKhoangCachGIS(poi.distance_m)}</div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          )}
          <div className="gis-room-list">
            <strong>Điểm tiện ích gần phòng ({danhSachHienThi.length})</strong>
            {danhSachHienThi.length === 0 && <p>Không có điểm phù hợp trong dữ liệu hiện tại.</p>}
            {danhSachHienThi.slice(0, 20).map((poi) => (
              <div className={`gis-room-list-item ${diemDuocChon?.id === poi.id ? 'is-selected' : ''}`} key={poi.id}>
                <button type="button" title="Xem vị trí trên bản đồ" onClick={() => setDiemDuocChon({ ...poi })}>
                  {NHAN_POI_GIS[poi.category] || '📌 Tiện ích'} · {tenPOIGIS(poi)}
                </button>
                <strong>{dinhDangKhoangCachGIS(poi.distance_m)}</strong>
              </div>
            ))}
            {danhSachHienThi.length > 20 &&
              <p className="gis-room-subtitle">Đang hiển thị 20 điểm gần nhất trong danh sách; các điểm khác có thể xem trên bản đồ.</p>}
          </div>
          <p className="gis-room-credit">Nguồn: © OpenStreetMap contributors (ODbL). Dữ liệu tiện ích có thể chưa đầy đủ.</p>
        </>
      )}
    </section>
  )
}

// BƯỚC 85.9: kiểm tra điểm nằm trong đa giác (ray casting), tọa độ [lat, lng].
function namTrongDaGiac(lat, lng, dinh) {
  if (!Array.isArray(dinh) || dinh.length < 3) return false
  let inside = false
  for (let i = 0, j = dinh.length - 1; i < dinh.length; j = i++) {
    const [yi, xi] = dinh[i]
    const [yj, xj] = dinh[j]
    const cross = (yi > lat) !== (yj > lat) &&
      lng < ((xj - xi) * (lat - yi)) / (yj - yi) + xi
    if (cross) inside = !inside
  }
  return inside
}

function VeVungTrenBanDo({ dangVe, onThemDinh }) {
  useMapEvents({ click(event) { if (dangVe) onThemDinh([event.latlng.lat, event.latlng.lng]) } })
  return null
}

function App() {
  if (window.location.pathname === '/gis-analysis') {
    return <GISAnalysis />
  }

  const [showDashboardAI, setShowDashboardAI] = useState(false)
  // Thông báo và xác nhận riêng của ứng dụng, không dùng hộp thoại trình duyệt.
  const [appNotice, setAppNotice] = useState(null)
  const [appConfirm, setAppConfirm] = useState(null)
  const confirmResolver = useRef(null)

  const thongBaoApp = (message, type = 'info') => {
    setAppNotice({ message: String(message), type })
  }

  const hoiXacNhan = (message) => new Promise((resolve) => {
    confirmResolver.current = resolve
    setAppConfirm(String(message))
  })

  const traLoiXacNhan = (accepted) => {
    const resolve = confirmResolver.current
    confirmResolver.current = null
    setAppConfirm(null)
    if (resolve) resolve(accepted)
  }
  // BƯỚC 82: Dự đoán giá thuê KNN từ backend.
  const [dienTichDuDoan, setDienTichDuDoan] = useState('25')
  const [khuVucDuDoan, setKhuVucDuDoan] = useState('')
  const [ketQuaDuDoan, setKetQuaDuDoan] = useState(null)
  const [loiDuDoan, setLoiDuDoan] = useState('')
  const [dangDuDoan, setDangDuDoan] = useState(false)

  const duDoanGiaThue = async (event) => {
    event.preventDefault()
    const area = Number(dienTichDuDoan)
    if (!Number.isFinite(area) || area < 5 || area > 300) {
      setLoiDuDoan('Diện tích phải từ 5 đến 300 m².')
      setKetQuaDuDoan(null)
      return
    }
    setDangDuDoan(true)
    setLoiDuDoan('')
    setKetQuaDuDoan(null)
    try {
      const params = new URLSearchParams({ area: String(area), district: khuVucDuDoan.trim() })
      const response = await fetch(`${API}/api/rooms/predict-price?${params}`)
      const payload = await response.json()
      if (!response.ok) {
        const detail = payload.detail
        throw new Error(typeof detail === 'string' ? detail : 'Không thể dự đoán giá thuê lúc này.')
      }
      if (!payload.data || !Number.isFinite(Number(payload.data.predicted_price))) {
        throw new Error('Dữ liệu dự đoán từ máy chủ không hợp lệ.')
      }
      setKetQuaDuDoan(payload.data)
    } catch (error) {
      setLoiDuDoan(error.message || 'Không thể kết nối máy chủ.')
    } finally {
      setDangDuDoan(false)
    }
  }

  const [showMap, setShowMap] = useState(false)
  const [dangVeVung, setDangVeVung] = useState(false)
  const [dinhDangVe, setDinhDangVe] = useState([])
  const [vungDaChot, setVungDaChot] = useState(null)
  const [trangPolygon, setTrangPolygon] = useState(1)
  const [ketQuaPostGIS, setKetQuaPostGIS] = useState(null)
  const [dangLocPostGIS, setDangLocPostGIS] = useState(false)
  const [loiPostGIS, setLoiPostGIS] = useState('')
  useEffect(() => {
    if (!vungDaChot) {
      setKetQuaPostGIS(null)
      setDangLocPostGIS(false)
      setLoiPostGIS('')
      return
    }
    const controller = new AbortController()
    setKetQuaPostGIS(null)
    setDangLocPostGIS(true)
    setLoiPostGIS('')
    fetch(`${API}/api/gis/rooms/within-polygon`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ coordinates: vungDaChot.map(([lat, lng]) => [lng, lat]) }),
      signal: controller.signal,
    })
      .then(async (response) => {
        const result = await response.json()
        if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Không lọc được vùng bằng PostGIS')
        if (!Array.isArray(result.data)) throw new Error('Phản hồi PostGIS không hợp lệ')
        setKetQuaPostGIS(result.data.map((room) => Number(room.id)))
      })
      .catch((error) => { if (error.name !== 'AbortError') setLoiPostGIS(error.message) })
      .finally(() => { if (!controller.signal.aborted) setDangLocPostGIS(false) })
    return () => controller.abort()
  }, [vungDaChot])
  const themDinhVung = (point) => setDinhDangVe((prev) => [...prev, point])
  const xoaVung = () => {
    setDinhDangVe([])
    setVungDaChot(null)
    setDangVeVung(false)
    setTrangPolygon(1)
  }

  // BƯỚC 74: Thống kê các tin đã duyệt từ PostgreSQL
  const [showStats, setShowStats] = useState(false)
  const [stats, setStats] = useState(null)
  const [statsLoading, setStatsLoading] = useState(false)
  const [statsError, setStatsError] = useState('')

  const taiThongKe = async () => {
    setStatsLoading(true)
    setStatsError('')
    try {
      const response = await fetch(`${API}/api/rooms/stats`, { cache: 'no-store' })
      const result = await response.json()
      if (!response.ok) throw new Error(result.detail || 'Không tải được thống kê!')
      setStats(result.data)
    } catch (error) {
      setStatsError(error.message)
    } finally {
      setStatsLoading(false)
    }
  }

  const moThongKe = () => {
    setShowStats(true)
    taiThongKe()
    window.setTimeout(() => document.getElementById('thong-ke-phong')?.scrollIntoView({ behavior: 'smooth' }), 50)
  }


  // DANH SÁCH PHÒNG
  const [phongTro, setPhongTro] = useState([])
  const [dangTaiPhong, setDangTaiPhong] = useState(true)
  const [loiTaiPhong, setLoiTaiPhong] = useState('')

  // TÌM KIẾM
  const [tuKhoa, setTuKhoa] = useState('')
  const [khuVuc, setKhuVuc] = useState('')
  const [khoangGia, setKhoangGia] = useState('all')
  const [khoangDienTich, setKhoangDienTich] = useState('all')
  const [loaiPhong, setLoaiPhong] = useState('all')
  const [sapXep, setSapXep] = useState('new')
  const [trangHienTai, setTrangHienTai] = useState(1)
  const [duLieuPhanTrang, setDuLieuPhanTrang] = useState({ data: [], total: 0, page: 1, total_pages: 1 })
  const [dangTaiTrang, setDangTaiTrang] = useState(true)
  const [loiTaiTrang, setLoiTaiTrang] = useState('')
  const [daLuu, setDaLuu] = useState([])
  const [phongYeuThich, setPhongYeuThich] = useState([])
  const [showFavorites, setShowFavorites] = useState(false)
  const [dangTaiYeuThich, setDangTaiYeuThich] = useState(false)
  const [loiYeuThich, setLoiYeuThich] = useState('')
  const [dangXuLyYeuThich, setDangXuLyYeuThich] = useState([])

  // TÀI KHOẢN
  const [nguoiDung, setNguoiDung] = useState(null)
  const [showLogin, setShowLogin] = useState(false)
  const [loaiForm, setLoaiForm] = useState('login')
  const [dangXuLy, setDangXuLy] = useState(false)
  const [thongBao, setThongBao] = useState('')

  const [usernameEmail, setUsernameEmail] = useState('')
  const [password, setPassword] = useState('')

  const [fullName, setFullName] = useState('')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [registerPassword, setRegisterPassword] = useState('')

  // HỒ SƠ CÁ NHÂN VÀ ĐỔI MẬT KHẨU
  const [showProfile, setShowProfile] = useState(false)
  const [profileTab, setProfileTab] = useState('info')
  const [profileForm, setProfileForm] = useState({ full_name: '', email: '', phone: '' })
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '', confirm_password: '' })
  const [profileBusy, setProfileBusy] = useState(false)
  const [profileMessage, setProfileMessage] = useState('')
  const [profileError, setProfileError] = useState('')

  // ĐĂNG TIN
  const [showPost, setShowPost] = useState(false)
  const [formDangTin, setFormDangTin] = useState({
    title: '',
    address: '',
    district: '',
    price: '',
    area: '',
    description: '',
    latitude: '',
    longitude: '',
  })
  const [anhDaChon, setAnhDaChon] = useState([])
  const [videoDaChon, setVideoDaChon] = useState(null)
  const [anhXemTruoc, setAnhXemTruoc] = useState([])
  const [videoXemTruoc, setVideoXemTruoc] = useState('')

  // QUẢN LÝ TIN ĐĂNG CỦA TÔI
  const [showMyRooms, setShowMyRooms] = useState(false)
  const [myRooms, setMyRooms] = useState([])
  const [loadingMyRooms, setLoadingMyRooms] = useState(false)
  const [myRoomsError, setMyRoomsError] = useState('')
  const [editingRoom, setEditingRoom] = useState(null)
  const [editForm, setEditForm] = useState({ title: '', address: '', district: '', price: '', area: '', description: '', latitude: '', longitude: '' })
  const [savingEdit, setSavingEdit] = useState(false)
  const [deletingRoomId, setDeletingRoomId] = useState(null)

  // ADMIN
  const [showAdmin, setShowAdmin] = useState(false)
  const [danhSachChoDuyet, setDanhSachChoDuyet] = useState([])
  const [dangTaiTinChoDuyet, setDangTaiTinChoDuyet] = useState(false)
  const [loiAdmin, setLoiAdmin] = useState('')
  const [thongBaoAdmin, setThongBaoAdmin] = useState('')
  const [xacNhanTin, setXacNhanTin] = useState(null)
  const [dangXuLyTin, setDangXuLyTin] = useState(false)
  const [adminTab, setAdminTab] = useState('rooms')
  const [adminUsers, setAdminUsers] = useState([])
  const [loadingAdminUsers, setLoadingAdminUsers] = useState(false)
  const [adminUsersError, setAdminUsersError] = useState('')
  const [adminUsersMessage, setAdminUsersMessage] = useState('')
  const [processingUserId, setProcessingUserId] = useState(null)

  // XEM CHI TIẾT VÀ LƯỚT ẢNH
  const [phongChiTiet, setPhongChiTiet] = useState(null)
  const [anhHienTai, setAnhHienTai] = useState(0)
  const [anhLoi, setAnhLoi] = useState(false)
  const [anhLoiCard, setAnhLoiCard] = useState([])
  const [viTriCham, setViTriCham] = useState(null)

  const taiDanhSachPhong = async () => {
    setDangTaiPhong(true)
    setLoiTaiPhong('')

    try {
      const response = await fetch(`${API}/api/rooms`, { cache: 'no-store' })
      if (!response.ok) {
        throw new Error('Không thể tải danh sách phòng trọ!')
      }

      const result = await response.json()
      const rooms = Array.isArray(result.data) ? result.data : []

      // BƯỚC 85.11: Đồng bộ tọa độ từ PostGIS khi API danh sách cũ
      // chưa trả latitude/longitude. Chỉ hỏi GIS cho phòng thiếu tọa độ.
      // Không làm hỏng việc tải danh sách nếu GIS tạm thời không hoạt động.
      const roomsWithCoordinates = await Promise.all(rooms.map(async (room) => {
        if (coToaDoHopLe(room) || room.status !== 'da_duyet') return room
        try {
          const gisResponse = await fetch(`${API}/api/gis/rooms/${room.id}/summary`, { cache: 'no-store' })
          if (!gisResponse.ok) return room
          const gisResult = await gisResponse.json()
          const summary = gisResult.data
          if (!summary || !coToaDoHopLe(summary)) return room
          return { ...room, latitude: Number(summary.latitude), longitude: Number(summary.longitude) }
        } catch {
          return room
        }
      }))

      setPhongTro(
        roomsWithCoordinates
          .filter((phong) => phong.status === 'da_duyet')
          .map((phong) => ({
            ...phong,
            title: phong.title || '',
            address: phong.address || '',
            price: Number(phong.price),
            area: Number(phong.area),
            images: Array.isArray(phong.images)
              ? phong.images
              : [],
            type: 'Phòng trọ',
            date: phong.created_at
              ? new Date(phong.created_at).toLocaleDateString('vi-VN')
              : 'Mới cập nhật',
          }))
      )
    } catch (error) {
      setLoiTaiPhong(error.message)
    } finally {
      setDangTaiPhong(false)
    }
  }

  useEffect(() => {
    taiDanhSachPhong()

    fetch(`${API}/api/auth/me`, {
      credentials: 'include',
    })
      .then(async (response) => {
        if (!response.ok) return
        const data = await response.json()
        setNguoiDung(data.user || data.thong_tin || data)
      })
      .catch(() => {})
  }, [])

  // Tự kiểm tra phiên đăng nhập: khi Admin khóa tài khoản, đóng các
  // cửa sổ riêng tư và đăng xuất trên giao diện mà không cần tải lại trang.
  useEffect(() => {
    if (!nguoiDung?.id) return

    let active = true
    let checking = false

    const kiemTraTaiKhoan = async () => {
      if (checking || document.visibilityState === 'hidden') return
      checking = true
      try {
        const response = await fetch(`${API}/api/auth/me`, {
          credentials: 'include',
          cache: 'no-store',
        })
        if (!active) return
        if (response.ok) return

        // Chỉ xử lý khi máy chủ xác nhận phiên không còn hợp lệ;
        // không đăng xuất vì lỗi mạng hoặc lỗi máy chủ tạm thời.
        if (response.status !== 401 && response.status !== 403) return
        const data = await response.json().catch(() => ({}))
        if (!active) return
        const detail = String(data.detail || data.message || '')
        const biKhoa = response.status === 403 && /khóa|khoá|locked|inactive|vô hiệu|disabled/i.test(detail)

        setNguoiDung(null)
        setShowProfile(false)
        setShowPost(false)
        setShowMyRooms(false)
        setMyRooms([])
        setEditingRoom(null)
        setShowFavorites(false)
        setDaLuu([])
        setPhongYeuThich([])
        setShowAdmin(false)
        setDanhSachChoDuyet([])
        setAppConfirm(null)
        if (confirmResolver.current) {
          confirmResolver.current(false)
          confirmResolver.current = null
        }
        setShowLogin(false)
        thongBaoApp(biKhoa
          ? 'Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên.'
          : 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.', 'error')
      } catch {
        // Mất kết nối tạm thời: không tự ý đăng xuất.
      } finally {
        checking = false
      }
    }

    const timer = window.setInterval(kiemTraTaiKhoan, 10000)
    const onVisible = () => { if (document.visibilityState === 'visible') kiemTraTaiKhoan() }
    document.addEventListener('visibilitychange', onVisible)
    return () => {
      active = false
      window.clearInterval(timer)
      document.removeEventListener('visibilitychange', onVisible)
    }
  }, [nguoiDung?.id])

  useEffect(() => {
    const urls = anhDaChon.map((file) => URL.createObjectURL(file))
    setAnhXemTruoc(urls)

    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url))
    }
  }, [anhDaChon])

  useEffect(() => {
    if (!videoDaChon) {
      setVideoXemTruoc('')
      return
    }

    const url = URL.createObjectURL(videoDaChon)
    setVideoXemTruoc(url)
    return () => URL.revokeObjectURL(url)
  }, [videoDaChon])

  // DANH SÁCH ẢNH CỦA MỘT PHÒNG
  const layAnhPhong = (phong) => {
    if (!phong) return []

    const danhSach = Array.isArray(phong.images)
      ? phong.images.filter(Boolean)
      : []

    if (danhSach.length > 0) return danhSach
    return phong.image ? [phong.image] : []
  }

  // MỞ CHI TIẾT PHÒNG
  const moChiTiet = (phong) => {
    setPhongChiTiet(phong)
    setAnhHienTai(0)
    setAnhLoi(false)
    setViTriCham(null)
  }

  const dongChiTiet = () => {
    setPhongChiTiet(null)
    setAnhHienTai(0)
    setAnhLoi(false)
  }

  // CHUYỂN ẢNH, TỰ QUAY VỀ ĐẦU DANH SÁCH
  const chuyenAnh = (buoc) => {
    const soAnh = layAnhPhong(phongChiTiet).length
    if (soAnh < 2) return

    setAnhHienTai((index) =>
      (index + buoc + soAnh) % soAnh
    )
    setAnhLoi(false)
  }

  // VUỐT ẢNH TRÊN ĐIỆN THOẠI
  const batDauVuot = (event) => {
    setViTriCham(event.touches[0].clientX)
  }

  const ketThucVuot = (event) => {
    if (viTriCham === null) return

    const viTriKetThuc = event.changedTouches[0].clientX
    const khoangCach = viTriCham - viTriKetThuc

    if (Math.abs(khoangCach) > 45) {
      chuyenAnh(khoangCach > 0 ? 1 : -1)
    }

    setViTriCham(null)
  }

  // PHÍM MŨI TÊN VÀ ESC
  useEffect(() => {
    if (!phongChiTiet) return

    const xuLyPhim = (event) => {
      if (event.key === 'Escape') {
        dongChiTiet()
      }

      if (event.key === 'ArrowRight') {
        const soAnh = layAnhPhong(phongChiTiet).length
        if (soAnh > 1) {
          setAnhHienTai((index) => (index + 1) % soAnh)
          setAnhLoi(false)
        }
      }

      if (event.key === 'ArrowLeft') {
        const soAnh = layAnhPhong(phongChiTiet).length
        if (soAnh > 1) {
          setAnhHienTai((index) =>
            (index - 1 + soAnh) % soAnh
          )
          setAnhLoi(false)
        }
      }
    }

    window.addEventListener('keydown', xuLyPhim)
    return () => window.removeEventListener('keydown', xuLyPhim)
  }, [phongChiTiet])

  // LỌC PHÒNG
  const danhSachPhong = phongTro
    .filter((phong) => {
      const keyword = tuKhoa.toLowerCase().trim()

      const khopTuKhoa =
        phong.title.toLowerCase().includes(keyword) ||
        phong.address.toLowerCase().includes(keyword) ||
        (phong.district || '').toLowerCase().includes(keyword)

      const khopKhuVuc = !khuVuc.trim() ||
        (phong.district || '').toLowerCase().includes(khuVuc.toLowerCase().trim()) ||
        (phong.address || '').toLowerCase().includes(khuVuc.toLowerCase().trim())

      const gia = phong.price / 1000000

      const khopGia =
        khoangGia === 'all' ||
        (khoangGia === 'under3' && gia < 3) ||
        (khoangGia === '3to5' && gia >= 3 && gia <= 5) ||
        (khoangGia === 'over5' && gia > 5)

      const dienTich = Number(phong.area)
      const khopDienTich =
        khoangDienTich === 'all' ||
        (khoangDienTich === 'under20' && dienTich < 20) ||
        (khoangDienTich === '20to30' && dienTich >= 20 && dienTich <= 30) ||
        (khoangDienTich === '30to50' && dienTich > 30 && dienTich <= 50) ||
        (khoangDienTich === 'over50' && dienTich > 50)

      const khopLoai =
        loaiPhong === 'all' || phong.type === loaiPhong

      return khopTuKhoa && khopKhuVuc && khopGia && khopDienTich && khopLoai
    })
    .sort((a, b) => {
      if (sapXep === 'low') return a.price - b.price
      if (sapXep === 'high') return b.price - a.price
      if (sapXep === 'area_small') return Number(a.area) - Number(b.area)
      if (sapXep === 'area_large') return Number(b.area) - Number(a.area)
      if (sapXep === 'old') return new Date(a.created_at || 0) - new Date(b.created_at || 0)
      return new Date(b.created_at || 0) -
        new Date(a.created_at || 0)
    })

  // Backend phân trang thẻ phòng. Dữ liệu bản đồ vẫn lấy từ API đầy đủ.
  const SO_PHONG_MOI_TRANG = 6
  // BƯỚC 85.10: kết quả không gian do PostGIS ST_Covers quyết định.
  // Vẫn áp dụng các bộ lọc từ khóa/giá/diện tích hiện tại lên tập ID trả về.
  // Không âm thầm quay về lọc frontend nếu backend gặp lỗi.
  const idPhongTrongVung = new Set(ketQuaPostGIS || [])
  const phongTrongVung = vungDaChot
    ? (ketQuaPostGIS ? danhSachPhong.filter((phong) => idPhongTrongVung.has(Number(phong.id))) : [])
    : null
  const tongKetQua = vungDaChot ? phongTrongVung.length : duLieuPhanTrang.total
  const tongSoTrang = vungDaChot ? Math.max(1, Math.ceil(tongKetQua / 6)) : (duLieuPhanTrang.total_pages || 1)
  const trangDangXem = vungDaChot ? Math.min(trangPolygon, tongSoTrang) : (duLieuPhanTrang.page || 1)
  const phongTrangHienTai = vungDaChot
    ? phongTrongVung.slice((trangDangXem - 1) * 6, trangDangXem * 6)
    : duLieuPhanTrang.data

  useEffect(() => {
    setTrangHienTai(1)
  }, [tuKhoa, khuVuc, khoangGia, khoangDienTich, loaiPhong, sapXep])

  useEffect(() => {
    const controller = new AbortController()
    const timer = window.setTimeout(async () => {
      setDangTaiTrang(true)
      setLoiTaiTrang('')
      try {
        const params = new URLSearchParams({
          page: String(trangHienTai), limit: String(SO_PHONG_MOI_TRANG),
          keyword: tuKhoa.trim(), district: khuVuc.trim(),
          price_range: khoangGia, area_range: khoangDienTich,
          room_type: loaiPhong, sort: sapXep,
        })
        const response = await fetch(`${API}/api/rooms/paged?${params}`, { signal: controller.signal })
        const result = await response.json()
        if (!response.ok) throw new Error(result.detail || 'Không tải được trang phòng trọ!')
        const rooms = (Array.isArray(result.data) ? result.data : []).map((phong) => ({
          ...phong, type: 'Phòng trọ',
          date: phong.created_at ? new Date(phong.created_at).toLocaleDateString('vi-VN') : 'Mới cập nhật',
        }))
        setDuLieuPhanTrang({ data: rooms, total: result.total, page: result.page, total_pages: result.total_pages })
      } catch (error) {
        if (error.name !== 'AbortError') setLoiTaiTrang(error.message)
      } finally {
        if (!controller.signal.aborted) setDangTaiTrang(false)
      }
    }, 200)
    return () => { window.clearTimeout(timer); controller.abort() }
  }, [trangHienTai, tuKhoa, khuVuc, khoangGia, khoangDienTich, loaiPhong, sapXep, phongTro])

  const chuyenTrang = (trangMoi) => {
    if (trangMoi < 1 || trangMoi > tongSoTrang || trangMoi === trangDangXem) return
    if (vungDaChot) setTrangPolygon(trangMoi)
    else setTrangHienTai(trangMoi)
    document.getElementById('danh-sach-phong')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const phongTrenBanDo = (phongTrongVung || danhSachPhong).filter(coToaDoHopLe)
  const dangLoc = Boolean(vungDaChot || tuKhoa.trim() || khuVuc.trim() || khoangGia !== 'all' || khoangDienTich !== 'all' || loaiPhong !== 'all')
  const xoaBoLoc = () => {
    setTuKhoa('')
    setKhuVuc('')
    setKhoangGia('all')
    setKhoangDienTich('all')
    setLoaiPhong('all')
    xoaVung()
  }

  // YÊU THÍCH: ĐỌC VÀ GHI TRỰC TIẾP VÀO POSTGRESQL
  const taiPhongYeuThich = async () => {
    setDangTaiYeuThich(true)
    setLoiYeuThich('')
    try {
      const response = await fetch(`${API}/api/favorites`, {
        credentials: 'include',
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Không tải được phòng yêu thích!')
      }
      const rooms = Array.isArray(data.data) ? data.data : []
      setPhongYeuThich(rooms)
      setDaLuu(rooms.map((room) => Number(room.room_id)))
    } catch (error) {
      setLoiYeuThich(error.message)
    } finally {
      setDangTaiYeuThich(false)
    }
  }

  useEffect(() => {
    if (nguoiDung?.id) {
      taiPhongYeuThich()
    } else {
      setDaLuu([])
      setPhongYeuThich([])
      setShowFavorites(false)
      setLoiYeuThich('')
    }
  }, [nguoiDung?.id])

  const toggleLuu = async (id) => {
    if (!nguoiDung) {
      moForm('login')
      setThongBao('Vui lòng đăng nhập để lưu phòng yêu thích!')
      return
    }
    if (dangXuLyYeuThich.includes(id)) return

    const daYeuThich = daLuu.includes(id)
    setDangXuLyYeuThich((prev) => [...prev, id])
    try {
      const response = await fetch(`${API}/api/favorites/${id}`, {
        method: daYeuThich ? 'DELETE' : 'POST',
        credentials: 'include',
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Không cập nhật được phòng yêu thích!')
      }
      await taiPhongYeuThich()
    } catch (error) {
      thongBaoApp(error.message)
    } finally {
      setDangXuLyYeuThich((prev) => prev.filter((item) => item !== id))
    }
  }

  const moPhongYeuThich = () => {
    if (!nguoiDung) {
      moForm('login')
      setThongBao('Vui lòng đăng nhập để xem phòng đã lưu!')
      return
    }
    setShowFavorites(true)
    taiPhongYeuThich()
  }

  const moForm = (loai) => {
    setLoaiForm(loai)
    setThongBao('')
    setShowLogin(true)
  }

  // ĐĂNG NHẬP
  const xuLyDangNhap = async (event) => {
    event.preventDefault()
    setDangXuLy(true)
    setThongBao('Đang kiểm tra tài khoản...')

    try {
      const response = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          username_email: usernameEmail,
          password,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.detail || data.message || 'Đăng nhập thất bại!'
        )
      }

      let user = data.user || data.thong_tin || data.data

      if (!user || !user.id) {
        const meResponse = await fetch(`${API}/api/auth/me`, {
          credentials: 'include',
        })

        if (meResponse.ok) {
          const meData = await meResponse.json()
          user = meData.user || meData.thong_tin || meData
        }
      }

      if (!user || !user.id) {
        throw new Error('Không lấy được thông tin tài khoản!')
      }

      setNguoiDung(user)
      setShowLogin(false)
      setShowAdmin(false)
      setUsernameEmail('')
      setPassword('')
      setThongBao('')
      thongBaoApp(`Xin chào ${user.full_name || user.username}!`)
    } catch (error) {
      setThongBao(error.message)
    } finally {
      setDangXuLy(false)
    }
  }

  // ĐĂNG KÝ
  const xuLyDangKy = async (event) => {
    event.preventDefault()

    if (registerPassword.length < 6) {
      setThongBao('Mật khẩu phải có ít nhất 6 ký tự!')
      return
    }

    setDangXuLy(true)
    setThongBao('Đang tạo tài khoản...')

    try {
      const response = await fetch(`${API}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          full_name: fullName,
          username,
          email,
          phone,
          password: registerPassword,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.detail || data.message || 'Đăng ký thất bại!'
        )
      }

      thongBaoApp(data.message || 'Đăng ký thành công!')

      setUsernameEmail(username)
      setPassword('')
      setFullName('')
      setUsername('')
      setEmail('')
      setPhone('')
      setRegisterPassword('')
      setThongBao('')
      setLoaiForm('login')
    } catch (error) {
      setThongBao(error.message)
    } finally {
      setDangXuLy(false)
    }
  }

  // MỞ HỒ SƠ VỚI THÔNG TIN MỚI NHẤT
  const moHoSo = async () => {
    if (!nguoiDung) return
    setProfileTab('info')
    setProfileMessage('')
    setProfileError('')
    setPasswordForm({ old_password: '', new_password: '', confirm_password: '' })
    setProfileForm({
      full_name: nguoiDung.full_name || '',
      email: nguoiDung.email || '',
      phone: nguoiDung.phone || '',
    })
    setShowProfile(true)
    try {
      const response = await fetch(`${API}/api/auth/me`, { credentials: 'include' })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Không tải được thông tin tài khoản!')
      const user = data.user
      if (user?.id) {
        setNguoiDung(user)
        setProfileForm({ full_name: user.full_name || '', email: user.email || '', phone: user.phone || '' })
      }
    } catch (error) {
      setProfileError(error.message)
    }
  }

  const luuHoSo = async (event) => {
    event.preventDefault()
    if (profileBusy) return
    setProfileBusy(true)
    setProfileMessage('')
    setProfileError('')
    try {
      const response = await fetch(`${API}/api/auth/profile`, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: profileForm.full_name.trim(),
          email: profileForm.email.trim(),
          phone: profileForm.phone.trim(),
        }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Không thể cập nhật hồ sơ!')
      setNguoiDung(data.user)
      setProfileForm({ full_name: data.user.full_name || '', email: data.user.email || '', phone: data.user.phone || '' })
      setProfileMessage(data.message || 'Cập nhật hồ sơ thành công!')
    } catch (error) {
      setProfileError(error.message)
    } finally {
      setProfileBusy(false)
    }
  }

  const doiMatKhau = async (event) => {
    event.preventDefault()
    if (profileBusy) return
    setProfileMessage('')
    setProfileError('')
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setProfileError('Xác nhận mật khẩu mới không khớp!')
      return
    }
    if (passwordForm.new_password.length < 6 || new TextEncoder().encode(passwordForm.new_password).length > 72) {
      setProfileError('Mật khẩu mới cần ít nhất 6 ký tự và tối đa 72 byte!')
      return
    }
    setProfileBusy(true)
    try {
      const response = await fetch(`${API}/api/auth/change-password`, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          old_password: passwordForm.old_password,
          new_password: passwordForm.new_password,
        }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Đổi mật khẩu thất bại!')
      setPasswordForm({ old_password: '', new_password: '', confirm_password: '' })
      setShowProfile(false)
      setNguoiDung(null)
      setShowMyRooms(false)
      setMyRooms([])
      setEditingRoom(null)
      setShowFavorites(false)
      setDaLuu([])
      setPhongYeuThich([])
      setShowAdmin(false)
      setDanhSachChoDuyet([])
      setShowLogin(true)
      setLoaiForm('login')
      setUsernameEmail('')
      setPassword('')
      setThongBao('Đổi mật khẩu thành công! Vui lòng đăng nhập lại bằng mật khẩu mới.')
    } catch (error) {
      setProfileError(error.message)
    } finally {
      setProfileBusy(false)
    }
  }

  // ĐĂNG XUẤT
  const xuLyDangXuat = async () => {
    try {
      const response = await fetch(`${API}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error('Đăng xuất không thành công!')
      }

      setNguoiDung(null)
      setShowProfile(false)
      setPasswordForm({ old_password: '', new_password: '', confirm_password: '' })
      setShowMyRooms(false)
      setMyRooms([])
      setEditingRoom(null)
      setDaLuu([])
      setPhongYeuThich([])
      setShowFavorites(false)
      setShowAdmin(false)
      setDanhSachChoDuyet([])
      thongBaoApp('Bạn đã đăng xuất thành công!')
    } catch (error) {
      thongBaoApp(error.message)
    }
  }

  // QUẢN LÝ TIN ĐĂNG CỦA TÔI
  const taiTinCuaToi = async () => {
    setLoadingMyRooms(true)
    setMyRoomsError('')
    try {
      const response = await fetch(`${API}/api/rooms/my`, { credentials: 'include' })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Không thể tải tin đăng của bạn!')
      setMyRooms(Array.isArray(data.data) ? data.data : [])
    } catch (error) {
      setMyRoomsError(error.message)
    } finally {
      setLoadingMyRooms(false)
    }
  }

  const moTinCuaToi = () => {
    if (!nguoiDung) {
      moForm('login')
      setThongBao('Vui lòng đăng nhập để quản lý tin đăng!')
      return
    }
    setShowMyRooms(true)
    taiTinCuaToi()
  }

  const moSuaTin = (room) => {
    setEditingRoom(room)
    setEditForm({
      title: room.title || '', address: room.address || '',
      district: room.district || '', price: String(room.price ?? ''),
      area: String(room.area ?? ''), description: room.description || '',
      latitude: room.latitude ?? '', longitude: room.longitude ?? '',
    })
  }

  const luuSuaTin = async (event) => {
    event.preventDefault()
    if (!editingRoom || savingEdit) return
    setSavingEdit(true)
    try {
      const response = await fetch(`${API}/api/rooms/${editingRoom.id}`, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...editForm,
          title: editForm.title.trim(),
          address: editForm.address.trim(),
          district: editForm.district.trim(),
          description: editForm.description.trim(),
          price: Number(editForm.price),
          area: Number(editForm.area),
          latitude: editForm.latitude === '' ? null : Number(editForm.latitude),
          longitude: editForm.longitude === '' ? null : Number(editForm.longitude),
        }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Không thể cập nhật tin đăng!')
      setEditingRoom(null)
      await Promise.all([taiTinCuaToi(), taiDanhSachPhong(), taiPhongYeuThich()])
      thongBaoApp(data.message || 'Đã cập nhật tin! Tin đang chờ duyệt lại.')
    } catch (error) {
      thongBaoApp(error.message)
    } finally {
      setSavingEdit(false)
    }
  }

  const xoaTinCuaToi = async (room) => {
    if (deletingRoomId !== null) return
    if (!(await hoiXacNhan(`Bạn chắc chắn muốn xóa vĩnh viễn tin #${room.id}: "${room.title}"?`))) return
    setDeletingRoomId(room.id)
    try {
      const response = await fetch(`${API}/api/rooms/${room.id}`, {
        method: 'DELETE', credentials: 'include',
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Không thể xóa tin đăng!')
      await Promise.all([taiTinCuaToi(), taiDanhSachPhong(), taiPhongYeuThich()])
      thongBaoApp(data.message || 'Đã xóa tin đăng!')
    } catch (error) {
      thongBaoApp(error.message)
    } finally {
      setDeletingRoomId(null)
    }
  }

  const nhanTrangThai = (status) => ({
    da_duyet: '✓ Đã duyệt', cho_duyet: '⏳ Chờ duyệt',
    tu_choi: '✕ Bị từ chối', bi_tu_choi: '✕ Bị từ chối',
  }[status] || status || 'Không xác định')

  // ADMIN: TẢI TIN CHỜ DUYỆT
  const taiTinChoDuyet = async () => {
    setDangTaiTinChoDuyet(true)
    setLoiAdmin('')

    try {
      const response = await fetch(
        `${API}/api/admin/rooms/pending`,
        { credentials: 'include' }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.detail || 'Không tải được danh sách tin!'
        )
      }

      setDanhSachChoDuyet(data.data || [])
    } catch (error) {
      setLoiAdmin(error.message)
    } finally {
      setDangTaiTinChoDuyet(false)
    }
  }

  // ADMIN: DANH SÁCH TÀI KHOẢN VÀ KHÓA / MỞ KHÓA
  const taiNguoiDungAdmin = async () => {
    setLoadingAdminUsers(true)
    setAdminUsersError('')
    try {
      const response = await fetch(`${API}/api/admin/users`, { credentials: 'include' })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Không tải được danh sách tài khoản!')
      setAdminUsers(Array.isArray(data.data) ? data.data : [])
    } catch (error) {
      setAdminUsersError(error.message)
    } finally {
      setLoadingAdminUsers(false)
    }
  }

  const doiTrangThaiTaiKhoan = async (user) => {
    if (processingUserId !== null || user.role === 'quan_tri' || user.id === nguoiDung?.id) return
    const isActive = user.is_active !== false
    const action = isActive ? 'lock' : 'unlock'
    const verb = isActive ? 'khóa' : 'mở khóa'
    if (!(await hoiXacNhan(`Bạn có chắc muốn ${verb} tài khoản ${user.username}?`))) return
    setProcessingUserId(user.id)
    setAdminUsersError('')
    setAdminUsersMessage('')
    try {
      const response = await fetch(`${API}/api/admin/users/${user.id}/${action}`, {
        method: 'PUT', credentials: 'include',
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || `Không thể ${verb} tài khoản!`)
      setAdminUsersMessage(data.message || `Đã ${verb} tài khoản ${user.username}!`)
      await taiNguoiDungAdmin()
    } catch (error) {
      setAdminUsersError(error.message)
    } finally {
      setProcessingUserId(null)
    }
  }

  const moQuanTri = () => {
    if (nguoiDung?.role !== 'quan_tri') {
      thongBaoApp('Bạn không có quyền quản trị viên!')
      return
    }

    setThongBaoAdmin('')
    setAdminTab('rooms')
    setShowAdmin(true)
    taiTinChoDuyet()
  }

  const xuLyTinDang = (roomId, hanhDong) => {
    setXacNhanTin({
      roomId,
      hanhDong,
      tenHanhDong: hanhDong === 'approve'
        ? 'duyệt'
        : 'từ chối',
    })
  }

  const xacNhanXuLyTin = async () => {
    if (!xacNhanTin || dangXuLyTin) return

    const { roomId, hanhDong, tenHanhDong } = xacNhanTin

    setDangXuLyTin(true)
    setLoiAdmin('')

    try {
      const response = await fetch(
        `${API}/api/admin/rooms/${roomId}/${hanhDong}`,
        {
          method: 'PUT',
          credentials: 'include',
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.detail || `${tenHanhDong} tin thất bại!`
        )
      }

      setXacNhanTin(null)
      setThongBaoAdmin(
        data.message || `${tenHanhDong} tin thành công!`
      )

      await taiTinChoDuyet()
      await taiDanhSachPhong()
    } catch (error) {
      setLoiAdmin(error.message)
      setXacNhanTin(null)
    } finally {
      setDangXuLyTin(false)
    }
  }

  // CHỌN ẢNH ĐĂNG TIN
  const xuLyChonAnh = (event) => {
    const files = Array.from(event.target.files || [])

    if (anhDaChon.length + files.length > 6) {
      thongBaoApp('Chỉ được chọn tối đa 6 ảnh!')
      event.target.value = ''
      return
    }

    const hopLe = ['image/jpeg', 'image/png', 'image/webp']

    if (files.some((file) => !hopLe.includes(file.type))) {
      thongBaoApp('Chỉ hỗ trợ ảnh JPG, PNG, WEBP!')
      event.target.value = ''
      return
    }

    if (files.some((file) => file.size > 10 * 1024 * 1024)) {
      thongBaoApp('Mỗi ảnh tối đa 10MB!')
      event.target.value = ''
      return
    }

    setAnhDaChon((prev) => [...prev, ...files])
    event.target.value = ''
  }

  const xuLyChonVideo = (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!['video/mp4', 'video/webm'].includes(file.type)) {
      thongBaoApp('Chỉ hỗ trợ video MP4 hoặc WEBM!')
      event.target.value = ''
      return
    }

    if (file.size > 100 * 1024 * 1024) {
      thongBaoApp('Video tối đa 100MB!')
      event.target.value = ''
      return
    }

    setVideoDaChon(file)
    event.target.value = ''
  }

  const xoaAnh = (index) => {
    setAnhDaChon((prev) =>
      prev.filter((_, i) => i !== index)
    )
  }

  // GỬI TIN ĐĂNG
  const xuLyDangTin = async (event) => {
    event.preventDefault()

    if (!nguoiDung) {
      setShowPost(false)
      moForm('login')
      return
    }

    setDangXuLy(true)

    try {
      const formData = new FormData()

      Object.entries(formDangTin).forEach(([key, value]) => {
        if ((key === 'latitude' || key === 'longitude') && value === '') return
        formData.append(key, value)
      })

      anhDaChon.forEach((anh) => {
        formData.append('images', anh)
      })

      if (videoDaChon) {
        formData.append('video', videoDaChon)
      }

      const response = await fetch(`${API}/api/rooms`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Đăng tin thất bại!')
      }

      thongBaoApp(data.message || 'Đăng tin thành công!')

      setFormDangTin({
        title: '',
        address: '',
        district: '',
        price: '',
        area: '',
        description: '',
        latitude: '',
        longitude: '',
      })

      setAnhDaChon([])
      setVideoDaChon(null)
      setShowPost(false)

      // Admin đăng tin xong sẽ thấy phòng ngay
      await taiDanhSachPhong()
      if (showMyRooms) await taiTinCuaToi()
    } catch (error) {
      thongBaoApp(error.message)
    } finally {
      setDangXuLy(false)
    }
  }

  const anhChiTiet = layAnhPhong(phongChiTiet)

  return (
    <div className="website">

      {/* HEADER */}
      <header className="header">
        <div className="header-container">
          <a className="logo" href="#">
            <span className="logo-icon">T</span>
            <span>
              Tronhanh<span className="logo-highlight">123</span>
            </span>
          </a>

          <nav className="navigation">
            <a className="active" href="#">Trang chủ</a>
            <a href="#danh-sach">Tìm phòng trọ</a>
            <a href="#danh-sach">Cho thuê phòng</a>
            <a href="#tien-ich">Tiện ích</a>
          </nav>

          <div className="header-actions">
            {nguoiDung ? (
              <>
                <span className="user-name">
                  Xin chào, {nguoiDung.full_name || nguoiDung.username}
                </span>

                <button type="button" className="login-button" onClick={moHoSo}>
                  Thông tin cá nhân
                </button>

                <button type="button" className="login-button" onClick={moTinCuaToi}>
                  Tin đăng của tôi
                </button>

                {nguoiDung.role === 'quan_tri' && (
                  <button
                    className="login-button"
                    onClick={moQuanTri}
                  >
                    Quản trị viên
                  </button>
                )}

                <button
                  className="login-button"
                  onClick={xuLyDangXuat}
                >
                  Đăng xuất
                </button>
              </>
            ) : (
              <button
                className="login-button"
                onClick={() => moForm('login')}
              >
                Đăng nhập
              </button>
            )}

            <button
              className="post-button"
              onClick={() => {
                if (!nguoiDung) {
                  moForm('login')
                  setThongBao('Vui lòng đăng nhập để đăng tin!')
                } else {
                  setShowPost(true)
                }
              }}
            >
              + Đăng tin
            </button>
          </div>
        </div>
      </header>

      {/* BANNER */}
      <section className="hero-section">
        <div className="hero-content">
          <span className="hero-label">
            NỀN TẢNG TÌM PHÒNG TRỌ
          </span>

          <h1>
            Tìm phòng trọ phù hợp<br />
            với cuộc sống của bạn
          </h1>

          <p>
            Khám phá phòng trọ được cập nhật tại Hà Nội.
          </p>

          <div className="search-box">
            <span className="search-icon">⌕</span>

            <input
              placeholder="Nhập tên phòng, quận hoặc khu vực..."
              value={tuKhoa}
              onChange={(event) => setTuKhoa(event.target.value)}
            />

            <button
              onClick={() =>
                document.getElementById('danh-sach')
                  ?.scrollIntoView({ behavior: 'smooth' })
              }
            >
              Tìm kiếm
            </button>
          </div>

          <div className="hero-tags">
            <span>Gợi ý:</span>
            <button onClick={() => setTuKhoa('Mỹ Đình')}>
              Mỹ Đình
            </button>
            <button onClick={() => setTuKhoa('Cầu Giấy')}>
              Cầu Giấy
            </button>
            <button onClick={() => setTuKhoa('Bắc Từ Liêm')}>
              Bắc Từ Liêm
            </button>
          </div>
        </div>
      </section>

      {/* DANH SÁCH PHÒNG */}
      <main className="main-container" id="danh-sach">
        <div className="breadcrumb">
          Trang chủ <span>›</span> Phòng trọ Hà Nội
        </div>

        <div className="section-heading">
          <div>
            <h2>Phòng trọ nổi bật</h2>
            <p>Khám phá những phòng trọ phù hợp với bạn</p>
          </div>

          <span className="result-count">
              {dangTaiPhong ? "Đang tải..." : `${tongKetQua} / ${phongTro.length} phòng trọ`}
          </span>
        </div>

        {/* BẢN ĐỒ WEBGIS: dùng cùng danh sách phòng đã lọc với các thẻ phòng. */}
        <section id="ban-do" style={{ marginBottom: 24, border: '1px solid #e2e8f0', borderRadius: 14, overflow: 'hidden', background: '#fff' }}>
          <div style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
            <div>
              <h2 style={{ margin: '0 0 5px', fontSize: 21 }}>📍 Bản đồ tìm phòng trọ</h2>
              <p style={{ margin: 0, color: '#64748b', fontSize: 14 }}>
                {phongTrenBanDo.length} / {danhSachPhong.length} phòng có tọa độ trong kết quả tìm kiếm
              </p>
            </div>
            <button type="button" style={styles.button} onClick={() => setShowMap((prev) => !prev)}>
              {showMap ? 'Ẩn bản đồ' : 'Hiện bản đồ'}
            </button>
          </div>
          {showMap && (
            <>
              <div style={{ padding: '0 20px 14px', display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                <button type="button" style={{ ...styles.button, background: dangVeVung ? '#b45309' : '#2563eb' }}
                  onClick={() => { setDangVeVung(true); setDinhDangVe([]); setVungDaChot(null); setTrangPolygon(1) }}>
                  {dangVeVung ? 'Đang vẽ: bấm trên bản đồ' : '✏️ Vẽ vùng lọc phòng'}
                </button>
                {dangVeVung && <button type="button" style={{ ...styles.button, background: '#15803d' }}
                  disabled={dinhDangVe.length < 3}
                  onClick={() => { setVungDaChot([...dinhDangVe]); setDangVeVung(false); setTrangPolygon(1) }}>
                  Hoàn tất vùng ({dinhDangVe.length} đỉnh)
                </button>}
                {(dangVeVung || vungDaChot) && <button type="button" style={{ ...styles.button, background: '#64748b' }} onClick={xoaVung}>Xóa vùng</button>}
                <span role="status" style={{ fontSize: 13, color: loiPostGIS ? '#b91c1c' : '#475569' }}>
                  {dangVeVung ? 'Nhấp ít nhất 3 điểm trên bản đồ, rồi chọn Hoàn tất vùng.' :
                    vungDaChot ? (dangLocPostGIS ? 'Đang truy vấn PostGIS...' : loiPostGIS ? `Lỗi PostGIS: ${loiPostGIS}` : `PostGIS ST_Covers: ${tongKetQua} phòng trong đa giác.`) : 'Có thể khoanh vùng tìm phòng bằng đa giác.'}
                </span>
              </div>
              <MapContainer center={HA_NOI} zoom={10} scrollWheelZoom={false}
                style={{ height: 420, width: '100%', zIndex: 0 }}>
                <TileLayer attribution={ESRI_ATTRIBUTION} url={ESRI_TILES} maxZoom={19} />
                <VeVungTrenBanDo dangVe={dangVeVung} onThemDinh={themDinhVung} />
                {dangVeVung && dinhDangVe.length >= 2 && <Polyline positions={dinhDangVe} pathOptions={{ color: '#f59e0b', weight: 3 }} />}
                {dangVeVung && dinhDangVe.map((point, index) => <Marker key={`dinh-${index}`} position={point} icon={L.divIcon({ className: 'polygon-vertex', html: '<span style="display:block;width:12px;height:12px;border-radius:50%;background:#f59e0b;border:2px solid white"></span>', iconSize: [16, 16] })} />)}
                {vungDaChot && <Polygon positions={vungDaChot} pathOptions={{ color: '#2563eb', fillColor: '#60a5fa', fillOpacity: 0.16, weight: 3 }} />}
                {phongTrenBanDo.map((phong) => (
                  <Marker key={phong.id} icon={GHIM}
                    position={[Number(phong.latitude), Number(phong.longitude)]}>
                    <Popup>
                      <div style={{ minWidth: 180, maxWidth: 250, color: '#1f2937' }}>
                        <strong>{phong.title}</strong>
                        <p style={{ margin: '6px 0' }}>{phong.address}</p>
                        <p style={{ margin: '6px 0', color: '#dc2626', fontWeight: 700 }}>{giaTrieu(phong.price)}</p>
                        <button type="button" style={{ ...styles.button, padding: '7px 12px' }}
                          onClick={() => moChiTiet(phong)}>Xem chi tiết</button>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
              {phongTrenBanDo.length === 0 && (
                <p style={{ margin: 0, padding: 14, color: '#92400e', background: '#fffbeb' }}>
                  Chưa có phòng nào trong kết quả tìm kiếm được gắn tọa độ. Bản đồ vẫn hoạt động; các phòng cũ cần cập nhật vĩ độ và kinh độ để hiện điểm đánh dấu.
                </p>
              )}
            </>
          )}
        </section>

        {/* BƯỚC 74: THỐNG KÊ TỪ DỮ LIỆU TIN ĐĂNG ĐÃ DUYỆT */}
        {showStats && (
          <section id="thong-ke-phong" style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 14, padding: 22, marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
              <div>
                <h2 style={{ margin: '0 0 6px' }}>📊 Thống kê phòng trọ Tronhanh123</h2>
                <p style={{ margin: 0, color: '#64748b', fontSize: 13 }}>Chỉ tính các tin đã duyệt trên website; không đại diện toàn bộ thị trường Hà Nội.</p>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button type="button" style={styles.button} onClick={taiThongKe} disabled={statsLoading}>↻ Cập nhật</button>
                <button type="button" style={{ ...styles.button, background: '#64748b' }} onClick={() => setShowStats(false)}>Đóng</button>
              </div>
            </div>
            {statsLoading && <p>Đang tải thống kê...</p>}
            {statsError && <p role="alert" style={{ color: '#dc2626' }}>{statsError}</p>}
            {stats && !statsLoading && !statsError && (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 12, margin: '20px 0' }}>
                  {[
                    ['Số phòng đã duyệt', stats.total_rooms.toLocaleString('vi-VN')],
                    ['Giá thuê trung bình', tien(stats.average_price)],
                    ['Diện tích trung bình', `${stats.average_area} m²`],
                    ['Giá thấp nhất', tien(stats.min_price)],
                    ['Giá cao nhất', tien(stats.max_price)],
                  ].map(([label, value]) => (
                    <div key={label} style={{ border: '1px solid #e2e8f0', background: '#f8fafc', padding: 15, borderRadius: 10 }}>
                      <p style={{ margin: '0 0 8px', color: '#64748b', fontSize: 13 }}>{label}</p>
                      <strong style={{ fontSize: 19, overflowWrap: 'anywhere' }}>{value}</strong>
                    </div>
                  ))}
                </div>
                {stats.total_rooms === 0 ? <p>Chưa có phòng đã duyệt để thống kê.</p> : (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(270px, 1fr))', gap: 26 }}>
                    <div>
                      <h3>Phân bố theo mức giá</h3>
                      {stats.by_price.map((item) => (
                        <div key={item.label} style={{ marginBottom: 15 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, fontSize: 14, marginBottom: 5 }}>
                            <span>{item.label}</span><strong>{item.count} phòng</strong>
                          </div>
                          <div style={{ background: '#e2e8f0', borderRadius: 20, height: 13, overflow: 'hidden' }}>
                            <div style={{ width: `${100 * item.count / stats.total_rooms}%`, background: '#2563eb', height: '100%', borderRadius: 20 }} />
                          </div>
                        </div>
                      ))}
                    </div>
                    <div>
                      <h3>Số phòng theo khu vực (tối đa 12)</h3>
                      {stats.by_district.map((item) => (
                        <div key={item.district} style={{ marginBottom: 15 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, fontSize: 14, marginBottom: 5 }}>
                            <span>{item.district}</span><strong>{item.count} phòng</strong>
                          </div>
                          <div style={{ background: '#e2e8f0', borderRadius: 20, height: 13, overflow: 'hidden' }}>
                            <div style={{ width: `${100 * item.count / stats.total_rooms}%`, background: '#16a34a', height: '100%', borderRadius: 20 }} />
                          </div>
                          <small style={{ color: '#64748b' }}>Giá TB: {tien(item.average_price)}</small>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </section>
        )}

        {/* BUOC_92_AI_DU_DOAN_GIA */}
        <RentPricePredictor />

        <div className="content-layout">

          {/* BỘ LỌC */}
          <aside className="filter-sidebar">
            <h3>Bộ lọc tìm kiếm</h3>

            <div className="filter-group">
              <label>Quận / huyện hoặc khu vực</label>
              <input
                placeholder="Nhập khu vực..."
                value={khuVuc}
                onChange={(event) =>
                  setKhuVuc(event.target.value)
                }
              />
            </div>

            <div className="filter-group">
              <label>Mức giá thuê</label>
              <select
                value={khoangGia}
                onChange={(event) =>
                  setKhoangGia(event.target.value)
                }
              >
                <option value="all">Tất cả mức giá</option>
                <option value="under3">Dưới 3 triệu</option>
                <option value="3to5">3 - 5 triệu</option>
                <option value="over5">Trên 5 triệu</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Diện tích phòng</label>
              <select
                value={khoangDienTich}
                onChange={(event) => setKhoangDienTich(event.target.value)}
              >
                <option value="all">Tất cả diện tích</option>
                <option value="under20">Dưới 20 m²</option>
                <option value="20to30">20–30 m²</option>
                <option value="30to50">Trên 30–50 m²</option>
                <option value="over50">Trên 50 m²</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Loại phòng</label>
              <select
                value={loaiPhong}
                onChange={(event) =>
                  setLoaiPhong(event.target.value)
                }
              >
                <option value="all">Tất cả loại phòng</option>
                <option value="Phòng trọ">Phòng trọ</option>
                <option value="Căn hộ mini">Căn hộ mini</option>
                <option value="Có nội thất">Có nội thất</option>
              </select>
            </div>

            <button
              className="clear-filter"
              onClick={xoaBoLoc}
            >
              Xóa bộ lọc
            </button>

            <div className="saved-box" onClick={moPhongYeuThich} role="button" tabIndex={0} onKeyDown={(event) => { if (event.key === 'Enter') moPhongYeuThich() }} style={{ cursor: 'pointer' }}>
              <span>♡</span>
              <div>
                <strong>Phòng đã lưu</strong>
                <p>{daLuu.length} phòng trọ yêu thích</p>
              </div>
            </div>
          </aside>

          {/* THẺ PHÒNG TRỌ */}
          <section className="room-section" id="danh-sach-phong">
            <div className="room-toolbar">
              <span>Danh sách phòng trọ</span>

              <select
                value={sapXep}
                onChange={(event) =>
                  setSapXep(event.target.value)
                }
              >
                <option value="new">Mới đăng nhất</option>
                <option value="old">Cũ nhất</option>
                <option value="low">Giá thấp đến cao</option>
                <option value="high">Giá cao đến thấp</option>
                <option value="area_small">Diện tích nhỏ đến lớn</option>
                <option value="area_large">Diện tích lớn đến nhỏ</option>
              </select>
            </div>

            {loiTaiPhong && (
              <p style={{ color: '#dc3545' }}>
                {loiTaiPhong}
              </p>
            )}

            {dangTaiPhong && (
              <p>Đang tải danh sách phòng trọ...</p>
            )}

            {!dangTaiPhong && !loiTaiPhong && !dangTaiTrang && !loiTaiTrang && (
              <p role="status" style={{ margin: '8px 0 16px', color: '#475569', fontSize: 14 }}>
                {dangLoc
                  ? `Tìm thấy ${tongKetQua} phòng phù hợp với các điều kiện đã chọn.`
                  : `Hiện có ${tongKetQua} phòng trọ.`}
              </p>
            )}
            {loiTaiTrang && <p role="alert" style={{ color: "#dc2626" }}>{loiTaiTrang}</p>}
            {dangTaiTrang && <p>Đang tải trang phòng trọ...</p>}
            <div className="room-grid">
              {!dangTaiTrang && !loiTaiTrang && phongTrangHienTai.length > 0 ? (
                phongTrangHienTai.map((phong) => {
                  const danhSachAnh = layAnhPhong(phong)
                  const anhDau = danhSachAnh[0]
                  const anhBiLoi = anhLoiCard.includes(phong.id)

                  return (
                    <article
                      className="room-card"
                      key={phong.id}
                    >
                      <div
                        className="room-image"
                        onClick={() => moChiTiet(phong)}
                        style={{ cursor: 'pointer' }}
                      >
                        {anhDau && !anhBiLoi ? (
                          <img
                            src={mediaUrl(anhDau)}
                            alt={phong.title}
                            style={{
                              width: '100%',
                              height: '100%',
                              objectFit: 'cover',
                            }}
                            onError={() =>
                              setAnhLoiCard((prev) =>
                                prev.includes(phong.id)
                                  ? prev
                                  : [...prev, phong.id]
                              )
                            }
                          />
                        ) : (
                          <span>🏠</span>
                        )}

                        <span className="image-label">
                          Phòng nổi bật
                        </span>

                        <button
                          className={`favorite-button ${
                            daLuu.includes(phong.id) ? 'saved' : ''
                          }`}
                          type="button"
                          aria-label={daLuu.includes(phong.id) ? 'Bỏ lưu phòng' : 'Lưu phòng'}
                          disabled={dangXuLyYeuThich.includes(phong.id)}
                          onClick={(event) => {
                            event.stopPropagation()
                            toggleLuu(phong.id)
                          }}
                        >
                          {daLuu.includes(phong.id) ? '♥' : '♡'}
                        </button>
                      </div>

                      <div className="room-info">
                        <span className="room-type">
                          {phong.type}
                        </span>

                        <h3>{phong.title}</h3>

                        <p className="room-address">
                          📍 {phong.address}
                        </p>

                        <div className="room-details">
                          <strong>{giaTrieu(phong.price)}</strong>
                          <span>{phong.area} m²</span>
                        </div>

                        <div className="room-footer">
                          <span>{phong.date}</span>

                          <button
                            onClick={() => moChiTiet(phong)}
                          >
                            Xem chi tiết →
                          </button>
                        </div>
                      </div>
                    </article>
                  )
                })
              ) : (
                !dangTaiPhong && !dangTaiTrang && !loiTaiTrang && (
                  <div className="no-result">
                    <strong>Không tìm thấy phòng trọ phù hợp.</strong>
                    <p style={{ margin: '10px 0' }}>Hãy thử thay đổi từ khóa, khu vực, mức giá hoặc diện tích.</p>
                    {dangLoc && <button type="button" style={styles.button} onClick={xoaBoLoc}>Xóa tất cả bộ lọc</button>}
                  </div>
                )
              )}
            </div>

            {!dangTaiPhong && !dangTaiTrang && !loiTaiPhong && !loiTaiTrang && tongKetQua > 0 && (
              <nav aria-label="Phân trang phòng trọ" style={{ marginTop: 24, padding: '20px 12px', borderTop: '1px solid #e2e8f0', width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, clear: 'both' }}>
                <p style={{ margin: 0, color: '#64748b', fontSize: 14 }}>
                  Hiển thị {(trangDangXem - 1) * SO_PHONG_MOI_TRANG + 1}–{Math.min(trangDangXem * SO_PHONG_MOI_TRANG, tongKetQua)} / {tongKetQua} phòng · Trang {trangDangXem}/{tongSoTrang}
                </p>
                {tongSoTrang > 1 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 8 }}>
                    <button type="button" disabled={trangDangXem === 1} onClick={() => chuyenTrang(trangDangXem - 1)}
                      style={{ ...styles.button, background: trangDangXem === 1 ? '#94a3b8' : '#2563eb', opacity: trangDangXem === 1 ? 0.65 : 1 }}>
                      ← Trang trước
                    </button>
                    {Array.from({ length: tongSoTrang }, (_, i) => i + 1).map((trang) => (
                      <button key={trang} type="button" aria-label={`Trang ${trang}`} aria-current={trang === trangDangXem ? 'page' : undefined}
                        onClick={() => chuyenTrang(trang)}
                        style={{ ...styles.button, minWidth: 40, background: trang === trangDangXem ? '#1d4ed8' : '#e2e8f0', color: trang === trangDangXem ? '#fff' : '#334155' }}>
                        {trang}
                      </button>
                    ))}
                    <button type="button" disabled={trangDangXem === tongSoTrang} onClick={() => chuyenTrang(trangDangXem + 1)}
                      style={{ ...styles.button, background: trangDangXem === tongSoTrang ? '#94a3b8' : '#2563eb', opacity: trangDangXem === tongSoTrang ? 0.65 : 1 }}>
                      Trang sau →
                    </button>
                  </div>
                )}
              </nav>
            )}
          </section>

          {/* TIỆN ÍCH */}
          <aside className="right-sidebar">
            <div className="side-box">
              <h3>Tiện ích Tronhanh123</h3>
              <a href="#ban-do" onClick={() => setShowMap(true)}>📍 Bản đồ tìm phòng</a>
              <a href="#du-doan-gia">💰 Dự đoán giá thuê</a>
              <button type="button" onClick={moThongKe} style={{ display: 'block', width: '100%', textAlign: 'left', border: 0, background: 'transparent', padding: '10px 0', cursor: 'pointer', font: 'inherit', color: 'inherit' }}>📊 Thống kê phòng trọ</button>
              <button type="button" onClick={moPhongYeuThich} style={{ display: 'block', width: '100%', textAlign: 'left', border: 0, background: 'transparent', padding: '10px 0', cursor: 'pointer', font: 'inherit', color: 'inherit' }}>♡ Phòng trọ đã lưu ({daLuu.length})</button>
            </div>

            <section className="side-box prediction-box" id="du-doan-gia" aria-label="Dự đoán giá thuê">
              <h3>💰 Dự đoán giá thuê KNN</h3>
              <p>Ước lượng từ các tin phòng trọ đã duyệt trên hệ thống.</p>
              <form onSubmit={duDoanGiaThue} className="prediction-form">
                <label htmlFor="dien-tich-du-doan">Diện tích (m²)</label>
                <input id="dien-tich-du-doan" type="number" min="5" max="300" step="0.1" required
                  value={dienTichDuDoan} onChange={(e) => setDienTichDuDoan(e.target.value)} />
                <label htmlFor="khu-vuc-du-doan">Quận / huyện (không bắt buộc)</label>
                <input id="khu-vuc-du-doan" type="text" maxLength="100" placeholder="Ví dụ: Cầu Giấy"
                  value={khuVucDuDoan} onChange={(e) => setKhuVucDuDoan(e.target.value)} />
                <button type="submit" disabled={dangDuDoan}>
                  {dangDuDoan ? 'Đang tính giá...' : 'Dự đoán giá thuê'}
                </button>
              </form>
              {loiDuDoan && <p className="prediction-error" role="alert">{loiDuDoan}</p>}
              {ketQuaDuDoan && (
                <div className="prediction-result" aria-live="polite">
                  <p>Giá thuê ước lượng</p>
                  <strong>{tien(ketQuaDuDoan.predicted_price)} / tháng</strong>
                  <p>Khoảng tham khảo: {tien(ketQuaDuDoan.suggested_min_price)} – {tien(ketQuaDuDoan.suggested_max_price)}</p>
                  <small>Dựa trên {ketQuaDuDoan.sample_count} tin phù hợp; sử dụng {ketQuaDuDoan.neighbors_used} láng giềng gần nhất.</small>
                  {Array.isArray(ketQuaDuDoan.warnings) && ketQuaDuDoan.warnings.map((warning, index) => (
                    <p className="prediction-warning" key={index}>⚠ {warning}</p>
                  ))}
                  <small>{ketQuaDuDoan.note}</small>
                </div>
              )}
            </section>

            <div
              className="side-box support-box"
              id="tien-ich"
            >
              <div className="support-icon">?</div>
              <h3>Bạn cần hỗ trợ?</h3>
              <p>
                Tronhanh123 đồng hành cùng bạn trong hành
                trình tìm phòng.
              </p>
              <button>Liên hệ hỗ trợ</button>
            </div>
          </aside>
        </div>
      </main>

      {/* FOOTER */}
      <footer className="footer">
        <div className="footer-content">
          <div className="logo footer-logo">
            <span className="logo-icon">T</span>
            <span>
              Tronhanh<span className="logo-highlight">123</span>
            </span>
          </div>
          <p>Nền tảng tìm kiếm và cho thuê phòng trọ.</p>
          <p>© 2026 Tronhanh123. All rights reserved.</p>
        </div>
      </footer>

      {/* ======================================= */}
      {/* CỬA SỔ XEM CHI TIẾT PHÒNG TRỌ */}
      {/* ======================================= */}
      {phongChiTiet && (
        <div
          style={styles.overlay}
          onClick={dongChiTiet}
        >
          <div
            style={styles.modal}
            onClick={(event) => event.stopPropagation()}
          >
            <button
              style={styles.close}
              onClick={dongChiTiet}
              aria-label="Đóng chi tiết"
            >
              ×
            </button>

            <h2 style={{ paddingRight: 40, marginBottom: 16 }}>
              {phongChiTiet.title}
            </h2>

            {/* KHUNG ẢNH LỚN */}
            <div
              onTouchStart={batDauVuot}
              onTouchEnd={ketThucVuot}
              style={{
                position: 'relative',
                background: '#111827',
                borderRadius: 12,
                overflow: 'hidden',
                height: 'min(52vw, 430px)',
                minHeight: 230,
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                touchAction: 'pan-y',
              }}
            >
              {anhChiTiet.length > 0 && !anhLoi ? (
                <img
                  key={`${phongChiTiet.id}-${anhHienTai}`}
                  src={mediaUrl(anhChiTiet[anhHienTai])}
                  alt={`Ảnh phòng trọ ${anhHienTai + 1}`}
                  onError={() => setAnhLoi(true)}
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'contain',
                    userSelect: 'none',
                  }}
                  draggable={false}
                />
              ) : (
                <div
                  style={{
                    color: 'white',
                    textAlign: 'center',
                    padding: 20,
                  }}
                >
                  <div style={{ fontSize: 65 }}>🏠</div>
                  <p>
                    {anhChiTiet.length === 0
                      ? 'Phòng này chưa có ảnh'
                      : 'Không tải được ảnh phòng trọ'}
                  </p>
                </div>
              )}

              {/* NÚT LÙI */}
              {anhChiTiet.length > 1 && (
                <button
                  type="button"
                  onClick={() => chuyenAnh(-1)}
                  aria-label="Ảnh trước"
                  style={{
                    position: 'absolute',
                    left: 12,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    width: 42,
                    height: 42,
                    borderRadius: '50%',
                    border: 0,
                    background: 'rgba(255,255,255,.9)',
                    fontSize: 26,
                    cursor: 'pointer',
                  }}
                >
                  ‹
                </button>
              )}

              {/* NÚT TIẾN */}
              {anhChiTiet.length > 1 && (
                <button
                  type="button"
                  onClick={() => chuyenAnh(1)}
                  aria-label="Ảnh tiếp theo"
                  style={{
                    position: 'absolute',
                    right: 12,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    width: 42,
                    height: 42,
                    borderRadius: '50%',
                    border: 0,
                    background: 'rgba(255,255,255,.9)',
                    fontSize: 26,
                    cursor: 'pointer',
                  }}
                >
                  ›
                </button>
              )}

              {/* SỐ THỨ TỰ ẢNH */}
              {anhChiTiet.length > 0 && (
                <div
                  style={{
                    position: 'absolute',
                    bottom: 12,
                    right: 12,
                    background: 'rgba(0,0,0,.65)',
                    color: 'white',
                    padding: '6px 13px',
                    borderRadius: 20,
                    fontSize: 14,
                  }}
                >
                  Ảnh {anhHienTai + 1} / {anhChiTiet.length}
                </div>
              )}
            </div>

            {/* DANH SÁCH ẢNH THU NHỎ */}
            {anhChiTiet.length > 1 && (
              <div
                style={{
                  display: 'flex',
                  gap: 10,
                  overflowX: 'auto',
                  padding: '14px 2px',
                }}
              >
                {anhChiTiet.map((anh, index) => (
                  <button
                    key={`${anh}-${index}`}
                    type="button"
                    onClick={() => {
                      setAnhHienTai(index)
                      setAnhLoi(false)
                    }}
                    style={{
                      flexShrink: 0,
                      padding: 0,
                      width: 90,
                      height: 65,
                      borderRadius: 8,
                      overflow: 'hidden',
                      cursor: 'pointer',
                      border: index === anhHienTai
                        ? '3px solid #2563eb'
                        : '2px solid #e5e7eb',
                      opacity: index === anhHienTai ? 1 : 0.7,
                    }}
                  >
                    <img
                      src={mediaUrl(anh)}
                      alt={`Chọn ảnh ${index + 1}`}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                      }}
                    />
                  </button>
                ))}
              </div>
            )}

            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 12,
                margin: '18px 0',
              }}
            >
              <strong
                style={{
                  color: '#dc2626',
                  fontSize: 23,
                }}
              >
                {giaTrieu(phongChiTiet.price)}
              </strong>

              <span
                style={{
                  background: '#eff6ff',
                  padding: '7px 12px',
                  borderRadius: 7,
                }}
              >
                📐 {phongChiTiet.area} m²
              </span>
            </div>

            <p>
              <strong>📍 Địa chỉ:</strong>{' '}
              {phongChiTiet.address}
            </p>

            <p>
              <strong>Khu vực:</strong>{' '}
              {phongChiTiet.district || 'Chưa cập nhật'}
            </p>

            <p>
              <strong>Ngày đăng:</strong>{' '}
              {phongChiTiet.date}
            </p>

            <hr
              style={{
                border: 0,
                borderTop: '1px solid #e5e7eb',
                margin: '20px 0',
              }}
            />

            <h3>Mô tả chi tiết</h3>

            <p
              style={{
                whiteSpace: 'pre-wrap',
                lineHeight: 1.8,
                marginTop: 10,
              }}
            >
              {phongChiTiet.description ||
                'Chưa có mô tả chi tiết.'}
            </p>

            <TienIchGIS phong={phongChiTiet} />

            {/* VIDEO PHÒNG */}
            {phongChiTiet.video && (
              <div style={{ marginTop: 25 }}>
                <h3>Video phòng trọ</h3>

                <video
                  src={mediaUrl(phongChiTiet.video)}
                  controls
                  style={{
                    width: '100%',
                    maxHeight: 400,
                    marginTop: 12,
                    borderRadius: 10,
                    background: '#111827',
                  }}
                />
              </div>
            )}

            <div
              style={{
                display: 'flex',
                gap: 12,
                flexWrap: 'wrap',
                marginTop: 25,
              }}
            >
              <button
                type="button"
                style={styles.button}
                disabled={dangXuLyYeuThich.includes(phongChiTiet.id) || phongChiTiet.status !== 'da_duyet'}
                onClick={() => toggleLuu(phongChiTiet.id)}
              >
                {daLuu.includes(phongChiTiet.id)
                  ? '♥ Đã lưu phòng'
                  : '♡ Lưu phòng yêu thích'}
              </button>

              <button
                type="button"
                onClick={dongChiTiet}
                style={{
                  ...styles.button,
                  background: '#64748b',
                }}
              >
                Đóng chi tiết
              </button>
            </div>
          </div>
        </div>
      )}

      {/* HỒ SƠ CÁ NHÂN */}
      {showProfile && nguoiDung && (
        <div style={{ ...styles.overlay, zIndex: 10003 }} onClick={() => { if (!profileBusy) setShowProfile(false) }}>
          <div style={{ ...styles.modal, maxWidth: 550 }} onClick={(event) => event.stopPropagation()}>
            <button type="button" style={styles.close} disabled={profileBusy} onClick={() => setShowProfile(false)} aria-label="Đóng">×</button>
            <h2>👤 Tài khoản cá nhân</h2>
            <p style={{ color: '#64748b' }}>Tên đăng nhập: <strong>{nguoiDung.username}</strong></p>
            <div style={{ display: 'flex', gap: 10, margin: '18px 0', flexWrap: 'wrap' }}>
              <button type="button" style={{ ...styles.button, background: profileTab === 'info' ? '#2563eb' : '#64748b' }}
                onClick={() => { setProfileTab('info'); setProfileError(''); setProfileMessage('') }}>Thông tin cá nhân</button>
              <button type="button" style={{ ...styles.button, background: profileTab === 'password' ? '#2563eb' : '#64748b' }}
                onClick={() => { setProfileTab('password'); setProfileError(''); setProfileMessage('') }}>Đổi mật khẩu</button>
            </div>
            {profileError && <p role="alert" style={{ color: '#dc2626' }}>{profileError}</p>}
            {profileMessage && <p role="status" style={{ color: '#15803d' }}>{profileMessage}</p>}
            {profileTab === 'info' ? (
              <form onSubmit={luuHoSo}>
                <label>Họ và tên</label>
                <input style={styles.input} required maxLength={150} value={profileForm.full_name}
                  onChange={(event) => setProfileForm((prev) => ({ ...prev, full_name: event.target.value }))} />
                <label>Email</label>
                <input style={styles.input} type="email" required maxLength={255} value={profileForm.email}
                  onChange={(event) => setProfileForm((prev) => ({ ...prev, email: event.target.value }))} />
                <label>Số điện thoại</label>
                <input style={styles.input} type="tel" maxLength={30} value={profileForm.phone}
                  onChange={(event) => setProfileForm((prev) => ({ ...prev, phone: event.target.value }))} />
                <button type="submit" style={styles.button} disabled={profileBusy}>
                  {profileBusy ? 'Đang lưu...' : 'Lưu thông tin'}
                </button>
              </form>
            ) : (
              <form onSubmit={doiMatKhau}>
                <label>Mật khẩu hiện tại</label>
                <input style={styles.input} type="password" autoComplete="current-password" required value={passwordForm.old_password}
                  onChange={(event) => setPasswordForm((prev) => ({ ...prev, old_password: event.target.value }))} />
                <label>Mật khẩu mới</label>
                <input style={styles.input} type="password" autoComplete="new-password" required minLength={6} value={passwordForm.new_password}
                  onChange={(event) => setPasswordForm((prev) => ({ ...prev, new_password: event.target.value }))} />
                <label>Xác nhận mật khẩu mới</label>
                <input style={styles.input} type="password" autoComplete="new-password" required minLength={6} value={passwordForm.confirm_password}
                  onChange={(event) => setPasswordForm((prev) => ({ ...prev, confirm_password: event.target.value }))} />
                <p style={{ fontSize: 13, color: '#64748b' }}>Sau khi đổi mật khẩu thành công, bạn sẽ cần đăng nhập lại.</p>
                <button type="submit" style={styles.button} disabled={profileBusy}>
                  {profileBusy ? 'Đang đổi...' : 'Xác nhận đổi mật khẩu'}
                </button>
              </form>
            )}
          </div>
        </div>
      )}

      {/* QUẢN LÝ TIN ĐĂNG CỦA TÔI */}
      {showMyRooms && (
        <div style={styles.overlay} onClick={() => { if (!savingEdit && deletingRoomId === null) setShowMyRooms(false) }}>
          <div style={styles.modal} onClick={(event) => event.stopPropagation()}>
            <button type="button" style={styles.close} onClick={() => setShowMyRooms(false)} aria-label="Đóng">×</button>
            <h2>🏠 Tin đăng của tôi</h2>
            <p>Xem và quản lý tin thuộc tài khoản của bạn, kể cả tin đang chờ duyệt.</p>
            <button type="button" style={{ ...styles.button, margin: '12px 0 20px' }} onClick={taiTinCuaToi} disabled={loadingMyRooms}>
              ↻ Tải lại danh sách
            </button>
            {loadingMyRooms && <p>Đang tải tin đăng...</p>}
            {myRoomsError && <p style={{ color: '#dc2626' }}>{myRoomsError}</p>}
            {!loadingMyRooms && !myRoomsError && myRooms.length === 0 && <p>Bạn chưa đăng tin nào.</p>}
            {myRooms.map((room) => {
              const anh = layAnhPhong(room)[0]
              return (
                <article key={room.id} style={{ display: 'flex', gap: 16, flexWrap: 'wrap', border: '1px solid #e5e7eb', borderRadius: 12, padding: 16, marginBottom: 14 }}>
                  <div style={{ width: 150, height: 115, background: '#f1f5f9', borderRadius: 8, overflow: 'hidden', display: 'grid', placeItems: 'center' }}>
                    {anh ? <img src={mediaUrl(anh)} alt={room.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : '🏠'}
                  </div>
                  <div style={{ flex: 1, minWidth: 210 }}>
                    <h3 style={{ margin: '0 0 8px' }}>{room.title}</h3>
                    <p style={{ margin: '5px 0' }}>Mã tin: #{room.id} · {nhanTrangThai(room.status)}</p>
                    <p style={{ margin: '5px 0' }}>📍 {room.address}</p>
                    <p style={{ margin: '5px 0' }}><strong>{giaTrieu(room.price)}</strong> · {room.area} m²</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 12 }}>
                      <button type="button" style={styles.button} onClick={() => {
                        setShowMyRooms(false)
                        moChiTiet({ ...room, date: room.created_at ? new Date(room.created_at).toLocaleDateString('vi-VN') : 'Mới cập nhật' })
                      }}>Xem chi tiết</button>
                      <button type="button" style={{ ...styles.button, background: '#0f766e' }} onClick={() => moSuaTin(room)}>✎ Chỉnh sửa</button>
                      <button type="button" style={{ ...styles.button, background: '#dc2626' }} disabled={deletingRoomId !== null} onClick={() => xoaTinCuaToi(room)}>
                        {deletingRoomId === room.id ? 'Đang xóa...' : '🗑 Xóa tin'}
                      </button>
                    </div>
                  </div>
                </article>
              )
            })}
          </div>
        </div>
      )}

      {/* FORM CHỈNH SỬA TIN ĐĂNG */}
      {editingRoom && (
        <div style={{ ...styles.overlay, zIndex: 10002 }} onClick={() => { if (!savingEdit) setEditingRoom(null) }}>
          <div style={{ ...styles.modal, maxWidth: 600 }} onClick={(event) => event.stopPropagation()}>
            <button type="button" style={styles.close} disabled={savingEdit} onClick={() => setEditingRoom(null)}>×</button>
            <h2>Chỉnh sửa tin #{editingRoom.id}</h2>
              <p style={{ color: '#b45309' }}>{nguoiDung?.role === 'quan_tri' ? 'Tin của Admin được duyệt tự động sau khi chỉnh sửa.' : 'Sau khi lưu, tin sẽ chuyển về Chờ duyệt để Admin kiểm tra lại.'} Ảnh và video được giữ nguyên.</p>
            <form onSubmit={luuSuaTin}>
              {[
                ['title', 'Tiêu đề phòng trọ', 'text'],
                ['address', 'Địa chỉ', 'text'],
                ['district', 'Quận / Huyện', 'text'],
                ['price', 'Giá thuê (VNĐ/tháng)', 'number'],
                ['area', 'Diện tích (m²)', 'number'],
              ].map(([key, label, type]) => (
                <div key={key}>
                  <label>{label}</label>
                  <input style={styles.input} type={type} min={type === 'number' ? 1 : undefined}
                    step={key === 'area' ? '0.1' : undefined} required
                    value={editForm[key]} onChange={(event) => setEditForm((prev) => ({ ...prev, [key]: event.target.value }))} />
                </div>
              ))}
              <label>📍 Chọn vị trí phòng trọ trên bản đồ</label>
              <BanDoChonViTri
                  address={editForm.address || ""}
                  value={
                    editForm.latitude != null &&
                    editForm.longitude != null &&
                    editForm.latitude !== "" &&
                    editForm.longitude !== ""
                      ? {
                          latitude: Number(editForm.latitude),
                          longitude: Number(editForm.longitude),
                        }
                      : null
                  }
                  onChange={({ latitude, longitude }) =>
                    setEditForm((prev) => ({
                      ...prev,
                      latitude,
                      longitude,
                    }))
                  }
                />
              <label>Mô tả phòng trọ</label>
              <textarea style={styles.input} rows={5} required value={editForm.description}
                onChange={(event) => setEditForm((prev) => ({ ...prev, description: event.target.value }))} />
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <button type="submit" style={styles.button} disabled={savingEdit}>{savingEdit ? 'Đang lưu...' : 'Lưu thay đổi'}</button>
                <button type="button" style={{ ...styles.button, background: '#64748b' }} disabled={savingEdit} onClick={() => setEditingRoom(null)}>Hủy</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DANH SÁCH PHÒNG YÊU THÍCH */}
      {showFavorites && (
        <div style={styles.overlay} onClick={() => setShowFavorites(false)}>
          <div style={styles.modal} onClick={(event) => event.stopPropagation()}>
            <button type="button" style={styles.close} onClick={() => setShowFavorites(false)} aria-label="Đóng">×</button>
            <h2>♥ Phòng trọ đã lưu ({daLuu.length})</h2>
            <p>Danh sách được lưu theo tài khoản của bạn trong PostgreSQL.</p>
            <button type="button" style={{ ...styles.button, marginBottom: 18 }} onClick={taiPhongYeuThich} disabled={dangTaiYeuThich}>
              ↻ Tải lại danh sách
            </button>
            {dangTaiYeuThich && <p>Đang tải phòng yêu thích...</p>}
            {loiYeuThich && <p style={{ color: '#dc2626' }}>{loiYeuThich}</p>}
            {!dangTaiYeuThich && !loiYeuThich && phongYeuThich.length === 0 && (
              <p>Bạn chưa lưu phòng trọ nào. Hãy bấm ♡ trên phòng bạn quan tâm.</p>
            )}
            {phongYeuThich.map((phong) => {
              const anh = layAnhPhong(phong)[0]
              return (
                <article key={phong.room_id} style={{ display: 'flex', gap: 15, padding: 14, border: '1px solid #e5e7eb', borderRadius: 12, marginBottom: 12, flexWrap: 'wrap' }}>
                  <div style={{ width: 140, height: 105, borderRadius: 8, overflow: 'hidden', background: '#e2e8f0', display: 'grid', placeItems: 'center' }}>
                    {anh ? <img src={mediaUrl(anh)} alt={phong.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : '🏠'}
                  </div>
                  <div style={{ flex: 1, minWidth: 170 }}>
                    <h3 style={{ margin: '0 0 8px' }}>{phong.title}</h3>
                    <p style={{ margin: '0 0 8px' }}>📍 {phong.address}</p>
                    <strong style={{ color: '#dc2626' }}>{giaTrieu(phong.price)}</strong>
                    <p style={{ margin: '6px 0' }}>{phong.area} m²</p>
                    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 10 }}>
                      <button type="button" style={styles.button} onClick={() => {
                        setShowFavorites(false)
                        moChiTiet({ ...phong, type: 'Phòng trọ', date: phong.saved_at ? new Date(phong.saved_at).toLocaleDateString('vi-VN') : 'Mới cập nhật' })
                      }}>Xem chi tiết</button>
                      <button type="button" disabled={dangXuLyYeuThich.includes(phong.room_id)} onClick={() => toggleLuu(phong.room_id)} style={{ ...styles.button, background: '#64748b' }}>♥ Bỏ lưu</button>
                    </div>
                  </div>
                </article>
              )
            })}
          </div>
        </div>
      )}

      {/* ======================================= */}
      {/* QUẢN TRỊ VIÊN */}
      {/* ======================================= */}
      {showAdmin && (
        <div
          style={styles.overlay}
          onClick={() => setShowAdmin(false)}
        >
          <div
            style={styles.modal}
            onClick={(event) => event.stopPropagation()}
          >
            <button
              style={styles.close}
              onClick={() => setShowAdmin(false)}
            >
              ×
            </button>

            <h2>Quản trị hệ thống</h2>
            <p>Quản trị viên: {nguoiDung?.username}</p>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', margin: '16px 0' }}>
              <button type="button" style={{ ...styles.button, background: adminTab === 'rooms' ? '#2563eb' : '#64748b' }} onClick={() => setAdminTab('rooms')}>Quản lý tin đăng</button>
              <button type="button" style={{ ...styles.button, background: adminTab === 'users' ? '#2563eb' : '#64748b' }} onClick={() => { setAdminTab('users'); taiNguoiDungAdmin() }}>Quản lý người dùng</button>
            </div>
            {adminTab === 'rooms' && (<>

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 10,
                margin: '20px 0',
              }}
            >
              <strong>
                Tin đang chờ duyệt: {danhSachChoDuyet.length}
              </strong>

              <button
                style={styles.button}
                onClick={taiTinChoDuyet}
                disabled={dangTaiTinChoDuyet}
              >
                ↻ Tải lại danh sách
              </button>
            </div>

            {thongBaoAdmin && (
              <p style={{ color: 'green' }}>
                {thongBaoAdmin}
              </p>
            )}

            {loiAdmin && (
              <p style={{ color: 'red' }}>{loiAdmin}</p>
            )}

            {dangTaiTinChoDuyet ? (
              <p>Đang tải danh sách...</p>
            ) : danhSachChoDuyet.length === 0 ? (
              <p>Hiện không có tin đăng đang chờ duyệt.</p>
            ) : (
              danhSachChoDuyet.map((tin) => (
                <article
                  key={tin.id}
                  style={{
                    border: '1px solid #e5e7eb',
                    borderRadius: 10,
                    padding: 16,
                    marginBottom: 16,
                  }}
                >
                  <h3>{tin.title}</h3>
                  <p><strong>Mã tin:</strong> {tin.id}</p>
                  <p><strong>Người đăng:</strong> {tin.user_id}</p>
                  <p><strong>Địa chỉ:</strong> {tin.address}</p>
                  <p><strong>Khu vực:</strong> {tin.district}</p>
                  <p><strong>Giá:</strong> {tien(tin.price)}</p>
                  <p><strong>Diện tích:</strong> {tin.area} m²</p>
                  <p><strong>Mô tả:</strong> {tin.description}</p>

                  {tin.images?.length > 0 && (
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns:
                          'repeat(auto-fill, minmax(130px, 1fr))',
                        gap: 10,
                        margin: '12px 0',
                      }}
                    >
                      {tin.images.map((anh, index) => (
                        <a
                          key={index}
                          href={mediaUrl(anh)}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <img
                            src={mediaUrl(anh)}
                            alt={`Ảnh ${index + 1}`}
                            style={{
                              width: '100%',
                              height: 110,
                              objectFit: 'cover',
                              borderRadius: 8,
                            }}
                          />
                        </a>
                      ))}
                    </div>
                  )}

                  {tin.video && (
                    <video
                      src={mediaUrl(tin.video)}
                      controls
                      style={{
                        width: '100%',
                        maxHeight: 280,
                      }}
                    />
                  )}

                  <div
                    style={{
                      display: 'flex',
                      gap: 10,
                      marginTop: 18,
                    }}
                  >
                    <button
                      style={{
                        ...styles.button,
                        background: '#16a34a',
                      }}
                      onClick={() =>
                        xuLyTinDang(tin.id, 'approve')
                      }
                    >
                      ✓ Duyệt tin
                    </button>

                    <button
                      style={{
                        ...styles.button,
                        background: '#dc2626',
                      }}
                      onClick={() =>
                        xuLyTinDang(tin.id, 'reject')
                      }
                    >
                      ✕ Từ chối
                    </button>
                  </div>
                </article>
              ))
            )}
            </>)}
            {adminTab === 'users' && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', margin: '20px 0' }}>
                  <strong>Danh sách người dùng ({adminUsers.length})</strong>
                  <button type="button" style={styles.button} disabled={loadingAdminUsers || processingUserId !== null} onClick={taiNguoiDungAdmin}>↻ Tải lại danh sách</button>
                </div>
                {adminUsersMessage && <p role="status" style={{ color: '#15803d' }}>{adminUsersMessage}</p>}
                {adminUsersError && <p role="alert" style={{ color: '#dc2626' }}>{adminUsersError}</p>}
                {loadingAdminUsers && <p>Đang tải danh sách người dùng...</p>}
                {!loadingAdminUsers && !adminUsersError && adminUsers.length === 0 && <p>Chưa có tài khoản nào.</p>}
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 690, textAlign: 'left' }}>
                    <thead><tr style={{ background: '#f1f5f9' }}>
                      {['ID', 'Tài khoản', 'Họ tên / Liên hệ', 'Vai trò', 'Số tin', 'Trạng thái', 'Thao tác'].map((name) => <th key={name} style={{ padding: 10, borderBottom: '1px solid #e5e7eb' }}>{name}</th>)}
                    </tr></thead>
                    <tbody>
                      {adminUsers.map((user) => (
                        <tr key={user.id}>
                          <td style={{ padding: 10, borderBottom: '1px solid #e5e7eb' }}>{user.id}</td>
                          <td style={{ padding: 10, borderBottom: '1px solid #e5e7eb' }}>{user.username}</td>
                          <td style={{ padding: 10, borderBottom: '1px solid #e5e7eb' }}>
                            <strong>{user.full_name || 'Chưa cập nhật'}</strong>
                            <div style={{ fontSize: 13, color: '#64748b' }}>{user.email}</div>
                            <div style={{ fontSize: 13, color: '#64748b' }}>{user.phone || ''}</div>
                          </td>
                          <td style={{ padding: 10, borderBottom: '1px solid #e5e7eb' }}>{user.role === 'quan_tri' ? 'Admin' : 'Người dùng'}</td>
                          <td style={{ padding: 10, borderBottom: '1px solid #e5e7eb' }}>{user.so_tin_dang ?? 0}</td>
                          <td style={{ padding: 10, borderBottom: '1px solid #e5e7eb', color: user.is_active === false ? '#dc2626' : '#15803d' }}>
                            {user.is_active === false ? 'Đã khóa' : 'Hoạt động'}
                          </td>
                          <td style={{ padding: 10, borderBottom: '1px solid #e5e7eb' }}>
                            {user.role === 'quan_tri' || user.id === nguoiDung?.id ? (
                              <span style={{ color: '#64748b' }}>Không áp dụng</span>
                            ) : (
                              <button type="button" style={{ ...styles.button, background: user.is_active === false ? '#15803d' : '#dc2626', padding: '8px 12px' }} disabled={processingUserId !== null || loadingAdminUsers} onClick={() => doiTrangThaiTaiKhoan(user)}>
                                {processingUserId === user.id ? 'Đang xử lý...' : user.is_active === false ? 'Mở khóa' : 'Khóa'}
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* XÁC NHẬN DUYỆT / TỪ CHỐI */}
      {xacNhanTin && (
        <div
          style={{ ...styles.overlay, zIndex: 10001 }}
          onClick={() => {
            if (!dangXuLyTin) setXacNhanTin(null)
          }}
        >
          <div
            style={{
              ...styles.modal,
              maxWidth: 420,
              textAlign: 'center',
            }}
            onClick={(event) => event.stopPropagation()}
          >
            <h2>
              Xác nhận {xacNhanTin.tenHanhDong} tin?
            </h2>

            <p>
              Bạn có chắc muốn {xacNhanTin.tenHanhDong}
              {' '}tin đăng này không?
            </p>

            <div
              style={{
                display: 'flex',
                gap: 12,
                justifyContent: 'center',
                marginTop: 20,
              }}
            >
              <button
                style={{
                  ...styles.button,
                  background: '#64748b',
                }}
                disabled={dangXuLyTin}
                onClick={() => setXacNhanTin(null)}
              >
                Hủy
              </button>

              <button
                style={{
                  ...styles.button,
                  background:
                    xacNhanTin.hanhDong === 'approve'
                      ? '#16a34a'
                      : '#dc2626',
                }}
                disabled={dangXuLyTin}
                onClick={xacNhanXuLyTin}
              >
                {dangXuLyTin ? 'Đang xử lý...' : 'Xác nhận'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ======================================= */}
      {/* FORM ĐĂNG TIN */}
      {/* ======================================= */}
      {showPost && (
        <div
          style={styles.overlay}
          onClick={() => setShowPost(false)}
        >
          <div
            style={{
              ...styles.modal,
              maxWidth: 600,
            }}
            onClick={(event) => event.stopPropagation()}
          >
            <button
              style={styles.close}
              onClick={() => setShowPost(false)}
            >
              ×
            </button>

            <h2>Đăng tin phòng trọ</h2>
            <p>Điền thông tin phòng trọ của bạn</p>

            <form onSubmit={xuLyDangTin}>
              {[
                ['title', 'Tiêu đề phòng trọ', 'text'],
                ['address', 'Địa chỉ', 'text'],
                ['district', 'Quận / Huyện', 'text'],
                ['price', 'Giá thuê (VNĐ/tháng)', 'number'],
                ['area', 'Diện tích (m²)', 'number'],
              ].map(([key, label, type]) => (
                <div key={key}>
                  <label>{label}</label>

                  <input
                    style={styles.input}
                    type={type}
                    min={type === 'number' ? 1 : undefined}
                    step={key === 'area' ? '0.1' : undefined}
                    value={formDangTin[key]}
                    onChange={(event) =>
                      setFormDangTin((prev) => ({
                        ...prev,
                        [key]: event.target.value,
                      }))
                    }
                    required
                  />
                </div>
              ))}

              <label>📍 Chọn vị trí phòng trọ trên bản đồ</label>
              <BanDoChonViTri
                  address={formDangTin.address}
                  value={
                    formDangTin.latitude != null &&
                    formDangTin.longitude != null &&
                    formDangTin.latitude !== '' &&
                    formDangTin.longitude !== ''
                      ? {
                          latitude: Number(formDangTin.latitude),
                          longitude: Number(formDangTin.longitude),
                        }
                      : null
                  }
                  onChange={({ latitude, longitude }) =>
                    setFormDangTin((prev) => ({
                      ...prev,
                      latitude,
                      longitude,
                    }))
                  }
                />
              <label>Mô tả phòng trọ</label>
              <textarea
                style={styles.input}
                rows={4}
                value={formDangTin.description}
                onChange={(event) =>
                  setFormDangTin((prev) => ({
                    ...prev,
                    description: event.target.value,
                  }))
                }
                required
              />

              <label>Ảnh phòng trọ (tối đa 6 ảnh)</label>
              <input
                style={styles.input}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                multiple
                onChange={xuLyChonAnh}
              />

              <p>Đã chọn {anhDaChon.length}/6 ảnh.</p>

              {anhXemTruoc.length > 0 && (
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(3, 1fr)',
                    gap: 10,
                    marginBottom: 15,
                  }}
                >
                  {anhXemTruoc.map((url, index) => (
                    <div
                      key={url}
                      style={{ position: 'relative' }}
                    >
                      <img
                        src={url}
                        alt={`Ảnh ${index + 1}`}
                        style={{
                          width: '100%',
                          height: 100,
                          objectFit: 'cover',
                          borderRadius: 8,
                        }}
                      />

                      <button
                        type="button"
                        onClick={() => xoaAnh(index)}
                        style={{
                          position: 'absolute',
                          top: 3,
                          right: 3,
                          background: '#dc2626',
                          color: 'white',
                          border: 0,
                          borderRadius: '50%',
                          width: 26,
                          height: 26,
                          cursor: 'pointer',
                        }}
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <label>Video phòng trọ (tối đa 1 video)</label>
              <input
                style={styles.input}
                type="file"
                accept="video/mp4,video/webm"
                onChange={xuLyChonVideo}
              />

              {videoXemTruoc && (
                <div style={{ marginBottom: 15 }}>
                  <video
                    src={videoXemTruoc}
                    controls
                    style={{
                      width: '100%',
                      maxHeight: 230,
                    }}
                  />

                  <button
                    type="button"
                    onClick={() => setVideoDaChon(null)}
                  >
                    Xóa video
                  </button>
                </div>
              )}

              <p style={{ color: '#64748b', fontSize: 14 }}>
                {nguoiDung?.role === 'quan_tri'
                  ? 'Tin của Admin được duyệt tự động.'
                  : 'Tin sẽ chờ quản trị viên duyệt trước khi hiển thị.'}
              </p>

              <button
                type="submit"
                style={{
                  ...styles.button,
                  width: '100%',
                }}
                disabled={dangXuLy}
              >
                {dangXuLy
                  ? 'Đang gửi tin...'
                  : 'Gửi tin đăng'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ======================================= */}
      {/* ĐĂNG NHẬP / ĐĂNG KÝ */}
      {/* ======================================= */}
      {showLogin && (
        <div
          style={styles.overlay}
          onClick={() => setShowLogin(false)}
        >
          <div
            style={{
              ...styles.modal,
              maxWidth: 450,
            }}
            onClick={(event) => event.stopPropagation()}
          >
            <button
              style={styles.close}
              onClick={() => setShowLogin(false)}
            >
              ×
            </button>

            <h2>
              {loaiForm === 'login'
                ? 'Đăng nhập'
                : 'Tạo tài khoản'}
            </h2>

            <p>Chào mừng bạn đến với Tronhanh123</p>

            <div
              style={{
                display: 'flex',
                gap: 10,
                margin: '18px 0',
              }}
            >
              <button
                type="button"
                style={{
                  ...styles.button,
                  background:
                    loaiForm === 'login'
                      ? '#2563eb'
                      : '#64748b',
                }}
                onClick={() => {
                  setLoaiForm('login')
                  setThongBao('')
                }}
              >
                Đăng nhập
              </button>

              <button
                type="button"
                style={{
                  ...styles.button,
                  background:
                    loaiForm === 'register'
                      ? '#2563eb'
                      : '#64748b',
                }}
                onClick={() => {
                  setLoaiForm('register')
                  setThongBao('')
                }}
              >
                Đăng ký
              </button>
            </div>

            {loaiForm === 'login' ? (
              <form onSubmit={xuLyDangNhap}>
                <label>Tên đăng nhập hoặc email</label>
                <input
                  style={styles.input}
                  value={usernameEmail}
                  onChange={(event) =>
                    setUsernameEmail(event.target.value)
                  }
                  required
                />

                <label>Mật khẩu</label>
                <input
                  style={styles.input}
                  type="password"
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  required
                />

                {thongBao && (
                  <p style={{ color: '#dc2626' }}>
                    {thongBao}
                  </p>
                )}

                <button
                  type="submit"
                  style={{
                    ...styles.button,
                    width: '100%',
                  }}
                  disabled={dangXuLy}
                >
                  {dangXuLy
                    ? 'Đang đăng nhập...'
                    : 'Đăng nhập'}
                </button>
              </form>
            ) : (
              <form onSubmit={xuLyDangKy}>
                {[
                  ['Họ và tên', fullName, setFullName, 'text'],
                  ['Tên đăng nhập', username, setUsername, 'text'],
                  ['Email', email, setEmail, 'email'],
                  ['Số điện thoại', phone, setPhone, 'tel'],
                  [
                    'Mật khẩu',
                    registerPassword,
                    setRegisterPassword,
                    'password',
                  ],
                ].map(([label, value, setter, type]) => (
                  <div key={label}>
                    <label>{label}</label>

                    <input
                      style={styles.input}
                      type={type}
                      value={value}
                      minLength={
                        type === 'password' ? 6 : undefined
                      }
                      onChange={(event) =>
                        setter(event.target.value)
                      }
                      required
                    />
                  </div>
                ))}

                {thongBao && (
                  <p style={{ color: '#dc2626' }}>
                    {thongBao}
                  </p>
                )}

                <button
                  type="submit"
                  style={{
                    ...styles.button,
                    width: '100%',
                  }}
                  disabled={dangXuLy}
                >
                  {dangXuLy
                    ? 'Đang đăng ký...'
                    : 'Tạo tài khoản'}
                </button>
              </form>
            )}
          </div>
        </div>
      )}

            {/* DASHBOARD_AI_BUOC_87 */}
      <button
        type="button"
        onClick={() => setShowDashboardAI(true)}
        style={{
          position: 'fixed',
          right: 22,
          bottom: 22,
          zIndex: 9000,
          background: '#2563eb',
          color: '#fff',
          border: 0,
          borderRadius: 30,
          padding: '14px 20px',
          fontWeight: 700,
          cursor: 'pointer',
          boxShadow: '0 8px 25px rgba(37,99,235,.3)',
        }}
      >
        📊 Dashboard AI
      </button>

      {showDashboardAI && (
        <DashboardAI onClose={() => setShowDashboardAI(false)} />
      )}
      {/* THÔNG BÁO CỦA ỨNG DỤNG */}
      {appNotice && (
        <div role="alert" style={{ position: 'fixed', top: 22, right: 22, zIndex: 20010,
          width: 'min(400px, calc(100vw - 44px))', background: '#fff', color: '#1e293b',
          borderLeft: `5px solid ${appNotice.type === 'error' ? '#dc2626' : '#2563eb'}`,
          boxShadow: '0 12px 35px rgba(0,0,0,.22)', borderRadius: 12,
          padding: '17px 45px 17px 18px', boxSizing: 'border-box' }}>
          <strong style={{ display: 'block', marginBottom: 6 }}>Thông báo Tronhanh123</strong>
          <div style={{ overflowWrap: 'anywhere' }}>{appNotice.message}</div>
          <button type="button" aria-label="Đóng thông báo" onClick={() => setAppNotice(null)}
            style={{ position: 'absolute', top: 8, right: 10, border: 0,
              background: 'transparent', cursor: 'pointer', fontSize: 24 }}>×</button>
        </div>
      )}

      {/* HỘP THOẠI XÁC NHẬN CỦA ỨNG DỤNG */}
      {appConfirm !== null && (
        <div style={{ ...styles.overlay, zIndex: 20020 }} onClick={() => traLoiXacNhan(false)}>
          <div role="dialog" aria-modal="true" aria-labelledby="app-confirm-title"
            style={{ ...styles.modal, maxWidth: 440 }} onClick={(event) => event.stopPropagation()}>
            <h2 id="app-confirm-title" style={{ marginTop: 0 }}>Xác nhận thao tác</h2>
            <p style={{ lineHeight: 1.6, margin: '18px 0 25px' }}>{appConfirm}</p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
              <button type="button" style={{ ...styles.button, background: '#64748b' }}
                onClick={() => traLoiXacNhan(false)}>Hủy</button>
              <button type="button" style={styles.button}
                onClick={() => traLoiXacNhan(true)}>Xác nhận</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App

