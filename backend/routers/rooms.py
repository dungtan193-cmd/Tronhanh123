from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from pathlib import Path
from typing import Optional
from math import isfinite
from statistics import median
from uuid import uuid4

from database.connection import ket_noi_db

router = APIRouter(prefix="/api/rooms", tags=["Quản lý phòng trọ"])


def kiem_tra_toa_do(latitude: Optional[float], longitude: Optional[float]):
    """Tọa độ phải đi thành cặp và nằm trong giới hạn địa lý."""
    if (latitude is None) != (longitude is None):
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp cả vĩ độ và kinh độ!")
    if latitude is not None and (
        not isfinite(latitude) or not isfinite(longitude)
        or not (-90 <= latitude <= 90)
        or not (-180 <= longitude <= 180)
    ):
        raise HTTPException(status_code=400, detail="Tọa độ không hợp lệ!")



def kiem_tra_tai_khoan_hoat_dong(request: Request):
    """Xác minh phiên đăng nhập và trạng thái tài khoản từ database."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Bạn cần đăng nhập!")

    conn = ket_noi_db()
    if conn is None:
        raise HTTPException(status_code=503, detail="Không kết nối được cơ sở dữ liệu!")

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT is_active FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user is None:
            request.session.clear()
            raise HTTPException(status_code=401, detail="Tài khoản không tồn tại!")
        if user[0] is False:
            request.session.clear()
            raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên!")
        return user_id
    finally:
        if cursor:
            cursor.close()
        conn.close()


def kiem_tra_noi_dung_phong(title, address, district, price, area, description):
    """Giới hạn dữ liệu và từ chối số NaN/Infinity ở cả POST và PUT."""
    for label, value, maximum in (
        ("Tiêu đề", title, 200),
        ("Địa chỉ", address, 300),
        ("Khu vực", district, 100),
        ("Mô tả", description, 10000),
    ):
        if not isinstance(value, str) or not value.strip():
            raise HTTPException(status_code=422, detail=f"{label} không được để trống!")
        if len(value.strip()) > maximum:
            raise HTTPException(status_code=422, detail=f"{label} vượt quá {maximum} ký tự!")
    if not isfinite(price) or not (100000 <= price <= 100000000):
        raise HTTPException(status_code=422, detail="Giá thuê phải từ 100.000 đến 100.000.000 đồng!")
    if not isfinite(area) or not (5 <= area <= 300):
        raise HTTPException(status_code=422, detail="Diện tích phải từ 5 đến 300 m²!")


# Thư mục lưu ảnh và video
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads" / "rooms"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_IMAGES = 6
MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_VIDEO_SIZE = 100 * 1024 * 1024

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".webm"}


def luu_file(file: UploadFile, loai: str, gioi_han: int):
    """Kiểm tra và lưu một ảnh hoặc video."""
    extension = Path(file.filename or "").suffix.lower()

    if loai == "image" and extension not in IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Ảnh chỉ hỗ trợ JPG, JPEG, PNG hoặc WEBP!")

    if loai == "video" and extension not in VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Video chỉ hỗ trợ MP4 hoặc WEBM!")

    # Đọc tối đa giới hạn + 1 byte để không nạp file quá lớn vào RAM.
    content = file.file.read(gioi_han + 1)
    if not content:
        raise HTTPException(status_code=400, detail="File tải lên đang trống!")
    if len(content) > gioi_han:
        raise HTTPException(status_code=400, detail=f"File vượt quá giới hạn {gioi_han // (1024 * 1024)} MB!")

    # Không chỉ tin vào phần mở rộng do người dùng cung cấp.
    if loai == "image":
        valid = (
            (extension in (".jpg", ".jpeg") and content.startswith(b"\xff\xd8\xff"))
            or (extension == ".png" and content.startswith(b"\x89PNG\r\n\x1a\n"))
            or (extension == ".webp" and content.startswith(b"RIFF") and content[8:12] == b"WEBP")
        )
    else:
        valid = (
            (extension == ".mp4" and len(content) >= 12 and content[4:8] == b"ftyp")
            or (extension == ".webm" and content.startswith(b"\x1a\x45\xdf\xa3"))
        )
    if not valid:
        raise HTTPException(status_code=400, detail="Nội dung file không khớp định dạng đã chọn!")

    ten_file = f"{uuid4().hex}{extension}"
    duong_dan = UPLOAD_DIR / ten_file
    duong_dan.write_bytes(content)
    return f"/uploads/rooms/{ten_file}", duong_dan



def _tai_media_hang_loat(cursor, room_ids):
    """Một truy vấn cho toàn bộ ảnh/video của danh sách phòng (tránh N+1)."""
    if not room_ids:
        return {}
    cursor.execute("""
        SELECT room_id, file_path, media_type
        FROM room_media
        WHERE room_id = ANY(%s)
        ORDER BY room_id, id
    """, (room_ids,))
    result = {room_id: {"images": [], "video": None} for room_id in room_ids}
    for room_id, path, kind in cursor.fetchall():
        if kind == "image":
            result[room_id]["images"].append(path)
        elif kind == "video" and result[room_id]["video"] is None:
            result[room_id]["video"] = path
    return result


@router.get("")
def danh_sach_phong():
    conn = ket_noi_db()

    if conn is None:
        raise HTTPException(status_code=503, detail="Không kết nối được cơ sở dữ liệu!")

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, title, address, district,
                   price, area, description, image, status, created_at, latitude, longitude
            FROM rooms
            WHERE status = 'da_duyet'
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        danh_sach = []

        media_map = _tai_media_hang_loat(cursor, [row[0] for row in rows])
        for row in rows:
            media = media_map[row[0]]

            danh_sach.append({
                "id": row[0],
                "user_id": row[1],
                "title": row[2],
                "address": row[3],
                "district": row[4],
                "price": float(row[5]),
                "area": float(row[6]),
                "description": row[7],
                "image": row[8],
                "status": row[9],
                "created_at": row[10].isoformat() if row[10] else None,
                "latitude": row[11],
                "longitude": row[12],
                "images": media["images"],
                "video": media["video"]
            })

        return {"status": "success", "data": danh_sach}
    finally:
        if cursor:
            cursor.close()
        conn.close()


@router.get("/paged")
def danh_sach_phong_phan_trang(
    page: int = 1,
    limit: int = 6,
    keyword: str = "",
    district: str = "",
    price_range: str = "all",
    area_range: str = "all",
    room_type: str = "all",
    sort: str = "new",
):
    """Lọc và phân trang phòng trọ trực tiếp trong PostgreSQL."""

    if page < 1 or limit < 1 or limit > 100:
        raise HTTPException(
            status_code=422,
            detail="Trang hoặc số phòng mỗi trang không hợp lệ!"
        )

    if price_range not in ("all", "under3", "3to5", "over5"):
        raise HTTPException(
            status_code=422,
            detail="Khoảng giá không hợp lệ!"
        )

    if area_range not in (
        "all", "under20", "20to30", "30to50", "over50"
    ):
        raise HTTPException(
            status_code=422,
            detail="Khoảng diện tích không hợp lệ!"
        )

    if sort not in ("new", "old", "low", "high", "area_small", "area_large"):
        raise HTTPException(
            status_code=422,
            detail="Kiểu sắp xếp không hợp lệ!"
        )

    conn = ket_noi_db()

    if conn is None:
        raise HTTPException(
            status_code=503,
            detail="Không kết nối được cơ sở dữ liệu!"
        )

    cursor = None

    try:
        cursor = conn.cursor()

        dieu_kien = ["status = 'da_duyet'"]
        tham_so = []

        # Lọc theo từ khóa
        if keyword.strip():
            dieu_kien.append(
                "(title ILIKE %s OR address ILIKE %s OR district ILIKE %s)"
            )
            tu_khoa = f"%{keyword.strip()}%"
            tham_so.extend([tu_khoa, tu_khoa, tu_khoa])

        # Lọc theo khu vực
        if district.strip():
            dieu_kien.append(
                "(district ILIKE %s OR address ILIKE %s)"
            )
            khu_vuc = f"%{district.strip()}%"
            tham_so.extend([khu_vuc, khu_vuc])

        # Lọc theo giá thuê
        if price_range == "under3":
            dieu_kien.append("price < 3000000")

        elif price_range == "3to5":
            dieu_kien.append(
                "price >= 3000000 AND price <= 5000000"
            )

        elif price_range == "over5":
            dieu_kien.append("price > 5000000")

        # Lọc theo diện tích
        if area_range == "under20":
            dieu_kien.append("area < 20")

        elif area_range == "20to30":
            dieu_kien.append(
                "area >= 20 AND area <= 30"
            )

        elif area_range == "30to50":
            dieu_kien.append(
                "area > 30 AND area <= 50"
            )

        elif area_range == "over50":
            dieu_kien.append("area > 50")

        # Hiện database chưa có cột type
        if room_type not in ("all", "Phòng trọ"):
            dieu_kien.append("1 = 0")

        where_sql = " AND ".join(
            f"({item})" for item in dieu_kien
        )

        # Đếm tổng số phòng phù hợp
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM rooms
            WHERE {where_sql}
            """,
            tuple(tham_so)
        )

        total = cursor.fetchone()[0]

        total_pages = max(
            1,
            (total + limit - 1) // limit
        )

        current_page = min(page, total_pages)

        # Sắp xếp
        kieu_sap_xep = {
            "new": "created_at DESC NULLS LAST, id DESC",
            "old": "created_at ASC NULLS LAST, id ASC",
            "low": "price ASC, id DESC",
            "high": "price DESC, id DESC",
            "area_small": "area ASC, id DESC",
            "area_large": "area DESC, id DESC"
        }

        order_sql = kieu_sap_xep[sort]

        offset = (current_page - 1) * limit

        # Chỉ lấy số phòng cần hiển thị
        cursor.execute(
            f"""
            SELECT
                id,
                user_id,
                title,
                address,
                district,
                price,
                area,
                description,
                image,
                status,
                created_at,
                latitude,
                longitude
            FROM rooms
            WHERE {where_sql}
            ORDER BY {order_sql}
            LIMIT %s OFFSET %s
            """,
            tuple(tham_so + [limit, offset])
        )

        rows = cursor.fetchall()
        danh_sach = []

        media_map = _tai_media_hang_loat(cursor, [row[0] for row in rows])
        for row in rows:
            media = media_map[row[0]]

            danh_sach.append({
                "id": row[0],
                "user_id": row[1],
                "title": row[2],
                "address": row[3],
                "district": row[4],
                "price": float(row[5]),
                "area": float(row[6]),
                "description": row[7],
                "image": row[8],
                "status": row[9],
                "created_at": (
                    row[10].isoformat()
                    if row[10]
                    else None
                ),
                "latitude": row[11],
                "longitude": row[12],
                "images": media["images"],
                "video": media["video"]
            })

        return {
            "status": "success",
            "data": danh_sach,
            "total": total,
            "page": current_page,
            "limit": limit,
            "total_pages": total_pages
        }

    finally:
        if cursor:
            cursor.close()
        conn.close()



