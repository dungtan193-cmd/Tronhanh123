from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/analytics", tags=["Analytics Charts"])

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

CHARTS = {
    "gia-thue": "bieu_do_gia_thue.png",
    "boxplot": "boxplot_gia_thue.png",
    "gia-theo-quan": "gia_trung_binh_theo_quan.png",
    "heatmap": "heatmap_tuong_quan.png",
    "shap-beeswarm": "shap_beeswarm_buoc86.png",
    "shap-summary": "shap_summary_bar_buoc86.png",
    "so-sanh-mo-hinh": "so_sanh_3_mo_hinh_buoc86.png",
    "so-sanh-bat-thuong": "so_sanh_bat_thuong_buoc86.png",
    "treemap": "treemap_phong_theo_quan.png",
    "violin": "violin_gia_thue.png",
}


@router.get("/charts")
def danh_sach_bieu_do():
    return [
        {
            "id": chart_id,
            "filename": filename,
            "url": f"/api/analytics/charts/{chart_id}",
        }
        for chart_id, filename in CHARTS.items()
        if (DATA_DIR / filename).is_file()
    ]


@router.get("/charts/{chart_id}")
def xem_bieu_do(chart_id: str):
    filename = CHARTS.get(chart_id)

    if filename is None:
        raise HTTPException(status_code=404, detail="Biểu đồ không tồn tại")

    path = DATA_DIR / filename

    if not path.is_file():
        raise HTTPException(status_code=404, detail="Chưa tạo ảnh biểu đồ")

    return FileResponse(path, media_type="image/png")
