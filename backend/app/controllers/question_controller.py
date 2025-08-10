from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.db import get_session
from app.models.models import Question


router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("/", response_model=List[Question])
def list_questions(
    business_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
) -> List[Question]:
    statement = select(Question)
    if business_id:
        statement = statement.where(Question.business_id == business_id)
    return list(session.exec(statement).all())


@router.post("/", response_model=Question, status_code=status.HTTP_201_CREATED)
def create_question(
    question: Question, session: Session = Depends(get_session)
) -> Question:
    session.add(question)
    session.commit()
    session.refresh(question)
    return question


@router.get("/{question_id}", response_model=Question)
def get_question(
    question_id: UUID, session: Session = Depends(get_session)
) -> Question:
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
        )
    return question


@router.put("/{question_id}", response_model=Question)
def update_question(
    question_id: UUID,
    question_update: Question,
    session: Session = Depends(get_session),
) -> Question:
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
        )
    for key, value in question_update.model_dump(exclude_unset=True).items():
        setattr(question, key, value)
    session.add(question)
    session.commit()
    session.refresh(question)
    return question


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(question_id: UUID, session: Session = Depends(get_session)):
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
        )
    session.delete(question)
    session.commit()