@router.get("/stats")
def thong_ke_phong_tro():
    """Thống kê các tin đã duyệt trên Tronhanh123, không phải toàn thị trường."""
    conn = ket_noi_db()
    if conn is None:
        raise HTTPException(status_code=503, detail="Không kết nối được cơ sở dữ liệu!")
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*), COALESCE(AVG(price), 0), COALESCE(AVG(area), 0),
                   COALESCE(MIN(price), 0), COALESCE(MAX(price), 0)
            FROM rooms WHERE status = 'da_duyet'
        """)
        total, avg_price, avg_area, min_price, max_price = cursor.fetchone()
        cursor.execute("""
            SELECT COALESCE(NULLIF(BTRIM(district), ''), 'Chưa xác định') AS khu_vuc,
                   COUNT(*) AS so_phong, ROUND(AVG(price)::numeric, 0) AS gia_trung_binh
            FROM rooms WHERE status = 'da_duyet'
            GROUP BY 1 ORDER BY so_phong DESC, khu_vuc ASC
            LIMIT 12
        """)
        by_district = [
            {"district": row[0], "count": row[1], "average_price": float(row[2])}
            for row in cursor.fetchall()
        ]
        cursor.execute("""
            SELECT COUNT(*) FILTER (WHERE price < 3000000),
                   COUNT(*) FILTER (WHERE price >= 3000000 AND price <= 5000000),
                   COUNT(*) FILTER (WHERE price > 5000000)
            FROM rooms WHERE status = 'da_duyet'
        """)
        a, b, c = cursor.fetchone()
        return {
            "status": "success",
            "data": {
                "total_rooms": total,
                "average_price": round(float(avg_price)),
                "average_area": round(float(avg_area), 1),
                "min_price": float(min_price),
                "max_price": float(max_price),
                "by_district": by_district,
                "by_price": [
                    {"label": "Dưới 3 triệu", "count": a},
                    {"label": "3–5 triệu", "count": b},
                    {"label": "Trên 5 triệu", "count": c},
                ],
            },
        }
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()



# Bước 76: KNN có kiểm tra dữ liệu, cảnh báo mẫu nhỏ và đánh giá holdout.
# Không yêu cầu scikit-learn; giữ nguyên cấu trúc phản hồi của Bước 75.
def _lay_mau_du_doan():
    conn = ket_noi_db()
    if conn is None:
        raise HTTPException(status_code=503, detail="Không kết nối được cơ sở dữ liệu!")
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, area, price, COALESCE(district, '')
            FROM rooms
            WHERE status = 'da_duyet'
              AND area BETWEEN 5 AND 300
              AND price BETWEEN 100000 AND 100000000
            ORDER BY id DESC
            LIMIT 10000
        """)
        return [
            (int(rid), float(a), float(p), str(d).strip())
            for rid, a, p, d in cursor.fetchall()
            if a is not None and p is not None
            and isfinite(float(a)) and isfinite(float(p))
        ]
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()


