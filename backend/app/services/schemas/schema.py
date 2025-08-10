from uuid import UUID
from typing import Optional, List, Dict, Any
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


# Business Creation schemas
class EmployeeSeedData(BaseModel):
    email: str  # Username will be extracted and domain replaced with business name
    bio: Optional[str] = None


class QuestionSeedData(BaseModel):
    content: str
    is_follow_up: bool = False


class BusinessSeedData(BaseModel):
    employees: List[EmployeeSeedData] = []
    questions: List[QuestionSeedData] = []


class CreateBusinessRequest(BaseModel):
    name: str
    seed_data: Optional[BusinessSeedData] = None


# Simulate Interview schemas
class SimulateInterviewRequest(BaseModel):
    business_id: UUID


class SimulateEmployeeInterviewRequest(BaseModel):
    employee_id: UUID
    interview_id: Optional[UUID] = None  # If not provided, creates new interview


class SimulatedQAExchange(BaseModel):
    question_id: UUID
    question_content: str
    response_content: str
    is_follow_up: bool
    order_index: Optional[int] = None


class SimulateEmployeeInterviewResponse(BaseModel):
    interview_id: UUID
    employee_id: UUID
    employee_email: str
    business_id: UUID
    business_name: str
    simulated_exchanges: List[SimulatedQAExchange]
    is_interview_complete: bool


class EmployeeSimulation(BaseModel):
    employee_id: UUID
    employee_email: str
    responses: List[Dict[str, Any]]


class SimulateInterviewResponse(BaseModel):
    interview_id: UUID
    business_id: UUID
    business_name: str
    employee_simulations: List[EmployeeSimulation]
    questions_asked: List[Dict[str, Any]]
