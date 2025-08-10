from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from app.agents.wiki_agent import generate_business_wiki

logger = logging.getLogger(__name__)


def read_file_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    logger.debug("Read file: %s (%d chars)", str(path), len(text))
    return text


def write_text(path: Path, text: str) -> None:
    bytes_written = path.write_text(text, encoding="utf-8")
    logger.debug("Wrote file: %s (%d chars)", str(path), len(text))
    return bytes_written


def build_wiki_from_yaml_text(yaml_text: str, model: str | None = None) -> str:
    resolved_model = model or os.getenv("SONNET_MODEL", "groq/moonshotai/kimi-k2-instruct")
    logger.info("Building wiki from YAML text", extra={"model": resolved_model})
    start_time = time.perf_counter()
    markdown = generate_business_wiki(yaml_text=yaml_text, model=resolved_model)
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    logger.info("Wiki generated from text in %d ms", duration_ms)
    logger.debug("Markdown length: %d chars", len(markdown))
    return markdown


def build_wiki_from_yaml_file(yaml_path: Path, output_path: Path | None = None) -> Path:
    logger.info("Building wiki from file: %s", str(yaml_path))
    start_time = time.perf_counter()

    yaml_text = read_file_text(yaml_path)
    markdown = build_wiki_from_yaml_text(yaml_text)

    if output_path is None:
        stem = yaml_path.stem
        output_path = yaml_path.parent / f"{stem}_wiki.md"

    write_text(output_path, markdown)

    duration_ms = int((time.perf_counter() - start_time) * 1000)
    logger.info("Wiki written to %s in %d ms", str(output_path), duration_ms)
    logger.debug("Output markdown length: %d chars", len(markdown))
    return output_path


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    backend_dir = Path(__file__).resolve().parents[2]
    yaml_path = backend_dir / "tests" / "mock_data.yaml"
    repo_root = backend_dir.parent
    docs_output = repo_root / "docs" / "docs" / "dunder_mifflin.md"

    logger.info("Starting wiki build", extra={"yaml": str(yaml_path), "output": str(docs_output)})
    output_path = build_wiki_from_yaml_file(yaml_path, output_path=docs_output)
    logger.info("Saved wiki to: %s", str(output_path))


if __name__ == "__main__":
    main()