def _knn_gia(mau, area, district):
    """Trả về ước lượng và thông tin hàng xóm; không dùng dữ liệu test trong train."""
    ten_khu_vuc = district.casefold()
    cung_khu_vuc = [r for r in mau if ten_khu_vuc and r[3].casefold() == ten_khu_vuc]
    candidates = cung_khu_vuc if len(cung_khu_vuc) >= 3 else mau
    scope = "cung_khu_vuc" if len(cung_khu_vuc) >= 3 else "toan_he_thong"
    scored = []
    for _, sample_area, price, sample_district in candidates:
        area_distance = abs(sample_area - area) / max(area, 10.0)
        district_penalty = (
            0.35 if ten_khu_vuc and sample_district.casefold() != ten_khu_vuc else 0.0
        )
        scored.append((area_distance + district_penalty, price))
    scored.sort(key=lambda r: r[0])
    nearest = scored[:min(7, len(scored))]
    weights = [1.0 / (0.15 + distance) for distance, _ in nearest]
    estimated = sum(w * p for w, (_, p) in zip(weights, nearest)) / sum(weights)
    prices = sorted(p for _, p in nearest)
    k = len(prices)
    lower = min(prices[int((k - 1) * 0.2)], estimated * 0.9)
    upper = max(prices[int((k - 1) * 0.8)], estimated * 1.1)
    return estimated, lower, upper, len(candidates), k, scope


