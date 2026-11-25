from backend.routers.ai_gis_research import router as ai_gis_research_router
from backend.routers.ai_gis import router as ai_gis_router
from backend.routers.ai_live import router as ai_live_router
from backend.routers.analytics_live import router as analytics_live_router
from backend.routers.analytics_charts import router as analytics_charts_router

from pathlib import Path
from backend.gis_buoc85_6 import router as gis_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from database.connection import ket_noi_db

from backend.routers.auth import router as auth_router
from backend.routers.rooms import router as rooms_router
from backend.routers.admin import router as admin_router
from backend.routers.favorites import router as favorites_router
from backend.routers.analytics import router as analytics_router


# ĐƯỜNG DẪN THƯ MỤC GỐC DỰ ÁN
BASE_DIR = Path(__file__).resolve().parent.parent

# THƯ MỤC LƯU ẢNH VÀ VIDEO
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# KHỞI TẠO FASTAPI

# ===== BUOC 93.23: AUTO AI LIFESPAN =====
from contextlib import asynccontextmanager
from backend.routers.ai_live import (
    start_auto_ai_refresh,
    stop_auto_ai_refresh,
)

@asynccontextmanager
async def tronhanh_lifespan(app: FastAPI):
    start_auto_ai_refresh()
    try:
        yield
    finally:
        stop_auto_ai_refresh()


app = FastAPI(
    lifespan=tronhanh_lifespan,
    title="Tronhanh123 API",
    description="Backend quản lý website tìm kiếm phòng trọ",
    version="1.0.0"
)
app.include_router(gis_router)

# QUẢN LÝ PHIÊN ĐĂNG NHẬP
app.add_middleware(
    SessionMiddleware,
    secret_key="tronhanh123-local-development-key",
    same_site="lax",
    https_only=False
)


# CHO PHÉP REACT KẾT NỐI BACKEND
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# PHỤC VỤ ẢNH VÀ VIDEO ĐÃ TẢI LÊN
app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOAD_DIR)),
    name="uploads"
)


# ĐĂNG KÝ CÁC ROUTER
app.include_router(auth_router)
app.include_router(rooms_router)
app.include_router(admin_router)
app.include_router(favorites_router)
app.include_router(ai_live_router)
app.include_router(analytics_live_router)
app.include_router(analytics_charts_router)
app.include_router(analytics_router)


# KIỂM TRA BACKEND
@app.get("/api/health")
def health_check():
    return {
        "status": "success",
        "message": "Tronhanh123 API đang hoạt động"
    }


# KIỂM TRA KẾT NỐI POSTGRESQL
@app.get("/api/db-check")
def database_check():
    conn = ket_noi_db()

    if conn is None:
        return {
            "status": "error",
            "message": "Không kết nối được PostgreSQL"
        }

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]

        cursor.close()

        return {
            "status": "success",
            "message": "Kết nối PostgreSQL thành công",
            "version": version
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

    finally:
        conn.close()





app.include_router(ai_gis_router)

app.include_router(ai_gis_research_router)
