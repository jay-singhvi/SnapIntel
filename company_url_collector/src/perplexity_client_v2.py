import requests
from typing import Dict, List, Any


class PerplexityClient:
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
        recency_mapping = {
            "24 hrs": "day",
            "7 days": "week",
            "1 Month": "month",
            "3 Months": "month",
            "6 Months": "month",
            "1 year": "year",
            "All time": None,
        }

        system_prompt = (
            "You are a URL focused data collection assistant that provides comprehensive lists of URLs related to company, its products and services"
            "You always try to find details on the company, its products and services and then try to find different types of content on internet like blogs, articles, news and press releases about the company, its products and services."
            "Focus on finding both company-owned sites and third-party mentions that are relevant to the company's products, services, blogs, articles, news, or industry presence."
        )

        user_prompt = (
            f"Find URLs related to the company '{company_name}' (their website is {company_url}). "
            f"Include both official company pages and third-party sites that mention the company. "
            f"Focus on recent information from the past {duration}. "
            f"For each URL, provide a title and brief description that explains how it relates to the company."
        )

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 8000,
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

        if recency_mapping.get(duration):
            payload["search_recency_filter"] = recency_mapping.get(duration)

        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error querying Perplexity API: {str(e)}")
