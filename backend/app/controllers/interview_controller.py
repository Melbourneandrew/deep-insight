from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.db import get_session
from app.models.models import Interview


router = APIRouter(prefix="/interviews", tags=["interviews"])


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
