from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.db import get_session
from app.models.models import QuestionResponse


router = APIRouter(prefix="/responses", tags=["responses"])


@router.get("/", response_model=List[QuestionResponse])
def list_responses(
    interview_id: UUID | None = Query(default=None),
    employee_id: UUID | None = Query(default=None),
    question_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
) -> List[QuestionResponse]:
    statement = select(QuestionResponse)
    if interview_id:
        statement = statement.where(QuestionResponse.interview_id == interview_id)
    if employee_id:
        statement = statement.where(QuestionResponse.employee_id == employee_id)
    if question_id:
        statement = statement.where(QuestionResponse.question_id == question_id)
    return session.exec(statement).all()


@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_response(
    response: QuestionResponse, session: Session = Depends(get_session)
) -> QuestionResponse:
    session.add(response)
    session.commit()
    session.refresh(response)
    return response


@router.get(
    "/{interview_id}/{employee_id}/{question_id}", response_model=QuestionResponse
)
def get_response(
    interview_id: UUID,
    employee_id: UUID,
    question_id: UUID,
    session: Session = Depends(get_session),
) -> QuestionResponse:
    response = session.get(
        QuestionResponse,
        {
            "interview_id": interview_id,
            "employee_id": employee_id,
            "question_id": question_id,
        },
    )
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Response not found"
        )
    return response


@router.put(
    "/{interview_id}/{employee_id}/{question_id}", response_model=QuestionResponse
)
def update_response(
    interview_id: UUID,
    employee_id: UUID,
    question_id: UUID,
    response_update: QuestionResponse,
    session: Session = Depends(get_session),
) -> QuestionResponse:
    response = session.get(
        QuestionResponse,
        {
            "interview_id": interview_id,
            "employee_id": employee_id,
            "question_id": question_id,
        },
    )
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Response not found"
        )
    for key, value in response_update.model_dump(exclude_unset=True).items():
        setattr(response, key, value)
    session.add(response)
    session.commit()
    session.refresh(response)
    return response


@router.delete(
    "/{interview_id}/{employee_id}/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_response(
    interview_id: UUID,
    employee_id: UUID,
    question_id: UUID,
    session: Session = Depends(get_session),
):
    response = session.get(
        QuestionResponse,
        {
            "interview_id": interview_id,
            "employee_id": employee_id,
            "question_id": question_id,
        },
    )
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Response not found"
        )
    session.delete(response)
    session.commit()
