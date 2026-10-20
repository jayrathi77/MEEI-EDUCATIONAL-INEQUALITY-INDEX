from fastapi import APIRouter, HTTPException
from app.services.data_service import data_service

router = APIRouter()


@router.get("/explainability/global")
def global_explainability():
    shap = data_service.global_shap
    if shap is None:
        return {"status": "NO_DATA", "message": "Run generate_explanations.py first."}
    return shap


@router.get("/explainability/district/{district_id}")
def district_explainability(district_id: str):
    index = data_service.local_shap_index
    local = data_service.local_shap
    if index is None or local is None:
        raise HTTPException(503, "SHAP data not available. Run generate_explanations.py first.")

    idx = index.get(district_id)
    if idx is None:
        raise HTTPException(404, f"No SHAP explanation for district '{district_id}'.")

    return local[idx]
