import logging
import os
from typing import List, Optional
from uuid import UUID, uuid4
from sqlmodel import Session, select
from fastapi import Depends
from app.services.schemas.schema import NextQuestionRequest, NextQuestionResponse
from app.models.models import Interview, Question, QuestionResponse
from app.db import get_session
import litellm

logger = logging.getLogger(__name__)


class NextQuestionService:
    """Service for getting the next question in an interview with follow-up generation"""

    def __init__(self, session: Session):
        self.session = session

    async def get_next_question(self, request: NextQuestionRequest) -> NextQuestionResponse:
        """
        Get the next question for an interview following the pattern:
        (base_question -> generated_followup_1 -> generated_followup_2) x N -> done

        Args:
            request: NextQuestionRequest containing interview_id

        Returns:
            NextQuestionResponse containing question and is_interview_over flag

        Raises:
            ValueError: If interview not found
        """
        # Validate interview exists
        interview = self.session.get(Interview, request.interview_id)
        if not interview:
            raise ValueError(f"Interview with ID {request.interview_id} not found")

        # Get all base questions for this business
        base_questions = self._get_base_questions(interview.business_id)
        if not base_questions:
            return NextQuestionResponse(question=None, is_interview_over=True)

        # Get all responses for this interview
        responses = self._get_interview_responses(request.interview_id)

        # Determine what the next question should be
        next_question = await self._determine_next_question(
            base_questions, responses, interview
        )

        if next_question:
            return NextQuestionResponse(question=next_question, is_interview_over=False)
        else:
            return NextQuestionResponse(question=None, is_interview_over=True)

    def _get_base_questions(self, business_id: UUID) -> List[Question]:
        """Get all base questions for a business, ordered by index."""
        statement = (
            select(Question)
            .where(Question.business_id == business_id)
            .where(Question.is_follow_up == False)
        )
        base_questions_raw = list(self.session.exec(statement))
        # Sort by order_index manually to handle None values
        return sorted(
            base_questions_raw,
            key=lambda q: q.order_index if q.order_index is not None else 999,
        )

    def _get_interview_responses(self, interview_id: UUID) -> List[QuestionResponse]:
        """Get all responses for an interview."""
        statement = select(QuestionResponse).where(
            QuestionResponse.interview_id == interview_id
        )
        return list(self.session.exec(statement))

    async def _determine_next_question(
        self,
        base_questions: List[Question],
        responses: List[QuestionResponse],
        interview: Interview,
    ) -> Optional[Question]:
        """Determine what the next question should be based on interview state."""

        if not responses:
            # No questions asked yet, start with the first base question
            return base_questions[0] if base_questions else None

        # Get the last question that was answered
        last_response = responses[-1]
        last_question = self.session.get(Question, last_response.question_id)

        if not last_question:
            return None

        if not last_question.is_follow_up:
            # Just answered a base question, generate first follow-up
            return await self._generate_follow_up_question(responses, interview, 1)
        else:
            # This was a follow-up question
            follow_up_count = self._count_recent_follow_ups(responses)

            if follow_up_count < 2:
                # Generate second follow-up
                return await self._generate_follow_up_question(
                    responses, interview, follow_up_count + 1
                )
            else:
                # Move to next base question
                current_base_index = self._get_current_base_question_index(
                    responses, base_questions
                )
                next_base_index = current_base_index + 1

                if next_base_index < len(base_questions):
                    return base_questions[next_base_index]
                else:
                    # All questions completed
                    return None

    def _count_recent_follow_ups(self, responses: List[QuestionResponse]) -> int:
        """Count how many follow-up questions have been asked since the last base question."""
        count = 0

        # Count backwards from the most recent response
        for response in reversed(responses):
            question = self.session.get(Question, response.question_id)
            if question and question.is_follow_up:
                count += 1
            else:
                # Hit a base question, stop counting
                break

        return count

    def _get_current_base_question_index(
        self, responses: List[QuestionResponse], base_questions: List[Question]
    ) -> int:
        """Find the index of the current base question being worked on."""

        # Look backwards through responses to find the most recent base question
        for response in reversed(responses):
            question = self.session.get(Question, response.question_id)
            if question and not question.is_follow_up:
                # Find this question in the base_questions list
                for i, base_q in enumerate(base_questions):
                    if base_q.id == question.id:
                        return i
                break

        return 0  # Default to first question if not found

    def _calculate_follow_up_order_index(
        self, responses: List[QuestionResponse], follow_up_number: int
    ) -> int:
        """Calculate the order_index for a follow-up question.

        Follow-ups are placed in the slots between scripted questions:
        - Scripted questions: 0, 3, 6, 9, ...
        - Follow-up slots: 1-2, 4-5, 7-8, ...
        """
        # Find the most recent base question to determine which slot we're in
        base_question_order_index = None

        for response in reversed(responses):
            question = self.session.get(Question, response.question_id)
            if (
                question
                and not question.is_follow_up
                and question.order_index is not None
            ):
                base_question_order_index = question.order_index
                break

        # Default to first base question if none found
        if base_question_order_index is None:
            base_question_order_index = 0

        # Calculate follow-up order_index: base + follow_up_number
        # For base question at index 0: follow-ups go to 1, 2
        # For base question at index 3: follow-ups go to 4, 5
        # For base question at index 6: follow-ups go to 7, 8
        return base_question_order_index + follow_up_number

    async def _generate_follow_up_question(
        self,
        responses: List[QuestionResponse],
        interview: Interview,
        follow_up_number: int,
    ) -> Question:
        """Generate a follow-up question using LiteLLM."""

        # Build conversation history for context
        conversation_history = self._build_conversation_history(responses)

        # Generate question using LiteLLM
        question_content = await self._generate_question_with_llm(
            conversation_history, follow_up_number
        )

        # Calculate the order_index for this follow-up question
        follow_up_order_index = self._calculate_follow_up_order_index(
            responses, follow_up_number
        )

        # Create and save the generated question
        generated_question = Question(
            id=uuid4(),
            content=question_content,
            business_id=interview.business_id,
            is_follow_up=True,
            order_index=follow_up_order_index,
        )

        self.session.add(generated_question)
        self.session.commit()
        self.session.refresh(generated_question)

        return generated_question

    def _build_conversation_history(
        self, responses: List[QuestionResponse]
    ) -> List[dict]:
        """Build conversation history in assistant/user format for LLM context."""
        conversation = []

        for response in responses:
            # Get the question content
            question = self.session.get(Question, response.question_id)
            if question:
                # Assistant asks question
                conversation.append({"role": "assistant", "content": question.content})
                # User answers
                conversation.append({"role": "user", "content": response.content})

        return conversation

    async def _generate_question_with_llm(
        self, conversation_history: List[dict], follow_up_number: int
    ) -> str:
        """Generate a follow-up question using LiteLLM with INTERVIEW_MODEL env var."""

        model = os.getenv("INTERVIEW_MODEL", "cerebras/gpt-oss-120b")

        system_prompt = f"""You are an AI interviewer conducting an employee interview. 

Based on the conversation history, generate a thoughtful follow-up question that:
1. Builds on the previous answers
2. Digs deeper into the topic
3. Helps understand the employee better
4. Is professional and engaging

This is follow-up question #{follow_up_number} in the current topic.

Respond with ONLY the question text, no additional formatting or explanation."""

        messages = (
            [{"role": "system", "content": system_prompt}]
            + conversation_history
            + [
                {
                    "role": "user",
                    "content": "Please generate the next follow-up question.",
                }
            ]
        )

        try:
            response = await litellm.acompletion(
                model=model, messages=messages, max_tokens=300, temperature=0.7
            )
            
            # Extract content using robust attribute access
            try:
                # Method 1: Try direct ModelResponse structure
                if hasattr(response, 'choices') and response.choices: # type: ignore
                    choice = response.choices[0] # type: ignore
                    if hasattr(choice, 'message') and choice.message: # type: ignore
                        message = choice.message # type: ignore
                        # Try content first
                        if hasattr(message, 'content') and message.content and message.content.strip():
                            content = message.content.strip()
                            logger.info(f"Successfully generated follow-up question: {content[:100]}...")
                            return content
                        # Try reasoning_content if content is empty (for reasoning models)
                        elif hasattr(message, 'reasoning_content') and message.reasoning_content and message.reasoning_content.strip():
                            reasoning = message.reasoning_content.strip()
                            logger.debug(f"Got reasoning content: {reasoning[:200]}...")
                            
                            # Extract the actual question from reasoning content
                            import re
                            
                            # Look for questions in quotes
                            question_patterns = [
                                r'"([^"]+\?)"',  # "Question ending with ?"
                                r'"([^"]+)"(?=\s*That|\s*It\'s|\s*Good)',  # "Question" followed by validation words
                                r'Let\'s craft:\s*"([^"]+)"',  # Let's craft: "Question"
                                r'craft a question:\s*"([^"]+)"',  # craft a question: "Question"
                            ]
                            
                            for pattern in question_patterns:
                                question_match = re.search(pattern, reasoning, re.IGNORECASE)
                                if question_match:
                                    question = question_match.group(1).strip()
                                    if len(question) > 10 and ('?' in question or question.endswith('.')):  # Basic validation
                                        logger.info(f"Extracted question from reasoning: {question[:100]}...")
                                        return question
                            
                            logger.error(f"Could not extract valid question from reasoning: {reasoning[:200]}...")
                            raise ValueError("Failed to parse LLM response - no valid content found")
                
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
                                    logger.info(f"Successfully generated follow-up question: {str(content)[:100]}...")
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
                    if content and not content.startswith("We need to generate") and not content.startswith("The user wants"):
                        logger.info(f"Successfully extracted question from string: {content[:100]}...")
                        return content
                    else:
                        logger.warning(f"Filtered out invalid question content: {content[:100]}...")
                
                # Try alternate content extraction patterns
                content_match = re.search(r'"content"\s*:\s*"([^"]+)"', response_str)
                if content_match:
                    content = content_match.group(1).strip()
                    if content and not content.startswith("We need to generate") and not content.startswith("The user wants"):
                        logger.info(f"Successfully extracted question from JSON pattern: {content[:100]}...")
                        return content
                
                # Log detailed debug info
                logger.error(f"Unable to parse LLM response. Response type: {type(response)}")
                logger.error(f"Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
                if hasattr(response, '__dict__'):
                    logger.error(f"Response dict: {response.__dict__}")
                
            except Exception as parse_error:
                logger.error(f"Exception during response parsing: {parse_error}")
                
            # If we reach here, all parsing methods failed
            raise ValueError("Failed to parse LLM response - no valid content found")
        except Exception as e:
            logger.error(f"Failed to generate follow-up question with LLM: {e}")
            raise ValueError(f"LLM question generation failed: {e}")


def get_next_question_service(
    session: Session = Depends(get_session),
) -> NextQuestionService:
    """Get NextQuestionService with injected dependencies"""
    return NextQuestionService(session)
