from app.services.schemas.schema import NextQuestionRequest, NextQuestionResponse


class NextQuestionService:
    """Service for getting the next question in an interview"""

    def get_next_question(self, request: NextQuestionRequest) -> NextQuestionResponse:
        """
        Get the next question for an interview

        Args:
            request: NextQuestionRequest containing interview_id

        Returns:
            NextQuestionResponse containing question and is_interview_over flag
        """
        # TODO: Implement next question logic
        # - Validate interview exists
        # - Get questions for the business
        # - Find next unanswered question
        # - Return question or mark interview as over

        # Return blank response for now
        return NextQuestionResponse(
            question="How far away is the sun?", is_interview_over=False
        )
