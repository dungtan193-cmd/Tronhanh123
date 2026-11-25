from pathlib import Path
import shutil

path = Path("backend/routers/ai_live.py")
backup = Path("backend/routers/ai_live_before_step92.py.bak")

content = path.read_text(encoding="utf-8-sig")
shutil.copy2(path, backup)

if "def predict_rent(" in content:
    print("API du doan da ton tai, khong them trung.")
else:
    content += '''

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
):
    rooms = read_rooms()

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
'''
    path.write_text(content, encoding="utf-8")
    print("Da them API /api/ai/live/predict")

print("Backup:", backup)
