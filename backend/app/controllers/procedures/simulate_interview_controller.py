from __future__ import annotations
import asyncio
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.services.schemas.schema import (
    SimulateInterviewRequest, 
    SimulateInterviewResponse,
    SimulateInterviewBackgroundResponse,
    SimulateEmployeeInterviewRequest,
    SimulateEmployeeInterviewResponse,
    SimulateEmployeeInterviewBackgroundResponse
)
from app.services.simulate_interview_service import get_simulate_interview_service


router = APIRouter(prefix="/simulate", tags=["simulate"])


# Background task functions
async def run_business_simulation_task(request: SimulateInterviewRequest):
    """Background task to run business interview simulation"""
    from app.db import engine
    from sqlmodel import Session
    
    with Session(engine) as session:
        service = get_simulate_interview_service(session)
        try:
            result = await service.simulate_business_interviews(request)
            print(f"Business simulation completed for business {request.business_id}")
            print(f"Simulated {len(result.employee_simulations)} employees")
        except Exception as e:
            print(f"Business simulation failed for business {request.business_id}: {e}")


async def run_employee_simulation_task(request: SimulateEmployeeInterviewRequest):
    """Background task to run employee interview simulation"""
    from app.db import engine
    from sqlmodel import Session
    
    with Session(engine) as session:
        service = get_simulate_interview_service(session)
        try:
            result = await service.simulate_employee_interview(request)
            print(f"Employee simulation completed for employee {request.employee_id}")
            print(f"Interview ID: {result.interview_id}, Exchanges: {len(result.simulated_exchanges)}")
        except Exception as e:
            print(f"Employee simulation failed for employee {request.employee_id}: {e}")


@router.post(
    "/interview",
    response_model=SimulateInterviewBackgroundResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def simulate_business_interviews(
    request: SimulateInterviewRequest,
    background_tasks: BackgroundTasks,
    service = Depends(get_simulate_interview_service)
) -> SimulateInterviewBackgroundResponse:
    """
    Start simulation of interviews for all employees in a business in the background.
    Returns immediately while the simulation runs asynchronously.
    """
    try:
        # Validate the request first (business exists, has employees and questions)
        from app.db import get_session
        from app.models.models import Business, Employee, Question
        from sqlmodel import select
        
        session = next(get_session())
        try:
            business = session.get(Business, request.business_id)
            if not business:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="Business not found"
                )
            
            employees = list(session.exec(
                select(Employee).where(Employee.business_id == request.business_id)
            ))
            if not employees:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="No employees found for this business"
                )
            
            questions = list(session.exec(
                select(Question)
                .where(Question.business_id == request.business_id)
                .where(Question.is_follow_up == False)
            ))
            if not questions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="No questions found for this business"
                )
                
        finally:
            session.close()
        
        # Add the simulation to background tasks
        background_tasks.add_task(run_business_simulation_task, request)
        
        return SimulateInterviewBackgroundResponse(
            message=f"Business interview simulation started for {len(employees)} employees",
            business_id=request.business_id,
            status="started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start simulation: {str(e)}"
        )


@router.post(
    "interview/{employee_id}",
    response_model=SimulateEmployeeInterviewBackgroundResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def simulate_employee_interview(
    employee_id: UUID,
    request: SimulateEmployeeInterviewRequest,
    background_tasks: BackgroundTasks,
    service = Depends(get_simulate_interview_service)
) -> SimulateEmployeeInterviewBackgroundResponse:
    """
    Start simulation of a complete interview for a single employee in the background.
    Returns immediately while the simulation runs asynchronously.
    """
    try:
        # Ensure the employee_id from the path matches the request
        if request.employee_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Employee ID in path must match employee ID in request body"
            )
        
        # Validate the employee exists first
        from app.db import get_session
        from app.models.models import Employee, Interview
        
        session = next(get_session())
        try:
            employee = session.get(Employee, request.employee_id)
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Employee with ID {request.employee_id} not found"
                )
            
            # If interview_id is provided, validate it
            if request.interview_id:
                interview = session.get(Interview, request.interview_id)
                if not interview:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Interview with ID {request.interview_id} not found"
                    )
                if employee.business_id != interview.business_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Employee and interview must belong to the same business"
                    )
        finally:
            session.close()
        
        # Add the simulation to background tasks
        background_tasks.add_task(run_employee_simulation_task, request)
        
        return SimulateEmployeeInterviewBackgroundResponse(
            message=f"Employee interview simulation started for {employee.email}",
            employee_id=request.employee_id,
            interview_id=request.interview_id,
            status="started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start simulation: {str(e)}"
        )