import React from "react";

const charts = [
  {
    title: "1. Giá thuê từng phòng",
    description: "So sánh giá thuê của 7 phòng được duyệt.",
    image: "/gis-charts/01_rental_prices.png",
  },
  {
    title: "2. Khoảng cách đến đại học",
    description: "Khoảng cách từ mỗi phòng đến trường đại học gần nhất.",
    image: "/gis-charts/02_university_distance.png",
  },
  {
    title: "3. Tiện ích trong bán kính 1 km",
    description: "Số lượng tiện ích xung quanh từng phòng.",
    image: "/gis-charts/03_amenities.png",
  },
  {
    title: "4. Khoảng cách và giá thuê",
    description: "Khảo sát mối quan hệ giữa vị trí và giá thuê.",
    image: "/gis-charts/04_distance_vs_price.png",
  },
];

export default function GISAnalysis() {
  return (
    <div style={{
      maxWidth: 1200,
      margin: "0 auto",
      padding: "32px 20px",
      fontFamily: "Arial, sans-serif",
    }}>
      <h1>Phân tích dữ liệu GIS</h1>

      <p>
        Dữ liệu từ PostgreSQL/PostGIS, gồm 7 phòng được duyệt
        và các tiện ích xung quanh.
      </p>

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
        gap: 24,
        marginTop: 28,
      }}>
        {charts.map((chart) => (
          <section key={chart.image} style={{
            background: "#fff",
            border: "1px solid #ddd",
            borderRadius: 12,
            padding: 16,
            boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
          }}>
            <h2 style={{ fontSize: 19 }}>{chart.title}</h2>
            <p style={{ color: "#555" }}>{chart.description}</p>

            <img
              src={chart.image}
              alt={chart.title}
              style={{ width: "100%", borderRadius: 8 }}
            />
          </section>
        ))}
      </div>

      <p style={{
        marginTop: 28,
        padding: 16,
        background: "#fff7ed",
        borderRadius: 8,
      }}>
        Lưu ý: Đây là phân tích mô tả trên 7 phòng.
        Phòng ID 3 có giá thuê bất thường cần kiểm tra.
        Kết quả chưa đủ để kết luận quan hệ nhân quả
        giữa vị trí và giá thuê.
      </p>
    </div>
  );
}
