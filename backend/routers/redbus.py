from fastapi import APIRouter
import json
import os

router = APIRouter(
    prefix="/api/redbus",
    tags=["redbus"]
)

@router.get("/metrics")
async def get_redbus_metrics():
    # In the future, this will connect to the Google Sheet and parse the live data
    # For now, it returns the mocked final calculations to build the UI with 100% accuracy.
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    mock_file = os.path.join(backend_dir, 'redbus_data.json')
    try:
        with open(mock_file, 'r') as f:
            data = json.load(f)
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}
