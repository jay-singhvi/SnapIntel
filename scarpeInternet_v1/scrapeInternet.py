import requests
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import urlparse, urljoin
import pandas as pd
from collections import deque


class WebScraper:
    def __init__(self, max_depth=5, max_breadth=5):
        self.max_depth = max_depth
        self.max_breadth = max_breadth
        self.visited_urls = set()
        self.discovery_sequence = []
        self.content_data = []
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def is_valid_url(self, url):
        """Check if the URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def normalize_url(self, url, base_url):
        """Normalize relative URLs to absolute URLs."""
        if not url:
            return None

        # Handle URLs that are already absolute
        if url.startswith(("http://", "https://")):
            return url

        # Handle fragment URLs (anchors on the same page)
        if url.startswith("#"):
            return None

        # Handle relative URLs
        return urljoin(base_url, url)

    def extract_text_content(self, soup):
        """Extract text content from the page, excluding scripts and styles."""
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Get text
        text = soup.get_text()

        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())

        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

        # Drop blank lines
        text = "\n".join(chunk for chunk in chunks if chunk)

        return text

    def get_links_and_content(self, url, depth):
        """Extract all links and content from a given URL."""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses

            # Check if the content is HTML
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type:
                return []

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract content
            content = self.extract_text_content(soup)
            title = soup.title.text if soup.title else "No Title"

            # Add to content data
            self.content_data.append(
                {
                    "url": url,
                    "depth": depth,
                    "discovery_index": len(self.discovery_sequence),
                    "title": title,
                    "content": content[:1000],  # Limit content length for storage
                }
            )

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

            # Respect max breadth
            return links[: self.max_breadth]

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return []

    def crawl(self, start_url, search_topic):
        """Crawl the web starting from the given URL with BFS approach."""
        # Reset tracking variables
        self.visited_urls = set()
        self.discovery_sequence = []
        self.content_data = []

        # Initialize queue with the start URL and depth 0
        queue = deque([(start_url, 0)])
        self.visited_urls.add(start_url)

        while queue:
            current_url, depth = queue.popleft()

            # Skip if we've reached max depth
            if depth > self.max_depth:
                continue

            print(f"Crawling: {current_url} (Depth: {depth})")

            # Add to discovery sequence
            self.discovery_sequence.append(current_url)

            # Get links from current URL
            links = self.get_links_and_content(current_url, depth)

            # Add new links to the queue
            for link in links:
                if link not in self.visited_urls:
                    queue.append((link, depth + 1))
                    self.visited_urls.add(link)

            # Polite scraping with a delay
            time.sleep(random.uniform(1, 3))

    def save_results(self, filename="scraping_results.csv"):
        """Save the scraped data to a CSV file."""
        if not self.content_data:
            print("No data to save.")
            return

        df = pd.DataFrame(self.content_data)
        df.to_csv(filename, index=False, encoding="utf-8")
        print(f"Results saved to {filename}")

    def search_content(self, search_topic):
        """Search for the topic in the scraped content."""
        if not self.content_data:
            print("No content to search in.")
            return []

        results = []
        for item in self.content_data:
            if (
                search_topic.lower() in item["content"].lower()
                or search_topic.lower() in item["title"].lower()
            ):
                results.append(item)

        return results


def main():
    # Example usage
    # topic = input("Enter the topic or statement to search for: ")
    # start_url = input("Enter the URL to start scraping from: ")

    topic = "How does Amazon price their SaaS tool?"
    start_url = "https://aws.amazon.com/connect/pricing/"

    # Input validation
    if not start_url.startswith(("http://", "https://")):
        start_url = "https://" + start_url

    scraper = WebScraper(max_depth=5, max_breadth=5)

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
        df = pd.DataFrame(results)
        df.to_csv(
            f'{topic.replace(" ", "_")}_results.csv', index=False, encoding="utf-8"
        )
        print(f"Found {len(results)} pages with content related to '{topic}'")
        print(f"Results saved to {topic.replace(' ', '_')}_results.csv")
    else:
        print(f"No content found related to '{topic}'")


if __name__ == "__main__":
    main()
