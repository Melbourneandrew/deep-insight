from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db import get_session
from app.services.schemas.schema import NextQuestionRequest, NextQuestionResponse
from app.services.next_question_service import get_next_question_service


router = APIRouter(prefix="/next-question", tags=["procedures"])


@router.post("/", response_model=NextQuestionResponse)
def next_question(
    request: NextQuestionRequest, session: Session = Depends(get_session)
) -> NextQuestionResponse:
    """Get the next question for an interview, following the pattern:
    (base_question -> generated_followup_1 -> generated_followup_2) x N -> done
    """
    try:
        service = get_next_question_service()
        return service.get_next_question(request, session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
