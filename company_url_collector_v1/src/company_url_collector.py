from typing import Dict, List, Any
from datetime import datetime


class CompanyURLCollector:
    """Main application for collecting and managing company-related URLs."""

    def __init__(self, api_key: str, storage_dir: str = "data"):
        from .perplexity_client import PerplexityClient
        from .url_extractor import URLExtractor
        from .url_storage import URLStorage

        self.perplexity_client = PerplexityClient(api_key)
        self.url_extractor = URLExtractor()
        self.url_storage = URLStorage(storage_dir)

    def collect_urls(
        self, company_name: str, company_url: str, duration: str
    ) -> Dict[str, Any]:
        """Collect URLs for a company and update storage."""
        try:
            # Step 1: Search for URLs using Perplexity
            print(
                f"Searching for URLs related to {company_name} from the past {duration}..."
            )
            perplexity_response = self.perplexity_client.search_company_urls(
                company_name, company_url, duration
            )

            # Step 2: Extract and validate URLs from the response
            print("Extracting and validating URLs...")
            raw_urls = self.url_extractor.extract_urls_from_response(
                perplexity_response
            )
            validated_urls = self.url_extractor.validate_urls(raw_urls)

            # Step 3: Update the stored URLs
            print("Updating URL storage...")
            all_urls = self.url_storage.update_urls(company_name, validated_urls)

            # Step 4: Prepare and return the result
            result = {
                "company": company_name,
                "search_time": datetime.now().isoformat(),
                "duration": duration,
                "new_urls_found": len(validated_urls),
                "total_urls_stored": len(all_urls),
                "new_urls": validated_urls,
                "all_urls": all_urls,
            }

            print(
                f"Successfully collected URLs for {company_name}. Found {len(validated_urls)} new URLs."
            )
            return result

        except Exception as e:
            error_result = {
                "company": company_name,
                "search_time": datetime.now().isoformat(),
                "duration": duration,
                "error": str(e),
                "success": False,
            }
            print(f"Error collecting URLs for {company_name}: {str(e)}")
            return error_result
