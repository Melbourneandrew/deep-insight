from uuid import UUID
from sqlmodel import Session

from app.models.models import Interview, Employee
from app.services.schemas.schema import StartInterviewRequest, StartInterviewResponse


class StartInterviewService:
    """Service for starting interviews"""

    def start_interview(self, request: StartInterviewRequest, session: Session) -> StartInterviewResponse:
        """
        Start an interview for an employee

        Args:
            request: StartInterviewRequest containing employee_id
            session: Database session

        Returns:
            StartInterviewResponse containing interview_id
            
        Raises:
            ValueError: If employee not found
        """
        # Validate that the employee exists
        employee = session.get(Employee, request.employee_id)
        if not employee:
            raise ValueError("Employee not found")
        
        # Create a new interview for this employee
        interview = Interview(business_id=employee.business_id, employee_id=employee.id)
        session.add(interview)
        session.commit()
        session.refresh(interview)
        
        return StartInterviewResponse(interview_id=interview.id)


# Global service instance
start_interview_service = StartInterviewService()


def get_start_interview_service() -> StartInterviewService:
    """Get the global start interview service instance."""
    return start_interview_service