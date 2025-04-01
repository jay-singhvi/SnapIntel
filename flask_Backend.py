from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from company_url_collector.src.company_url_collector import CompanyURLCollector

load_dotenv()
app = Flask(__name__)

api_key = os.environ.get("PERPLEXITY_API_KEY")
collector = CompanyURLCollector(api_key)

@app.route("/api/collect-urls", methods=["POST"])
def collect_urls():
    data = request.json
    required_fields = ["company_name", "company_url", "duration"]
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
        
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
    
    # Count statistics for first-party and relevant URLs
    first_party_urls = [url for url in urls if url.get("is_first_party", False)]
    third_party_urls = [url for url in urls if not url.get("is_first_party", False)]
    relevant_urls = [url for url in urls if url.get("is_relevant", True)]
    irrelevant_urls = [url for url in urls if not url.get("is_relevant", True)]
    
    return jsonify({
        "company": company_name,
        "urls": urls,
        "count": len(urls),
        "first_party_count": len(first_party_urls),
        "third_party_count": len(third_party_urls),
        "relevant_count": len(relevant_urls),
        "irrelevant_count": len(irrelevant_urls)
    })

@app.route("/api/filter-urls/<company_name>", methods=["GET"])
def filter_urls(company_name):
    from company_url_collector.src.url_storage import URLStorage
    
    storage = URLStorage()
    urls = storage.get_stored_urls(company_name)
    
    # Get filter parameters
    is_first_party = request.args.get("is_first_party")
    is_relevant = request.args.get("is_relevant")
    
    # Apply filters
    if is_first_party is not None:
        is_first_party = is_first_party.lower() == "true"
        urls = [url for url in urls if url.get("is_first_party", False) == is_first_party]
        
    if is_relevant is not None:
        is_relevant = is_relevant.lower() == "true"
        urls = [url for url in urls if url.get("is_relevant", True) == is_relevant]
    
    return jsonify({
        "company": company_name,
        "filtered_urls": urls,
        "count": len(urls)
    })

if __name__ == "__main__":
    app.run(debug=True)
