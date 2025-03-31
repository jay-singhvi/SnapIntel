import requests
from typing import Dict, List, Any


class PerplexityClient:
    """Client for interacting with Perplexity API to gather company-related URLs."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def search_company_urls(
        self,
        company_name: str,
        company_url: str,
        duration: str,
        model: str = "sonar-pro",
    ) -> Dict[str, Any]:
        """Search for URLs related to a company using Perplexity."""

        # Map duration to appropriate search filter
        recency_mapping = {
            "24 hrs": "day",
            "7 days": "week",
            "1 Month": "month",
            "3 Months": "month",
            "6 Months": "month",
            "1 year": "year",
            "All time": None,
        }

        # Create system and user prompts
        system_prompt = "You are a data collection assistant that provides comprehensive lists of URLs related to companies."
        user_prompt = f"""Find the most relevant URLs about the company "{company_name}" (website: {company_url}) from the past {duration}.
        Include URLs about their products, services, news, press releases, and any significant mentions.
        Format your response as a JSON array of objects with 'url', 'title', and 'description' fields."""

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 2000,
            "web_search_options": {"search_context_size": "high"},
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "schema": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"},
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                            },
                            "required": ["url", "title", "description"],
                        },
                    }
                },
            },
        }

        # Add recency filter if applicable
        if recency_mapping.get(duration):
            payload["search_recency_filter"] = recency_mapping.get(duration)

        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error querying Perplexity API: {str(e)}")
