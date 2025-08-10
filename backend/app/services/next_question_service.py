from sqlmodel import Session, select
from fastapi import Depends
from app.services.schemas.schema import NextQuestionRequest, NextQuestionResponse
from app.models.models import Interview, Question, QuestionResponse
from app.db import get_session


class NextQuestionService:
    """Service for getting the next question in an interview"""

    def __init__(self, session: Session):
        self.session = session

    def get_next_question(self, request: NextQuestionRequest) -> NextQuestionResponse:
        """
        Get the next question for an interview

        Args:
            request: NextQuestionRequest containing interview_id

        Returns:
            NextQuestionResponse containing question and is_interview_over flag

        Raises:
            ValueError: If interview does not exist
        """
        # Validate interview exists
        interview = self.session.get(Interview, request.interview_id)
        if not interview:
            raise ValueError(f"Interview with ID {request.interview_id} not found")

        # Get the first unanswered question using LEFT JOIN
        # This finds questions that don't have responses for this interview
        unanswered_question_stmt = (
            select(Question)
            .outerjoin(
                QuestionResponse,
                (QuestionResponse.question_id == Question.id)
                & (QuestionResponse.interview_id == request.interview_id),
            )
            .where(
                (Question.business_id == interview.business_id)
                & (QuestionResponse.question_id.is_(None))  # No response exists
            )
            .order_by(Question.order_index.asc())
        )

        unanswered_question = self.session.exec(unanswered_question_stmt).first()

        if unanswered_question:
            return NextQuestionResponse(
                question=unanswered_question, is_interview_over=False
            )

        # All questions have been answered
        return NextQuestionResponse(question=None, is_interview_over=True)


def get_next_question_service(
    session: Session = Depends(get_session),
) -> NextQuestionService:
    """Get NextQuestionService with injected dependencies"""
    return NextQuestionService(session)
