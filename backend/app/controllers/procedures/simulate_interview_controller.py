from __future__ import annotations
import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.schemas.schema import (
    SimulateInterviewRequest, 
    SimulateInterviewResponse,
    SimulateEmployeeInterviewRequest,
    SimulateEmployeeInterviewResponse
)
from app.services.simulate_interview_service import get_simulate_interview_service


router = APIRouter(prefix="/simulate", tags=["simulate"])


@router.post(
    "/interview",
    response_model=SimulateInterviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def simulate_business_interviews(
    request: SimulateInterviewRequest,
    service = Depends(get_simulate_interview_service)
) -> SimulateInterviewResponse:
    """
    Simulate interviews for all employees in a business using parallel processing.
    Uses asyncio.gather to run multiple employee simulations concurrently.
    """
    try:
        return await service.simulate_business_interviews(request)
    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "no employees" in error_message.lower() or "no questions" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=error_message)


@router.post(
    "interview/{employee_id}",
    response_model=SimulateEmployeeInterviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def simulate_employee_interview(
    employee_id: UUID,
    request: SimulateEmployeeInterviewRequest,
    service = Depends(get_simulate_interview_service)
) -> SimulateEmployeeInterviewResponse:
    """
    Simulate a complete interview for a single employee.
    Takes an employee_id and optional interview_id (creates new if not provided).
    Runs through the actual interview flow with AI-generated responses.
    """
    try:
        # Ensure the employee_id from the path matches the request
        if request.employee_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Employee ID in path must match employee ID in request body"
            )
        
        return await service.simulate_employee_interview(request)
    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "must belong to the same business" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=error_message)