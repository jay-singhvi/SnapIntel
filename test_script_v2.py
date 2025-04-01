from dotenv import load_dotenv
import os
import json
from company_url_collector.src.company_url_collector import CompanyURLCollector

# Load environment variables
load_dotenv()
api_key = os.environ.get("PERPLEXITY_API_KEY")

# Initialize the collector
collector = CompanyURLCollector(api_key)

# Collect URLs for a company
company_name = "granica.ai"
company_url = "https://granica.ai/"
duration = "1 year"

print(f"Collecting URLs for {company_name} from the past {duration}...")
result = collector.collect_urls(
    company_name=company_name, company_url=company_url, duration=duration
)

# Output the results
print(f"\nResults Summary:")
print(f"- Total new URLs found: {result['new_urls_found']}")
print(
    f"- First-party URLs: {result['first_party_urls_found']} ({round(result['first_party_urls_found']/result['new_urls_found']*100 if result['new_urls_found'] > 0 else 0)}%)"
)
print(
    f"- Third-party URLs: {result['third_party_urls_found']} ({round(result['third_party_urls_found']/result['new_urls_found']*100 if result['new_urls_found'] > 0 else 0)}%)"
)
print(
    f"- Relevant URLs: {result['relevant_urls_found']} ({round(result['relevant_urls_found']/result['new_urls_found']*100 if result['new_urls_found'] > 0 else 0)}%)"
)
print(
    f"- Irrelevant URLs: {result['irrelevant_urls_found']} ({round(result['irrelevant_urls_found']/result['new_urls_found']*100 if result['new_urls_found'] > 0 else 0)}%)"
)
print(f"- Total URLs stored: {result['total_urls_stored']}")

# Print detailed information for the first 5 URLs
print(f"\nDetailed URL Information (first 5):")
for i, url_entry in enumerate(result["new_urls"][:5]):
    print(f"\nURL {i+1}: {url_entry['url']}")
    print(f"Title: {url_entry['title']}")
    print(f"First Party: {'Yes' if url_entry.get('is_first_party', False) else 'No'}")
    print(f"Relevant: {'Yes' if url_entry.get('is_relevant', True) else 'No'}")
    print(f"Description: {url_entry['description']}")

# Save the full results to a JSON file
output_file = f"{company_name}_results.json"
with open(output_file, "w") as f:
    json.dump(result, f, indent=2)
print(f"\nFull results saved to {output_file}")
