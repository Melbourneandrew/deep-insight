from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.schemas.schema import SimulateInterviewRequest, SimulateInterviewResponse
from app.services.simulate_interview_service import get_simulate_interview_service


router = APIRouter(prefix="/simulate", tags=["simulate"])


@router.post(
    "/interview",
    response_model=SimulateInterviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def simulate_interview(
    request: SimulateInterviewRequest,
    service = Depends(get_simulate_interview_service)
) -> SimulateInterviewResponse:
    """
    Simulate an interview for a business by generating responses for all employees
    to all questions in the business.
    """
    try:
        return service.simulate_interview(request)
    except ValueError as e:
        # Convert service ValueError to appropriate HTTP status
        error_message = str(e)
        if "not found" in error_message.lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "no employees" in error_message.lower() or "no questions" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=error_message)