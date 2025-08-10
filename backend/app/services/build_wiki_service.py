import asyncio
import logging
import os
import shutil
import sys
from pathlib import Path
from uuid import UUID

import yaml
from app.agents.chain import run_chain
from app.db import get_session
from app.models.models import (Business, Employee, Interview, Question,
                               QuestionResponse)
from app.services.schemas.schema import BuildWikiRequest, BuildWikiResponse
from fastapi import Depends
from sqlmodel import Session, select

logger = logging.getLogger(__name__)


class BuildWikiService:
    """Service for building wiki documentation from interview data"""

    def __init__(self, session: Session):
        self.session = session

    async def build_wiki(self, request: BuildWikiRequest) -> BuildWikiResponse:
        """
        Build wiki documentation from interview data for a business.
        
        Args:
            request: BuildWikiRequest containing business_id
            
        Returns:
            BuildWikiResponse containing success status and build results
            
        Raises:
            ValueError: If business not found or no interview data exists
        """
        # Get the business
        business = self.session.get(Business, request.business_id)
        if not business:
            raise ValueError("Business not found")

        # Generate YAML from interview data in the database
        yaml_text = self._generate_yaml_from_interviews(request.business_id)
        if not yaml_text.strip():
            raise ValueError("No interview data found for this business")

        # Get docs directory path
        backend_dir = Path(__file__).resolve().parents[2]
        repo_root = backend_dir.parent
        docs_root_dir = repo_root / "docs"
        docs_output_dir = docs_root_dir / "docs"

        # Clear the docs output directory before building
        self._clear_docs_folder(docs_output_dir)

        # Get model from environment variable with default
        model = os.getenv("WIKI_MODEL", "openai/gpt-5-mini-2025-08-07")

        # Build wiki using the existing build_wiki_from_yaml_text function
        sections_plan, created_files = await run_chain(yaml_text, docs_output_dir, docs_root_dir, model=model)

        # Convert Path objects to strings for the response
        file_paths = [str(file_path) for file_path in created_files]

        return BuildWikiResponse(
            success=True,
            business_id=request.business_id,
            sections_plan=sections_plan,
            files_created=file_paths
        )

    def _clear_docs_folder(self, docs_output_dir: Path) -> None:
        """
        Clear all contents of the docs output directory.
        
        Args:
            docs_output_dir: Path to the docs directory to clear
        """
        if docs_output_dir.exists():
            logger.info(f"Clearing contents of {docs_output_dir}")
            # Remove all contents but keep the directory itself
            for item in docs_output_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            logger.info("Docs folder cleared successfully")
        else:
            logger.info(f"Docs directory {docs_output_dir} does not exist, creating it")
            docs_output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_yaml_from_interviews(self, business_id: UUID) -> str:
        """
        Generate YAML content from interview data for a business.
        
        Args:
            business_id: UUID of the business
            
        Returns:
            YAML string containing employee interview data
        """
        # Get all employees for the business
        employees = list(self.session.exec(
            select(Employee).where(Employee.business_id == business_id)
        ))

        if not employees:
            return ""

        # Build the data structure
        yaml_data = {"employees": []}

        for employee in employees:
            # Get all interviews for this employee
            interviews = list(self.session.exec(
                select(Interview).where(
                    Interview.employee_id == employee.id,
                    Interview.business_id == business_id
                )
            ))

            if not interviews:
                continue

            # Collect all Q&A for this employee across all interviews
            qa_pairs = []
            
            for interview in interviews:
                # Get all responses for this interview
                responses = list(self.session.exec(
                    select(QuestionResponse)
                    .where(QuestionResponse.interview_id == interview.id)
                    .join(Question, QuestionResponse.question_id == Question.id)
                    .order_by(Question.order_index)
                ))

                for response in responses:
                    # Get the question content
                    question = self.session.get(Question, response.question_id)
                    if question:
                        qa_pairs.append({
                            "question": question.content,
                            "answer": response.content
                        })

            if qa_pairs:
                employee_data = {
                    "name": employee.email.split("@")[0].replace(".", " ").title(),
                    "qa": qa_pairs
                }
                    
                yaml_data["employees"].append(employee_data)

        # Convert to YAML string
        return yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True)


def get_build_wiki_service(
    session: Session = Depends(get_session),
) -> BuildWikiService:
    """Get BuildWikiService with injected dependencies"""
    return BuildWikiService(session)
