from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.db import create_db_and_tables
from app.controllers.business_controller import router as business_router
from app.controllers.employee_controller import router as employee_router
from app.controllers.question_controller import router as question_router
from app.controllers.interview_controller import router as interview_router
from app.controllers.response_controller import router as response_router
from app.controllers.procedures.start_interview_controller import router as start_interview_router
from app.controllers.procedures.answer_question_controller import router as answer_question_router
from app.controllers.procedures.next_question_controller import router as next_question_router
from app.controllers.procedures.simulate_interview_controller import (
    router as simulate_router,
)
from app.controllers.procedures.start_interview_controller import (
    router as start_interview_router,
)
from app.controllers.procedures.next_question_controller import (
    router as next_question_router,
)
from app.controllers.procedures.answer_question_controller import (
    router as answer_question_router,
)


load_dotenv()

app = FastAPI(title="Deep Insight API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
app.include_router(start_interview_router)
app.include_router(answer_question_router)
app.include_router(next_question_router)
app.include_router(simulate_router)

app.include_router(start_interview_router)
app.include_router(next_question_router)
app.include_router(answer_question_router)
