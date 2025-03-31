from dotenv import load_dotenv

load_dotenv()  # Load API key from .env file

from company_url_collector.src.company_url_collector import CompanyURLCollector
import os

# Get API key from environment
api_key = os.environ.get("PERPLEXITY_API_KEY")

# Initialize the collector
collector = CompanyURLCollector(api_key)

# Collect URLs
result = collector.collect_urls(
    company_name="granica.ai", company_url="https://granica.ai/", duration="1 Month"
)

# Print the results
print(f"Found {result['new_urls_found']} new URLs")
print(f"Total URLs stored: {result['total_urls_stored']}")
