from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path

from app.agents.prompts.plan_doc_sections import PLAN_DOC_SECTIONS_PROMPT
from app.agents.prompts.write_doc import (WRITE_DOC_PROMPT,
                                          WRITE_DOC_USER_PROMPT)
from app.services.mkdocs_service import create_mkdocs_nav_service
from litellm import acompletion

logger = logging.getLogger(__name__)


async def plan_documentation_sections(yaml_text: str, model: str = "openai/gpt-5-mini-2025-08-07") -> dict:
    """
    Plan documentation sections based on employee Q&A data.
    
    Args:
        yaml_text: The employee Q&A YAML data
        model: The LLM model to use
        
    Returns:
        Dictionary containing the structured navigation plan
    """
    logger.info("Planning documentation sections", extra={"model": model, "yaml_chars": len(yaml_text)})
    
    response = await acompletion(
        model=model,
        messages=[
            {"role": "system", "content": PLAN_DOC_SECTIONS_PROMPT},
            {
                "role": "user", 
                "content": f"Analyze this employee Q&A data and create a navigation structure:\n\n```yaml\n{yaml_text}\n```"
            },
        ],
    )
    
    logger.info("Response received")
    content = response["choices"][0]["message"]["content"]
    logger.debug("Response content length: %d chars", len(content))
    
    # Post-process to extract and parse JSON
    parsed_response = _extract_and_parse_json(content)
    logger.info("Successfully parsed JSON response", extra={"sections_count": len(parsed_response.get("sections", []))})
    
    return parsed_response


