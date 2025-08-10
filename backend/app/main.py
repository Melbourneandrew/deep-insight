from fastapi import FastAPI

from app.db import create_db_and_tables
from app.controllers.business_controller import router as business_router
from app.controllers.employee_controller import router as employee_router
from app.controllers.question_controller import router as question_router
from app.controllers.interview_controller import router as interview_router
from app.controllers.response_controller import router as response_router


app = FastAPI(title="Deep Insight API", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Deep Insight backend is running"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(business_router)
app.include_router(employee_router)
app.include_router(question_router)
app.include_router(interview_router)
app.include_router(response_router)
