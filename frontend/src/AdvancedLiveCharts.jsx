import { useMemo } from 'react'

const COLORS = ['#2563eb', '#16a34a', '#f59e0b', '#9333ea', '#0891b2', '#ef4444']

const money = (n) => Number(n || 0).toLocaleString('vi-VN') + ' đ'

const card = {
  background: '#fff',
  border: '1px solid #e2e8f0',
  borderRadius: 14,
  padding: 20,
  marginBottom: 20,
}

function correlation(xs, ys) {
  const n = xs.length
  if (n < 2) return null

  const mx = xs.reduce((a, b) => a + b, 0) / n
  const my = ys.reduce((a, b) => a + b, 0) / n

  let numerator = 0
  let dx = 0
  let dy = 0

  for (let i = 0; i < n; i++) {
    const a = xs[i] - mx
    const b = ys[i] - my
    numerator += a * b
    dx += a * a
    dy += b * b
  }

  if (dx === 0 || dy === 0) return null
  return numerator / Math.sqrt(dx * dy)
}

function Heatmap({ rooms }) {
  const data = rooms.map(r => ({
    price: Number(r.price),
    area: Number(r.area),
    pricePerM2: Number(r.price) / Number(r.area),
  }))

  const fields = [
    ['price', 'Giá thuê'],
    ['area', 'Diện tích'],
    ['pricePerM2', 'Giá/m²'],
  ]

  return (
    <div style={card}>
      <h3>Heatmap tương quan – dữ liệu trực tiếp</h3>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ borderCollapse: 'collapse', width: '100%' }}>
          <thead>
            <tr>
              <th style={{ padding: 12 }}></th>
              {fields.map(([key, label]) => (
                <th key={key} style={{ padding: 12 }}>{label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {fields.map(([key1, label]) => (
              <tr key={key1}>
                <th style={{ padding: 12, textAlign: 'left' }}>{label}</th>
                {fields.map(([key2]) => {
                  const value = correlation(
                    data.map(d => d[key1]),
                    data.map(d => d[key2])
                  )

                  const strength = value === null ? 0 : Math.abs(value)
                  const background = value === null
                    ? '#e2e8f0'
                    : value >= 0
                      ? `rgba(37,99,235,${0.12 + strength * 0.75})`
                      : `rgba(239,68,68,${0.12 + strength * 0.75})`

                  return (
                    <td key={key2} style={{
                      background,
                      padding: 20,
                      textAlign: 'center',
                      border: '2px solid white',
                      borderRadius: 8,
                      fontWeight: 700,
                    }}>
                      {value === null ? 'N/A' : value.toFixed(2)}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p style={{ color: '#64748b', fontSize: 13 }}>
        Xanh: tương quan dương. Đỏ: tương quan âm.
        N/A: không đủ dữ liệu hoặc biến không có độ biến thiên.
      </p>
    </div>
  )
}

function Treemap({ districtStats }) {
  const total = districtStats.reduce((s, d) => s + Number(d.count), 0)

  return (
    <div style={card}>
      <h3>Treemap tỷ lệ phòng theo quận</h3>
      {total === 0 ? (
        <p>Chưa có dữ liệu.</p>
      ) : (
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          width: '100%',
          minHeight: 230,
          borderRadius: 12,
          overflow: 'hidden',
        }}>
          {districtStats.map((d, i) => (
            <div key={d.district} style={{
              flexGrow: Number(d.count),
              flexBasis: 0,
              minWidth: 110,
              minHeight: 110,
              background: COLORS[i % COLORS.length],
              color: 'white',
              padding: 15,
              border: '2px solid white',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              textAlign: 'center',
            }}>
              <strong>{d.district}</strong>
              <span>{d.count} phòng</span>
              <strong>{(Number(d.count) / total * 100).toFixed(1)}%</strong>
            </div>
          ))}
        </div>
      )}
      <p style={{ color: '#64748b', fontSize: 13 }}>
        Diện tích các ô thể hiện tương đối tỷ lệ số phòng theo khu vực.
      </p>
    </div>
  )
}

function ViolinPlot({ rooms }) {
  const prices = rooms.map(r => Number(r.price)).filter(Number.isFinite)

  if (prices.length < 2) {
    return <div style={card}>Violin Plot cần ít nhất 2 phòng hợp lệ.</div>
  }

  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const bandwidth = Math.max((max - min) / 8, 100000)

  const points = Array.from({ length: 70 }, (_, i) => {
    const value = min + (max - min || 1) * i / 69

    const density = prices.reduce((sum, p) => {
      const z = (value - p) / bandwidth
      return sum + Math.exp(-0.5 * z * z)
    }, 0) / (prices.length * bandwidth * Math.sqrt(2 * Math.PI))

    return { value, density }
  })

  const maxDensity = Math.max(...points.map(p => p.density)) || 1
  const y = v => 280 - ((v - min) / (max - min || 1)) * 240
  const w = d => d / maxDensity * 115

  const right = points.map(p => `${350 + w(p.density)},${y(p.value)}`)
  const left = [...points].reverse().map(p => `${350 - w(p.density)},${y(p.value)}`)

  return (
    <div style={card}>
      <h3>Violin Plot phân bố giá thuê</h3>
      <svg viewBox="0 0 700 330" style={{ width: '100%', maxHeight: 400 }}>
        <line x1="350" y1="35" x2="350" y2="285" stroke="#94a3b8" strokeDasharray="4 4" />
        <polygon
          points={[...right, ...left].join(' ')}
          fill="#93c5fd"
          stroke="#2563eb"
          strokeWidth="2"
        />
        {prices.map((p, i) => (
          <circle key={i} cx="350" cy={y(p)} r="3" fill="#1d4ed8" />
        ))}
        <text x="470" y="42" fontSize="14">{money(max)}</text>
        <text x="470" y="282" fontSize="14">{money(min)}</text>
      </svg>
      <p style={{ color: '#64748b', fontSize: 13 }}>
        Bề rộng thể hiện mật độ giá thuê ước lượng bằng Gaussian KDE.
        Với ít phòng, hình dạng phân bố chỉ mang tính tham khảo.
      </p>
    </div>
  )
}

export default function AdvancedLiveCharts({ rooms = [], districtStats = [] }) {
  const validRooms = useMemo(
    () => rooms.filter(r =>
      Number.isFinite(Number(r.price)) &&
      Number(r.price) > 0 &&
      Number.isFinite(Number(r.area)) &&
      Number(r.area) > 0
    ),
    [rooms]
  )

  return (
    <div>
      <ViolinPlot rooms={validRooms} />
      <Heatmap rooms={validRooms} />
      <Treemap districtStats={districtStats} />
    </div>
  )
}
