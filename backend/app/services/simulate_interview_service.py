from typing import List
from uuid import UUID
from sqlmodel import Session, select
from fastapi import Depends

from app.db import get_session
from app.models.models import Business, Employee, Question, Interview, QuestionResponse
from app.services.schemas.schema import (
    SimulateInterviewRequest,
    SimulateInterviewResponse,
    EmployeeSimulation,
)


class SimulateInterviewService:
    """Service for simulating interviews"""

    def __init__(self, session: Session):
        self.session = session

    def simulate_interview(self, request: SimulateInterviewRequest) -> SimulateInterviewResponse:
        """
        Simulate an interview for a business by generating responses for all employees
        to all questions in the business.

        Args:
            request: SimulateInterviewRequest containing business_id

        Returns:
            SimulateInterviewResponse containing simulation results

        Raises:
            ValueError: If business not found, or no employees/questions exist
        """
        # Get the business
        business = self.session.get(Business, request.business_id)
        if not business:
            raise ValueError("Business not found")

        # Get all employees and questions for the business
        employees = list(self.session.exec(
            select(Employee).where(Employee.business_id == request.business_id)
        ))

        questions_stmt = (
            select(Question)
            .where(Question.business_id == request.business_id)
            .where(Question.is_follow_up == False)
        )
        questions_raw = list(self.session.exec(questions_stmt))
        # Sort by order_index manually to handle None values
        questions = sorted(questions_raw, key=lambda q: q.order_index if q.order_index is not None else 999)

        if not employees:
            raise ValueError("No employees found for this business")

        if not questions:
            raise ValueError("No questions found for this business")

        # Simulate responses for each employee to each question
        employee_simulations = []

        for employee in employees:
            # Create a separate interview for each employee
            interview = Interview(business_id=request.business_id, employee_id=employee.id)
            self.session.add(interview)
            self.session.commit()
            self.session.refresh(interview)
            
            responses = []

            for question in questions:
                # Generate a simulated response based on employee bio and question
                simulated_content = self._generate_simulated_response(employee, question)

                # Create the response record
                response = QuestionResponse(
                    interview_id=interview.id,
                    employee_id=employee.id,
                    question_id=question.id,
                    content=simulated_content,
                )
                self.session.add(response)

                responses.append(
                    {
                        "question_id": str(question.id),
                        "question_content": question.content,
                        "response_content": simulated_content,
                        "is_follow_up": question.is_follow_up,
                    }
                )

            employee_simulations.append(
                EmployeeSimulation(
                    employee_id=employee.id,
                    employee_email=employee.email,
                    responses=responses,
                )
            )

        # Commit all responses
        self.session.commit()

        # Prepare questions data
        questions_asked = [
            {
                "question_id": str(q.id),
                "content": q.content,
                "is_follow_up": q.is_follow_up,
                "order_index": q.order_index,
            }
            for q in questions
        ]

        # Use the last interview created (they all belong to same business anyway)
        return SimulateInterviewResponse(
            interview_id=interview.id,
            business_id=request.business_id,
            business_name=business.name,
            employee_simulations=employee_simulations,
            questions_asked=questions_asked,
        )

    def _generate_simulated_response(self, employee: Employee, question: Question) -> str:
        """
        Generate a simulated response based on employee bio and question content.
        This is a simple implementation - in a real system, you might use AI/LLM here.
        """
        base_responses = [
            f"Based on my experience, I would approach this by...",
            f"In my role, I've found that...",
            f"From my perspective, the key considerations are...",
            f"I believe the best approach would be to...",
            f"Drawing from my background, I think...",
        ]

        # Simple logic to vary responses based on question content
        if "challenge" in question.content.lower():
            return f"One significant challenge I've faced was... {employee.bio[:50] if employee.bio else 'In my experience,'} I overcame it by focusing on systematic problem-solving."
        elif "strength" in question.content.lower():
            return f"My key strength is... {employee.bio[:50] if employee.bio else 'I bring valuable experience'} which allows me to contribute effectively to team goals."
        elif "weakness" in question.content.lower():
            return f"An area I'm working to improve is... I've been actively addressing this through focused learning and seeking feedback."
        elif "goal" in question.content.lower():
            return f"My professional goals include... {employee.bio[:50] if employee.bio else 'I aim to grow'} while contributing to organizational success."
        else:
            # Default response incorporating employee bio if available
            bio_context = (
                f" Drawing from my background: {employee.bio[:100]}..."
                if employee.bio
                else ""
            )
            return f"Regarding this question, I believe the key factors to consider are...{bio_context}"


def get_simulate_interview_service(
    session: Session = Depends(get_session),
) -> SimulateInterviewService:
    """Get SimulateInterviewService with injected dependencies"""
    return SimulateInterviewService(session)
