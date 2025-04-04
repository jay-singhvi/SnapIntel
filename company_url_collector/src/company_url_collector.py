from typing import Dict, List, Any
from datetime import datetime

class CompanyURLCollector:
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
        try:
            print(
                f"Searching for URLs related to {company_name} from the past {duration}..."
            )
            perplexity_response = self.perplexity_client.search_company_urls(
                company_name, company_url, duration
            )
            
            print("Extracting and validating URLs...")
            raw_urls = self.url_extractor.extract_urls_from_response(
                perplexity_response
            )
            validated_urls = self.url_extractor.validate_urls(raw_urls, company_url)
            
            print("Updating URL storage...")
            all_urls = self.url_storage.update_urls(company_name, validated_urls)
            
            # Count statistics for first-party and relevant URLs
            first_party_count = sum(1 for url in validated_urls if url.get("is_first_party", False))
            third_party_count = len(validated_urls) - first_party_count
            relevant_count = sum(1 for url in validated_urls if url.get("is_relevant", True))
            irrelevant_count = len(validated_urls) - relevant_count
            
            result = {
                "company": company_name,
                "company_url": company_url,
                "search_time": datetime.now().isoformat(),
                "duration": duration,
                "new_urls_found": len(validated_urls),
                "total_urls_stored": len(all_urls),
                "first_party_urls_found": first_party_count,
                "third_party_urls_found": third_party_count,
                "relevant_urls_found": relevant_count,
                "irrelevant_urls_found": irrelevant_count,
                "new_urls": validated_urls,
                "all_urls": all_urls,
            }
            
            print(
                f"Successfully collected URLs for {company_name}. Found {len(validated_urls)} new URLs "
                f"({first_party_count} from company site, {third_party_count} from third-party sites)."
            )
            
            return result
        except Exception as e:
            error_result = {
                "company": company_name,
                "company_url": company_url,
                "search_time": datetime.now().isoformat(),
                "duration": duration,
                "error": str(e),
                "success": False,
            }
            print(f"Error collecting URLs for {company_name}: {str(e)}")
            return error_result
