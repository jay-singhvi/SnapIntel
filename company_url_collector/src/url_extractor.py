"""
Updated URL extractor with better error handling and compatibility with Perplexity API responses.
"""

from datetime import datetime
from typing import Dict, List, Any
import json
import re
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("URLExtractor")


class URLExtractor:
    @staticmethod
    def extract_urls_from_response(
        perplexity_response: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """
        Extract URL data from the Perplexity API response.

        Args:
            perplexity_response: The raw response from the Perplexity API

        Returns:
            A list of dictionaries containing URL data
        """
        try:
            logger.info("Extracting URLs from Perplexity response")

            # Log response keys for debugging
            logger.debug(f"Response keys: {perplexity_response.keys()}")

            if (
                "choices" not in perplexity_response
                or not perplexity_response["choices"]
            ):
                logger.error("No choices found in response")
                logger.debug(
                    f"Response content: {json.dumps(perplexity_response, indent=2)}"
                )
                return []

            # Get the content from the first choice
            choice = perplexity_response["choices"][0]
            logger.debug(f"Choice keys: {choice.keys()}")

            if "message" not in choice:
                logger.error("No message in choice")
                return []

            message = choice["message"]
            logger.debug(f"Message keys: {message.keys()}")

            if "content" not in message:
                logger.error("No content in message")
                return []

            content = message["content"]
            logger.debug(f"Content type: {type(content)}")

            # Handle different content types
            url_data = []

            if isinstance(content, str):
                # If content is a string, try to parse it as JSON
                try:
                    logger.debug(f"Content preview: {content[:200]}...")
                    url_data = json.loads(content)
                    logger.info(
                        f"Successfully parsed JSON string. Found {len(url_data)} URLs"
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing content as JSON: {str(e)}")
                    logger.debug(f"Content: {content}")
                    return []
            elif isinstance(content, list):
                # If content is already a list, use it directly
                url_data = content
                logger.info(f"Content is already a list. Found {len(url_data)} URLs")
            else:
                logger.error(f"Unexpected content type: {type(content)}")
                return []

            # Add timestamp to each entry
            timestamp = datetime.now().isoformat()
            for entry in url_data:
                entry["timestamp"] = timestamp

            # Log summary of extracted data
            logger.info(f"Extracted {len(url_data)} URLs from response")
            if url_data and len(url_data) > 0:
                logger.debug(f"First URL: {url_data[0].get('url', 'N/A')}")

            return url_data

        except Exception as e:
            logger.error(
                f"Error extracting URLs from Perplexity response: {str(e)}",
                exc_info=True,
            )
            raise Exception(f"Error extracting URLs from Perplexity response: {str(e)}")

    @staticmethod
    def validate_urls(
        url_data: List[Dict[str, str]], company_url: str = None
    ) -> List[Dict[str, str]]:
        """
        Validate and classify URLs from the extracted data.

        Args:
            url_data: List of URL data dictionaries
            company_url: The company's website URL for classification

        Returns:
            List of validated and classified URL dictionaries
        """
        validated_data = []
        company_domain = (
            URLExtractor._extract_domain(company_url) if company_url else None
        )

        logger.info(
            f"Validating {len(url_data)} URLs against company domain: {company_domain}"
        )

        for entry in url_data:
            url = entry.get("url", "")

            # Basic URL validation
            if not url or not (url.startswith("http://") or url.startswith("https://")):
                logger.debug(f"Skipping invalid URL: {url}")
                continue

            # Classify URL
            is_company_url = URLExtractor._is_company_url(url, company_domain)
            entry["is_first_party"] = is_company_url

            # Assess relevance
            entry["is_relevant"] = URLExtractor._assess_relevance(
                url,
                entry.get("title", ""),
                entry.get("description", ""),
                company_domain,
            )

            validated_data.append(entry)

        logger.info(f"Validated {len(validated_data)} URLs")
        first_party_count = sum(
            1 for url in validated_data if url.get("is_first_party", False)
        )
        logger.info(
            f"First-party URLs: {first_party_count}, Third-party URLs: {len(validated_data) - first_party_count}"
        )

        return validated_data

    @staticmethod
    def _extract_domain(url: str) -> str:
        """
        Extract the domain from a URL.

        Args:
            url: The URL to extract domain from

        Returns:
            The extracted domain
        """
        if not url:
            return ""

        # Add scheme if missing
        if not url.startswith("http"):
            url = f"https://{url}"

        try:
            parsed_url = urlparse(url)
            domain_parts = parsed_url.netloc.split(".")

            # Handle special cases like .co.uk, .com.au, etc.
            if len(domain_parts) > 2 and domain_parts[-2] in [
                "co",
                "com",
                "org",
                "net",
                "gov",
                "edu",
            ]:
                return f"{domain_parts[-3]}.{domain_parts[-2]}.{domain_parts[-1]}"

            if len(domain_parts) > 1:
                return f"{domain_parts[-2]}.{domain_parts[-1]}"

            return parsed_url.netloc

            # return parsed_url

        except Exception as e:
            logger.error(f"Error extracting domain from {url}: {str(e)}")
            return ""

    @staticmethod
    def _is_company_url(url: str, company_domain: str) -> bool:
        """
        Check if a URL belongs to the company domain.

        Args:
            url: The URL to check
            company_domain: The company's domain

        Returns:
            True if the URL belongs to the company domain, False otherwise
        """
        if not url or not company_domain:
            return False

        try:
            url_domain = URLExtractor._extract_domain(url)
            # For more accurate matching, normalize domains
            url_domain = url_domain.lower()
            company_domain = company_domain.lower()

            # Check if URL domain matches or is a subdomain of company domain
            return url_domain == company_domain or url_domain.endswith(
                f".{company_domain}"
            )

        except Exception as e:
            logger.error(
                f"Error checking if URL {url} belongs to company domain {company_domain}: {str(e)}"
            )
            return False

    @staticmethod
    def _assess_relevance(
        url: str, title: str, description: str, company_domain: str
    ) -> bool:
        """
        Assess the relevance of a URL to the company.

        Args:
            url: The URL to assess
            title: The title of the URL
            description: The description of the URL
            company_domain: The company's domain

        Returns:
            True if the URL is relevant, False otherwise
        """
        # Company URLs are considered relevant by default
        if URLExtractor._is_company_url(url, company_domain):
            return True

        # Check for irrelevant patterns in URL
        irrelevant_patterns = [
            # r'\.gov\/',                    # Government sites may be less relevant
            # r'wikipedia\.org\/',           # Wikipedia can be too general
            # r'youtube\.com\/watch',        # Generic YouTube videos
            r"*login*",  # Login pages
            r"*jobs*",  # Generic job listings
            r"/terms-of-service",  # Terms pages
            r"/privacy-policy",  # Privacy policies
            r"/about-cookies",  # Cookie policies
            r"/sitemap\.xml",  # Site maps
            r"/robots\.txt",  # Robots files
        ]

        for pattern in irrelevant_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                logger.debug(f"URL {url} matches irrelevant pattern {pattern}")
                return False

        # Check for irrelevant terms in title or description
        irrelevant_terms = [
            # 'policy', 'terms', 'conditions', 'cookie', 'privacy',
            # 'login', 'sign in', 'register', 'account', 'copyright',
            "404",
            "not found",
            "error",
        ]

        combined_text = f"{title.lower()} {description.lower()}"
        for term in irrelevant_terms:
            if term in combined_text:
                logger.debug(
                    f"URL {url} contains irrelevant term '{term}' in title/description"
                )
                return False

        # Default to considering relevant
        return True
