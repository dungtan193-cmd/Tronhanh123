
from fastapi import APIRouter, HTTPException, Request

from database.connection import ket_noi_db


router = APIRouter(
    prefix="/api/admin",
    tags=["Quản trị viên"]
)


# ==========================================
# KIỂM TRA QUYỀN ADMIN
# ==========================================

def kiem_tra_admin(request: Request):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Bạn chưa đăng nhập!"
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

        cursor.execute(
            """
            SELECT role, is_active
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if user is None:
            request.session.clear()
            raise HTTPException(
                status_code=401,
                detail="Tài khoản không tồn tại!"
            )

        if user[1] is False:
            request.session.clear()
            raise HTTPException(
                status_code=403,
                detail="Tài khoản của bạn đã bị khóa!"
            )

        if user[0] != "quan_tri":
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền quản trị viên!"
            )

        return user_id

    finally:
        if cursor:
            cursor.close()
        conn.close()


# ==========================================
# ADMIN: DANH SÁCH TIN CHỜ DUYỆT
# ==========================================

@router.get("/rooms/pending")
def danh_sach_tin_cho_duyet(request: Request):
    kiem_tra_admin(request)

    conn = ket_noi_db()

    if conn is None:
        raise HTTPException(
            status_code=503,
            detail="Lỗi kết nối cơ sở dữ liệu!"
        )

    cursor = None

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, user_id, title, address, district,
                   price, area, description, image, created_at
            FROM rooms
            WHERE status = 'cho_duyet'
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        danh_sach = []

        for row in rows:
            cursor.execute("""
                SELECT file_path, media_type
                FROM room_media
                WHERE room_id = %s
                ORDER BY id
            """, (row[0],))

            media = cursor.fetchall()

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
                "created_at": (
                    row[9].isoformat()
                    if row[9] else None
                ),
                "images": [
                    item[0]
                    for item in media
                    if item[1] == "image"
                ],
                "video": next(
                    (
                        item[0]
                        for item in media
                        if item[1] == "video"
                    ),
                    None
                )
            })

        return {
            "status": "success",
            "data": danh_sach
        }

    finally:
        if cursor:
            cursor.close()
        conn.close()


# ==========================================
# ADMIN: DUYỆT TIN
# ==========================================

@router.put("/rooms/{room_id}/approve")
def duyet_tin(room_id: int, request: Request):
    kiem_tra_admin(request)

    conn = ket_noi_db()

    if conn is None:
        raise HTTPException(
            status_code=503,
            detail="Lỗi kết nối cơ sở dữ liệu!"
        )

    cursor = None

    try:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE rooms
            SET status = 'da_duyet'
            WHERE id = %s
              AND status = 'cho_duyet'
            RETURNING id
        """, (room_id,))

        result = cursor.fetchone()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tin đang chờ duyệt!"
            )

        conn.commit()

        # Queue OSM sync after successful approval.
        try:
            from backend.services.osm_sync_worker import enqueue_room
            enqueue_room(conn, room_id)
        except Exception:
            import logging
            logging.exception("Could not enqueue OSM sync for room %s", room_id)


        return {
            "status": "success",
            "message": "Duyệt tin thành công!",
            "room_id": room_id
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Không thể duyệt tin!"
        )

    finally:
        if cursor:
            cursor.close()
        conn.close()


# ==========================================
# ADMIN: TỪ CHỐI TIN
# ==========================================

@router.put("/rooms/{room_id}/reject")
def tu_choi_tin(room_id: int, request: Request):
    kiem_tra_admin(request)

    conn = ket_noi_db()

    if conn is None:
        raise HTTPException(
            status_code=503,
            detail="Lỗi kết nối cơ sở dữ liệu!"
        )

    cursor = None

    try:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE rooms
            SET status = 'tu_choi'
            WHERE id = %s
              AND status = 'cho_duyet'
            RETURNING id
        """, (room_id,))

        result = cursor.fetchone()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tin đang chờ duyệt!"
            )

        conn.commit()

        return {
            "status": "success",
            "message": "Từ chối tin thành công!",
            "room_id": room_id
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Không thể từ chối tin!"
        )

    finally:
        if cursor:
            cursor.close()
        conn.close()


# ==========================================
# ADMIN: XEM DANH SÁCH NGƯỜI DÙNG
# ==========================================

@router.get("/users")
def danh_sach_nguoi_dung(request: Request):
    kiem_tra_admin(request)

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
            SELECT
                u.id,
                u.username,
                u.full_name,
                u.email,
                u.phone,
                u.role,
                u.is_active,
                COUNT(r.id) AS so_tin_dang
            FROM users u
            LEFT JOIN rooms r ON r.user_id = u.id
            GROUP BY
                u.id,
                u.username,
                u.full_name,
                u.email,
                u.phone,
                u.role,
                u.is_active
            ORDER BY u.id DESC
        """)

        rows = cursor.fetchall()
        danh_sach = []

        for row in rows:
            danh_sach.append({
                "id": row[0],
                "username": row[1],
                "full_name": row[2],
                "email": row[3],
                "phone": row[4],
                "role": row[5],
                "is_active": row[6],
                "so_tin_dang": row[7]
            })

        return {
            "status": "success",
            "total": len(danh_sach),
            "data": danh_sach
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Không thể tải danh sách người dùng!"
        )

    finally:
        if cursor:
            cursor.close()
        conn.close()


# ==========================================
# ADMIN: KHÓA TÀI KHOẢN
# ==========================================

@router.put("/users/{user_id}/lock")
def khoa_tai_khoan(user_id: int, request: Request):
    admin_id = kiem_tra_admin(request)

    if user_id == admin_id:
        raise HTTPException(
            status_code=400,
            detail="Bạn không thể tự khóa tài khoản của mình!"
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

        cursor.execute(
            """
            UPDATE users
            SET is_active = FALSE
            WHERE id = %s
              AND role <> 'quan_tri'
            RETURNING id, username
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if user is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Không tìm thấy tài khoản người dùng "
                    "hoặc không được phép khóa Admin!"
                )
            )

        conn.commit()

        return {
            "status": "success",
            "message": f"Đã khóa tài khoản {user[1]}!",
            "user_id": user[0],
            "is_active": False
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Không thể khóa tài khoản!"
        )

    finally:
        if cursor:
            cursor.close()
        conn.close()


# ==========================================
# ADMIN: MỞ KHÓA TÀI KHOẢN
# ==========================================

@router.put("/users/{user_id}/unlock")
def mo_khoa_tai_khoan(user_id: int, request: Request):
    kiem_tra_admin(request)

    conn = ket_noi_db()

    if conn is None:
        raise HTTPException(
            status_code=503,
            detail="Không kết nối được cơ sở dữ liệu!"
        )

    cursor = None

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE users
            SET is_active = TRUE
            WHERE id = %s
              AND role <> 'quan_tri'
            RETURNING id, username
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if user is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Không tìm thấy tài khoản người dùng "
                    "hoặc không được phép mở khóa Admin!"
                )
            )

        conn.commit()

        return {
            "status": "success",
            "message": f"Đã mở khóa tài khoản {user[1]}!",
            "user_id": user[0],
            "is_active": True
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Không thể mở khóa tài khoản!"
        )

    finally:
        if cursor:
            cursor.close()
        conn.close()
