from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from company_url_collector.src.company_url_collector import CompanyURLCollector

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize the collector
api_key = os.environ.get("PERPLEXITY_API_KEY")
collector = CompanyURLCollector(api_key)


@app.route("/api/collect-urls", methods=["POST"])
def collect_urls():
    data = request.json

    # Validate input
    required_fields = ["company_name", "company_url", "duration"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Valid durations
    valid_durations = [
        "24 hrs",
        "7 days",
        "1 Month",
        "3 Months",
        "6 Months",
        "1 year",
        "All time",
    ]
    if data["duration"] not in valid_durations:
        return (
            jsonify(
                {
                    "error": f"Invalid duration. Must be one of: {', '.join(valid_durations)}"
                }
            ),
            400,
        )

    # Collect URLs
    result = collector.collect_urls(
        company_name=data["company_name"],
        company_url=data["company_url"],
        duration=data["duration"],
    )

    return jsonify(result)


@app.route("/api/get-urls/<company_name>", methods=["GET"])
def get_urls(company_name):
    from company_url_collector.src.url_storage import URLStorage

    storage = URLStorage()
    urls = storage.get_stored_urls(company_name)

    return jsonify({"company": company_name, "urls": urls, "count": len(urls)})


if __name__ == "__main__":
    app.run(debug=True)
