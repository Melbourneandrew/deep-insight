from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.models.models import Business


router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.get("/", response_model=List[Business])
def list_businesses(session: Session = Depends(get_session)) -> List[Business]:
    return list(session.exec(select(Business)).all())


@router.post("/", response_model=Business, status_code=status.HTTP_201_CREATED)
def create_business(
    business: Business, session: Session = Depends(get_session)
) -> Business:
    session.add(business)
    session.commit()
    session.refresh(business)
    return business


@router.get("/{business_id}", response_model=Business)
def get_business(
    business_id: UUID, session: Session = Depends(get_session)
) -> Business:
    business = session.get(Business, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Business not found"
        )
    return business


@router.put("/{business_id}", response_model=Business)
def update_business(
    business_id: UUID,
    business_update: Business,
    session: Session = Depends(get_session),
) -> Business:
    business = session.get(Business, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Business not found"
        )
    for key, value in business_update.model_dump(exclude_unset=True).items():
        setattr(business, key, value)
    session.add(business)
    session.commit()
    session.refresh(business)
    return business


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business(business_id: UUID, session: Session = Depends(get_session)):
    business = session.get(Business, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Business not found"
        )
    session.delete(business)
    session.commit()
