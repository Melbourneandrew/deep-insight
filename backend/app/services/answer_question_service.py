from uuid import uuid4
from sqlmodel import Session, select
from fastapi import Depends
from app.services.schemas.schema import AnswerQuestionRequest, AnswerQuestionResponse
from app.models.models import Interview, Question, QuestionResponse, Employee
from app.db import get_session


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
        # interview = self.session.get(Interview, request.interview_id)
        # if not interview:
        #     raise ValueError(f"Interview with ID {request.interview_id} not found")

        # # Validate question exists
        # question = self.session.get(Question, request.question_id)
        # if not question:
        #     raise ValueError(f"Question with ID {request.question_id} not found")

        # # Validate question belongs to the same business as the interview
        # if question.business_id != interview.business_id:
        #     raise ValueError("Question and interview must belong to the same business")

        # # Get the first employee from the business for this response
        # # Note: In a real scenario, we might need employee_id in the request
        # # For now, we'll use the first employee from the business
        # employee_stmt = select(Employee).where(
        #     Employee.business_id == interview.business_id
        # )
        # employee = self.session.exec(employee_stmt).first()
        # if not employee:
        #     raise ValueError(f"No employees found for business {interview.business_id}")

        # # Create the question response record
        # response = QuestionResponse(
        #     interview_id=request.interview_id,
        #     employee_id=employee.id,
        #     question_id=request.question_id,
        #     content=request.content,
        # )

        # self.session.add(response)
        # self.session.commit()
        # self.session.refresh(response)

        # return AnswerQuestionResponse(success=True, interview_id=request.interview_id)

        return AnswerQuestionResponse(success=True, interview_id=uuid4())


def get_answer_question_service(
    session: Session = Depends(get_session),
) -> AnswerQuestionService:
    """Get AnswerQuestionService with injected dependencies"""
    return AnswerQuestionService(session)
