import requests
from typing import Dict

from ..settings.config import Config

class SerperSearchService:
    def __init__(self):
        self.api_key = Config.SERPER_API_KEY
        self.base_url = "https://google.serper.dev/search"

    def search_climate_data(self, location: str, query_type: str = "general") -> Dict:
        if not self.api_key:
            return {"error": "Serper API key not configured"}
        queries = {
            "weather": f"current weather {location} extreme weather alerts",
            "risks": f"climate risks {location} flooding hurricane drought wildfire",
            "news": f"climate change impact {location} business operations 2024 2025",
            "projections": f"climate projections {location} sea level rise temperature",
            "general": f"climate risks business impact {location}"
        }
        q = queries.get(query_type, queries["general"])
        headers = {'X-API-KEY': self.api_key, 'Content-Type': 'application/json'}
        payload = {'q': q, 'num': 8, 'gl': 'us'}
        try:
            resp = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return {"success": True, "results": data.get("organic", []), "news": data.get("news", []), "query": q}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Search failed: {str(e)}"}
