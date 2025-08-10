from __future__ import annotations

import logging
from pathlib import Path

import langchain
from app.agents.prompts.deep_system import DEEP_SYSTEM_PROMPT
from app.services.mkdocs_service import create_mkdocs_nav_service
from deepagents import create_deep_agent
from langchain_core.tools import tool

langchain.debug = True

logger = logging.getLogger(__name__)


async def run_deep_wiki_agent(yaml_text: str, output_dir: Path, model: str, docs_root_dir: Path | None = None) -> list[Path]:
    """
    Runs the deep agent to generate a multi-page wiki.

    Args:
        yaml_text: The employee Q&A data.
        output_dir: The directory to write the markdown files to.
        model: The LLM model to use.
        docs_root_dir: The root docs directory containing mkdocs.yml (optional).

    Returns:
        A list of paths to the generated files.
    """
    logger.info("Starting deep wiki agent", extra={"model": model})

    output_files: list[Path] = []
    
    # Initialize mkdocs service if docs_root_dir is provided
    mkdocs_service = None
    if docs_root_dir:
        try:
            mkdocs_path = docs_root_dir / "mkdocs.yml"
            logger.info("Looking for mkdocs.yml at: %s", mkdocs_path)
            logger.info("docs_root_dir exists: %s", docs_root_dir.exists())
            logger.info("mkdocs.yml exists: %s", mkdocs_path.exists())
            
            mkdocs_service = create_mkdocs_nav_service(docs_root_dir)
            logger.info("Initialized mkdocs navigation service for %s", docs_root_dir)
        except Exception as e:
            logger.error("Failed to initialize mkdocs service: %s", e)
            logger.error("docs_root_dir: %s", docs_root_dir)
            if docs_root_dir:
                logger.error("docs_root_dir contents: %s", list(docs_root_dir.iterdir()) if docs_root_dir.exists() else "directory does not exist")

    # @tool
    # def write_file(filename: str, content: str) -> str:
    #     """
    #     Writes a file to the output directory.

    #     Args:
    #         filename: The name of the file to write (e.g., 'dunder_mifflin.md').
    #         content: The content to write to the file.

    #     Returns:
    #         A confirmation message.
    #     """
    #     # Prevent creation of mkdocs.yml files - use navigation tools instead
    #     if filename.lower() in ["mkdocs.yml", "mkdocs.yml"]:
    #         return "Error: Cannot create mkdocs.yml files. Use update_navigation or add_navigation_entry tools instead."
        
    #     file_path = output_dir / filename
    #     file_path.parent.mkdir(parents=True, exist_ok=True)
    #     file_path.write_text(content, encoding="utf-8")
    #     output_files.append(file_path)
    #     logger.info("Wrote wiki file: %s", file_path)
    #     return f"Successfully wrote file to {file_path}"

    @tool
    def update_navigation(nav_entries: list[dict[str, str]]) -> str:
        """
        Updates the mkdocs.yml navigation section with new entries.
        
        Args:
            nav_entries: List of navigation entries, each as {"Title": "filename.md"}
            
        Returns:
            A confirmation message.
        """
        if not mkdocs_service:
            return f"MkDocs service not available. Checked for mkdocs.yml at: {docs_root_dir / 'mkdocs.yml' if docs_root_dir else 'No docs_root_dir provided'}"
        
        try:
            mkdocs_service.update_nav(nav_entries)
            return f"Successfully updated navigation with {len(nav_entries)} entries"
        except Exception as e:
            logger.error("Failed to update navigation: %s", e)
            return f"Failed to update navigation: {e}"

    @tool  
    def add_navigation_entry(title: str, filename: str) -> str:
        """
        Adds a single entry to the mkdocs.yml navigation.
        
        Args:
            title: Display title for the nav entry
            filename: Markdown filename (e.g., "company_snapshot.md")
            
        Returns:
            A confirmation message.
        """
        if not mkdocs_service:
            return f"MkDocs service not available. Checked for mkdocs.yml at: {docs_root_dir / 'mkdocs.yml' if docs_root_dir else 'No docs_root_dir provided'}"
        
        try:
            mkdocs_service.add_nav_entry(title, filename)
            return f"Successfully added navigation entry: {title} -> {filename}"
        except Exception as e:
            logger.error("Failed to add navigation entry: %s", e)
            return f"Failed to add navigation entry: {e}"

    # Prepare tools list based on availability of mkdocs service
    tools = [] #[write_file]
    if mkdocs_service:
        tools.extend([update_navigation, add_navigation_entry])
    else:
        logger.warning("No mkdocs service available - agent will only be able to analyze YAML data, not update navigation")

    agent = create_deep_agent(
        tools=tools,
        instructions=DEEP_SYSTEM_PROMPT,
        model=model,
    )

    config = {
        "recursion_limit": 100  # Increase the limit as needed
    }

    initial_state = {
        "messages": [
            {
                "role": "user",
                "content": f"Analyze the following YAML data and create a navigation plan for a company wiki. Update the mkdocs.yml navigation structure accordingly.\n\n```yaml\n{yaml_text}\n```",
            }
        ]
    }

    await agent.ainvoke(initial_state, config=config)

    return output_files
