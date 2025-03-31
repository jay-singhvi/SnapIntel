import os
import json
from typing import Dict, List, Any
from datetime import datetime


class URLStorage:
    """Manages storage and updates of company-related URLs."""

    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def _get_storage_path(self, company_name: str) -> str:
        """Get the file path for a company's URL data."""
        # Normalize company name for file naming
        normalized_name = company_name.lower().replace(" ", "_").replace(".", "_")
        return os.path.join(self.storage_dir, f"{normalized_name}_urls.json")

    def get_stored_urls(self, company_name: str) -> List[Dict[str, str]]:
        """Get the stored URLs for a company."""
        file_path = self._get_storage_path(company_name)

        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If the file is corrupted, return an empty list
            return []

    def update_urls(
        self, company_name: str, new_urls: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Update the stored URLs for a company without overwriting existing ones."""
        existing_urls = self.get_stored_urls(company_name)

        # Create a set of existing URLs to check for duplicates
        existing_url_set = {entry["url"] for entry in existing_urls}

        # Add only new URLs that don't exist already
        for url_entry in new_urls:
            if url_entry["url"] not in existing_url_set:
                existing_urls.append(url_entry)
                existing_url_set.add(url_entry["url"])

        # Save the updated list
        file_path = self._get_storage_path(company_name)
        with open(file_path, "w") as f:
            json.dump(existing_urls, f, indent=2)

        return existing_urls