def _extract_and_parse_json(content: str) -> dict:
    """
    Extract and parse JSON from LLM response content.
    
    Args:
        content: Raw LLM response content
        
    Returns:
        Parsed JSON as dictionary
        
    Raises:
        ValueError: If JSON cannot be extracted or parsed
    """
    # Try to find JSON within code blocks first
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find JSON without code blocks
        json_match = re.search(r'(\{.*\})', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # If no JSON structure found, try parsing the entire content
            json_str = content.strip()
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON from response", extra={"content": content[:500], "error": str(e)})
        raise ValueError(f"Could not parse JSON from LLM response: {e}")


async def write_documentation_content(yaml_text: str, title: str, section_name: str, model: str = "openai/gpt-5-mini-2025-08-07", semaphore: asyncio.Semaphore = None) -> str:
    """
    Write documentation content for a specific document using LLM.
    
    Args:
        yaml_text: The employee Q&A YAML data
        title: The document title
        section_name: The section this document belongs to
        model: The LLM model to use
        semaphore: Semaphore to limit concurrent requests
        
    Returns:
        Generated markdown content for the document
    """
    async with semaphore if semaphore else asyncio.nullcontext():
        logger.info("Writing documentation content", extra={"title": title, "section": section_name, "model": model})
        
        user_prompt = WRITE_DOC_USER_PROMPT.format(
            title=title,
            section_name=section_name,
            yaml_text=yaml_text
        )
        
        response = await acompletion(
            model=model,
            messages=[
                {"role": "system", "content": WRITE_DOC_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        
        logger.info("Documentation content generated for: %s", title)
        content = response["choices"][0]["message"]["content"]
        logger.debug("Generated content length: %d chars", len(content))
        
        return content





def _collect_docs_to_create(sections: list, docs_output_dir: Path) -> list[dict]:
    """Collect all documents that need to be created from sections."""
    docs_to_create = []
    
    for section in sections:
        if not isinstance(section, dict):
            continue
            
        section_name = section.get("section_name")
        docs = section.get("docs", [])
        
        if not section_name or not docs:
            logger.warning("Skipping section with missing name or docs: %s", section)
            continue
        
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            
            title = doc.get("title")
            filepath = doc.get("doc_filepath")
            
            if not title or not filepath:
                logger.warning("Skipping doc with missing title or filepath: %s", doc)
                continue
            
            # Create the full path
            full_path = docs_output_dir / filepath
            
            # Only add to creation list if it doesn't exist
            if not full_path.exists():
                docs_to_create.append({
                    "title": title,
                    "filepath": filepath,
                    "full_path": full_path,
                    "section_name": section_name
                })
            else:
                logger.debug("File already exists, skipping: %s", filepath)
    
    return docs_to_create


async def _create_single_doc(doc_info: dict, yaml_text: str, model: str, semaphore: asyncio.Semaphore) -> Path:
    """Create a single documentation file with content generation."""
    title = doc_info["title"]
    filepath = doc_info["filepath"]
    full_path = doc_info["full_path"]
    section_name = doc_info["section_name"]
    
    # Create parent directories if needed
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate actual content using LLM with semaphore
    logger.info("Generating content for: %s", title)
    content = await write_documentation_content(yaml_text, title, section_name, model, semaphore)
    
    # Write to file
    full_path.write_text(content, encoding="utf-8")
    logger.info("Created file with generated content: %s", filepath)
    return full_path


async def create_documentation_files(sections_json: dict, docs_output_dir: Path, yaml_text: str, model: str = "openai/gpt-5-mini-2025-08-07") -> list[Path]:
    """
    Create markdown files for all documents in the navigation structure using async processing.
    
    Args:
        sections_json: JSON structure with sections and docs
        docs_output_dir: Directory where markdown files should be created
        yaml_text: The employee Q&A YAML data for content generation
        model: The LLM model to use for content generation
        
    Returns:
        List of created file paths
    """
    if not isinstance(sections_json, dict) or "sections" not in sections_json:
        raise ValueError("JSON must contain 'sections' key")
    
    sections = sections_json["sections"]
    if not isinstance(sections, list):
        raise ValueError("'sections' must be a list")
    
    # Ensure docs output directory exists
    docs_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize created files list - no hardcoded index.md anymore
    created_files = []
    
    # Collect all documents that need to be created
    docs_to_create = _collect_docs_to_create(sections, docs_output_dir)
    
    if not docs_to_create:
        logger.info("No new documentation files to create")
        return created_files
    
    # Create all documents concurrently with semaphore limiting
    logger.info("Creating %d documentation files concurrently (max 10 at a time)", len(docs_to_create))
    semaphore = asyncio.Semaphore(10)
    
    new_files = await asyncio.gather(*[
        _create_single_doc(doc, yaml_text, model, semaphore) 
        for doc in docs_to_create
    ])
    created_files.extend(new_files)
    
    logger.info("Created %d new documentation files", len(created_files))
    return created_files


def update_mkdocs_navigation(sections_json: dict, docs_root_dir: Path) -> None:
    """
    Update mkdocs.yml navigation from JSON structure.
    
    Args:
        sections_json: JSON structure with sections and docs
        docs_root_dir: Path to the docs directory containing mkdocs.yml
    """
    mkdocs_service = create_mkdocs_nav_service(docs_root_dir)
    mkdocs_service.update_nav_from_json(sections_json)
    logger.info("Updated mkdocs.yml navigation")


async def run_chain(yaml_text: str, docs_output_dir: Path, docs_root_dir: Path, model: str = "openai/gpt-5-mini-2025-08-07") -> tuple[dict, list[Path]]:
    """
    Run the complete documentation chain: plan sections, create files, and update navigation.
    
    Args:
        yaml_text: The employee Q&A YAML data
        docs_output_dir: Directory where markdown files should be created
        docs_root_dir: Path to the docs directory containing mkdocs.yml
        model: The LLM model to use
        
    Returns:
        Tuple of (sections_plan, created_files)
    """
    logger.info("Running documentation chain")
    
    # Step 1: Plan documentation sections
    sections_plan = await plan_documentation_sections(yaml_text, model=model)

    # Step 2: Update mkdocs.yml navigation
    update_mkdocs_navigation(sections_plan, docs_root_dir)
    
    # Step 3: Create documentation files with generated content (async with semaphore)
    created_files = await create_documentation_files(sections_plan, docs_output_dir, yaml_text, model)
    
    logger.info("Documentation chain completed", extra={
        "sections_count": len(sections_plan.get("sections", [])),
        "files_created": len(created_files)
    })
    
    return sections_plan, created_files

