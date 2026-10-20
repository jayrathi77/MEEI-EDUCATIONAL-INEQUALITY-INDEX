from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from app.services.data_service import data_service
import io
import csv

router = APIRouter()


@router.get("/priorities")
def get_priorities(
    state: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=2000),
):
    pdata = data_service.priorities
    if pdata is None:
        return {"status": "NO_DATA", "message": "Run build_priority_list.py first."}

    districts = pdata.get("districts", [])
    if state:
        districts = [d for d in districts if d.get("state_name", "").lower() == state.lower()]

    total = len(districts)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = districts[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "prioritization_rule": pdata.get("prioritization_rule"),
        "note": pdata.get("note"),
        "districts": page_data,
    }


@router.get("/priorities/export")
def export_priorities(state: str | None = Query(None)):
    pdata = data_service.priorities
    if pdata is None:
        return {"status": "NO_DATA"}

    districts = pdata.get("districts", [])
    if state:
        districts = [d for d in districts if d.get("state_name", "").lower() == state.lower()]

    if not districts:
        return {"status": "EMPTY"}

    output = io.StringIO()
    fields = [k for k in districts[0] if k != "top_drivers"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for d in districts:
        row = {k: v for k, v in d.items() if k != "top_drivers"}
        writer.writerow(row)

    output.seek(0)
    filename = f"priority_districts{'_' + state if state else ''}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
