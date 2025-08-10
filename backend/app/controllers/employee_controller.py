from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.db import get_session
from app.models.models import Employee


router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/", response_model=List[Employee])
def list_employees(
    business_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
) -> List[Employee]:
    statement = select(Employee)
    if business_id:
        statement = statement.where(Employee.business_id == business_id)
    return session.exec(statement).all()


@router.post("/", response_model=Employee, status_code=status.HTTP_201_CREATED)
def create_employee(
    employee: Employee, session: Session = Depends(get_session)
) -> Employee:
    session.add(employee)
    session.commit()
    session.refresh(employee)
    return employee


@router.get("/{employee_id}", response_model=Employee)
def get_employee(
    employee_id: UUID, session: Session = Depends(get_session)
) -> Employee:
    employee = session.get(Employee, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )
    return employee


@router.put("/{employee_id}", response_model=Employee)
def update_employee(
    employee_id: UUID,
    employee_update: Employee,
    session: Session = Depends(get_session),
) -> Employee:
    employee = session.get(Employee, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )
    for key, value in employee_update.model_dump(exclude_unset=True).items():
        setattr(employee, key, value)
    session.add(employee)
    session.commit()
    session.refresh(employee)
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: UUID, session: Session = Depends(get_session)):
    employee = session.get(Employee, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )
    session.delete(employee)
    session.commit()
