import requests
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import urlparse, urljoin
import pandas as pd
from collections import deque
import spacy
import logging
import concurrent.futures
from tqdm import tqdm
import os


class EnhancedWebScraper:
    def __init__(
        self,
        max_depth=5,
        max_breadth=5,
        relevance_threshold=0.3,
        allowed_domains=None,
        concurrent_requests=5,
    ):
        self.max_depth = max_depth
        self.max_breadth = max_breadth
        self.relevance_threshold = relevance_threshold
        self.allowed_domains = allowed_domains  # List of allowed domains to crawl
        self.concurrent_requests = concurrent_requests

        self.visited_urls = set()
        self.discovery_sequence = []
        self.content_data = []

        # Set up headers rotation for avoiding detection
        self.headers_list = [
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
            },
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15"
            },
        ]

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            filename="web_scraper.log",
        )
        self.logger = logging.getLogger("WebScraper")

        # Load spaCy model for relevance filtering
        try:
            self.nlp = spacy.load("en_core_web_md")
            self.logger.info("Successfully loaded spaCy model")
        except OSError:
            self.logger.warning(
                "spaCy model not found. Install with: python -m spacy download en_core_web_md"
            )
            print(
                "spaCy model not found. Install with: python -m spacy download en_core_web_md"
            )
            self.nlp = None

    def is_valid_url(self, url):
        """Check if the URL is valid and within allowed domains if specified."""
        try:
            result = urlparse(url)
            is_valid = all([result.scheme, result.netloc]) and result.scheme in [
                "http",
                "https",
            ]

            # Check if the domain is allowed
            if is_valid and self.allowed_domains:
                domain = result.netloc
                return any(
                    domain.endswith(allowed_domain)
                    for allowed_domain in self.allowed_domains
                )

            return is_valid
        except ValueError:
            return False

    def normalize_url(self, url, base_url):
        """Normalize relative URLs to absolute URLs."""
        if not url:
            return None

        # Handle URLs that are already absolute
        if url.startswith(("http://", "https://")):
            normalized_url = url
        # Handle fragment URLs (anchors on the same page)
        elif url.startswith("#"):
            return None
        # Handle relative URLs
        else:
            normalized_url = urljoin(base_url, url)

        # Remove fragments from URLs to avoid duplicate content
        parsed = urlparse(normalized_url)
        return (
            parsed.scheme
            + "://"
            + parsed.netloc
            + parsed.path
            + (f"?{parsed.query}" if parsed.query else "")
        )

    def extract_text_content(self, soup):
        """Extract text content from the page, excluding scripts and styles."""
        # Remove script, style, and hidden elements
        for element in soup(["script", "style", "meta", "[document]", "head", "title"]):
            element.decompose()

        # Get text
        text = soup.get_text(separator=" ", strip=True)

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def is_content_relevant(self, content, topic):
        """Determine if the content is relevant to the search topic using spaCy."""
        if not self.nlp:
            return True  # If spaCy is not available, consider all content relevant

        if not content or len(content) < 100:
            return False  # Skip very short content

        # Process with spaCy - limit content length for efficiency
        doc_content = self.nlp(content[:5000])
        doc_topic = self.nlp(topic)

        # Calculate similarity
        similarity = doc_content.similarity(doc_topic)
        self.logger.debug(f"Content similarity: {similarity}")

        return similarity > self.relevance_threshold

    def fetch_url(self, url_data):
        """Fetch a URL and extract links and content."""
        url, depth = url_data

        try:
            # Random headers to avoid detection
            headers = random.choice(self.headers_list)
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Check if the content is HTML
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type:
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract content
            content = self.extract_text_content(soup)
            title = soup.title.text.strip() if soup.title else "No Title"

            # Extract links
            links = []
            for link in soup.find_all("a", href=True):
                href = link.get("href")
                full_url = self.normalize_url(href, url)

                if (
                    full_url
                    and self.is_valid_url(full_url)
                    and full_url not in self.visited_urls
                ):
                    links.append(full_url)

            return {
                "url": url,
                "depth": depth,
                "title": title,
                "content": content,
                "links": links[: self.max_breadth],  # Respect max breadth
            }

        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def crawl(self, start_url, search_topic):
        """Crawl the web starting from the given URL with BFS approach and concurrent requests."""
        # Reset tracking variables
        self.visited_urls = set()
        self.discovery_sequence = []
        self.content_data = []

        # Initialize queue with the start URL and depth 0
        queue = deque([(start_url, 0)])
        self.visited_urls.add(start_url)

        with tqdm(desc="Crawling", unit="pages") as pbar:
            while queue:
                # Get batch of URLs to process concurrently
                batch = []
                for _ in range(min(self.concurrent_requests, len(queue))):
                    if queue:
                        batch.append(queue.popleft())

                # Process batch with concurrent requests
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=self.concurrent_requests
                ) as executor:
                    future_to_url = {
                        executor.submit(self.fetch_url, url_data): url_data
                        for url_data in batch
                    }

                    for future in concurrent.futures.as_completed(future_to_url):
                        url_data = future_to_url[future]
                        current_url, depth = url_data

                        try:
                            result = future.result()
                            if not result:
                                continue

                            # Add to discovery sequence
                            self.discovery_sequence.append(current_url)

                            # Check if content is relevant to the search topic
                            if self.is_content_relevant(
                                result["content"], search_topic
                            ):
                                # Add to content data
                                self.content_data.append(
                                    {
                                        "url": result["url"],
                                        "depth": result["depth"],
                                        "discovery_index": len(self.discovery_sequence)
                                        - 1,
                                        "title": result["title"],
                                        "content": result["content"][
                                            :1000
                                        ],  # Limit content length for storage
                                        "relevance_score": (
                                            self.nlp(
                                                result["content"][:5000]
                                            ).similarity(self.nlp(search_topic))
                                            if self.nlp
                                            else 1.0
                                        ),
                                    }
                                )

                                self.logger.info(
                                    f"Found relevant content at {result['url']}"
                                )

                            # Add new links to the queue if not at max depth
                            if depth < self.max_depth:
                                for link in result["links"]:
                                    if link not in self.visited_urls:
                                        queue.append((link, depth + 1))
                                        self.visited_urls.add(link)

                        except Exception as e:
                            self.logger.error(
                                f"Error processing {current_url}: {str(e)}"
                            )

                # Update progress bar
                pbar.update(len(batch))

                # Polite scraping with a short delay between batches
                time.sleep(random.uniform(0.5, 1.5))

    def save_results(self, filename="scraping_results.csv"):
        """Save the scraped data to a CSV file."""
        if not self.content_data:
            print("No data to save.")
            return

        df = pd.DataFrame(self.content_data)

        # Sort by relevance score if available
        if self.nlp and "relevance_score" in df.columns:
            df = df.sort_values(by="relevance_score", ascending=False)

        # Make sure the directory exists
        dir_name = os.path.dirname(filename)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)

        df.to_csv(filename, index=False, encoding="utf-8")
        print(f"Results saved to {filename}")

    def search_content(self, search_topic):
        """Search for the topic in the scraped content with relevance ranking."""
        if not self.content_data:
            print("No content to search in.")
            return []

        results = []
        for item in self.content_data:
            # Calculate relevance if not already done
            if "relevance_score" not in item and self.nlp:
                content_doc = self.nlp(item["content"][:5000])
                topic_doc = self.nlp(search_topic)
                relevance = content_doc.similarity(topic_doc)
                item["relevance_score"] = relevance

            if (
                search_topic.lower() in item["content"].lower()
                or search_topic.lower() in item["title"].lower()
                or (
                    "relevance_score" in item
                    and item["relevance_score"] > self.relevance_threshold
                )
            ):
                results.append(item)

        # Sort results by relevance if possible
        if self.nlp:
            results = sorted(
                results, key=lambda x: x.get("relevance_score", 0), reverse=True
            )

        return results


