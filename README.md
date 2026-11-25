# TRONHANH123 – HỆ THỐNG TÌM KIẾM VÀ QUẢN LÝ PHÒNG TRỌ

## 1. Giới thiệu dự án

**Tronhanh123** là hệ thống website hỗ trợ tìm kiếm, đăng tin và quản lý phòng trọ. Dự án hướng đến việc giúp người thuê dễ dàng tìm được phòng phù hợp, đồng thời hỗ trợ chủ trọ đăng tin và quản lý thông tin cho thuê.

Hệ thống được xây dựng với giao diện tiếng Việt, bố cục trực quan và tích hợp các chức năng phân tích dữ liệu, bản đồ GIS và trí tuệ nhân tạo.

## 2. Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Frontend | ReactJS, Vite, JavaScript, CSS |
| Backend | Python, FastAPI |
| Cơ sở dữ liệu | PostgreSQL |
| Bản đồ | GIS, dữ liệu OpenStreetMap |
| Trí tuệ nhân tạo | Machine Learning |
| Công cụ phát triển | Visual Studio Code, Git, GitHub, Docker |

## 3. Các chức năng chính

- **Đăng ký và đăng nhập:** Hỗ trợ người dùng tạo tài khoản và đăng nhập hệ thống.
- **Tìm kiếm phòng trọ:** Hiển thị danh sách phòng trọ, hỗ trợ tìm kiếm và lọc thông tin.
- **Đăng tin cho thuê:** Chủ trọ có thể đăng thông tin phòng cho thuê.
- **Quản lý tin đăng:** Hỗ trợ quản lý và kiểm duyệt tin đăng.
- **Lưu tin yêu thích:** Người dùng có thể lưu những phòng trọ quan tâm.
- **Bản đồ GIS:** Hiển thị thông tin phòng trọ và hỗ trợ phân tích vị trí.
- **Dự đoán giá thuê:** Ứng dụng Machine Learning để hỗ trợ dự đoán giá phòng.
- **Thống kê và phân tích:** Cung cấp biểu đồ và thông tin phân tích dữ liệu phòng trọ.
- **Quản trị hệ thống:** Hỗ trợ quản lý tài khoản và nội dung hệ thống.

## 4. Cấu trúc dự án

```text
Tronhanh123/
├── backend/             # API và xử lý nghiệp vụ
│   ├── routers/         # Các API chức năng
│   └── services/        # Các dịch vụ xử lý
├── database/            # Kết nối và thao tác cơ sở dữ liệu
├── frontend/            # Giao diện ReactJS
│   ├── public/
│   └── src/
├── data/                # Dữ liệu phục vụ phân tích
├── models/              # Mô hình Machine Learning
├── pages/               # Các trang chức năng
├── assets/              # Tài nguyên dự án
├── reports/             # Báo cáo và kết quả phân tích
├── test/                # Các chương trình kiểm thử
├── app.py
└── requirements.txt
```

## 5. Hướng dẫn cài đặt và chạy dự án

### Yêu cầu môi trường

- Python
- Node.js và npm
- PostgreSQL
- Docker (nếu sử dụng PostgreSQL qua Docker)
- Visual Studio Code

### Bước 1: Cài đặt thư viện Backend

Mở terminal tại thư mục dự án:

```powershell
pip install -r requirements.txt
```

### Bước 2: Khởi động cơ sở dữ liệu

Đảm bảo PostgreSQL đang hoạt động và thông tin kết nối trong dự án đã được cấu hình chính xác.

Nếu sử dụng container PostgreSQL đã tạo trước đó:

```powershell
docker start postgres_db
```

### Bước 3: Chạy Backend

Tại thư mục gốc `D:\baicuoiki`, mở terminal và chạy:

```powershell
uvicorn backend.main:app --reload
```

Backend mặc định:

```text
http://127.0.0.1:8000
```

Tài liệu API:

```text
http://127.0.0.1:8000/docs
```

### Bước 4: Chạy Frontend

Mở terminal thứ hai:

```powershell
cd frontend
npm install
npm run dev
```

Truy cập giao diện website tại:

```text
http://localhost:5173
```

## 6. Mục tiêu dự án

- Xây dựng hệ thống hỗ trợ tìm kiếm và quản lý phòng trọ.
- Ứng dụng công nghệ Web vào giải quyết nhu cầu thực tế.
- Tích hợp GIS để hỗ trợ tìm kiếm và phân tích vị trí.
- Ứng dụng Machine Learning trong phân tích và dự đoán giá thuê.
- Xây dựng hệ thống có khả năng mở rộng và phát triển thêm chức năng.

## 7. Thông tin dự án

- **Tên dự án:** Tronhanh123
- **Lĩnh vực:** Công nghệ thông tin – Quản lý phòng trọ
- **Ngôn ngữ lập trình:** Python, JavaScript
- **Repository:** https://github.com/dungtan193-cmd/Tronhanh123

---

*Tronhanh123 – Hệ thống tìm kiếm và quản lý phòng trọ.*