"""Interview service for managing interview workflow and logic."""

import logging
import os
from typing import List, Optional
from uuid import UUID, uuid4
from sqlmodel import Session, select

from app.models.models import Interview, Question, QuestionResponse, Employee
import litellm

logger = logging.getLogger(__name__)


class InterviewService:
    """Service for managing interview operations."""
    
    def start_interview(self, employee_id: UUID, session: Session) -> Interview:
        """
        Start a new interview for an employee.
        
        Args:
            employee_id: ID of the employee being interviewed
            session: Database session
            
        Returns:
            Created Interview instance
            
        Raises:
            ValueError: If employee not found
        """
        # Validate that the employee exists
        employee = session.get(Employee, employee_id)
        if not employee:
            raise ValueError("Employee not found")
        
        # Create a new interview for this employee
        interview = Interview(business_id=employee.business_id, employee_id=employee.id)
        session.add(interview)
        session.commit()
        session.refresh(interview)
        
        return interview
    
    def answer_question(
        self, 
        interview_id: UUID, 
        question_id: UUID, 
        content: str, 
        session: Session
    ) -> bool:
        """
        Record an employee's answer to a question during an interview.
        
        Args:
            interview_id: ID of the interview
            question_id: ID of the question being answered
            content: The answer content
            session: Database session
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If interview or question not found, or validation fails
        """
        # Validate that the interview exists
        interview = session.get(Interview, interview_id)
        if not interview:
            raise ValueError("Interview not found")
        
        # Validate that the question exists
        question = session.get(Question, question_id)
        if not question:
            raise ValueError("Question not found")
        
        # Validate that the question belongs to the same business as the interview
        if question.business_id != interview.business_id:
            raise ValueError("Question does not belong to the same business as the interview")
        
        # Create the question response using the employee_id from the interview
        response = QuestionResponse(
            interview_id=interview_id,
            employee_id=interview.employee_id,
            question_id=question_id,
            content=content
        )
        session.add(response)
        session.commit()
        
        return True
    
    def next_question(self, interview_id: UUID, session: Session) -> Optional[Question]:
        """
        Get the next question for an interview following the pattern:
        (base_question -> generated_followup_1 -> generated_followup_2) x N -> done
        
        Args:
            interview_id: ID of the interview
            session: Database session
            
        Returns:
            Next Question instance or None if interview is complete
            
        Raises:
            ValueError: If interview not found
        """
        # Validate that the interview exists
        interview = session.get(Interview, interview_id)
        if not interview:
            raise ValueError("Interview not found")
        
        # Get all base questions for this business
        base_questions = self._get_base_questions(interview.business_id, session)
        if not base_questions:
            return None  # No questions configured for this business
        
        # Get all responses for this interview
        responses = self._get_interview_responses(interview_id, session)
        
        # Determine what the next question should be
        return self._determine_next_question(base_questions, responses, interview, session)
    
    def _get_base_questions(self, business_id: UUID, session: Session) -> List[Question]:
        """Get all base questions for a business, ordered by index."""
        statement = (
            select(Question)
            .where(Question.business_id == business_id)
            .where(Question.is_follow_up == False)
        )
        base_questions_raw = list(session.exec(statement))
        # Sort by order_index manually to handle None values
        return sorted(base_questions_raw, key=lambda q: q.order_index if q.order_index is not None else 999)
    
    def _get_interview_responses(self, interview_id: UUID, session: Session) -> List[QuestionResponse]:
        """Get all responses for an interview."""
        statement = (
            select(QuestionResponse)
            .where(QuestionResponse.interview_id == interview_id)
        )
        return list(session.exec(statement))
    
    def _determine_next_question(
        self,
        base_questions: List[Question],
        responses: List[QuestionResponse],
        interview: Interview,
        session: Session
    ) -> Optional[Question]:
        """Determine what the next question should be based on interview state."""
        
        if not responses:
            # No questions asked yet, start with the first base question
            return base_questions[0] if base_questions else None
        
        # Get the last question that was answered
        last_response = responses[-1]
        last_question = session.get(Question, last_response.question_id)
        
        if not last_question:
            return None
        
        if not last_question.is_follow_up:
            # Just answered a base question, generate first follow-up
            return self._generate_follow_up_question(responses, interview, session, 1)
        else:
            # This was a follow-up question
            follow_up_count = self._count_recent_follow_ups(responses, session)
            
            if follow_up_count < 2:
                # Generate second follow-up
                return self._generate_follow_up_question(responses, interview, session, follow_up_count + 1)
            else:
                # Move to next base question
                current_base_index = self._get_current_base_question_index(responses, base_questions, session)
                next_base_index = current_base_index + 1
                
                if next_base_index < len(base_questions):
                    return base_questions[next_base_index]
                else:
                    # All questions completed
                    return None
    
    def _count_recent_follow_ups(self, responses: List[QuestionResponse], session: Session) -> int:
        """Count how many follow-up questions have been asked since the last base question."""
        count = 0
        
        # Count backwards from the most recent response
        for response in reversed(responses):
            question = session.get(Question, response.question_id)
            if question and question.is_follow_up:
                count += 1
            else:
                # Hit a base question, stop counting
                break
        
        return count
    
    def _get_current_base_question_index(
        self,
        responses: List[QuestionResponse],
        base_questions: List[Question],
        session: Session
    ) -> int:
        """Find the index of the current base question being worked on."""
        
        # Look backwards through responses to find the most recent base question
        for response in reversed(responses):
            question = session.get(Question, response.question_id)
            if question and not question.is_follow_up:
                # Find this question in the base_questions list
                for i, base_q in enumerate(base_questions):
                    if base_q.id == question.id:
                        return i
                break
        
        return 0  # Default to first question if not found
    
    def _generate_follow_up_question(
        self,
        responses: List[QuestionResponse],
        interview: Interview,
        session: Session,
        follow_up_number: int
    ) -> Question:
        """Generate a follow-up question using LiteLLM."""
        
        # Build conversation history for context
        conversation_history = self._build_conversation_history(responses, session)
        
        # Generate question using LiteLLM
        question_content = self._generate_question_with_llm(conversation_history, follow_up_number)
        
        # Create and save the generated question
        generated_question = Question(
            id=uuid4(),
            content=question_content,
            business_id=interview.business_id,
            is_follow_up=True,
            order_index=None  # Follow-ups don't have order indices
        )
        
        session.add(generated_question)
        session.commit()
        session.refresh(generated_question)
        
        return generated_question
    
    def _build_conversation_history(self, responses: List[QuestionResponse], session: Session) -> List[dict]:
        """Build conversation history in assistant/user format for LLM context."""
        conversation = []
        
        for response in responses:
            # Get the question content
            question = session.get(Question, response.question_id)
            if question:
                # Assistant asks question
                conversation.append({
                    "role": "assistant",
                    "content": question.content
                })
                # User answers
                conversation.append({
                    "role": "user", 
                    "content": response.content
                })
        
        return conversation
    
    def _generate_question_with_llm(self, conversation_history: List[dict], follow_up_number: int) -> str:
        """Generate a follow-up question using LiteLLM with INTERVIEW_MODEL env var."""
        
        model = os.getenv("INTERVIEW_MODEL", "openrouter/openai/gpt-oss-120b")
        
        system_prompt = f"""You are an AI interviewer conducting an employee interview. 

Based on the conversation history, generate a thoughtful follow-up question that:
1. Builds on the previous answers
2. Digs deeper into the topic
3. Helps understand the employee better
4. Is professional and engaging

This is follow-up question #{follow_up_number} in the current topic.

Respond with ONLY the question text, no additional formatting or explanation."""

        messages = [
            {"role": "system", "content": system_prompt}
        ] + conversation_history + [
            {"role": "user", "content": "Please generate the next follow-up question."}
        ]
        
        try:
            response = litellm.completion(
                model=model,
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            # Extract content safely - handle various response types
            try:
                # Try basic attribute access first
                if hasattr(response, 'choices') and getattr(response, 'choices', None):
                    choices = getattr(response, 'choices')
                    if choices and len(choices) > 0:
                        choice = choices[0]
                        if hasattr(choice, 'message'):
                            message = getattr(choice, 'message', None)
                            if message and hasattr(message, 'content'):
                                content = getattr(message, 'content', None)
                                if content and isinstance(content, str):
                                    return content.strip()
                
                # Alternative parsing for different response formats
                if hasattr(response, '__dict__'):
                    response_dict = getattr(response, '__dict__', {})
                    if 'choices' in response_dict and response_dict['choices']:
                        choice = response_dict['choices'][0]
                        if isinstance(choice, dict) and 'message' in choice and 'content' in choice['message']:
                            content = choice['message']['content']
                            if content and isinstance(content, str):
                                return content.strip()
                
            except (AttributeError, KeyError, IndexError, TypeError, Exception) as parse_error:
                logger.error(f"Failed to parse follow-up question response: {parse_error}")
                raise ValueError(f"Failed to parse follow-up question response: {parse_error}")
            
            # If we reach here, parsing failed but no exception was caught
            raise ValueError("Failed to parse LLM response - no valid content found")
            
        except Exception as e:
            logger.error(f"Error generating follow-up question: {e}")
            raise e


# Global service instance
interview_service = InterviewService()


def get_interview_service() -> InterviewService:
    """Get the global interview service instance."""
    return interview_service
