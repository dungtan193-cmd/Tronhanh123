import json
from database.connection import ket_noi_db


def _chuyen_danh_sach(row):
    """Chuyển một dòng dữ liệu phòng trọ thành dictionary."""
    try:
        danh_sach_anh = json.loads(row[7]) if row[7] else []
    except (TypeError, json.JSONDecodeError):
        danh_sach_anh = []

    return {
        "id": row[0],
        "title": row[1],
        "address": row[2],
        "district": row[3],
        "price": row[4],
        "area": row[5],
        "description": row[6],
        "images": danh_sach_anh,
        "video": row[8],
        "username": row[9] if len(row) > 9 else None,
    }


def them_phong(user_id, title, address, district, price, area, description,
               images=None, video=None):
    """Admin đăng tin được duyệt ngay; tài khoản thường phải chờ duyệt."""
    conn = ket_noi_db()
    if conn is None:
        return False, "Không thể kết nối cơ sở dữ liệu!"

    cursor = None
    try:
        cursor = conn.cursor()
        # Lấy quyền từ database, không tin vào role do frontend gửi lên.
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user is None:
            return False, "Không tìm thấy tài khoản đăng tin!"

        trang_thai = "da_duyet" if user[0] == "quan_tri" else "cho_duyet"

        cursor.execute(
            """
            INSERT INTO rooms
                (user_id, title, address, district, price, area,
                 description, images, video, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id, title, address, district, price, area, description,
                json.dumps(images or [], ensure_ascii=False), video, trang_thai,
            ),
        )
        conn.commit()
        if trang_thai == "da_duyet":
            return True, "Đăng tin thành công! Tin của quản trị viên đã được hiển thị công khai."
        return True, "Đăng tin thành công! Tin đang chờ quản trị viên duyệt."
    except Exception as e:
        conn.rollback()
        return False, f"Lỗi đăng tin: {e}"
    finally:
        if cursor:
            cursor.close()
        conn.close()


def lay_phong_cho_duyet():
    """Lấy tin chờ duyệt, kèm ảnh, video và người đăng."""
    conn = ket_noi_db()
    if conn is None:
        return []

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT r.id, r.title, r.address, r.district, r.price, r.area,
                   r.description, r.images, r.video, u.username
            FROM rooms r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.status = 'cho_duyet'
            ORDER BY r.created_at DESC
            """
        )
        return [_chuyen_danh_sach(row) for row in cursor.fetchall()]
    except Exception as e:
        print("Lỗi lấy tin chờ duyệt:", e)
        return []
    finally:
        if cursor:
            cursor.close()
        conn.close()


def cap_nhat_trang_thai(room_id, status):
    """Admin duyệt hoặc từ chối tin."""
    if status not in ("da_duyet", "tu_choi"):
        return False, "Trạng thái không hợp lệ!"

    conn = ket_noi_db()
    if conn is None:
        return False, "Không thể kết nối cơ sở dữ liệu!"

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE rooms SET status = %s WHERE id = %s AND status = 'cho_duyet'",
            (status, room_id),
        )
        if cursor.rowcount == 0:
            conn.rollback()
            return False, "Không tìm thấy tin đang chờ duyệt."
        conn.commit()
        return True, "Đã cập nhật trạng thái tin đăng."
    except Exception as e:
        conn.rollback()
        return False, f"Lỗi cập nhật trạng thái: {e}"
    finally:
        if cursor:
            cursor.close()
        conn.close()


def lay_phong_da_duyet():
    """Chỉ lấy tin đã duyệt để hiển thị công khai, kèm ảnh/video."""
    conn = ket_noi_db()
    if conn is None:
        return []

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, title, address, district, price, area,
                   description, images, video, NULL
            FROM rooms
            WHERE status = 'da_duyet'
            ORDER BY created_at DESC
            """
        )
        return [_chuyen_danh_sach(row) for row in cursor.fetchall()]
    except Exception as e:
        print("Lỗi lấy tin đã duyệt:", e)
        return []
    finally:
        if cursor:
            cursor.close()
        conn.close()
