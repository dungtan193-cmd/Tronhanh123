from pathlib import Path
import csv
import math

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/analytics", tags=["Analytics AI"])

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"


def doc_csv(ten_file):
    duong_dan = DATA_DIR / ten_file

    if not duong_dan.is_file():
        return []

    with duong_dan.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def so_thuc(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError):
        return None


@router.get("/dashboard")
def dashboard_ai():
    phong = doc_csv("rooms_clean_normalized.csv")

    if not phong:
        raise HTTPException(
            status_code=404,
            detail="Chưa có dữ liệu phân tích. Hãy chạy bước 86 trước."
        )

    du_lieu = []
    for p in phong:
        gia = so_thuc(p.get("price"))
        dien_tich = so_thuc(p.get("area"))

        if gia is None or dien_tich is None or dien_tich <= 0:
            continue

        du_lieu.append({
            "id": p.get("id"),
            "district": p.get("district") or "Chưa xác định",
            "price": gia,
            "area": dien_tich,
            "price_per_m2": gia / dien_tich,
        })

    if not du_lieu:
        raise HTTPException(
            status_code=404,
            detail="Không có bản ghi giá thuê hợp lệ."
        )

    theo_quan = {}

    for p in du_lieu:
        quan = p["district"]

        if quan not in theo_quan:
            theo_quan[quan] = {
                "district": quan,
                "count": 0,
                "total_price": 0,
            }

        theo_quan[quan]["count"] += 1
        theo_quan[quan]["total_price"] += p["price"]

    thong_ke_quan = []

    for item in theo_quan.values():
        thong_ke_quan.append({
            "district": item["district"],
            "count": item["count"],
            "average_price": round(
                item["total_price"] / item["count"], 2
            ),
        })

    thong_ke_quan.sort(
        key=lambda x: x["count"],
        reverse=True
    )

    return {
        "total_rooms": len(du_lieu),
        "average_price": round(
            sum(p["price"] for p in du_lieu) / len(du_lieu), 2
        ),
        "min_price": min(p["price"] for p in du_lieu),
        "max_price": max(p["price"] for p in du_lieu),
        "district_count": len(thong_ke_quan),
        "district_stats": thong_ke_quan,
        "rooms": du_lieu,
        "note": (
            "Dữ liệu phân tích thử nghiệm từ bước 86. "
            "Chưa phải dữ liệu thời gian thực."
        ),
    }


@router.get("/models")
def ket_qua_mo_hinh():
    return {
        "knn": doc_csv("danh_gia_knn_buoc86.csv"),
        "random_forest": doc_csv("danh_gia_random_forest_buoc86.csv"),
        "model_comparison": doc_csv("so_sanh_3_mo_hinh_buoc86.csv"),
        "shap": doc_csv("shap_feature_importance_buoc86.csv"),
        "note": (
            "Các mô hình được thử nghiệm trên tập dữ liệu rất nhỏ. "
            "Không sử dụng kết quả này để khẳng định độ chính xác thực tế."
        ),
    }


@router.get("/anomalies")
def phong_bat_thuong():
    return {
        "iqr": doc_csv("bao_cao_bat_thuong_buoc86.csv"),
        "isolation_forest": doc_csv("isolation_forest_buoc86.csv"),
        "comparison": doc_csv("so_sanh_iqr_isolation_forest.csv"),
        "note": (
            "Phòng được đánh dấu bất thường cần kiểm tra thủ công. "
            "Không đồng nghĩa với dữ liệu sai."
        ),
    }
