"""
Improved test script with better error handling and debugging capabilities.
"""

from dotenv import load_dotenv
import os
import json
import logging
import time
import sys

# Add import paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import directly from the fixed modules if testing independently
# Otherwise import from the regular package structure
try:
    # Try importing from fixed modules (if running independently)
    from fixed_perplexity_client import PerplexityClient
    from fixed_url_extractor import URLExtractor
    from company_url_collector.src.url_storage import URLStorage
except ImportError:
    # Fall back to regular imports (if running as part of the package)
    from company_url_collector.src.perplexity_client import PerplexityClient
    from company_url_collector.src.url_extractor import URLExtractor
    from company_url_collector.src.url_storage import URLStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("url_collector_test.log"), logging.StreamHandler()],
)
logger = logging.getLogger("TestScript")


def test_url_collection(
    api_key, company_name, company_url, duration, save_raw_response=True
):
    """
    Test the URL collection functionality with detailed error reporting.

    Args:
        api_key: Perplexity API key
        company_name: Name of the company to search for
        company_url: URL of the company's website
        duration: Time range for the search
        save_raw_response: Whether to save the raw API response to a file

    Returns:
        None
    """
    logger.info(f"Starting URL collection test for {company_name}")
    start_time = time.time()

    try:
        # Initialize components
        perplexity_client = PerplexityClient(api_key)
        url_extractor = URLExtractor()
        url_storage = URLStorage("data")

        # Step 1: Make API request
        logger.info("Step 1: Querying Perplexity API...")
        perplexity_response = perplexity_client.search_company_urls(
            company_name, company_url, duration
        )

        # Save raw response for debugging if enabled
        if save_raw_response:
            with open(f"{company_name}_raw_response.json", "w") as f:
                json.dump(perplexity_response, f, indent=2)
            logger.info(f"Saved raw API response to {company_name}_raw_response.json")

        # Step 2: Extract URLs from response
        logger.info("Step 2: Extracting URLs from response...")
        try:
            raw_urls = url_extractor.extract_urls_from_response(perplexity_response)
            logger.info(f"Extracted {len(raw_urls)} URLs from response")
        except Exception as e:
            logger.error(f"Error extracting URLs: {str(e)}", exc_info=True)
            # Try to extract useful information even if there was an error
            logger.info("Attempting to save partial response data for analysis...")
            with open(f"{company_name}_extraction_error.json", "w") as f:
                json.dump(
                    {
                        "error": str(e),
                        "response_keys": (
                            list(perplexity_response.keys())
                            if isinstance(perplexity_response, dict)
                            else "Not a dict"
                        ),
                        "response_preview": (
                            str(perplexity_response)[:1000] + "..."
                            if len(str(perplexity_response)) > 1000
                            else str(perplexity_response)
                        ),
                    },
                    f,
                    indent=2,
                )
            raise

        # Step 3: Validate URLs
        logger.info("Step 3: Validating URLs...")
        validated_urls = url_extractor.validate_urls(raw_urls, company_url)
        logger.info(f"Validated {len(validated_urls)} URLs")

        # Step 4: Update URL storage
        logger.info("Step 4: Updating URL storage...")
        all_urls = url_storage.update_urls(company_name, validated_urls)
        logger.info(f"Total URLs in storage: {len(all_urls)}")

        # Calculate statistics
        first_party_count = sum(
            1 for url in validated_urls if url.get("is_first_party", False)
        )
        third_party_count = len(validated_urls) - first_party_count
        relevant_count = sum(
            1 for url in validated_urls if url.get("is_relevant", True)
        )
        irrelevant_count = len(validated_urls) - relevant_count

        # Print report
        logger.info(f"\nResults Summary:")
        logger.info(f"- Total new URLs found: {len(validated_urls)}")
        logger.info(
            f"- First-party URLs: {first_party_count} ({int(first_party_count/len(validated_urls)*100 if validated_urls else 0)}%)"
        )
        logger.info(
            f"- Third-party URLs: {third_party_count} ({int(third_party_count/len(validated_urls)*100 if validated_urls else 0)}%)"
        )
        logger.info(
            f"- Relevant URLs: {relevant_count} ({int(relevant_count/len(validated_urls)*100 if validated_urls else 0)}%)"
        )
        logger.info(
            f"- Irrelevant URLs: {irrelevant_count} ({int(irrelevant_count/len(validated_urls)*100 if validated_urls else 0)}%)"
        )
        logger.info(f"- Total URLs stored: {len(all_urls)}")

        # Print first 5 URLs for inspection
        logger.info(f"\nDetailed URL Information (first 5):")
        for i, url_entry in enumerate(validated_urls[:5]):
            logger.info(f"\nURL {i+1}: {url_entry['url']}")
            logger.info(f"Title: {url_entry['title']}")
            logger.info(
                f"First Party: {'Yes' if url_entry.get('is_first_party', False) else 'No'}"
            )
            logger.info(
                f"Relevant: {'Yes' if url_entry.get('is_relevant', True) else 'No'}"
            )
            logger.info(f"Description: {url_entry['description']}")

        # Save results to file
        output_file = f"{company_name}_results.json"
        with open(output_file, "w") as f:
            json.dump(
                {
                    "company": company_name,
                    "company_url": company_url,
                    "duration": duration,
                    "new_urls_found": len(validated_urls),
                    "total_urls_stored": len(all_urls),
                    "first_party_urls_found": first_party_count,
                    "third_party_urls_found": third_party_count,
                    "relevant_urls_found": relevant_count,
                    "irrelevant_urls_found": irrelevant_count,
                    "new_urls": validated_urls,
                    "all_urls": all_urls,
                },
                f,
                indent=2,
            )
        logger.info(f"Full results saved to {output_file}")

        elapsed_time = time.time() - start_time
        logger.info(f"Test completed successfully in {elapsed_time:.2f} seconds")

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        elapsed_time = time.time() - start_time
        logger.info(f"Test failed after {elapsed_time:.2f} seconds")
        raise


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    api_key = os.environ.get("PERPLEXITY_API_KEY")

    if not api_key:
        logger.error("PERPLEXITY_API_KEY environment variable not set")
        sys.exit(1)

    # Test parameters
    company_name = "granica.ai"
    company_url = "https://granica.ai/"
    duration = "1 Month"

    # Run test
    try:
        test_url_collection(api_key, company_name, company_url, duration)
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        sys.exit(1)
