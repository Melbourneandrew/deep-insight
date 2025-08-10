import asyncio
import logging
from pathlib import Path

from app.agents.chain import run_chain

logger = logging.getLogger(__name__)


async def build_wiki_from_yaml_text(
    yaml_text: str, docs_root_dir: Path, model: str = "openai/gpt-5-mini-2025-08-07"
) -> tuple[dict, list[Path]]:
    """
    Build complete wiki from YAML text: plan navigation, create files, and update mkdocs.yml.
    
    Args:
        yaml_text: The employee Q&A YAML data
        docs_root_dir: Path to the docs directory containing mkdocs.yml
        model: The LLM model to use
        
    Returns:
        Tuple of (sections_plan, created_files)
    """
    logger.info("Building wiki from YAML text")

    # Run the complete chain: plan sections, create files, and update navigation
    docs_output_dir = docs_root_dir / "docs"
    sections_plan, created_files = await run_chain(yaml_text, docs_output_dir, docs_root_dir, model=model)

    logger.info("Wiki build completed")
    return sections_plan, created_files


async def main() -> None:
    """Main function to test wiki building with mock data."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    backend_dir = Path(__file__).resolve().parents[2]
    mock_data_path = backend_dir / "tests" / "mock_data.yaml"
    repo_root = backend_dir.parent
    docs_root_dir = repo_root / "docs"

    logger.info("Starting wiki build", extra={"yaml": str(mock_data_path), "docs_root": str(docs_root_dir)})
    
    # Read YAML file and build wiki
    yaml_text = mock_data_path.read_text(encoding="utf-8")
    sections_plan, created_files = await build_wiki_from_yaml_text(yaml_text, docs_root_dir=docs_root_dir)
    
    logger.info("Wiki build completed", extra={
        "sections_count": len(sections_plan.get("sections", [])),
        "files_created": len(created_files)
    })


if __name__ == "__main__":
    asyncio.run(main())

