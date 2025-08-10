from sqlmodel import Session
from fastapi import Depends
from app.services.schemas.schema import StartInterviewRequest, StartInterviewResponse
from app.models.models import Employee, Interview
from app.db import get_session


class StartInterviewService:
    """Service for starting interviews"""

    def __init__(self, session: Session):
        self.session = session

    def start_interview(self, request: StartInterviewRequest) -> StartInterviewResponse:
        """
        Start an interview for an employee

        Args:
            request: StartInterviewRequest containing employee_id

        Returns:
            StartInterviewResponse containing interview_id

        Raises:
            ValueError: If employee does not exist
        """
        # Validate employee exists
        employee = self.session.get(Employee, request.employee_id)
        if not employee:
            raise ValueError(f"Employee with ID {request.employee_id} not found")

        # Create new interview record
        interview = Interview(
            business_id=employee.business_id, employee_id=request.employee_id
        )

        self.session.add(interview)
        self.session.commit()
        self.session.refresh(interview)

        return StartInterviewResponse(interview_id=interview.id)


def get_start_interview_service(
    session: Session = Depends(get_session),
) -> StartInterviewService:
    """Get StartInterviewService with injected dependencies"""
    return StartInterviewService(session)
