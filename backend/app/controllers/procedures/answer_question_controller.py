from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.schemas.schema import AnswerQuestionRequest, AnswerQuestionResponse
from app.services.answer_question_service import (
    AnswerQuestionService,
    get_answer_question_service,
)


router = APIRouter(prefix="/procedures", tags=["procedures"])


@router.post(
    "/answer-question",
    response_model=AnswerQuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def answer_question(
    request: AnswerQuestionRequest,
    service: AnswerQuestionService = Depends(get_answer_question_service),
) -> AnswerQuestionResponse:
    """Answer a question in an interview"""
    try:
        return service.answer_question(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
