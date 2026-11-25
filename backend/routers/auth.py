
import bcrypt

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from psycopg2 import IntegrityError

from database.auth import dang_ky, dang_nhap
from database.connection import ket_noi_db


router = APIRouter(
    prefix="/api/auth",
    tags=["Xác thực"]
)


# =========================
# DỮ LIỆU ĐĂNG KÝ
# =========================

class DangKyRequest(BaseModel):
    full_name: str
    username: str
    email: str
    phone: str
    password: str


# =========================
# DỮ LIỆU ĐĂNG NHẬP
# =========================

class DangNhapRequest(BaseModel):
    username_email: str
    password: str


# =========================
# DỮ LIỆU CẬP NHẬT HỒ SƠ
# =========================

class CapNhatHoSoRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=1, max_length=255)
    phone: str = Field(default="", max_length=30)


# =========================
# DỮ LIỆU ĐỔI MẬT KHẨU
# =========================

class DoiMatKhauRequest(BaseModel):
    old_password: str
    new_password: str


# =========================
# KIỂM TRA TÀI KHOẢN
# =========================

def kiem_tra_tai_khoan(request: Request):
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
            SELECT id, username, email,
                   full_name, phone, role, is_active
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

        if user[6] is False:
            request.session.clear()
            raise HTTPException(
                status_code=403,
                detail=(
                    "Tài khoản của bạn đã bị khóa. "
                    "Vui lòng liên hệ quản trị viên!"
                )
            )

        return {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "full_name": user[3],
            "phone": user[4],
            "role": user[5]
        }

    finally:
        if cursor:
            cursor.close()
        conn.close()


# =========================
# ĐĂNG KÝ
# =========================

@router.post("/register")
def register(data: DangKyRequest):
    thanh_cong, thong_bao = dang_ky(
        data.full_name,
        data.username,
        data.email,
        data.phone,
        data.password
    )

    if not thanh_cong:
        raise HTTPException(
            status_code=400,
            detail=thong_bao
        )

    return {
        "status": "success",
        "message": thong_bao
    }


# =========================
# ĐĂNG NHẬP
# =========================

@router.post("/login")
def login(data: DangNhapRequest, request: Request):
    thanh_cong, thong_bao, thong_tin = dang_nhap(
        data.username_email,
        data.password
    )

    if not thanh_cong:
        raise HTTPException(
            status_code=401,
            detail=thong_bao
        )

    request.session.clear()
    request.session["user_id"] = thong_tin["id"]

    return {
        "status": "success",
        "message": thong_bao,
        "user": thong_tin
    }


# =========================
# LẤY THÔNG TIN NGƯỜI DÙNG
# =========================

@router.get("/me")
def get_current_user(request: Request):
    user = kiem_tra_tai_khoan(request)

    return {
        "status": "success",
        "user": user
    }


# =========================
# ĐĂNG XUẤT
# =========================

@router.post("/logout")
def logout(request: Request):
    request.session.clear()

    return {
        "status": "success",
        "message": "Đăng xuất thành công!"
    }


# =========================
# CẬP NHẬT THÔNG TIN CÁ NHÂN
# =========================

@router.put("/profile")
def cap_nhat_ho_so(
    data: CapNhatHoSoRequest,
    request: Request
):
    user = kiem_tra_tai_khoan(request)
    user_id = user["id"]

    full_name = data.full_name.strip()
    email = data.email.strip().lower()
    phone = data.phone.strip()

    if not full_name:
        raise HTTPException(
            status_code=400,
            detail="Họ và tên không được để trống!"
        )

    if not email or "@" not in email:
        raise HTTPException(
            status_code=400,
            detail="Email không hợp lệ!"
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
            SET full_name = %s,
                email = %s,
                phone = %s
            WHERE id = %s AND is_active = TRUE
            RETURNING id, username, email,
                      full_name, phone, role
            """,
            (full_name, email, phone, user_id)
        )

        updated_user = cursor.fetchone()

        if updated_user is None:
            conn.rollback()
            request.session.clear()
            raise HTTPException(
                status_code=403,
                detail="Tài khoản không tồn tại hoặc đã bị khóa!"
            )

        conn.commit()

        return {
            "status": "success",
            "message": "Cập nhật thông tin cá nhân thành công!",
            "user": {
                "id": updated_user[0],
                "username": updated_user[1],
                "email": updated_user[2],
                "full_name": updated_user[3],
                "phone": updated_user[4],
                "role": updated_user[5]
            }
        }

    except IntegrityError:
        conn.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email này đã được sử dụng!"
        )

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Không thể cập nhật thông tin cá nhân!"
        )

    finally:
        if cursor:
            cursor.close()
        conn.close()


# =========================
# ĐỔI MẬT KHẨU
# =========================

@router.put("/change-password")
def doi_mat_khau(
    data: DoiMatKhauRequest,
    request: Request
):
    user = kiem_tra_tai_khoan(request)
    user_id = user["id"]

    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Mật khẩu mới phải có ít nhất 6 ký tự!"
        )

    if data.old_password == data.new_password:
        raise HTTPException(
            status_code=400,
            detail="Mật khẩu mới phải khác mật khẩu cũ!"
        )

    if len(data.new_password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Mật khẩu mới không được vượt quá 72 byte!"
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
            SELECT password, is_active
            FROM users
            WHERE id = %s
            FOR UPDATE
            """,
            (user_id,)
        )

        account = cursor.fetchone()

        if account is None:
            request.session.clear()
            raise HTTPException(
                status_code=401,
                detail="Tài khoản không tồn tại!"
            )

        if account[1] is False:
            request.session.clear()
            raise HTTPException(
                status_code=403,
                detail="Tài khoản đã bị khóa!"
            )

        try:
            mat_khau_hop_le = bcrypt.checkpw(
                data.old_password.encode("utf-8"),
                account[0].encode("utf-8")
            )
        except (ValueError, TypeError):
            mat_khau_hop_le = False

        if not mat_khau_hop_le:
            raise HTTPException(
                status_code=400,
                detail="Mật khẩu hiện tại không chính xác!"
            )

        mat_khau_moi = bcrypt.hashpw(
            data.new_password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute(
            """
            UPDATE users
            SET password = %s
            WHERE id = %s AND is_active = TRUE
            """,
            (mat_khau_moi, user_id)
        )

        conn.commit()

        request.session.clear()

        return {
            "status": "success",
            "message": (
                "Đổi mật khẩu thành công! "
                "Vui lòng đăng nhập lại."
            )
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Không thể đổi mật khẩu!"
        )

    finally:
        if cursor:
            cursor.close()
        conn.close()
