
import psycopg2

def ket_noi_db():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="tronhanh123",
            user="postgres",
            password="123456",
            port="5432"
        )
        return conn

    except Exception as e:
        print("Lỗi kết nối database:", e)
        return None


if __name__ == "__main__":
    conn = ket_noi_db()

    if conn:
        print("KẾT NỐI POSTGRESQL THÀNH CÔNG!")
        conn.close()
    else:
        print("KẾT NỐI THẤT BẠI!")
