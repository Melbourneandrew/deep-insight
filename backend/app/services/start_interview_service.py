from uuid import uuid4
from app.services.schemas.schema import StartInterviewRequest, StartInterviewResponse


class StartInterviewService:
    """Service for starting interviews"""

    def start_interview(self, request: StartInterviewRequest) -> StartInterviewResponse:
        """
        Start an interview for an employee

        Args:
            request: StartInterviewRequest containing employee_id

        Returns:
            StartInterviewResponse containing interview_id
        """
        # TODO: Implement interview creation logic
        # - Validate employee exists
        # - Create new interview record
        # - Return interview ID

        # Return blank response for now
        return StartInterviewResponse(interview_id=uuid4())
