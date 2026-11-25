import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ScatterChart,
  Scatter,
  ZAxis,
  Cell,
} from 'recharts'

const COLORS = [
  '#2563eb', '#16a34a', '#f59e0b',
  '#9333ea', '#ef4444', '#0891b2'
]

const money = (n) => Number(n || 0).toLocaleString('vi-VN') + ' đ'

const cardStyle = {
  background: '#fff',
  border: '1px solid #e2e8f0',
  borderRadius: 14,
  padding: 20,
  marginBottom: 20,
}

function quantile(sorted, q) {
  if (!sorted.length) return 0

  const pos = (sorted.length - 1) * q
  const lower = Math.floor(pos)
  const upper = Math.ceil(pos)

  if (lower === upper) return sorted[lower]

  return sorted[lower] +
    (sorted[upper] - sorted[lower]) * (pos - lower)
}

function Boxplot({ rooms }) {
  const prices = rooms
    .map((r) => Number(r.price))
    .filter((n) => Number.isFinite(n) && n > 0)
    .sort((a, b) => a - b)

  if (!prices.length) return <p>Chưa có dữ liệu.</p>

  const q1 = quantile(prices, 0.25)
  const median = quantile(prices, 0.5)
  const q3 = quantile(prices, 0.75)
  const iqr = q3 - q1
  const lowFence = q1 - 1.5 * iqr
  const highFence = q3 + 1.5 * iqr
  const inliers = prices.filter((p) => p >= lowFence && p <= highFence)
  const low = Math.min(...inliers)
  const high = Math.max(...inliers)
  const outliers = prices.filter((p) => p < lowFence || p > highFence)

  const width = 760
  const left = 55
  const right = 720
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || 1
  const x = (value) => left + ((value - min) / range) * (right - left)

  return (
    <div style={cardStyle}>
      <h3>Boxplot giá thuê – cập nhật trực tiếp</h3>
      <svg viewBox="0 0 760 180" style={{ width: '100%' }}>
        <line x1={left} y1="100" x2={right} y2="100" stroke="#cbd5e1" />
        <line x1={x(low)} y1="65" x2={x(low)} y2="115" stroke="#2563eb" strokeWidth="3" />
        <line x1={x(high)} y1="65" x2={x(high)} y2="115" stroke="#2563eb" strokeWidth="3" />
        <line x1={x(low)} y1="90" x2={x(q1)} y2="90" stroke="#2563eb" strokeWidth="3" />
        <line x1={x(q3)} y1="90" x2={x(high)} y2="90" stroke="#2563eb" strokeWidth="3" />
        <rect
          x={x(q1)}
          y="55"
          width={Math.max(1, x(q3) - x(q1))}
          height="70"
          fill="#bfdbfe"
          stroke="#2563eb"
          strokeWidth="2"
        />
        <line x1={x(median)} y1="55" x2={x(median)} y2="125" stroke="#dc2626" strokeWidth="3" />
        {outliers.map((p, i) => (
          <circle key={i} cx={x(p)} cy="90" r="6" fill="#ef4444" />
        ))}
        <text x={left} y="155" fontSize="13">{money(min)}</text>
        <text x={right} y="155" textAnchor="end" fontSize="13">{money(max)}</text>
      </svg>
      <p>Q1: {money(q1)} | Trung vị: {money(median)} | Q3: {money(q3)}</p>
      <p>Giá trị ngoại lệ theo IQR: {outliers.length} phòng</p>
    </div>
  )
}

function LiveCharts({ rooms = [], districtStats = [] }) {
  const validRooms = rooms.filter(
    (r) => Number(r.price) > 0 && Number(r.area) > 0
  )

  const scatterData = validRooms.map((r) => ({
    id: r.id,
    area: Number(r.area),
    price: Number(r.price),
    district: r.district,
  }))

  return (
    <div>
      <div style={cardStyle}>
        <h3>Giá thuê trung bình theo quận</h3>
        <div style={{ width: '100%', height: 320 }}>
          <ResponsiveContainer>
            <BarChart data={districtStats} margin={{ top: 10, right: 20, left: 20, bottom: 35 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="district" interval={0} angle={-15} textAnchor="end" height={65} />
              <YAxis tickFormatter={(v) => `${(v / 1000000).toFixed(1)}tr`} />
              <Tooltip formatter={(v) => money(v)} />
              <Bar dataKey="average_price" name="Giá trung bình">
                {districtStats.map((d, i) => (
                  <Cell key={d.district} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <Boxplot rooms={validRooms} />

      <div style={cardStyle}>
        <h3>Diện tích và giá thuê từng phòng</h3>
        <div style={{ width: '100%', height: 330 }}>
          <ResponsiveContainer>
            <ScatterChart margin={{ top: 15, right: 25, bottom: 20, left: 20 }}>
              <CartesianGrid />
              <XAxis type="number" dataKey="area" name="Diện tích" unit=" m²" />
              <YAxis type="number" dataKey="price" name="Giá thuê" tickFormatter={(v) => `${(v / 1000000).toFixed(1)}tr`} />
              <ZAxis range={[90, 90]} />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                formatter={(value, name) => name === 'Giá thuê' ? money(value) : value}
              />
              <Scatter name="Phòng trọ" data={scatterData} fill="#2563eb" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={cardStyle}>
        <h3>Số lượng phòng theo quận</h3>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <BarChart data={districtStats}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="district" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" name="Số phòng" fill="#16a34a" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

export default LiveCharts
