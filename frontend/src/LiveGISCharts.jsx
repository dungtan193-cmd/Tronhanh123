import { useEffect, useState } from 'react'

const API = 'http://localhost:8000'

export default function LiveGISCharts() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [updatedAt, setUpdatedAt] = useState(null)

  useEffect(() => {
    let active = true
    let busy = false

    async function refresh() {
      if (busy) return
      busy = true

      try {
        const response = await fetch(
          `${API}/api/ai/gis/features`,
          { cache: 'no-store' }
        )

        if (!response.ok) {
          throw new Error(`API GIS lỗi ${response.status}`)
        }

        const result = await response.json()

        if (active) {
          setData(result)
          setError('')
          setUpdatedAt(new Date())
        }
      } catch (err) {
        if (active) setError(err.message)
      } finally {
        busy = false
      }
    }

    refresh()

    const timer = setInterval(refresh, 10000)

    return () => {
      active = false
      clearInterval(timer)
    }
  }, [])

  const rooms = data?.rooms || []

  const average = (field) => {
    const values = rooms
      .map(room => Number(room[field]))
      .filter(Number.isFinite)

    if (!values.length) return 0

    return values.reduce((a, b) => a + b, 0) / values.length
  }

  const totalAmenities = (room) =>
    ['bus_stops_1km', 'schools_1km', 'hospitals_1km', 'parks_1km']
      .reduce((sum, key) => sum + Number(room[key] || 0), 0)

  const number = (value) =>
    Number(value || 0).toLocaleString('vi-VN')

  const card = {
    padding: 18,
    background: '#fff',
    border: '1px solid #e2e8f0',
    borderRadius: 12,
  }

  return (
    <section style={{ marginTop: 24 }}>
      <h2>Phân tích GIS tự động</h2>

      <p>
        Dữ liệu lấy trực tiếp từ PostgreSQL/PostGIS,
        cập nhật mỗi 10 giây.
      </p>

      {updatedAt && (
        <p style={{ fontSize: 13, color: '#64748b' }}>
          Cập nhật lúc: {updatedAt.toLocaleTimeString('vi-VN')}
        </p>
      )}

      {error && (
        <p style={{ color: '#dc2626' }}>
          Không thể cập nhật GIS: {error}
        </p>
      )}

      {!data && !error && <p>Đang tải dữ liệu GIS...</p>}

      {data && (
        <>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: 16,
            marginBottom: 24,
          }}>
            <div style={card}>
              <p>Số phòng đủ điều kiện GIS</p>
              <h2>{number(data.total_rooms)}</h2>
            </div>

            <div style={card}>
              <p>Khoảng cách đại học trung bình</p>
              <h2>{number(average('nearest_university_m').toFixed(1))} m</h2>
            </div>

            <div style={card}>
              <p>Tiện ích trung bình trong 1 km</p>
              <h2>
                {rooms.length
                  ? (rooms.reduce((s, r) => s + totalAmenities(r), 0) / rooms.length).toFixed(1)
                  : 0}
              </h2>
            </div>
          </div>

          <div style={{ ...card, overflowX: 'auto' }}>
            <h3>Đặc trưng GIS của các phòng</h3>

            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
              textAlign: 'left',
            }}>
              <thead>
                <tr>
                  {[
                    'Phòng',
                    'Giá thuê',
                    'Đại học gần nhất',
                    'Xe buýt',
                    'Trường học',
                    'Bệnh viện',
                    'Công viên',
                  ].map(label => (
                    <th key={label} style={{
                      padding: 10,
                      borderBottom: '1px solid #cbd5e1',
                    }}>
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {rooms.map(room => (
                  <tr key={room.room_id}>
                    <td style={{ padding: 10 }}>{room.room_id}</td>
                    <td style={{ padding: 10 }}>{number(room.price)} đ</td>
                    <td style={{ padding: 10 }}>
                      {room.nearest_university_m == null
                        ? 'Chưa có dữ liệu'
                        : `${number(room.nearest_university_m)} m`}
                    </td>
                    <td style={{ padding: 10 }}>{room.bus_stops_1km}</td>
                    <td style={{ padding: 10 }}>{room.schools_1km}</td>
                    <td style={{ padding: 10 }}>{room.hospitals_1km}</td>
                    <td style={{ padding: 10 }}>{room.parks_1km}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p style={{ marginTop: 14, color: '#64748b' }}>
            Khi phòng mới được duyệt và có tọa độ hợp lệ,
            dữ liệu GIS sẽ tự xuất hiện ở lần cập nhật tiếp theo.
          </p>
        </>
      )}
    </section>
  )
}
