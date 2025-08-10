from sqlmodel import Session, select
from fastapi import Depends
from app.services.schemas.schema import AnswerQuestionRequest, AnswerQuestionResponse
from app.models.models import Interview, Question, QuestionResponse
from app.db import get_session
from uuid import uuid4


class AnswerQuestionService:
    """Service for answering questions in an interview"""

    def __init__(self, session: Session):
        self.session = session

    def answer_question(self, request: AnswerQuestionRequest) -> AnswerQuestionResponse:
        """
        Answer a question in an interview

        Args:
            request: AnswerQuestionRequest containing interview_id, question_id, and content

        Returns:
            AnswerQuestionResponse containing success flag and interview_id

        Raises:
            ValueError: If interview or question does not exist, or if they don't belong to the same business
        """
        # Validate interview exists
        interview = self.session.get(Interview, request.interview_id)
        if not interview:
            raise ValueError(f"Interview with ID {request.interview_id} not found")

        # Validate question exists
        question = self.session.get(Question, request.question_id)
        if not question:
            raise ValueError(f"Question with ID {request.question_id} not found")

        # Validate question belongs to the same business as the interview
        if question.business_id != interview.business_id:
            raise ValueError("Question and interview must belong to the same business")

        # Check if a response already exists for this combination
        existing_response_stmt = select(QuestionResponse).where(
            QuestionResponse.interview_id == request.interview_id,
            QuestionResponse.employee_id == interview.employee_id,
            QuestionResponse.question_id == request.question_id
        )
        existing_response = self.session.exec(existing_response_stmt).first()

        if existing_response:
            # Update the existing response content
            existing_response.content = request.content
            self.session.commit()
            self.session.refresh(existing_response)
        else:
            # Create a new question response record using the employee from the interview
            response = QuestionResponse(
                interview_id=request.interview_id,
                employee_id=interview.employee_id,
                question_id=request.question_id,
                content=request.content,
            )

            self.session.add(response)
            self.session.commit()
            self.session.refresh(response)

        return AnswerQuestionResponse(success=True, interview_id=request.interview_id)


def get_answer_question_service(
    session: Session = Depends(get_session),
) -> AnswerQuestionService:
    """Get AnswerQuestionService with injected dependencies"""
    return AnswerQuestionService(session)
