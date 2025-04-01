"""
Updated Perplexity client with improved error handling and compatibility with the API.
"""

import requests
import json
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("PerplexityClient")


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
        """
        Search for URLs related to a company using the Perplexity API.

        Args:
            company_name: Name of the company to search for
            company_url: URL of the company's website
            duration: Time range for the search
            model: Perplexity model to use

        Returns:
            Dict containing the API response
        """
        recency_mapping = {
            "24 hrs": "day",
            "7 days": "week",
            "1 Month": "month",
            "3 Months": "month",
            "6 Months": "month",
            "1 year": "year",
            "All time": None,
        }

        # Updated system prompt with better formatting
        system_prompt = (
            "You are a URL focused data collection assistant that provides comprehensive lists of URLs related to company, its products and services. You always try to find details on the company, its products and services and then try to find different types of content on internet like blogs, articles, news and press releases about the company, its products and services. Focus on finding both company-owned sites and third-party mentions that are relevant to the company's products, services, blogs, articles, news, or industry presence."
        )

        # User prompt with explicit JSON formatting instruction
        user_prompt = (
            f"Find URLs related to the company '{company_name}' (their website is {company_url}). Include both official company pages and third-party sites that mention the company. Focus on recent information from the past {duration}. For each URL, provide a title and brief description that explains how it relates to the company. Return only a valid JSON array where each item has the properties: url, title, and description."
        )

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 4000,  # Reduced from 8000 to ensure faster responses
            "web_search_options": {"search_context_size": "high"},
        }

        # Add structured output format
        payload["response_format"] = {
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
        }

        # Add recency filter if applicable
        if recency_mapping.get(duration):
            payload["search_recency_filter"] = recency_mapping.get(duration)

        logger.info(
            f"Searching for URLs related to {company_name} with duration {duration}"
        )
        logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")

        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()

            # Log response info for debugging
            api_response = response.json()
            logger.debug(f"API response keys: {api_response.keys()}")

            return api_response

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                try:
                    error_data = e.response.json()
                    logger.error(f"Error response: {json.dumps(error_data, indent=2)}")
                except:
                    logger.error(f"Raw error response: {e.response.text}")
            raise Exception(f"Error querying Perplexity API: {str(e)}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise Exception(f"Error querying Perplexity API: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise Exception(f"Unexpected error in Perplexity API request: {str(e)}")
