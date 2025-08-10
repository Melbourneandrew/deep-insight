from uuid import UUID
from typing import Optional
from pydantic import BaseModel

from app.models.models import QuestionBase


# Start Interview schemas
class StartInterviewRequest(BaseModel):
    employee_id: UUID


class StartInterviewResponse(BaseModel):
    interview_id: UUID


# Next Question schemas
class NextQuestionRequest(BaseModel):
    interview_id: UUID


class NextQuestionResponse(BaseModel):
    question: Optional[QuestionBase] = None
    is_interview_over: bool = False


# Answer Question schemas
class AnswerQuestionRequest(BaseModel):
    interview_id: UUID
    question_id: UUID
    content: str


class AnswerQuestionResponse(BaseModel):
    success: bool
    interview_id: UUID
