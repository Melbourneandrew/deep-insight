from __future__ import annotations

import json
import os
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.models.models import Business, Employee, Question
from app.services.schemas.schema import CreateBusinessRequest, BusinessSeedData


router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.get("/", response_model=List[Business])
def list_businesses(session: Session = Depends(get_session)) -> List[Business]:
    return list(session.exec(select(Business)).all())


def _generate_employee_email(original_email: str, business_name: str) -> str:
    """Generate employee email using the username from original email and business domain."""
    # Extract username from original email (part before @)
    username = original_email.split("@")[0]
    # Clean business name: remove spaces, convert to lowercase, remove special chars
    clean_name = "".join(c.lower() for c in business_name if c.isalnum())
    return f"{username}@{clean_name}.com"


def _load_default_seed_data() -> BusinessSeedData:
    """Load default seed data from JSON file."""
    current_dir = os.path.dirname(__file__)
    default_seed_path = os.path.join(current_dir, "..", "default_business_seed.json")

    try:
        with open(default_seed_path, "r") as f:
            seed_json = json.load(f)
        return BusinessSeedData(**seed_json)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # Fallback to minimal default data if file is missing or invalid
        return BusinessSeedData(
            employees=[{"email": "admin@company.com", "bio": "Default administrator"}],
            questions=[{"content": "How are you doing today?", "is_follow_up": False}],
        )


def _seed_business_data(
    business: Business, seed_data: BusinessSeedData, session: Session
):
    """Seed a business with employees and questions."""
    # Create employees
    for employee_data in seed_data.employees:
        generated_email = _generate_employee_email(employee_data.email, business.name)
        employee = Employee(
            email=generated_email, bio=employee_data.bio, business_id=business.id
        )
        session.add(employee)

    # Create questions
    for question_data in seed_data.questions:
        question = Question(
            content=question_data.content,
            is_follow_up=question_data.is_follow_up,
            business_id=business.id,
        )
        session.add(question)


@router.post("/", response_model=Business, status_code=status.HTTP_201_CREATED)
def create_business(
    request: CreateBusinessRequest, session: Session = Depends(get_session)
) -> Business:
    # Create the business
    business = Business(name=request.name)
    session.add(business)
    session.flush()  # Flush to get the business ID

    # Determine seed data to use
    seed_data = request.seed_data if request.seed_data else _load_default_seed_data()

    # Seed the business with employees and questions
    _seed_business_data(business, seed_data, session)

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