def _lam_tron_gia(value):
    return int(round(value / 10000) * 10000)


@router.get("/predict-price")
def du_doan_gia_thue(area: float, district: str = ""):
    """Ước lượng tham khảo bằng weighted KNN trên tin đã duyệt."""
    if not isfinite(area) or not (5 <= area <= 300):
        raise HTTPException(status_code=422, detail="Diện tích phải từ 5 đến 300 m²!")
    district = district.strip()
    if len(district) > 100:
        raise HTTPException(status_code=422, detail="Tên khu vực quá dài!")

    samples = _lay_mau_du_doan()
    if len(samples) < 3:
        raise HTTPException(
            status_code=422,
            detail="Chưa đủ dữ liệu (cần ít nhất 3 tin đã duyệt) để ước lượng giá."
        )

    estimated, lower, upper, count, k, scope = _knn_gia(samples, area, district)
    warnings = []
    if len(samples) < 10:
        warnings.append("Hệ thống có ít hơn 10 tin hợp lệ; kết quả có thể thiếu ổn định.")
    if district and scope == "toan_he_thong":
        warnings.append("Khu vực này có dưới 3 tin hợp lệ; đã dùng dữ liệu toàn hệ thống.")
    if min(abs(s[1] - area) for s in samples) > max(10, area * 0.5):
        warnings.append("Ít phòng có diện tích gần với diện tích yêu cầu.")

    return {
        "status": "success",
        "data": {
            "area": area,
            "district": district,
            "predicted_price": _lam_tron_gia(estimated),
            "suggested_min_price": _lam_tron_gia(lower),
            "suggested_max_price": _lam_tron_gia(upper),
            "sample_count": count,
            "neighbors_used": k,
            "scope": scope,
            "method": "weighted_knn",
            "total_valid_samples": len(samples),
            "warnings": warnings,
            "note": "Ước lượng từ tin đã duyệt trên Tronhanh123, không phải giá thị trường được bảo đảm. Khoảng giá không phải khoảng tin cậy thống kê."
        }
    }


