import {
  ResponsiveContainer,
  LineChart,
  Line,
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

export default function PredictionComparisonCharts({ models }) {
  const rf = models?.random_forest

  if (!rf?.predicted_values?.length) {
    return (
      <div style={card}>
        Chưa có dữ liệu dự đoán ngoài mẫu để hiển thị.
      </div>
    )
  }

  const rows = rf.predicted_values.map((predicted, index) => {
    const actual = Number(rf.actual_values?.[index] || 0)
    const estimate = Number(predicted || 0)

    return {
      room: `#${rf.room_ids?.[index] ?? index + 1}`,
      actual,
      predicted: estimate,
      error: estimate - actual,
    }
  })

  return (
    <div>
      <div style={card}>
        <h3>Giá thuê thực tế và Random Forest dự đoán</h3>

        <p style={{ color: '#64748b' }}>
          Mỗi điểm là một phòng. Dự đoán được tạo bằng
          K-Fold Cross-Validation.
        </p>

        <div style={{ width: '100%', height: 360 }}>
          <ResponsiveContainer>
            <LineChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="room" interval="preserveStartEnd" />
              <YAxis
                width={75}
                tickFormatter={(v) => (v / 1000000).toFixed(1) + 'tr'}
              />
              <Tooltip formatter={(value) => money(value)} />
              <Legend />
              <Line
                type="monotone"
                dataKey="actual"
                name="Giá thực tế"
                stroke="#2563eb"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="predicted"
                name="AI dự đoán"
                stroke="#f97316"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={card}>
        <h3>Sai số dự đoán theo từng phòng</h3>

        <p style={{ color: '#64748b' }}>
          Sai số = giá dự đoán − giá thực tế.
          Giá trị dương nghĩa là AI dự đoán cao hơn giá thực tế.
        </p>

        <div style={{ width: '100%', height: 330 }}>
          <ResponsiveContainer>
            <BarChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="room" interval="preserveStartEnd" />
              <YAxis
                width={75}
                tickFormatter={(v) => (v / 1000000).toFixed(1) + 'tr'}
              />
              <Tooltip formatter={(value) => money(value)} />
              <ReferenceLine y={0} stroke="#334155" />
              <Bar
                dataKey="error"
                name="Sai số dự đoán"
                fill="#8b5cf6"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <p style={{ color: '#64748b', fontSize: 13 }}>
        Lưu ý: Đây là dự đoán ngoài mẫu trong đánh giá chéo,
        không phải dự đoán giá cho một phòng hoàn toàn mới.
      </p>
    </div>
  )
}
