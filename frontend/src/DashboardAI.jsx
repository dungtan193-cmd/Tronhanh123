import LiveGISCharts from './LiveGISCharts'
import PredictionComparisonCharts from './PredictionComparisonCharts'
import ModelComparisonCharts from './ModelComparisonCharts'
import AdvancedLiveCharts from './AdvancedLiveCharts'
import LiveCharts from './LiveCharts'
import { useEffect, useState } from 'react'

const API = 'http://localhost:8000'

const tien = (n) =>
  Number(n || 0).toLocaleString('vi-VN') + ' đ'

const card = {
  background: '#fff',
  border: '1px solid #e2e8f0',
  borderRadius: 14,
  padding: 20,
  boxShadow: '0 4px 14px rgba(15,23,42,.05)',
}

function CotGia({ label, value, max, color = '#2563eb' }) {
  const phanTram = max > 0 ? Math.max(0, Math.min(100, value / max * 100)) : 0

  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 7 }}>
        <strong>{label}</strong>
        <span>{tien(value)}</span>
      </div>
      <div style={{ background: '#e2e8f0', height: 14, borderRadius: 20, overflow: 'hidden' }}>
        <div style={{ background: color, width: `${phanTram}%`, height: '100%', borderRadius: 20 }} />
      </div>
    </div>
  )
}

