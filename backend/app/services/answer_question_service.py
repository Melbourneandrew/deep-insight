from uuid import UUID
from sqlmodel import Session

from app.models.models import Interview, Question, QuestionResponse
from app.services.schemas.schema import AnswerQuestionRequest, AnswerQuestionResponse


class AnswerQuestionService:
    """Service for answering questions in an interview"""

    def answer_question(self, request: AnswerQuestionRequest, session: Session) -> AnswerQuestionResponse:
        """
        Answer a question in an interview

        Args:
            request: AnswerQuestionRequest containing interview_id, question_id, and content
            session: Database session

        Returns:
            AnswerQuestionResponse containing success flag and interview_id
            
        Raises:
            ValueError: If interview or question not found, or validation fails
        """
        # Validate that the interview exists
        interview = session.get(Interview, request.interview_id)
        if not interview:
            raise ValueError("Interview not found")
        
        # Validate that the question exists
        question = session.get(Question, request.question_id)
        if not question:
            raise ValueError("Question not found")
        
        # Validate that the question belongs to the same business as the interview
        if question.business_id != interview.business_id:
            raise ValueError("Question does not belong to the same business as the interview")
        
        # Create the question response using the employee_id from the interview
        response = QuestionResponse(
            interview_id=request.interview_id,
            employee_id=interview.employee_id,
            question_id=request.question_id,
            content=request.content
        )
        session.add(response)
        session.commit()
        
        return AnswerQuestionResponse(success=True, interview_id=request.interview_id)


# Global service instance
answer_question_service = AnswerQuestionService()


def get_answer_question_service() -> AnswerQuestionService:
    """Get the global answer question service instance."""
    return answer_question_service