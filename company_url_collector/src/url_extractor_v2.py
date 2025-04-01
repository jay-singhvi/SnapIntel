from datetime import datetime
from typing import Dict, List, Any, Set
import json
import re
from urllib.parse import urlparse


class URLExtractor:
    @staticmethod
    def extract_urls_from_response(
        perplexity_response: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        try:
            content = (
                perplexity_response.get("choices", [])[0]
                .get("message", {})
                .get("content", "")
            )
            url_data = json.loads(content)
            timestamp = datetime.now().isoformat()
            for entry in url_data:
                entry["timestamp"] = timestamp
            return url_data
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            raise Exception(f"Error extracting URLs from Perplexity response: {str(e)}")

    @staticmethod
    def validate_urls(
        url_data: List[Dict[str, str]], company_url: str = None
    ) -> List[Dict[str, str]]:
        validated_data = []
        company_domain = (
            URLExtractor._extract_domain(company_url) if company_url else None
        )

        for entry in url_data:
            url = entry.get("url", "")

            # Basic URL validation
            if not url or not (url.startswith("http://") or url.startswith("https://")):
                continue

            # Classify URL as first-party or third-party
            is_company_url = URLExtractor._is_company_url(url, company_domain)
            entry["is_first_party"] = is_company_url

            # Assess relevance based on title, description, and URL
            entry["is_relevant"] = URLExtractor._assess_relevance(
                url,
                entry.get("title", ""),
                entry.get("description", ""),
                company_domain,
            )

            validated_data.append(entry)

        return validated_data

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract the base domain from a URL."""
        if not url:
            return ""

        # Ensure URL has scheme
        if not url.startswith("http"):
            url = f"https://{url}"

        try:
            parsed_url = urlparse(url)
            # Get domain without subdomains (e.g., extract 'example.com' from 'sub.example.com')
            domain_parts = parsed_url.netloc.split(".")

            # Handle special cases like co.uk
            if len(domain_parts) > 2 and domain_parts[-2] in [
                "co",
                "com",
                "org",
                "net",
                "gov",
                "edu",
            ]:
                return f"{domain_parts[-3]}.{domain_parts[-2]}.{domain_parts[-1]}"

            # Standard case
            if len(domain_parts) > 1:
                return f"{domain_parts[-2]}.{domain_parts[-1]}"

            return parsed_url.netloc
        except Exception:
            return ""

    @staticmethod
    def _is_company_url(url: str, company_domain: str) -> bool:
        """Determine if a URL belongs to the company's domain."""
        if not url or not company_domain:
            return False

        try:
            url_domain = URLExtractor._extract_domain(url)
            return url_domain == company_domain
        except Exception:
            return False

    @staticmethod
    def _assess_relevance(
        url: str, title: str, description: str, company_domain: str
    ) -> bool:
        """
        Assess if a URL is relevant to the company based on content analysis.

        This function uses heuristics to determine relevance:
        1. Company domain URLs are considered relevant by default
        2. Third-party URLs are analyzed for relevance indicators
        """
        # Company's own URLs are always considered relevant
        if URLExtractor._is_company_url(url, company_domain):
            return True

        # Common irrelevant patterns
        irrelevant_patterns = [
            # r'\.gov\/',                    # Government sites may be less relevant
            # r'wikipedia\.org\/',           # Wikipedia can be too general
            # r'youtube\.com\/watch',        # Generic YouTube videos
            r"facebook\.com\/login",  # Login pages
            r"linkedin\.com\/jobs",  # Generic job listings
            r"/terms-of-service",  # Terms pages
            r"/privacy-policy",  # Privacy policies
            r"/about-cookies",  # Cookie policies
            r"/sitemap\.xml",  # Site maps
            r"/robots\.txt",  # Robots files
        ]

        for pattern in irrelevant_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False

        # Check if the title or description contain common irrelevant terms
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
                return False

        # If we passed all the above checks, the URL is likely relevant
        return True
