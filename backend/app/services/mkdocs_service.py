from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class MkDocsNavService:
    """
    Service for safely updating the navigation section of mkdocs.yml files.

    This service preserves all existing configuration while only allowing
    updates to the nav section.
    """

    def __init__(self, mkdocs_path: Path):
        """
        Initialize the service with the path to mkdocs.yml.

        Args:
            mkdocs_path: Path to the mkdocs.yml file
        """
        self.mkdocs_path = mkdocs_path
        self._config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load the current mkdocs.yml configuration."""
        logger.info("Attempting to load mkdocs config from: %s", self.mkdocs_path)
        logger.info("mkdocs_path absolute: %s", self.mkdocs_path.absolute())
        logger.info("mkdocs_path exists: %s", self.mkdocs_path.exists())

        if not self.mkdocs_path.exists():
            raise FileNotFoundError(
                f"mkdocs.yml not found at {self.mkdocs_path} (absolute: {self.mkdocs_path.absolute()})"
            )

        with open(self.mkdocs_path, "r", encoding="utf-8") as f:
            try:
                # Try unsafe_load first for full mkdocs compatibility
                self._config = yaml.unsafe_load(f)
            except Exception as e:
                logger.warning(
                    "Failed to load with unsafe_load, trying safe_load: %s", e
                )
                # Fall back to safe_load if unsafe_load fails (e.g., missing dependencies)
                f.seek(0)  # Reset file pointer
                self._config = yaml.safe_load(f)

        logger.debug("Loaded mkdocs config from %s", self.mkdocs_path)

    def _save_config(self) -> None:
        """Save the configuration back to mkdocs.yml."""
        with open(self.mkdocs_path, "w", encoding="utf-8") as f:
            yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)

        logger.info("Updated mkdocs config at %s", self.mkdocs_path)

    def get_current_nav(self) -> list[dict[str, str]]:
        """
        Get the current navigation structure.

        Returns:
            List of navigation entries as dicts with title->filename mapping
        """
        return self._config.get("nav", [])

    def update_nav(self, nav_entries: list[dict[str, Any]]) -> None:
        """
        Update the navigation section with new entries.

        Args:
            nav_entries: List of navigation entries, supports nested structure
        """
        if not isinstance(nav_entries, list):
            raise ValueError("nav_entries must be a list")

        self._config["nav"] = nav_entries
        self._save_config()

        logger.info("Updated navigation with %d entries", len(nav_entries))

    def add_nav_entry(self, title: str, filename: str) -> None:
        """
        Add a single navigation entry.

        Args:
            title: Display title for the nav entry
            filename: Markdown filename (e.g., "company_snapshot.md")
        """
        current_nav = self.get_current_nav()
        new_entry = {title: filename}

        # Check if entry already exists (by filename)
        for entry in current_nav:
            if filename in entry.values():
                logger.debug("Nav entry for %s already exists, skipping", filename)
                return

        current_nav.append(new_entry)
        self.update_nav(current_nav)

        logger.info("Added nav entry: %s -> %s", title, filename)

    def remove_nav_entry(self, filename: str) -> bool:
        """
        Remove a navigation entry by filename.

        Args:
            filename: Markdown filename to remove

        Returns:
            True if entry was found and removed, False otherwise
        """
        current_nav = self.get_current_nav()
        original_length = len(current_nav)

        # Filter out entries that contain the filename
        updated_nav = [entry for entry in current_nav if filename not in entry.values()]

        if len(updated_nav) < original_length:
            self.update_nav(updated_nav)
            logger.info("Removed nav entry for %s", filename)
            return True

        logger.debug("Nav entry for %s not found", filename)
        return False

    def clear_nav(self) -> None:
        """Clear all navigation entries."""
        self.update_nav([])
        logger.info("Cleared all navigation entries")

    def update_site_name(self, site_name: str) -> None:
        """
        Update the site_name in the mkdocs configuration.

        Args:
            site_name: The name to set as the site title
        """
        self._config["site_name"] = site_name
        self._save_config()
        logger.info("Updated site_name to: %s", site_name)

    def update_nav_from_json(
        self, sections_json: dict[str, Any], site_name: str = None
    ) -> None:
        """
        Update navigation from JSON structure returned by LLM.

        Expected JSON format:
        {
            "sections": [
                {
                    "section_name": "Section Name",
                    "docs": [
                        {
                            "title": "Document Title",
                            "doc_filepath": "section_folder/document_name.md"
                        }
                    ]
                }
            ]
        }

        Args:
            sections_json: JSON structure with sections and docs
            site_name: Optional site name to update in the configuration
        """
        # Update site name if provided
        if site_name:
            self.update_site_name(site_name)
        if not isinstance(sections_json, dict) or "sections" not in sections_json:
            raise ValueError("JSON must contain 'sections' key")

        sections = sections_json["sections"]
        if not isinstance(sections, list):
            raise ValueError("'sections' must be a list")

        nav_entries = []

        for section in sections:
            if not isinstance(section, dict):
                continue

            section_name = section.get("section_name")
            docs = section.get("docs", [])

            if not section_name or not docs:
                logger.warning(
                    "Skipping section with missing name or docs: %s", section
                )
                continue

            if len(docs) == 1:
                # Single document - add as direct nav entry
                doc = docs[0]
                nav_entries.append({section_name: doc.get("doc_filepath", "")})
            else:
                # Multiple documents - create nested structure
                section_dict = {}
                section_docs = {}

                for doc in docs:
                    if not isinstance(doc, dict):
                        continue

                    title = doc.get("title")
                    filepath = doc.get("doc_filepath")

                    if title and filepath:
                        section_docs[title] = filepath

                if section_docs:
                    section_dict[section_name] = section_docs
                    nav_entries.append(section_dict)

        self.update_nav(nav_entries)
        logger.info("nav_entries: %s", nav_entries)
        logger.info("Updated navigation from JSON with %d sections", len(sections))


def create_mkdocs_nav_service(docs_dir: Path) -> MkDocsNavService:
    """
    Create a MkDocsNavService for the given docs directory.

    Args:
        docs_dir: Path to the docs directory containing mkdocs.yml

    Returns:
        Configured MkDocsNavService instance
    """
    mkdocs_path = docs_dir / "mkdocs.yml"
    return MkDocsNavService(mkdocs_path)
