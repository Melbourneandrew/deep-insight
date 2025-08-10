from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.models.models import QuestionBase
from pydantic import BaseModel


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


# Build Wiki schemas
class BuildWikiRequest(BaseModel):
    business_id: UUID


class BuildWikiResponse(BaseModel):
    success: bool
    business_id: UUID
    sections_plan: Dict[str, Any]
    files_created: List[str]  # List of file paths as strings