@router.get("/predict-price/evaluate")
def danh_gia_du_doan_gia():
    """Đánh giá holdout 20% theo ID, không trộn mẫu test vào train."""
    samples = _lay_mau_du_doan()
    if len(samples) < 15:
        raise HTTPException(
            status_code=422,
            detail="Cần ít nhất 15 tin hợp lệ để đánh giá mô hình dự đoán."
        )

    # Chia xác định theo ID để có thể chạy lại và so sánh.
    # Dữ liệu sắp xếp id giảm dần; lấy mỗi mẫu thứ 5 làm tập kiểm thử.
    test = [r for i, r in enumerate(samples) if i % 5 == 0]
    train = [r for i, r in enumerate(samples) if i % 5 != 0]
    errors = []
    percentage_errors = []
    for _, area, actual, district in test:
        predicted, _, _, _, _, _ = _knn_gia(train, area, district)
        errors.append(abs(predicted - actual))
        percentage_errors.append(abs(predicted - actual) / actual * 100)

    return {
        "status": "success",
        "data": {
            "method": "weighted_knn",
            "evaluation": "deterministic_holdout_80_20",
            "train_count": len(train),
            "test_count": len(test),
            "mae_vnd": round(sum(errors) / len(errors)),
            "mape_percent": round(sum(percentage_errors) / len(percentage_errors), 2),
            "median_absolute_error_vnd": round(median(errors)),
            "note": "Đánh giá nội bộ trên tin đã duyệt; không chứng minh độ chính xác cho toàn thị trường."
        }
    }




@router.get("/my")
def danh_sach_tin_cua_toi(request: Request):
    user_id = kiem_tra_tai_khoan_hoat_dong(request)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Bạn cần đăng nhập để xem tin đăng của mình!"
        )

    conn = ket_noi_db()

    if conn is None:
        raise HTTPException(
            status_code=503,
            detail="Không kết nối được cơ sở dữ liệu!"
        )

    cursor = None

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, user_id, title, address, district,
                   price, area, description, image, status, created_at, latitude, longitude
            FROM rooms
            WHERE user_id = %s
            ORDER BY created_at DESC, id DESC
        """, (user_id,))

        rows = cursor.fetchall()
        danh_sach = []

        media_map = _tai_media_hang_loat(cursor, [row[0] for row in rows])
        for row in rows:
            media = media_map[row[0]]

            danh_sach.append({
                "id": row[0],
                "user_id": row[1],
                "title": row[2],
                "address": row[3],
                "district": row[4],
                "price": float(row[5]),
                "area": float(row[6]),
                "description": row[7],
                "image": row[8],
                "status": row[9],
                "created_at": (
                    row[10].isoformat() if row[10] else None
                ),
                "latitude": row[11],
                "longitude": row[12],
                "images": media["images"],
                "video": media["video"]
            })

        return {
            "status": "success",
            "total": len(danh_sach),
            "data": danh_sach
        }

    finally:
        if cursor:
            cursor.close()
        conn.close()


# ===== BƯỚC 77: Chi tiết phòng, phòng liên quan và lượt xem =====
def _tao_bang_luot_xem(cursor):
    """Tạo bảng đếm lượt xem nếu chưa có, không sửa bảng rooms."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS room_view_counts (
            room_id INTEGER PRIMARY KEY REFERENCES rooms(id) ON DELETE CASCADE,
            view_count BIGINT NOT NULL DEFAULT 0
        )
    """)


def _phong_thanh_dict(cursor, row, views=0):
    cursor.execute("""
        SELECT file_path, media_type FROM room_media
        WHERE room_id = %s ORDER BY id
    """, (row[0],))
    media = cursor.fetchall()
    return {
        "id": row[0], "user_id": row[1], "title": row[2],
        "address": row[3], "district": row[4],
        "price": float(row[5]), "area": float(row[6]),
        "description": row[7], "image": row[8], "status": row[9],
        "created_at": row[10].isoformat() if row[10] else None,
        "latitude": row[11], "longitude": row[12],
        "images": [item[0] for item in media if item[1] == "image"],
        "video": next((item[0] for item in media if item[1] == "video"), None),
        "view_count": int(views or 0)
    }


@router.get("/popular")
def phong_noi_bat(limit: int = 6):
    """Tin đã duyệt có lượt xem cao; các tin bằng lượt xem xếp mới trước."""
    if not 1 <= limit <= 30:
        raise HTTPException(status_code=422, detail="limit phải từ 1 đến 30")
    conn = ket_noi_db()
    if conn is None:
        raise HTTPException(status_code=503, detail="Không kết nối được cơ sở dữ liệu!")
    cursor = None
    try:
        cursor = conn.cursor()
        _tao_bang_luot_xem(cursor)
        cursor.execute("""
            SELECT r.id, r.user_id, r.title, r.address, r.district,
                   r.price, r.area, r.description, r.image, r.status,
                   r.created_at, r.latitude, r.longitude,
                   COALESCE(v.view_count, 0)
            FROM rooms r
            LEFT JOIN room_view_counts v ON v.room_id = r.id
            WHERE r.status = 'da_duyet'
            ORDER BY COALESCE(v.view_count, 0) DESC,
                     r.created_at DESC NULLS LAST, r.id DESC
            LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()
        data = [_phong_thanh_dict(cursor, row[:13], row[13]) for row in rows]
        conn.commit()
        return {"status": "success", "total": len(data), "data": data}
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Không thể lấy danh sách phòng nổi bật!")
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()


