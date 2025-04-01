# Company URL Collector

A tool for collecting and managing URLs related to companies using the Perplexity API.

## Overview

This tool helps gather URLs related to specific companies, categorizing them as first-party (from the company's own domain) or third-party (mentions from other domains), and evaluating their relevance to the company's business.

## Features

- Collects company-related URLs using Perplexity's advanced search capabilities
- Classifies URLs as first-party or third-party
- Evaluates URL relevance based on content analysis
- Stores and manages collected URLs with duplication prevention
- REST API for integration with web applications
- Supports filtering by URL type and relevance

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/SnapIntel.git
   cd SnapIntel
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file with:
   ```
   PERPLEXITY_API_KEY=your_perplexity_api_key
   ```

## Usage

### Command Line Interface

```bash
python -m company_url_collector.src.main --company "Elastic" --url "https://elastic.co" --duration "1 Month" --output results.json
```

Parameters:
- `--company`: Company name to search for
- `--url`: Company's website URL (used for classification)
- `--duration`: Time range for search (options: "24 hrs", "7 days", "1 Month", "3 Months", "6 Months", "1 year", "All time")
- `--output`: Optional filename to save results
- `--api-key`: Optional Perplexity API key (can also be set via environment variable)

### Python API

```python
from company_url_collector.src.company_url_collector import CompanyURLCollector
import os

api_key = os.environ.get("PERPLEXITY_API_KEY")
collector = CompanyURLCollector(api_key)

result = collector.collect_urls(
    company_name="granica.ai", 
    company_url="https://granica.ai/", 
    duration="1 Month"
)

# Access URL classification information
for url_entry in result['new_urls']:
    print(f"URL: {url_entry['url']}")
    print(f"First Party: {url_entry['is_first_party']}")
    print(f"Relevant: {url_entry['is_relevant']}")
```

### REST API

Start the Flask server:

```bash
python flask_Backend.py
```

#### Endpoints:

1. Collect URLs:
   ```
   POST /api/collect-urls
   
   {
     "company_name": "Elastic",
     "company_url": "https://elastic.co",
     "duration": "1 Month"
   }
   ```

2. Get stored URLs:
   ```
   GET /api/get-urls/{company_name}
   ```

3. Filter URLs:
   ```
   GET /api/filter-urls/{company_name}?is_first_party=true&is_relevant=true
   ```

## URL Classification

The tool categorizes URLs in two ways:

### First-Party vs Third-Party

- **First-Party**: URLs from the company's own domain
- **Third-Party**: URLs from other domains that mention the company

### Relevance Assessment

URLs are evaluated for relevance to the company's business using heuristics:
- Company's own URLs are considered relevant by default
- Third-party URLs are analyzed for relevance indicators
- Common irrelevant patterns are filtered out (login pages, generic terms, etc.)

## Data Storage

URLs are stored in JSON files in the `data` directory, organized by company name. The storage system prevents duplication of URLs when performing repeated searches.

## License

[MIT License](LICENSE)