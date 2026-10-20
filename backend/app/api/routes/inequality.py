from fastapi import APIRouter
from app.services.data_service import data_service

router = APIRouter()


@router.get("/iop/summary")
def iop_summary():
    iop = data_service.iop
    if iop is None:
        return {"status": "NO_DATA", "message": "Run estimate_iop.py first."}
    return iop


@router.get("/iop/circumstances")
def iop_circumstances():
    iop = data_service.iop
    if iop is None:
        return {"status": "NO_DATA"}
    circumstances = iop.get("circumstance_importance", {})
    sorted_circumstances = sorted(circumstances.items(), key=lambda x: x[1]["rank"])
    return {
        "estimation_level": iop.get("estimation_level"),
        "circumstances": [
            {"name": k, **v} for k, v in sorted_circumstances
        ],
    }
