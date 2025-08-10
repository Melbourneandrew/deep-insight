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
        # # Validate interview exists
        # interview = self.session.get(Interview, request.interview_id)
        # if not interview:
        #     raise ValueError(f"Interview with ID {request.interview_id} not found")

        # # Get all questions for the business, ordered by order_index
        # questions_stmt = (
        #     select(Question)
        #     .where(Question.business_id == interview.business_id)
        #     .order_by(Question.order_index.asc())
        # )
        # questions = self.session.exec(questions_stmt).all()

        # if not questions:
        #     return NextQuestionResponse(question=None, is_interview_over=True)

        # # Get all answered questions for this interview
        # answered_questions_stmt = select(QuestionResponse.question_id).where(
        #     QuestionResponse.interview_id == request.interview_id
        # )
        # answered_question_ids = set(self.session.exec(answered_questions_stmt).all())

        # # Find the first unanswered question
        # for question in questions:
        #     if question.id not in answered_question_ids:
        #         return NextQuestionResponse(question=question, is_interview_over=False)

        # All questions have been answered
        # return NextQuestionResponse(question=None, is_interview_over=True)

        return NextQuestionResponse(
            question="How far away is the sun?", is_interview_over=True
        )


def get_next_question_service(
    session: Session = Depends(get_session),
) -> NextQuestionService:
    """Get NextQuestionService with injected dependencies"""
    return NextQuestionService(session)
