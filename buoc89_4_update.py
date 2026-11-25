from pathlib import Path
import re
import shutil

path = Path("frontend/src/DashboardAI.jsx")
backup = Path("frontend/src/DashboardAI_truoc_buoc89_4.jsx.bak")

original = path.read_text(encoding="utf-8-sig")
shutil.copy2(path, backup)
content = original

# 1. Thêm state AI
anchor = "  const [liveData, setLiveData] = useState(null)"

if anchor not in content:
    raise RuntimeError("Không tìm thấy state liveData")

if "const [aiData, setAiData]" not in content:
    content = content.replace(
        anchor,
        anchor + """
  const [aiData, setAiData] = useState(null)
  const [aiStatus, setAiStatus] = useState('loading')
  const [aiError, setAiError] = useState('')
  const [aiUpdatedAt, setAiUpdatedAt] = useState(null)
""",
        1
    )

# 2. Thêm polling API AI mỗi 10 giây
anchor = "  const tabs = ["

if anchor not in content:
    raise RuntimeError("Không tìm thấy danh sách tabs")

effect = """
  useEffect(() => {
    let active = true
    let busy = false

    async function refreshAI() {
      if (busy) return
      busy = true

      try {
        const response = await fetch(
          `${API}/api/ai/live/status`,
          { cache: 'no-store' }
        )

        if (!response.ok) {
          throw new Error(`API AI trả về lỗi ${response.status}`)
        }

        const data = await response.json()

        if (!active) return

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
  }, [])

"""

if "async function refreshAI()" not in content:
    content = content.replace(anchor, effect + anchor, 1)

# 3. Thay ba tab AI cũ
start = content.find("{tab === 'models' && (")
end = content.find(
    "<p style={{ color: '#64748b', marginTop: 20, fontSize: 14 }}>",
    start
)

if start < 0 or end < 0 or end <= start:
    raise RuntimeError("Không xác định được vùng ba tab AI cũ")

# Tìm hết đoạn chú thích nguồn dữ liệu cũ.
footer_end = content.find("</p>", end)

if footer_end < 0:
    raise RuntimeError("Không tìm thấy cuối chú thích cũ")

footer_end += len("</p>")

replacement = """
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
"""

content = content[:start] + replacement + content[footer_end:]

# 4. Bỏ yêu cầu tải API models/anomalies cũ.
old_urls = """          '/api/analytics/live/dashboard',
          '/api/analytics/models',
          '/api/analytics/anomalies',"""

new_urls = """          '/api/analytics/live/dashboard',"""

if old_urls not in content:
    raise RuntimeError("Không tìm thấy danh sách API cũ")

content = content.replace(old_urls, new_urls, 1)

old_parse = "const [d, m, a] = await Promise.all(responses.map((r) => r.json()))"
new_parse = "const [d] = await Promise.all(responses.map((r) => r.json()))"

if old_parse not in content:
    raise RuntimeError("Không tìm thấy phần đọc kết quả API cũ")

content = content.replace(old_parse, new_parse, 1)

content = content.replace("          setModels(m)\n", "", 1)
content = content.replace("          setAnomalies(a)\n", "", 1)

# Xóa state không còn sử dụng.
content = content.replace(
    "  const [models, setModels] = useState(null)\n", "", 1
)
content = content.replace(
    "  const [anomalies, setAnomalies] = useState(null)\n", "", 1
)

path.write_text(content, encoding="utf-8")

print("Đã cập nhật DashboardAI.jsx")
print("Đã sao lưu tại:", backup)
print("Ba tab AI đã chuyển sang /api/ai/live/status")
