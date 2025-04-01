import argparse
import json
import os
import sys


def main():
    """Main entry point for the company URL collector application."""

    parser = argparse.ArgumentParser(
        description="Collect company-related URLs using Perplexity API"
    )
    parser.add_argument("--company", required=True, help="Name of the company")
    parser.add_argument("--url", required=True, help="URL of the company website")
    parser.add_argument(
        "--duration",
        required=True,
        choices=[
            "24 hrs",
            "7 days",
            "1 Month",
            "3 Months",
            "6 Months",
            "1 year",
            "All time",
        ],
        help="Time duration for the search",
    )
    parser.add_argument("--output", help="Output file to save results (optional)")
    parser.add_argument(
        "--api-key",
        help="Perplexity API key (alternatively set PERPLEXITY_API_KEY env variable)",
    )

    args = parser.parse_args()

    # Get API key from args or environment variable
    api_key = args.api_key or os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        print(
            "Error: Perplexity API key not provided. Use --api-key or set PERPLEXITY_API_KEY environment variable"
        )
        sys.exit(1)

    # Import here to avoid circular imports
    from .company_url_collector import CompanyURLCollector

    # Initialize the collector
    collector = CompanyURLCollector(api_key)

    # Collect URLs
    result = collector.collect_urls(args.company, args.url, args.duration)

    # Save or print the results
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
