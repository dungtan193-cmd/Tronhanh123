import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import make_pipeline

from database.connection import ket_noi_db

router = APIRouter(prefix="/api/ai/live", tags=["Live AI"])

MIN_TRAINING_ROOMS = 30

# Một tác vụ AI tại một thời điểm.
executor = ThreadPoolExecutor(max_workers=1)
lock = threading.Lock()

def new_ai_state():
    return {
        "status": "not_started",
        "fingerprint": None,
        "updated_at": None,
        "result": None,
        "error": None,
    }


states = {
    "real": new_ai_state(),
    "demo": new_ai_state(),
}

# Tuong thich voi code cu
state = states["real"]


# ===== BUOC 93.30: REAL AND DEMO AI =====
from fastapi import Query as AIQuery

def read_rooms(mode="real"):

    if mode not in ("real", "demo"):
        raise ValueError("Che do AI khong hop le")

    conn = ket_noi_db()

    if conn is None:
        raise RuntimeError("Không kết nối được PostgreSQL")

    cursor = None

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                id,
                COALESCE(NULLIF(TRIM(district), ''), 'Chưa xác định'),
                price,
                area
            FROM rooms
            WHERE status = 'da_duyet'
              AND price > 0
              AND area > 0
              AND (
                  %s = 'demo'
                  OR title NOT LIKE '[DEMO-AI-89-%%'
              )
            ORDER BY id
        """, (mode,))

        rows = cursor.fetchall()

        return [
            {
                "id": int(row[0]),
                "district": str(row[1]),
                "price": float(row[2]),
                "area": float(row[3]),
            }
            for row in rows
        ]

    finally:
        if cursor is not None:
            cursor.close()
        conn.close()


def fingerprint_rooms(rooms):
    raw = json.dumps(
        rooms,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(
        ("ai-version-91|" + raw).encode("utf-8")
    ).hexdigest()


def detect_iqr(rooms):
    if len(rooms) < 4:
        return {
            "status": "insufficient_data",
            "outliers": [],
            "message": "IQR cần thêm dữ liệu để phân tích có ý nghĩa.",
        }

    prices = np.array([r["price"] for r in rooms], dtype=float)

    q1, q3 = np.percentile(prices, [25, 75])
    iqr = q3 - q1

    lower = float(q1 - 1.5 * iqr)
    upper = float(q3 + 1.5 * iqr)

    outliers = [
        {
            "id": r["id"],
            "district": r["district"],
            "price": r["price"],
        }
        for r in rooms
        if r["price"] < lower or r["price"] > upper
    ]

    return {
        "status": "ready",
        "q1": float(q1),
        "q3": float(q3),
        "lower_bound": lower,
        "upper_bound": upper,
        "outliers": outliers,
    }


def detect_isolation_forest(rooms):
    if len(rooms) < 10:
        return {
            "status": "insufficient_data",
            "outliers": [],
            "message": "Cần ít nhất 10 phòng để chạy Isolation Forest thử nghiệm.",
        }

    features = np.array(
        [
            [
                np.log1p(r["price"]),
                np.log1p(r["area"]),
                np.log1p(r["price"] / r["area"]),
            ]
            for r in rooms
        ],
        dtype=float,
    )

    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42,
    )

    labels = model.fit_predict(features)
    scores = model.decision_function(features)

    outliers = [
        {
            "id": r["id"],
            "district": r["district"],
            "price": r["price"],
            "score": float(scores[i]),
        }
        for i, r in enumerate(rooms)
        if labels[i] == -1
    ]

    return {
        "status": "ready",
        "outliers": outliers,
        "message": "Kết quả phát hiện bất thường chỉ mang tính tham khảo.",
    }



def normalize_district(value):
    """
    Chuẩn hóa tên quận để tránh tạo đặc trưng trùng lặp.
    Không thay đổi dữ liệu gốc trong PostgreSQL.
    """
    import unicodedata

    text = unicodedata.normalize("NFC", str(value or ""))
    text = " ".join(text.strip().split())

    mapping = {
        "cầu giấy": "Cầu Giấy",
        "đống đa": "Đống Đa",
        "thanh xuân": "Thanh Xuân",
        "hai bà trưng": "Hai Bà Trưng",
        "nam từ liêm": "Nam Từ Liêm",
        "bắc từ liêm": "Bắc Từ Liêm",
        "hoàng mai": "Hoàng Mai",
        "long biên": "Long Biên",
        "hà đông": "Hà Đông",
        "ba đình": "Ba Đình",
        "tây hồ": "Tây Hồ",
        "hoàn kiếm": "Hoàn Kiếm",
        "thanh trì": "Thanh Trì",
        "gia lâm": "Gia Lâm",
        "đông anh": "Đông Anh",
    }

    key = text.casefold()

    for prefix in ("quận ", "huyện ", "q. ", "q.", "h. ", "h."):
        if key.startswith(prefix):
            key = key[len(prefix):].strip()
            break

    return mapping.get(key, text or "Chưa xác định")


def prepare_features(rooms):
    df = pd.DataFrame(rooms)

    # Chuẩn hóa tên quận trước khi mã hóa One-Hot.
    df["district"] = df["district"].apply(normalize_district)

    # Không dùng ID để dự đoán giá.
    X = pd.get_dummies(
        df[["area", "district"]],
        columns=["district"],
        dtype=float,
    )

    y = df["price"].to_numpy(dtype=float)

    return X, y


def evaluate_model(model, X, y):
    folds = min(5, len(y))

    cv = KFold(
        n_splits=folds,
        shuffle=True,
        random_state=42,
    )

    predictions = cross_val_predict(model, X, y, cv=cv)

    return {
        "mae": round(float(mean_absolute_error(y, predictions)), 2),
        "rmse": round(
            float(np.sqrt(mean_squared_error(y, predictions))), 2
        ),
        "r2": round(float(r2_score(y, predictions)), 4),
        "evaluation": f"{folds}-fold cross-validation",
        "actual_values": [
            round(float(v), 2) for v in y
        ],
        "predicted_values": [
            round(float(v), 2) for v in predictions
        ],
    }


def train_models(rooms):
    n = len(rooms)

    if n < MIN_TRAINING_ROOMS:
        return {
            "status": "insufficient_data",
            "total_rooms": n,
            "minimum_rooms": MIN_TRAINING_ROOMS,
            "message": (
                f"Hiện có {n} phòng hợp lệ. "
                f"Cần tối thiểu {MIN_TRAINING_ROOMS} phòng "
                "để bắt đầu thử nghiệm huấn luyện."
            ),
            "models": {},
            "shap": None,
        }

    X, y = prepare_features(rooms)

    knn = make_pipeline(
        SimpleImputer(strategy="median"),
        KNeighborsRegressor(n_neighbors=5),
    )

    rf = RandomForestRegressor(
        n_estimators=100,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=1,
    )

    results = {
        "knn": evaluate_model(knn, X, y),
        "random_forest": evaluate_model(rf, X, y),
    }

    room_ids = [int(room["id"]) for room in rooms]

    for metrics in results.values():
        metrics["room_ids"] = room_ids

    # Huấn luyện mô hình cuối trên toàn bộ dữ liệu.
    # Kết quả CV phía trên vẫn là đánh giá ngoài mẫu.
    rf.fit(X, y)

    shap_result = None

    try:
        import shap

        # Giới hạn số mẫu để tránh tính toán quá nặng.
        sample = X.iloc[: min(100, len(X))]
        explainer = shap.TreeExplainer(rf)
        values = explainer.shap_values(sample)

        importance = np.abs(np.asarray(values)).mean(axis=0)

        shap_result = {
            "status": "ready",
            "features": sorted(
                [
                    {
                        "feature": str(name),
                        "mean_abs_shap": float(value),
                    }
                    for name, value in zip(X.columns, importance)
                ],
                key=lambda item: item["mean_abs_shap"],
                reverse=True,
            ),
            "message": (
                "Mức ảnh hưởng trung bình của từng đặc trưng "
                "trong mô hình Random Forest hiện tại."
            ),
        }

    except Exception as exc:
        shap_result = {
            "status": "error",
            "message": f"Không tính được SHAP: {type(exc).__name__}",
        }

    return {
        "status": "ready",
        "total_rooms": n,
        "minimum_rooms": MIN_TRAINING_ROOMS,
        "models": results,
        "shap": shap_result,
        "message": (
            "Đã huấn luyện và đánh giá thử nghiệm. "
            "Cần kiểm định thêm trước khi sử dụng để định giá thực tế."
        ),
    }


def calculate_ai(rooms):
    return {
        "total_rooms": len(rooms),
        "iqr": detect_iqr(rooms),
        "isolation_forest": detect_isolation_forest(rooms),
        "training": train_models(rooms),
    }


def background_update(rooms, fingerprint, mode="real"):
    state = states[mode]
    try:
        result = calculate_ai(rooms)

        with lock:
            state["result"] = result
            state["fingerprint"] = fingerprint
            state["updated_at"] = datetime.now(
                timezone.utc
            ).isoformat()
            state["status"] = "ready"
            state["error"] = None

    except Exception as exc:
        with lock:
            state["status"] = "error"
            state["error"] = str(exc)


@router.get("/status")
def ai_status(mode: str = AIQuery(default="real", pattern="^(real|demo)$")):
    state = states[mode]
    try:
        rooms = read_rooms(mode)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Không đọc được dữ liệu phòng từ PostgreSQL",
        )

    current_fingerprint = fingerprint_rooms(rooms)

    with lock:
        needs_update = (
            state["fingerprint"] != current_fingerprint
            and state["status"] != "processing"
        )

        if needs_update:
            state["status"] = "processing"
            state["error"] = None

            executor.submit(
                background_update,
                rooms,
                current_fingerprint,
                mode,
            )

        status = state["status"]
        updated_at = state["updated_at"]
        error = state["error"]
        result = state["result"]
        cached_fingerprint = state["fingerprint"]

    is_current = (
        status == "ready"
        and cached_fingerprint == current_fingerprint
    )

    return {
        "mode": mode,
        "contains_demo_data": mode == "demo",
        "status": status,
        "is_current": is_current,
        "updated_at": updated_at,
        "total_rooms_in_database": len(rooms),
        "error": error,
        "result": result if is_current else None,
        "message": (
            "Kết quả AI đang được cập nhật."
            if not is_current and status == "processing"
            else None
        ),
    }


# ===== BUOC 92: DU DOAN GIA THUE =====

from fastapi import Query

prediction_cache = {
    "fingerprint": None,
    "model": None,
    "columns": None,
}

prediction_lock = threading.Lock()


@router.get("/predict")
def predict_rent(
    district: str = Query(min_length=2, max_length=100),
    area: float = Query(gt=0, le=500),
    mode: str = Query(default="real", pattern="^(real|demo)$"),
):
    rooms = read_rooms(mode)

    if len(rooms) < MIN_TRAINING_ROOMS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Can it nhat {MIN_TRAINING_ROOMS} phong hop le. "
                f"Hien co {len(rooms)} phong."
            ),
        )

    normalized = normalize_district(district)
    known_districts = {
        normalize_district(room["district"])
        for room in rooms
    }

    if normalized not in known_districts:
        raise HTTPException(
            status_code=422,
            detail="Khu vuc nay chua co trong du lieu huan luyen.",
        )

    fingerprint = fingerprint_rooms(rooms)

    with prediction_lock:
        if (
            prediction_cache["fingerprint"] != fingerprint
            or prediction_cache["model"] is None
        ):
            X, y = prepare_features(rooms)

            model = RandomForestRegressor(
                n_estimators=100,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=1,
            )
            model.fit(X, y)

            prediction_cache["model"] = model
            prediction_cache["columns"] = list(X.columns)
            prediction_cache["fingerprint"] = fingerprint

        model = prediction_cache["model"]
        columns = prediction_cache["columns"]

        input_df = pd.DataFrame([{
            "area": area,
            "district": normalized,
        }])

        encoded = pd.get_dummies(
            input_df,
            columns=["district"],
            dtype=float,
        )

        encoded = encoded.reindex(
            columns=columns,
            fill_value=0,
        )

        predicted = float(model.predict(encoded)[0])

    return {
        "district": normalized,
        "area": area,
        "predicted_price": round(predicted),
        "currency": "VND",
        "training_rooms": len(rooms),
        "model": "Random Forest",
        "is_demo": True,
        "warning": (
            "Ket qua thu nghiem. Du lieu huan luyen "
            "co phong gia lap, khong phai bao gia thi truong."
        ),
    }


# ===== BUOC 93.22: AUTO AI REFRESH =====
import logging
import time

logger = logging.getLogger(__name__)

_auto_ai_stop = threading.Event()
_auto_ai_thread = None
_auto_ai_lock = threading.Lock()


def _auto_ai_loop():
    while not _auto_ai_stop.is_set():
        try:
            ai_status(mode="real")
        except Exception:
            logger.exception("Auto AI refresh failed")

        _auto_ai_stop.wait(30)


def start_auto_ai_refresh():
    global _auto_ai_thread

    with _auto_ai_lock:
        if _auto_ai_thread is not None and _auto_ai_thread.is_alive():
            return

        _auto_ai_stop.clear()
        _auto_ai_thread = threading.Thread(
            target=_auto_ai_loop,
            name="tronhanh-auto-ai",
            daemon=True,
        )
        _auto_ai_thread.start()


def stop_auto_ai_refresh():
    _auto_ai_stop.set()

    with _auto_ai_lock:
        thread = _auto_ai_thread

    if thread is not None and thread.is_alive():
        thread.join(timeout=5)
