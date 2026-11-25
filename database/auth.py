
import bcrypt
from database.connection import ket_noi_db


# =========================
# CHỨC NĂNG ĐĂNG KÝ
# =========================

def dang_ky(full_name, username, email, phone, password):
    conn = ket_noi_db()

    if conn is None:
        return False, "Không thể kết nối cơ sở dữ liệu!"

    cursor = None

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id FROM users
            WHERE username = %s OR email = %s
            """,
            (username, email)
        )

        if cursor.fetchone():
            return False, "Tên đăng nhập hoặc email đã tồn tại!"

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute(
            """
            INSERT INTO users
            (full_name, username, email, phone, password, role)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                full_name,
                username,
                email,
                phone,
                hashed_password,
                "nguoi_thue"
            )
        )

        conn.commit()
        return True, "Đăng ký tài khoản thành công!"

    except Exception as e:
        conn.rollback()
        return False, f"Lỗi đăng ký: {e}"

    finally:
        if cursor:
            cursor.close()
        conn.close()


# =========================
# CHỨC NĂNG ĐĂNG NHẬP
# =========================

def dang_nhap(username_email, password):
    conn = ket_noi_db()

    if conn is None:
        return False, "Không thể kết nối cơ sở dữ liệu!", None

    cursor = None

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, username, email, password,
                   full_name, role, is_active
            FROM users
            WHERE username = %s OR email = %s
            """,
            (username_email, username_email)
        )

        user = cursor.fetchone()

        if user is None:
            return False, "Tài khoản không tồn tại!", None

        password_hash = user[3]

        if not bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        ):
            return False, "Mật khẩu không chính xác!", None

        # Kiểm tra trạng thái tài khoản
        if user[6] is False:
            return (
                False,
                "Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên!",
                None
            )

        thong_tin = {
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "full_name": user[4],
            "role": user[5]
        }

        return True, "Đăng nhập thành công!", thong_tin

    except Exception as e:
        return False, f"Lỗi đăng nhập: {e}", None

    finally:
        if cursor:
            cursor.close()
        conn.close()
