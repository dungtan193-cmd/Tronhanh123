
from fastapi import APIRouter, HTTPException, Request

from database.connection import ket_noi_db


router = APIRouter(
    prefix="/api/favorites",
    tags=["Phòng trọ yêu thích"]
)


# ======================================
# KIỂM TRA NGƯỜI DÙNG VÀ TRẠNG THÁI
# ======================================
def lay_user_id(request: Request):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Vui lòng đăng nhập để sử dụng chức năng này!"
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
            SELECT is_active
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

        if user[0] is False:
            request.session.clear()
            raise HTTPException(
                status_code=403,
                detail=(
                    "Tài khoản của bạn đã bị khóa. "
                    "Vui lòng liên hệ quản trị viên!"
                )
            )

        return user_id

    finally:
        if cursor:
            cursor.close()
        conn.close()


# ======================================
# LẤY DANH SÁCH PHÒNG ĐÃ LƯU
# ======================================
@router.get("")
def danh_sach_yeu_thich(request: Request):
    user_id = lay_user_id(request)

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
            SELECT
                f.id,
                f.room_id,
                f.created_at,
                r.title,
                r.address,
                r.district,
                r.price,
                r.area,
                r.description,
                r.image,
                r.status
            FROM favorite_rooms AS f
            JOIN rooms AS r ON r.id = f.room_id
            WHERE f.user_id = %s
              AND r.status = 'da_duyet'
            ORDER BY f.created_at DESC, f.id DESC
            """,
            (user_id,)
        )

        rows = cursor.fetchall()
        danh_sach = []

        for row in rows:
            room_id = row[1]

            cursor.execute(
                """
                SELECT file_path, media_type
                FROM room_media
                WHERE room_id = %s
                ORDER BY id
                """,
                (room_id,)
            )

            media = cursor.fetchall()

            danh_sach.append({
                "favorite_id": row[0],
                "id": room_id,
                "room_id": room_id,
                "saved_at": (
                    row[2].isoformat()
                    if row[2] else None
                ),
                "title": row[3],
                "address": row[4],
                "district": row[5],
                "price": float(row[6]),
                "area": float(row[7]),
                "description": row[8],
                "image": row[9],
                "status": row[10],
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
            "total": len(danh_sach),
            "data": danh_sach
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Không thể tải danh sách phòng yêu thích!"
        )

    finally:
        if cursor:
            cursor.close()
        conn.close()


# ======================================
# LƯU PHÒNG YÊU THÍCH
# ======================================
@router.post("/{room_id}")
def luu_phong_yeu_thich(
    room_id: int,
    request: Request
):
    user_id = lay_user_id(request)

    conn = ket_noi_db()

    if conn is None:
        raise HTTPException(
            status_code=503,
            detail="Không kết nối được cơ sở dữ liệu!"
        )

    cursor = None

    try:
        cursor = conn.cursor()

        # Kiểm tra phòng có tồn tại và đã duyệt
        cursor.execute(
            """
            SELECT id
            FROM rooms
            WHERE id = %s
              AND status = 'da_duyet'
            """,
            (room_id,)
        )

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Phòng trọ không tồn tại hoặc chưa được duyệt!"
            )

        # Tránh lưu trùng một phòng
        cursor.execute(
            """
            INSERT INTO favorite_rooms (user_id, room_id)
            VALUES (%s, %s)
            ON CONFLICT (user_id, room_id)
            DO NOTHING
            RETURNING id
            """,
            (user_id, room_id)
        )

        ket_qua = cursor.fetchone()
        conn.commit()

        return {
            "status": "success",
            "message": (
                "Đã lưu phòng vào danh sách yêu thích!"
                if ket_qua
                else "Phòng này đã có trong danh sách yêu thích!"
            ),
            "room_id": room_id,
            "is_favorite": True
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Không thể lưu phòng yêu thích!"
        )

    finally:
        if cursor:
            cursor.close()
        conn.close()


# ======================================
# BỎ LƯU PHÒNG YÊU THÍCH
# ======================================
@router.delete("/{room_id}")
def bo_luu_phong_yeu_thich(
    room_id: int,
    request: Request
):
    user_id = lay_user_id(request)

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
            DELETE FROM favorite_rooms
            WHERE user_id = %s
              AND room_id = %s
            RETURNING id
            """,
            (user_id, room_id)
        )

        ket_qua = cursor.fetchone()
        conn.commit()

        return {
            "status": "success",
            "message": (
                "Đã bỏ lưu phòng yêu thích!"
                if ket_qua
                else "Phòng này chưa có trong danh sách yêu thích!"
            ),
            "room_id": room_id,
            "is_favorite": False
        }

    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Không thể bỏ lưu phòng yêu thích!"
        )

    finally:
        if cursor:
            cursor.close()
        conn.close()