@router.get("/{room_id}/related")
def phong_lien_quan(room_id: int, limit: int = 6):
    """Gợi ý tin đã duyệt: ưu tiên cùng khu vực, rồi diện tích và giá gần."""
    if not 1 <= limit <= 30:
        raise HTTPException(status_code=422, detail="limit phải từ 1 đến 30")
    conn = ket_noi_db()
    if conn is None:
        raise HTTPException(status_code=503, detail="Không kết nối được cơ sở dữ liệu!")
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT district, price, area FROM rooms
            WHERE id = %s AND status = 'da_duyet'
        """, (room_id,))
        source = cursor.fetchone()
        if source is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng đã duyệt!")
        district, price, area = source
        cursor.execute("""
            SELECT id, user_id, title, address, district, price, area,
                   description, image, status, created_at, latitude, longitude
            FROM rooms
            WHERE status = 'da_duyet' AND id <> %s
            ORDER BY
                CASE WHEN LOWER(BTRIM(COALESCE(district, ''))) =
                          LOWER(BTRIM(COALESCE(%s, ''))) THEN 0 ELSE 1 END,
                ABS(area - %s) ASC,
                ABS(price - %s) ASC,
                created_at DESC NULLS LAST, id DESC
            LIMIT %s
        """, (room_id, district, area, price, limit))
        rows = cursor.fetchall()
        return {"status": "success", "room_id": room_id,
                "total": len(rows), "data": [_phong_thanh_dict(cursor, r) for r in rows]}
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()


@router.get("/{room_id}")
def chi_tiet_phong(room_id: int):
    """Chi tiết tin đã duyệt; mỗi lần gọi API được tính một lượt xem."""
    conn = ket_noi_db()
    if conn is None:
        raise HTTPException(status_code=503, detail="Không kết nối được cơ sở dữ liệu!")
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, title, address, district, price, area,
                   description, image, status, created_at, latitude, longitude
            FROM rooms WHERE id = %s AND status = 'da_duyet'
        """, (room_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng đã duyệt!")
        _tao_bang_luot_xem(cursor)
        cursor.execute("""
            INSERT INTO room_view_counts (room_id, view_count)
            VALUES (%s, 1)
            ON CONFLICT (room_id) DO UPDATE
            SET view_count = room_view_counts.view_count + 1
            RETURNING view_count
        """, (room_id,))
        views = cursor.fetchone()[0]
        data = _phong_thanh_dict(cursor, row, views)
        conn.commit()
        return {"status": "success", "data": data}
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Không thể tải chi tiết phòng!")
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()


@router.post("")
def dang_tin(
    request: Request,
    title: str = Form(...),
    address: str = Form(...),
    district: str = Form(...),
    price: float = Form(...),
    area: float = Form(...),
    description: str = Form(...),
    latitude: Optional[float] = Form(default=None),
    longitude: Optional[float] = Form(default=None),
    images: list[UploadFile] = File(default=[]),
    video: Optional[UploadFile] = File(default=None)
):
    user_id = kiem_tra_tai_khoan_hoat_dong(request)

    if not user_id:
        raise HTTPException(status_code=401, detail="Bạn cần đăng nhập để đăng tin!")

    kiem_tra_toa_do(latitude, longitude)

    kiem_tra_noi_dung_phong(title, address, district, price, area, description)

    if len(images) > MAX_IMAGES:
        raise HTTPException(status_code=400, detail="Mỗi tin đăng chỉ được tải tối đa 6 ảnh!")

    conn = ket_noi_db()

    if conn is None:
        raise HTTPException(status_code=503, detail="Không kết nối được cơ sở dữ liệu!")

    cursor = None
    cac_file_da_luu = []

    try:
        cursor = conn.cursor()

        # Xác định quyền thực tế của người đăng từ PostgreSQL.
        # Không lấy quyền từ frontend để tránh giả mạo Admin.
        cursor.execute("SELECT role, is_active FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user is None:
            raise HTTPException(status_code=401, detail="Tài khoản đăng tin không tồn tại!")

        if user[1] is False:
            request.session.clear()
            raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa!")

        trang_thai = "da_duyet" if user[0] == "quan_tri" else "cho_duyet"

        duong_dan_anh = []
        for anh in images:
            duong_dan, file_that = luu_file(anh, "image", MAX_IMAGE_SIZE)
            duong_dan_anh.append(duong_dan)
            cac_file_da_luu.append(file_that)

        duong_dan_video = None
        if video and video.filename:
            duong_dan_video, file_that = luu_file(video, "video", MAX_VIDEO_SIZE)
            cac_file_da_luu.append(file_that)

        cursor.execute("""
            INSERT INTO rooms (
                user_id, title, address, district,
                price, area, description, image, status, latitude, longitude
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            user_id, title.strip(), address.strip(), district.strip(), price, area,
            description.strip(), duong_dan_anh[0] if duong_dan_anh else None,
            trang_thai, latitude, longitude
        ))

        room_id = cursor.fetchone()[0]

        for duong_dan in duong_dan_anh:
            cursor.execute("""
                INSERT INTO room_media (room_id, file_path, media_type)
                VALUES (%s, %s, %s)
            """, (room_id, duong_dan, "image"))

        if duong_dan_video:
            cursor.execute("""
                INSERT INTO room_media (room_id, file_path, media_type)
                VALUES (%s, %s, %s)
            """, (room_id, duong_dan_video, "video"))

        conn.commit()

        # Queue OSM sync after successful room creation.
        if trang_thai == "da_duyet" and latitude is not None and longitude is not None:
            try:
                from backend.services.osm_sync_worker import enqueue_room
                enqueue_room(conn, room_id)
            except Exception:
                import logging
                logging.exception("Could not enqueue OSM sync for room %s", room_id)


        thong_bao = (
            "Đăng tin thành công! Tin của quản trị viên đã được hiển thị công khai."
            if trang_thai == "da_duyet"
            else "Đăng tin thành công! Tin đang chờ quản trị viên duyệt."
        )
        return {
            "status": "success",
            "message": thong_bao,
            "room_id": room_id,
            "room_status": trang_thai,
            "so_anh": len(duong_dan_anh),
            "co_video": duong_dan_video is not None
        }

    except HTTPException:
        conn.rollback()
        for file_path in cac_file_da_luu:
            file_path.unlink(missing_ok=True)
        raise
    except Exception:
        conn.rollback()
        for file_path in cac_file_da_luu:
            file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Không thể đăng tin. Vui lòng thử lại!")
    finally:
        if cursor:
            cursor.close()
        conn.close()
        
from pydantic import BaseModel, Field


class CapNhatPhongRequest(BaseModel):
    title: str = Field(min_length=1)
    address: str = Field(min_length=1)
    district: str = Field(min_length=1)
    price: float = Field(ge=100000, le=100000000, allow_inf_nan=False)
    area: float = Field(ge=5, le=300, allow_inf_nan=False)
    description: str = Field(min_length=1)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@router.put("/{room_id}")
def cap_nhat_phong(
    room_id: int,
    data: CapNhatPhongRequest,
    request: Request
):
    user_id = kiem_tra_tai_khoan_hoat_dong(request)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Bạn cần đăng nhập để chỉnh sửa tin!"
        )

    conn = ket_noi_db()

    if conn is None:
        raise HTTPException(
            status_code=503,
            detail="Không kết nối được cơ sở dữ liệu!"
        )

    kiem_tra_toa_do(data.latitude, data.longitude)
    kiem_tra_noi_dung_phong(data.title, data.address, data.district, data.price, data.area, data.description)

    cursor = None

    try:
        cursor = conn.cursor()

        # Kiểm tra tin có tồn tại và thuộc người dùng hay không
        cursor.execute("""
            SELECT user_id, status
            FROM rooms
            WHERE id = %s
        """, (room_id,))

        room = cursor.fetchone()

        if room is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tin đăng!"
            )

        if room[0] != user_id:
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền chỉnh sửa tin này!"
            )

        # Lấy vai trò từ database, không tin dữ liệu gửi từ frontend.
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user is None:
            raise HTTPException(status_code=401, detail="Tài khoản không tồn tại!")

        trang_thai = "da_duyet" if user[0] == "quan_tri" else "cho_duyet"

        cursor.execute("""
            UPDATE rooms
            SET title = %s,
                address = %s,
                district = %s,
                price = %s,
                area = %s,
                description = %s,
                latitude = COALESCE(%s, latitude),
                longitude = COALESCE(%s, longitude),
                status = %s
            WHERE id = %s AND user_id = %s
        """, (
            data.title.strip(),
            data.address.strip(),
            data.district.strip(),
            data.price,
            data.area,
            data.description.strip(),
            data.latitude,
            data.longitude,
            trang_thai,
            room_id,
            user_id
        ))

        conn.commit()

        return {
            "status": "success",
            "message": (
                "Cập nhật tin đăng thành công! Tin của Admin đã được duyệt tự động."
                if trang_thai == "da_duyet"
                else "Cập nhật tin đăng thành công! Tin đang chờ quản trị viên duyệt lại."
            ),
            "room_id": room_id,
            "room_status": trang_thai
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Không thể cập nhật tin đăng!"
        )

    finally:
        if cursor:
            cursor.close()
        conn.close()

@router.delete("/{room_id}")
def xoa_tin_dang(room_id: int, request: Request):
    user_id = kiem_tra_tai_khoan_hoat_dong(request)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Bạn cần đăng nhập để xóa tin!"
        )

    conn = ket_noi_db()

    if conn is None:
        raise HTTPException(
            status_code=503,
            detail="Không kết nối được cơ sở dữ liệu!"
        )

    cursor = None

    try:
        cursor = conn.cursor()

        # Kiểm tra phòng tồn tại và thuộc tài khoản hiện tại
        cursor.execute("""
            SELECT user_id
            FROM rooms
            WHERE id = %s
        """, (room_id,))

        room = cursor.fetchone()

        if room is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tin đăng!"
            )

        if room[0] != user_id:
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền xóa tin này!"
            )

        # Xóa dữ liệu phụ thuộc trước khi xóa phòng
        cursor.execute("""
            DELETE FROM favorite_rooms
            WHERE room_id = %s
        """, (room_id,))

        cursor.execute("""
            DELETE FROM room_media
            WHERE room_id = %s
        """, (room_id,))

        cursor.execute("""
            DELETE FROM rooms
            WHERE id = %s AND user_id = %s
        """, (room_id, user_id))

        conn.commit()

        return {
            "status": "success",
            "message": "Đã xóa tin đăng thành công!",
            "room_id": room_id
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Không thể xóa tin đăng!"
        )

    finally:
        if cursor:
            cursor.close()
        conn.close()



# Background OpenStreetMap synchronization.
from backend.services.osm_sync_worker import start_worker
start_worker(ket_noi_db)
