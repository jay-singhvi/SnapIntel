from datetime import datetime
from typing import Dict, List, Any
import json


class URLExtractor:
    """Extracts and processes URLs from Perplexity API responses."""

    @staticmethod
    def extract_urls_from_response(
        perplexity_response: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """Extract URLs from a Perplexity API response."""
        try:
            # Extract content from the response
            content = (
                perplexity_response.get("choices", [])[0]
                .get("message", {})
                .get("content", "")
            )

            # Parse the JSON content
            url_data = json.loads(content)

            # Add timestamp to each URL entry
            timestamp = datetime.now().isoformat()
            for entry in url_data:
                entry["timestamp"] = timestamp

            return url_data
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            raise Exception(f"Error extracting URLs from Perplexity response: {str(e)}")

    @staticmethod
    def validate_urls(url_data: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Validate the extracted URLs."""
        validated_data = []

        for entry in url_data:
            # Basic validation - ensure URL starts with http or https
            url = entry.get("url", "")
            if url and (url.startswith("http://") or url.startswith("https://")):
                validated_data.append(entry)

        return validated_data
