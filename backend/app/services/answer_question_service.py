from app.services.schemas.schema import AnswerQuestionRequest, AnswerQuestionResponse


class AnswerQuestionService:
    """Service for answering questions in an interview"""

    def answer_question(self, request: AnswerQuestionRequest) -> AnswerQuestionResponse:
        """
        Answer a question in an interview

        Args:
            request: AnswerQuestionRequest containing interview_id, question_id, and content

        Returns:
            AnswerQuestionResponse containing success flag and interview_id
        """
        # TODO: Implement answer question logic
        # - Validate interview and question exist
        # - Create response record
        # - Link response to interview and question
        # - Return success status

        # Return blank response for now
        return AnswerQuestionResponse(success=True, interview_id=request.interview_id)
