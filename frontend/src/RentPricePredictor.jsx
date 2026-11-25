import { useState } from 'react'

const API = 'http://localhost:8000'

const districts = [
  'Cầu Giấy',
  'Đống Đa',
  'Thanh Xuân',
  'Hai Bà Trưng',
  'Nam Từ Liêm',
  'Bắc Từ Liêm',
  'Hoàng Mai',
  'Hà Đông',
]

export default function RentPricePredictor() {
  const [district, setDistrict] = useState('Cầu Giấy')
  const [area, setArea] = useState('25')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function predict(event) {
    event.preventDefault()

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const params = new URLSearchParams({
        district,
        area,
      })

      const response = await fetch(
        `${API}/api/ai/live/predict?${params}`
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          typeof data.detail === 'string'
            ? data.detail
            : 'Không thể dự đoán giá thuê.'
        )
      }

      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section style={{
      background: '#fff',
      border: '1px solid #e2e8f0',
      borderRadius: 18,
      padding: 24,
      margin: '24px 0',
      boxShadow: '0 6px 24px rgba(15,23,42,.06)',
    }}>
      <h2 style={{ marginTop: 0 }}>
        🤖 Dự đoán giá phòng trọ bằng AI
      </h2>

      <p style={{ color: '#64748b' }}>
        Nhập diện tích và khu vực để tham khảo mức giá
        từ mô hình Random Forest.
      </p>

      <form onSubmit={predict} style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 12,
        alignItems: 'end',
      }}>
        <label style={{ flex: '1 1 180px' }}>
          <span style={{ display: 'block', marginBottom: 7 }}>
            Quận / khu vực
          </span>

          <select
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            style={{
              width: '100%',
              padding: 12,
              borderRadius: 9,
              border: '1px solid #cbd5e1',
            }}
          >
            {districts.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <label style={{ flex: '1 1 150px' }}>
          <span style={{ display: 'block', marginBottom: 7 }}>
            Diện tích (m²)
          </span>

          <input
            type="number"
            min="1"
            max="500"
            step="0.5"
            required
            value={area}
            onChange={(e) => setArea(e.target.value)}
            style={{
              width: '100%',
              boxSizing: 'border-box',
              padding: 12,
              borderRadius: 9,
              border: '1px solid #cbd5e1',
            }}
          />
        </label>

        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '13px 20px',
            border: 0,
            borderRadius: 9,
            background: '#2563eb',
            color: '#fff',
            cursor: loading ? 'wait' : 'pointer',
            fontWeight: 700,
          }}
        >
          {loading ? 'Đang dự đoán...' : 'Dự đoán giá'}
        </button>
      </form>

      {error && (
        <p style={{ color: '#dc2626' }}>{error}</p>
      )}

      {result && (
        <div style={{
          marginTop: 20,
          padding: 20,
          borderRadius: 12,
          background: '#eff6ff',
        }}>
          <div style={{ color: '#475569' }}>
            Giá thuê AI dự đoán
          </div>

          <div style={{
            fontSize: 30,
            fontWeight: 800,
            color: '#1d4ed8',
            margin: '8px 0',
          }}>
            {Number(result.predicted_price)
              .toLocaleString('vi-VN')} đ/tháng
          </div>

          <p>
            {result.district} · {result.area} m²
          </p>

          <p style={{ fontSize: 13, color: '#92400e' }}>
            Kết quả chỉ để kiểm thử đồ án.
            Mô hình hiện có sử dụng dữ liệu phòng giả lập,
            không phải báo giá thuê thực tế.
          </p>
        </div>
      )}
    </section>
  )
}