def sanitize_filename(filename):
    """Sanitize the filename to avoid invalid characters."""
    # Replace characters that are invalid in Windows filenames
    invalid_chars = r'[\\/*?:"<>|]'
    return re.sub(invalid_chars, "_", filename)


def main():
    # Example usage with hardcoded values for testing
    topic = "How does Amazon price their SaaS tool?"
    start_url = "https://aws.amazon.com/connect/pricing/"

    # Uncomment these lines for interactive mode
    # topic = input("Enter the topic or statement to search for: ")
    # start_url = input("Enter the URL to start scraping from: ")

    max_depth = 5  # Default value
    max_breadth = 5  # Default value
    relevance_threshold = 0.3  # Default value

    # Uncomment these lines for interactive mode
    # max_depth = int(input("Enter maximum crawling depth (default 5): ") or 5)
    # max_breadth = int(input("Enter maximum links to follow per page (default 5): ") or 5)
    # relevance_threshold = float(input("Enter relevance threshold (0.0-1.0, default 0.3): ") or 0.3)

    # Domain restriction (optional)
    # restrict_domains = input("Restrict to specific domains? (y/n, default n): ").lower() == 'y'
    restrict_domains = False  # Default value
    allowed_domains = None
    if restrict_domains:
        domains = input(
            "Enter comma-separated domains (e.g., example.com,sub.example.com): "
        )
        allowed_domains = [d.strip() for d in domains.split(",")]

    # Input validation
    if not start_url.startswith(("http://", "https://")):
        start_url = "https://" + start_url

    # Create scraper with parameters
    scraper = EnhancedWebScraper(
        max_depth=max_depth,
        max_breadth=max_breadth,
        relevance_threshold=relevance_threshold,
        allowed_domains=allowed_domains,
        concurrent_requests=5,
    )

    print(f"Starting to scrape for topic: {topic}")
    print(f"Starting URL: {start_url}")

    # Start crawling
    scraper.crawl(start_url, topic)

    # Save all results
    scraper.save_results("all_scraped_content.csv")

    # Search for topic in content
    results = scraper.search_content(topic)

    # Save topic-specific results if found
    if results:
        # Sanitize filename to avoid invalid characters
        safe_filename = sanitize_filename(f'{topic.replace(" ", "_")}_results.csv')

        df = pd.DataFrame(results)
        df.to_csv(safe_filename, index=False, encoding="utf-8")

        print(f"Found {len(results)} pages with content related to '{topic}'")
        print(f"Results saved to {safe_filename}")
    else:
        print(f"No content found related to '{topic}'")


if __name__ == "__main__":
    main()
