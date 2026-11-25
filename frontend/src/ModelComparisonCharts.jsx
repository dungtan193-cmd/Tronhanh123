import {
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts'

const card = {
  background: '#fff',
  border: '1px solid #e2e8f0',
  borderRadius: 14,
  padding: 18,
  marginTop: 20,
}

const money = (value) =>
  Number(value || 0).toLocaleString('vi-VN') + ' đ'

export default function ModelComparisonCharts({ models }) {
  const rows = Object.entries(models || {}).map(([key, metrics]) => ({
    name:
      key === 'knn'
        ? 'KNN'
        : key === 'random_forest'
          ? 'Random Forest'
          : key,
    mae: Number(metrics.mae || 0),
    rmse: Number(metrics.rmse || 0),
    r2: Number(metrics.r2 || 0),
  }))

  if (!rows.length) {
    return (
      <div style={card}>
        Chưa có kết quả mô hình để vẽ biểu đồ.
      </div>
    )
  }

  return (
    <div>
      <div style={card}>
        <h3>So sánh sai số MAE và RMSE</h3>
        <p style={{ color: '#64748b' }}>
          Sai số càng thấp thì mô hình càng tốt trên dữ liệu đánh giá.
        </p>

        <div style={{ width: '100%', height: 320 }}>
          <ResponsiveContainer>
            <BarChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis
                width={85}
                tickFormatter={(value) =>
                  (value / 1000000).toFixed(1) + 'tr'
                }
              />
              <Tooltip formatter={(value) => money(value)} />
              <Legend />
              <Bar dataKey="mae" name="MAE" fill="#2563eb" />
              <Bar dataKey="rmse" name="RMSE" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={card}>
        <h3>So sánh hệ số R²</h3>
        <p style={{ color: '#64748b' }}>
          R² có thể âm nếu mô hình dự đoán kém hơn cách
          dùng giá trung bình làm dự đoán.
        </p>

        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <BarChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis width={65} />
              <Tooltip formatter={(value) => Number(value).toFixed(4)} />
              <ReferenceLine y={0} stroke="#334155" />
              <Bar dataKey="r2" name="R²" fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
