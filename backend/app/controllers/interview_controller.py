from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from pydantic import BaseModel

from app.db import get_session
from app.models.models import Interview, Question, QuestionResponse, Employee


router = APIRouter(prefix="/interviews", tags=["interviews"])


class QuestionResponseDetail(BaseModel):
    question_id: str
    question_content: str
    question_is_follow_up: bool
    employee_id: str
    employee_email: str
    response_content: str


class InterviewDetail(BaseModel):
    interview_id: str
    business_id: str
    questions_and_responses: List[QuestionResponseDetail]


@router.get("/", response_model=List[Interview])
def list_interviews(
    business_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
) -> List[Interview]:
    statement = select(Interview)
    if business_id:
        statement = statement.where(Interview.business_id == business_id)
    return list(session.exec(statement).all())


@router.post("/", response_model=Interview, status_code=status.HTTP_201_CREATED)
def create_interview(
    interview: Interview, session: Session = Depends(get_session)
) -> Interview:
    session.add(interview)
    session.commit()
    session.refresh(interview)
    return interview


@router.get("/{interview_id}", response_model=Interview)
def get_interview(
    interview_id: UUID, session: Session = Depends(get_session)
) -> Interview:
    interview = session.get(Interview, interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found"
        )
    return interview


@router.put("/{interview_id}", response_model=Interview)
def update_interview(
    interview_id: UUID,
    interview_update: Interview,
    session: Session = Depends(get_session),
) -> Interview:
    interview = session.get(Interview, interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found"
        )
    for key, value in interview_update.model_dump(exclude_unset=True).items():
        setattr(interview, key, value)
    session.add(interview)
    session.commit()
    session.refresh(interview)
    return interview


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(interview_id: UUID, session: Session = Depends(get_session)):
    interview = session.get(Interview, interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found"
        )
    session.delete(interview)
    session.commit()


@router.get("/business/{business_id}/details", response_model=List[InterviewDetail])
def get_business_interview_details(
    business_id: UUID, session: Session = Depends(get_session)
) -> List[InterviewDetail]:
    """Get all interviews for a business with their questions and responses"""
    # Get all interviews for the business
    interview_statement = select(Interview).where(Interview.business_id == business_id)
    interviews = session.exec(interview_statement).all()

    result = []
    for interview in interviews:
        # Get all responses for this interview with joined question and employee data
        response_statement = (
            select(QuestionResponse, Question, Employee)
            .join(Question, QuestionResponse.question_id == Question.id)
            .join(Employee, QuestionResponse.employee_id == Employee.id)
            .where(QuestionResponse.interview_id == interview.id)
            .order_by(Question.order_index)
        )

        responses_with_details = session.exec(response_statement).all()

        questions_and_responses = [
            QuestionResponseDetail(
                question_id=str(response.question_id),
                question_content=question.content,
                question_is_follow_up=question.is_follow_up,
                employee_id=str(response.employee_id),
                employee_email=employee.email,
                response_content=response.content,
            )
            for response, question, employee in responses_with_details
        ]

        result.append(
            InterviewDetail(
                interview_id=str(interview.id),
                business_id=str(interview.business_id),
                questions_and_responses=questions_and_responses,
            )
        )

    return result