function DashboardAI({ onClose }) {
  const [dashboard, setDashboard] = useState(null)
  const [liveData, setLiveData] = useState(null)
  const [aiData, setAiData] = useState(null)
  const [aiMode, setAiMode] = useState('real')
  const [aiRoomCount, setAiRoomCount] = useState(null)
  const [aiStatus, setAiStatus] = useState('loading')
  const [aiError, setAiError] = useState('')
  const [aiUpdatedAt, setAiUpdatedAt] = useState(null)

  const [liveError, setLiveError] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('overview')

  useEffect(() => {
    const controller = new AbortController()

    async function load() {
      try {
        const urls = [
          '/api/analytics/live/dashboard',
        ]

        const responses = await Promise.all(
          urls.map((url) => fetch(API + url, { signal: controller.signal }))
        )

        for (const response of responses) {
          if (!response.ok) {
            throw new Error(`API trả về lỗi ${response.status}`)
          }
        }

        const [d] = await Promise.all(responses.map((r) => r.json()))

        if (!controller.signal.aborted) {
          setDashboard(d)
        }
      } catch (err) {
        if (!controller.signal.aborted) setError(err.message)
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }

    load()
    return () => controller.abort()
  }, [])

  useEffect(() => {
    let active = true

    async function refreshLive() {
      try {
        const response = await fetch(
          `${API}/api/analytics/live/dashboard`,
          { cache: 'no-store' }
        )

        if (!response.ok) {
          throw new Error(`API lỗi ${response.status}`)
        }

        const data = await response.json()

        if (active) {
          setLiveData(data)
          setLiveError('')
        }
      } catch (err) {
        if (active) setLiveError(err.message)
      }
    }

    refreshLive()
    const timer = setInterval(refreshLive, 10000)

    return () => {
      active = false
      clearInterval(timer)
    }
  }, [])

  useEffect(() => {
    let active = true
    let busy = false

    async function refreshAI() {
      if (busy) return
      busy = true

      try {
        const response = await fetch(
          `${API}/api/ai/live/status?mode=${aiMode}`,
          { cache: 'no-store' }
        )

        if (!response.ok) {
          throw new Error(`API AI trả về lỗi ${response.status}`)
        }

        const data = await response.json()

        if (!active) return

        setAiRoomCount(data.total_rooms_in_database ?? null)
        setAiStatus(data.status)
        setAiError(data.error || '')
        setAiUpdatedAt(data.updated_at || null)

        // Không hiển thị kết quả cũ khi dữ liệu đang thay đổi.
        setAiData(
          data.is_current && data.status === 'ready'
            ? data.result
            : null
        )
      } catch (err) {
        if (active) {
          setAiStatus('error')
          setAiError(err.message)
          setAiData(null)
        }
      } finally {
        busy = false
      }
    }

    refreshAI()
    const timer = setInterval(refreshAI, 10000)

    return () => {
      active = false
      clearInterval(timer)
    }
  }, [aiMode])

  const tabs = [
    ['overview', '📊 Tổng quan'],
    ['charts', '📈 Biểu đồ phân tích'],
    ['models', '🤖 Mô hình AI'],
    ['anomalies', '🔎 Bất thường'],
    ['shap', '🧠 Giải thích SHAP'],
  ]

  const maxGia = Math.max(
    1,
    ...(liveData?.district_stats || []).map((d) => Number(d.average_price) || 0)
  )

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 15000,
      background: '#f1f5f9',
      overflowY: 'auto',
      color: '#0f172a',
    }}>
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 18px 50px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 15,
          marginBottom: 24,
        }}>
          <div>
            <h1 style={{ margin: 0 }}>📊 Dashboard AI – Tronhanh123</h1>
            <p style={{ color: '#64748b' }}>
              Phân tích dữ liệu phòng trọ và đánh giá trí tuệ nhân tạo
            </p>
          </div>
          <button type="button" onClick={onClose} style={{
            border: 0, background: '#2563eb', color: 'white',
            padding: '12px 20px', borderRadius: 9, cursor: 'pointer',
          }}>
            ← Quay lại website
          </button>
        </div>

        {loading && <div style={card}>Đang tải dữ liệu phân tích...</div>}
        {error && <div style={{ ...card, color: '#dc2626' }}>Không tải được Dashboard: {error}</div>}

        {!liveData && !liveError && (
          <div style={card}>
            Đang tải dữ liệu trực tiếp từ PostgreSQL...
          </div>
        )}

        {!liveData && liveError && (
          <div style={{ ...card, color: '#dc2626' }}>
            Không tải được dữ liệu PostgreSQL: {liveError}
          </div>
        )}

        {liveData && (
          <>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 24 }}>
              {tabs.map(([key, label]) => (
                <button key={key} type="button" onClick={() => setTab(key)}
                  style={{
                    padding: '11px 16px',
                    borderRadius: 9,
                    border: '1px solid #cbd5e1',
                    background: tab === key ? '#2563eb' : 'white',
                    color: tab === key ? 'white' : '#334155',
                    cursor: 'pointer',
                    fontWeight: 600,
                  }}>
                  {label}
                </button>
              ))}
            </div>

            {tab === 'overview' && (
              <>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
                  gap: 16,
                  marginBottom: 22,
                }}>
                  {[
                    ['Tổng số phòng', liveData.total_rooms],
                    ['Giá trung bình', tien(liveData.average_price)],
                    ['Giá thấp nhất', tien(liveData.min_price)],
                    ['Giá cao nhất', tien(liveData.max_price)],
                    ['Số khu vực', liveData.district_count],
                  ].map(([label, value]) => (
                    <div key={label} style={card}>
                      <div style={{ color: '#64748b', marginBottom: 12 }}>{label}</div>
                      <strong style={{ fontSize: 23 }}>{value}</strong>
                    </div>
                  ))}
                </div>

                <div style={card}>
                  <h2>Giá thuê trung bình theo quận</h2>
                  {liveData.district_stats.map((d) => (
                    <CotGia key={d.district} label={`${d.district} (${d.count} phòng)`}
                      value={Number(d.average_price)} max={maxGia} />
                  ))}
                </div>

                <div style={{ ...card, marginTop: 20 }}>
                  <h2>Danh sách dữ liệu phân tích</h2>
                  <p style={{ color: '#64748b' }}>Thống kê tổng quan có thể bao gồm phòng demo; bộ lọc AI thực tế chỉ áp dụng cho các tab AI.</p>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                      <thead>
                        <tr>
                          {['Mã phòng', 'Khu vực', 'Giá thuê', 'Diện tích', 'Giá/m²'].map((h) => (
                            <th key={h} style={{ padding: 12, borderBottom: '2px solid #e2e8f0' }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {liveData.rooms.map((p, i) => (
                          <tr key={`${p.id}-${i}`}>
                            <td style={{ padding: 12, borderBottom: '1px solid #e2e8f0' }}>#{p.id}</td>
                            <td style={{ padding: 12, borderBottom: '1px solid #e2e8f0' }}>{p.district}</td>
                            <td style={{ padding: 12, borderBottom: '1px solid #e2e8f0' }}>{tien(p.price)}</td>
                            <td style={{ padding: 12, borderBottom: '1px solid #e2e8f0' }}>{p.area} m²</td>
                            <td style={{ padding: 12, borderBottom: '1px solid #e2e8f0' }}>{tien(p.price_per_m2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}

                                    {/* BIỂU ĐỒ ĐỘNG TỪ POSTGRESQL */}
            {tab === 'charts' && (
              <div>
                <h2>Biểu đồ phân tích dữ liệu trực tiếp</h2>
                <p>
                  Dữ liệu lấy từ PostgreSQL và cập nhật mỗi 10 giây.
                </p>

                {liveError && (
                  <p style={{ color: '#dc2626' }}>
                    Không thể cập nhật dữ liệu: {liveError}
                  </p>
                )}

                {liveData && (
                  <>
                    <LiveCharts
                      rooms={liveData.rooms}
                      districtStats={liveData.district_stats}
                    />

                    <LiveGISCharts />
                    <AdvancedLiveCharts
                      rooms={liveData.rooms}
                      districtStats={liveData.district_stats}
                    />
                  </>
                )}
              </div>
            )}

            {['models', 'anomalies', 'shap'].includes(tab) && (
              <div style={{ ...card, marginBottom: 16 }}>
                <h3 style={{ marginTop: 0 }}>Chế độ phân tích AI</h3>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  {[
                    ['real', 'AI thực tế'],
                    ['demo', 'AI thử nghiệm (có dữ liệu demo)'],
                  ].map(([mode, label]) => (
                    <button
                      key={mode}
                      type="button"
                      onClick={() => {
                        if (mode === aiMode) return
                        setAiData(null)
                        setAiStatus('loading')
                        setAiError('')
                        setAiUpdatedAt(null)
                        setAiRoomCount(null)
                        setAiMode(mode)
                      }}
                      style={{
                        padding: '10px 14px',
                        borderRadius: 9,
                        cursor: 'pointer',
                        border: '1px solid #cbd5e1',
                        background: aiMode === mode ? '#2563eb' : '#fff',
                        color: aiMode === mode ? '#fff' : '#334155',
                        fontWeight: 600,
                      }}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                <p style={{ marginBottom: 0, color: '#475569' }}>
                  {aiMode === 'real'
                    ? 'Chỉ sử dụng phòng thật đã duyệt. Chưa đủ 30 phòng thì không huấn luyện mô hình dự đoán.'
                    : 'Bao gồm phòng demo để minh họa thuật toán; không dùng kết quả này để khẳng định độ chính xác thực tế.'}
                  {aiRoomCount !== null && ` Số phòng AI: ${aiRoomCount}.`}
                </p>
              </div>
            )}

            {['models', 'anomalies', 'shap'].includes(tab) && (
              <div style={{ ...card, marginBottom: 16 }}>
                <p style={{ margin: 0 }}>
                  <strong>Trạng thái AI: </strong>
                  {aiStatus === 'ready'
                    ? 'Đã cập nhật'
                    : aiStatus === 'processing'
                      ? 'Đang tính toán...'
                      : aiStatus === 'loading'
                        ? 'Đang tải...'
                        : 'Có lỗi'}
                </p>

                {aiUpdatedAt && (
                  <p style={{ color: '#64748b', marginBottom: 0 }}>
                    Cập nhật lúc: {new Date(aiUpdatedAt).toLocaleString('vi-VN')}
                  </p>
                )}

                {aiError && (
                  <p style={{ color: '#dc2626' }}>{aiError}</p>
                )}

                {!aiData && !aiError && (
                  <p>Đang chờ kết quả AI mới nhất từ PostgreSQL.</p>
                )}
              </div>
            )}

            {tab === 'models' && (
              <div style={card}>
                <h2>Đánh giá mô hình AI</h2>

                {aiData && (
                  <>
                    <p>
                      Số phòng hợp lệ: <strong>{aiData.total_rooms}</strong>
                    </p>

                    {aiData.training?.status !== 'ready' ? (
                      <p style={{ color: '#b45309' }}>
                        {aiData.training?.message ||
                          'Chưa có kết quả huấn luyện.'}
                      </p>
                    ) : (
                      <>
                        <p>
                          Kết quả đánh giá chéo trên dữ liệu hiện tại.
                          MAE và RMSE càng thấp càng tốt; R² càng cao càng tốt.
                        </p>

                        <div style={{ overflowX: 'auto' }}>
                          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                              <tr>
                                {['Mô hình', 'MAE', 'RMSE', 'R²'].map(label => (
                                  <th
                                    key={label}
                                    style={{
                                      padding: 12,
                                      textAlign: 'left',
                                      borderBottom: '1px solid #e2e8f0'
                                    }}
                                  >
                                    {label}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {Object.entries(aiData.training?.models || {}).map(
                                ([name, metrics]) => (
                                  <tr key={name}>
                                    <td style={{ padding: 12 }}>{name}</td>
                                    <td style={{ padding: 12 }}>{tien(metrics.mae)}</td>
                                    <td style={{ padding: 12 }}>{tien(metrics.rmse)}</td>
                                    <td style={{ padding: 12 }}>{metrics.r2}</td>
                                  </tr>
                                )
                              )}
                            </tbody>
                          </table>
                        </div>

                        <ModelComparisonCharts
                          models={aiData.training?.models}
                        />

                        <PredictionComparisonCharts
                          models={aiData.training?.models}
                        />

                        <p style={{ color: '#b45309' }}>
                          Kết quả chỉ mang tính thử nghiệm, chưa đủ cơ sở
                          để định giá phòng trọ thực tế.
                        </p>
                      </>
                    )}
                  </>
                )}
              </div>
            )}

            {tab === 'anomalies' && (
              <div style={card}>
                <h2>Phát hiện phòng có giá bất thường</h2>

                {aiData && (
                  <>
                    <h3>Phương pháp IQR</h3>

                    <p>
                      {aiData.iqr?.status === 'ready'
                        ? `Phát hiện ${aiData.iqr.outliers?.length || 0} phòng có giá nằm ngoài ngưỡng IQR.`
                        : aiData.iqr?.message}
                    </p>

                    {(aiData.iqr?.outliers || []).map(room => (
                      <p key={room.id}>
                        Phòng #{room.id} – {room.district} – {tien(room.price)}
                      </p>
                    ))}

                    <h3>Isolation Forest</h3>

                    {aiData.isolation_forest?.status !== 'ready' ? (
                      <p style={{ color: '#b45309' }}>
                        {aiData.isolation_forest?.message}
                      </p>
                    ) : (
                      <>
                        <p>
                          Phát hiện {aiData.isolation_forest.outliers?.length || 0}
                          {' '}phòng có dấu hiệu bất thường.
                        </p>

                        {(aiData.isolation_forest.outliers || []).map(room => (
                          <p key={room.id}>
                            Phòng #{room.id} – {room.district} – {tien(room.price)}
                          </p>
                        ))}
                      </>
                    )}

                    <p style={{ color: '#64748b' }}>
                      Phòng bị đánh dấu bất thường không nhất thiết có dữ liệu sai.
                      Cần kiểm tra trước khi đưa ra quyết định.
                    </p>
                  </>
                )}
              </div>
            )}

            {tab === 'shap' && (
              <div style={card}>
                <h2>Giải thích Random Forest bằng SHAP</h2>

                {aiData && (
                  aiData.training?.shap?.status === 'ready' ? (
                    <>
                      <p>
                        Mức ảnh hưởng SHAP trung bình của các đặc trưng
                        trong mô hình hiện tại.
                      </p>

                      {(aiData.training.shap.features || []).map(item => (
                        <div key={item.feature} style={{ marginBottom: 14 }}>
                          <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            gap: 12
                          }}>
                            <strong>{item.feature}</strong>
                            <span>{tien(item.mean_abs_shap)}</span>
                          </div>

                          <div style={{
                            background: '#e2e8f0',
                            height: 12,
                            borderRadius: 8,
                            overflow: 'hidden',
                            marginTop: 6
                          }}>
                            <div style={{
                              height: '100%',
                              background: '#6366f1',
                              width: `${
                                100 * item.mean_abs_shap /
                                Math.max(
                                  1,
                                  ...(aiData.training.shap.features || [])
                                    .map(x => x.mean_abs_shap)
                                )
                              }%`
                            }} />
                          </div>
                        </div>
                      ))}
                    </>
                  ) : (
                    <p style={{ color: '#b45309' }}>
                      {aiData.training?.shap?.message ||
                        aiData.training?.message ||
                        'Chưa có dữ liệu SHAP cho mô hình hiện tại.'}
                    </p>
                  )
                )}
              </div>
            )}

          </>
        )}
      </div>
    </div>
  )
}

export default DashboardAI






