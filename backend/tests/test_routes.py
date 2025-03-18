# backend/routes/test_routes.py

from fastapi import APIRouter
from tests.test_services import test_function

router = APIRouter()

@router.get("/test")
def test_route():
    result = test_function()
    return {"message": "Test successful", "result": result}
