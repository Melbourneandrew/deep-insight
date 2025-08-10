import asyncio
import logging
import os
from typing import List
from uuid import UUID
from sqlmodel import Session, select
from fastapi import Depends

from app.db import get_session
from app.models.models import Business, Employee, Question, Interview, QuestionResponse
from app.services.schemas.schema import (
    SimulateInterviewRequest,
    SimulateInterviewResponse,
    SimulateEmployeeInterviewRequest,
    SimulateEmployeeInterviewResponse,
    SimulatedQAExchange,
    EmployeeSimulation,
    NextQuestionRequest,
    AnswerQuestionRequest,
    StartInterviewRequest,
)
from app.services.next_question_service import get_next_question_service
from app.services.answer_question_service import get_answer_question_service
from app.services.start_interview_service import get_start_interview_service
import litellm

logger = logging.getLogger(__name__)


class SimulateInterviewService:
    """Service for simulating interviews - both individual and business-wide"""

    def __init__(self, session: Session):
        self.session = session

    async def simulate_business_interviews(self, request: SimulateInterviewRequest) -> SimulateInterviewResponse:
        """
        Simulate interviews for all employees in a business using parallel processing.
        Uses asyncio.gather to run employee simulations concurrently.

        Args:
            request: SimulateInterviewRequest containing business_id

        Returns:
            SimulateInterviewResponse containing results for all employees

        Raises:
            ValueError: If business not found, or no employees/questions exist
        """
        # Get the business
        business = self.session.get(Business, request.business_id)
        if not business:
            raise ValueError("Business not found")

        # Get all employees for the business
        employees = list(self.session.exec(
            select(Employee).where(Employee.business_id == request.business_id)
        ))

        if not employees:
            raise ValueError("No employees found for this business")

        # Get all base questions to validate there are questions
        questions_stmt = (
            select(Question)
            .where(Question.business_id == request.business_id)
            .where(Question.is_follow_up == False)
        )
        questions = list(self.session.exec(questions_stmt))

        if not questions:
            raise ValueError("No questions found for this business")

        # Create tasks for parallel employee simulations
        logger.info(f"Starting parallel simulation for {len(employees)} employees")
        
        simulation_tasks = []
        for employee in employees:
            # Create a separate session for each async task to avoid conflicts
            task = self._simulate_single_employee_with_new_session(employee.id)
            simulation_tasks.append(task)

        # Run all simulations in parallel with timeout and retry logic
        try:
            employee_simulation_results = await asyncio.wait_for(
                asyncio.gather(*simulation_tasks, return_exceptions=True),
                timeout=120.0  # 2 minute timeout for all simulations
            )
        except asyncio.TimeoutError:
            logger.error("Parallel simulation timed out after 2 minutes")
            raise ValueError("Simulation timed out - please try again")

        # Process results and handle any exceptions
        successful_simulations = []
        failed_simulations = []

        for i, result in enumerate(employee_simulation_results):
            employee = employees[i]
            if isinstance(result, Exception):
                logger.error(f"Failed to simulate interview for employee {employee.id}: {result}")
                failed_simulations.append(employee.id)
                # Continue with other successful simulations rather than failing completely
            else:
                successful_simulations.append(result)

        # Require at least one successful simulation
        if not successful_simulations:
            raise ValueError(f"All {len(employees)} employee simulations failed. Please check the logs and try again.")

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

        # Use the first successful simulation's interview_id as the main interview_id
        main_interview_id = successful_simulations[0]["interview_id"]

        return SimulateInterviewResponse(
            interview_id=main_interview_id,
            business_id=request.business_id,
            business_name=business.name,
            employee_simulations=successful_simulations,
            questions_asked=questions_asked,
        )

    async def _simulate_single_employee_with_new_session(self, employee_id: UUID) -> dict:
        """
        Simulate interview for a single employee using a new database session.
        This is used for parallel processing to avoid session conflicts.
        """
        # Create a new session for this task
        from app.db import engine
        from sqlmodel import Session
        
        with Session(engine) as new_session:
            temp_service = SimulateInterviewService(new_session)
            
            # Create a new interview for this employee
            employee = new_session.get(Employee, employee_id)
            if not employee:
                raise ValueError(f"Employee {employee_id} not found")

            start_service = get_start_interview_service(new_session)
            start_request = StartInterviewRequest(employee_id=employee_id)
            start_response = start_service.start_interview(start_request)

            # Simulate the employee interview
            simulate_request = SimulateEmployeeInterviewRequest(
                employee_id=employee_id,
                interview_id=start_response.interview_id
            )
            
            result = await temp_service.simulate_employee_interview(simulate_request)
            
            # Convert to the format expected by business simulation
            responses = []
            for exchange in result.simulated_exchanges:
                responses.append({
                    "question_id": str(exchange.question_id),
                    "question_content": exchange.question_content,
                    "response_content": exchange.response_content,
                    "is_follow_up": exchange.is_follow_up,
                })

            return {
                "interview_id": result.interview_id,
                "employee_id": result.employee_id,
                "employee_email": result.employee_email,
                "responses": responses,
            }

    async def simulate_employee_interview(self, request: SimulateEmployeeInterviewRequest) -> SimulateEmployeeInterviewResponse:
        """
        Simulate a complete interview for a single employee by following the actual interview flow.

        Args:
            request: SimulateEmployeeInterviewRequest containing employee_id and optional interview_id

        Returns:
            SimulateEmployeeInterviewResponse containing the simulated interview results

        Raises:
            ValueError: If employee not found or interview/employee don't match
        """
        # Validate employee exists
        employee = self.session.get(Employee, request.employee_id)
        if not employee:
            raise ValueError(f"Employee with ID {request.employee_id} not found")

        # Get or create interview
        if request.interview_id:
            interview = self.session.get(Interview, request.interview_id)
            if not interview:
                raise ValueError(f"Interview with ID {request.interview_id} not found")
            
            # Validate employee belongs to the same business as the interview
            if employee.business_id != interview.business_id:
                raise ValueError("Employee and interview must belong to the same business")
            
            # Update interview to be associated with this employee
            interview.employee_id = request.employee_id
            self.session.commit()
        else:
            # Create a new interview
            start_service = get_start_interview_service(self.session)
            start_request = StartInterviewRequest(employee_id=request.employee_id)
            start_response = start_service.start_interview(start_request)
            
            interview = self.session.get(Interview, start_response.interview_id)
            if not interview:
                raise ValueError(f"Failed to create or retrieve interview {start_response.interview_id}")

        # Get business for response
        business = self.session.get(Business, interview.business_id)
        if not business:
            raise ValueError("Business not found")

        # Get required services
        next_question_service = get_next_question_service(self.session)
        answer_question_service = get_answer_question_service(self.session)

        simulated_exchanges = []
        max_questions = 50  # Safety limit to prevent infinite loops

        for i in range(max_questions):
            # Get the next question
            next_question_request = NextQuestionRequest(interview_id=interview.id)
            next_question_response = next_question_service.get_next_question(next_question_request)

            if next_question_response.is_interview_over or not next_question_response.question:
                logger.info(f"Interview simulation completed after {i} questions")
                break

            question_base = next_question_response.question
            
            # Get the full Question object from the database
            question = self.session.get(Question, question_base.id)
            if not question:
                logger.error(f"Could not find question with ID {question_base.id}")
                break

            # Generate AI response based on employee bio and question
            ai_response_content = await self._generate_ai_response(employee, question)

            # Save the response using the actual answer question service
            answer_request = AnswerQuestionRequest(
                interview_id=interview.id,
                question_id=question.id,
                content=ai_response_content
            )
            answer_question_service.answer_question(answer_request)

            # Add to simulated exchanges
            simulated_exchanges.append(
                SimulatedQAExchange(
                    question_id=question.id,
                    question_content=question.content,
                    response_content=ai_response_content,
                    is_follow_up=question.is_follow_up,
                    order_index=question.order_index,
                )
            )

            logger.info(f"Simulated Q&A #{i+1}: {question.content[:50]}...")

        is_complete = len(simulated_exchanges) < max_questions  # If we didn't hit the limit, it's complete

        return SimulateEmployeeInterviewResponse(
            interview_id=interview.id,
            employee_id=request.employee_id,
            employee_email=employee.email,
            business_id=interview.business_id,
            business_name=business.name,
            simulated_exchanges=simulated_exchanges,
            is_interview_complete=is_complete,
        )

    async def _generate_ai_response(self, employee: Employee, question: Question) -> str:
        """
        Generate an AI response based on the employee's bio and the question content.
        Uses litellm with async support for better performance in parallel processing.
        """
        model = os.getenv("INTERVIEW_MODEL", "openrouter/openai/gpt-oss-120b")
        logger.info(f"Generating AI response for employee {employee.email} using model: {model}")

        # Build system prompt with employee context
        bio_context = f"Employee bio: {employee.bio}" if employee.bio else "No specific bio available."
        
        system_prompt = f"""You are role-playing as an employee in a job interview. 

{bio_context}

Respond to interview questions as this employee would, drawing from their background and experience. Your responses should be:
1. Professional and authentic
2. 1-3 sentences long
3. Specific and detailed when possible
4. Consistent with the employee's background
5. Natural and conversational

Respond only with the answer content, no additional formatting or explanation."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Interview question: {question.content}"}
        ]

        try:
            # Use sync completion with proper error handling for better reliability
            response = litellm.completion(
                model=model,
                messages=messages,
                max_tokens=200,
                temperature=0.7,
                timeout=30  # 30 second timeout per request
            )

            # Extract content using robust attribute access
            try:
                # Method 1: Try direct ModelResponse structure
                if hasattr(response, 'choices') and response.choices:
                    choice = response.choices[0]
                    if hasattr(choice, 'message') and choice.message:
                        message = choice.message
                        # Try content first
                        if hasattr(message, 'content') and message.content and message.content.strip():
                            content = message.content.strip()
                            logger.info(f"Successfully generated AI response: {content[:100]}...")
                            return content
                        # Try reasoning_content if content is empty (for reasoning models)
                        elif hasattr(message, 'reasoning_content') and message.reasoning_content and message.reasoning_content.strip():
                            content = message.reasoning_content.strip()
                            # For employee responses, try to extract the actual answer from reasoning
                            if '"' in content:
                                # Look for quoted responses in reasoning
                                import re
                                response_match = re.search(r'"([^"]+\.)"', content)
                                if response_match:
                                    response_text = response_match.group(1).strip()
                                    logger.info(f"Extracted response from reasoning: {response_text[:100]}...")
                                    return response_text
                            logger.info(f"Using reasoning content as response: {content[:100]}...")
                            return content
                
                # Method 2: Try dict-like access on response object
                try:
                    if hasattr(response, '__dict__') or hasattr(response, '__getitem__'):
                        # Try to access as dict or dict-like object
                        choices = getattr(response, 'choices', None)
                        if choices and len(choices) > 0:
                            choice = choices[0]
                            message = getattr(choice, 'message', None)
                            if message:
                                content = getattr(message, 'content', None)
                                if content and str(content).strip():
                                    logger.info(f"Successfully generated AI response: {str(content)[:100]}...")
                                    return str(content).strip()
                except (AttributeError, TypeError, IndexError):
                    pass
                
                # Method 3: Convert to string and extract meaningful content
                response_str = str(response)
                logger.debug(f"Raw response: {response_str[:200]}...")
                
                # Look for content patterns in the string representation
                import re
                content_match = re.search(r"content='([^']+)'", response_str)
                if content_match:
                    content = content_match.group(1).strip()
                    # Filter out system prompts/reasoning that leaked through
                    if content and not content.startswith("We need to") and not content.startswith("The user wants"):
                        logger.info(f"Successfully extracted response from string: {content[:100]}...")
                        return content
                    else:
                        logger.warning(f"Filtered out invalid response content: {content[:100]}...")
                
                # Try alternate content extraction patterns
                content_match = re.search(r'"content"\s*:\s*"([^"]+)"', response_str)
                if content_match:
                    content = content_match.group(1).strip()
                    if content and not content.startswith("We need to") and not content.startswith("The user wants"):
                        logger.info(f"Successfully extracted response from JSON pattern: {content[:100]}...")
                        return content
                
                # Log detailed debug info
                logger.error(f"Unable to parse AI response. Response type: {type(response)}")
                logger.error(f"Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
                if hasattr(response, '__dict__'):
                    logger.error(f"Response dict: {response.__dict__}")
                
            except Exception as parse_error:
                logger.error(f"Exception during AI response parsing: {parse_error}")
                
            # If we reach here, all parsing methods failed
            raise ValueError("Failed to parse LLM response - no valid content found")

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            raise e


def get_simulate_interview_service(
    session: Session = Depends(get_session),
) -> SimulateInterviewService:
    """Get SimulateInterviewService with injected dependencies"""
    return SimulateInterviewService(session)