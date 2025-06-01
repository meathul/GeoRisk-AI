import os
import json
import requests
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()

class Config:
    WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    WATSONX_APIKEY = os.getenv("WATSONX_AI_API", "")
    WATSONX_PROJECT_ID = os.getenv("PROJECT_ID", "")
    SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
    CLIMATE_DB_DIR = "climate_chroma_db"
    BUSINESS_DB_DIR = "risk_chroma_db"


def setup_watsonx_model():
    params = {
        GenParams.DECODING_METHOD: "greedy",
        GenParams.MAX_NEW_TOKENS: 800,
        GenParams.TEMPERATURE: 0.7,
        GenParams.STOP_SEQUENCES: ["\n\n"]
    }
    return ModelInference(
        model_id="meta-llama/llama-3-3-70b-instruct",
        params=params,
        credentials={"url": Config.WATSONX_URL, "apikey": Config.WATSONX_APIKEY},
        project_id=Config.WATSONX_PROJECT_ID
    )


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

class LocationExtractor:
    def __init__(self, model):
        self.model = model

    def extract_location(self, text: str) -> str:
        prompt = (
            "Extract the location from this query. "
            "If no specific location is mentioned, respond with 'New York, NY'.\n\n"
            f"Query: {text}\n\nLocation:"
        )
        response = self.model.generate_text(prompt).strip()
        return response or "New York, NY"


class ClimateAgent:
    def __init__(self, climate_retriever, serper_service, model):
        self.retriever = climate_retriever
        self.serper = serper_service
        self.model = model

    def analyze_climate_risks(self, location: str, user_query: str) -> Dict:
        # 1. Real-time search data
        search_results = {
            "weather": self.serper.search_climate_data(location, "weather"),
            "risks": self.serper.search_climate_data(location, "risks"),
            "news": self.serper.search_climate_data(location, "news"),
            "projections": self.serper.search_climate_data(location, "projections")
        }

        # 2. Knowledge base retrieval
        climate_queries = [
            f"climate change impacts {location} temperature precipitation extreme weather",
            f"sea level rise flooding {location} coastal risks",
            f"drought water scarcity {location} agriculture",
            f"extreme heat heatwave {location} infrastructure"
        ]
        all_docs = []
        if self.retriever:
            for q in climate_queries:
                docs = self.retriever.invoke(q)
                all_docs.extend(docs[:2])

        # 3. Build context
        context = self._build_context(search_results, all_docs)

        # 4. Generate analysis
        prompt = self._build_analysis_prompt(location, user_query, context)
        enhanced_params = {
            "decoding_method": "greedy",
            "max_new_tokens": 2000,
            "temperature": 0.8,
            "stop_sequences": ["\n\n\n"]
        }
        analysis = self.model.generate_text(prompt=prompt, params=enhanced_params).strip()

        return {
            "analysis": analysis,
            "location": location,
            "search_data": search_results,
            "sources_used": len(all_docs),
            "search_queries_used": len(climate_queries)
        }

    def _build_context(self, search_results: Dict, local_docs: List) -> str:
        parts = []
        for stype, results in search_results.items():
            if results.get("success"):
                parts.append(f"\n--- {stype.upper()} ---")
                for item in results.get("results", [])[:5]:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    link = item.get("link", "")
                    if title and snippet:
                        parts.append(f"• {title}\n  Summary: {snippet}\n  Source: {link}\n")
                news_items = results.get("news", [])
                if news_items:
                    parts.append(f"--- {stype.upper()} NEWS ---")
                    for news in news_items[:3]:
                        title = news.get("title", "")
                        snippet = news.get("snippet", "")
                        if title and snippet:
                            parts.append(f"• {title}: {snippet}")
        if local_docs:
            parts.append("\n--- LOCAL CLIMATE DATABASE ---")
            for doc in local_docs[:8]:
                source = doc.metadata.get("source", "Unknown Source")
                content = doc.page_content[:500] + "..."
                parts.append(f"\nDocument: {source}\nContent: {content}")
        return "\n".join(parts)

    def _build_analysis_prompt(self, location: str, user_query: str, context: str) -> str:
        return f"""You are a Senior Climate Risk Analyst with 15+ years of experience.

            LOCATION: {location}
            USER QUESTION: {user_query}

            DATA SOURCES:
            {context}

            Provide a detailed analysis covering current conditions, historical trends, future projections, risk assessment, economic impacts, data confidence, and limitations.
            Use at least 4-5 points in each section and include specific examples and numbers.

            CLIMATE ANALYSIS:"""

class BusinessRiskAgent:
    def __init__(self, business_retriever, model):
        self.retriever = business_retriever
        self.model = model

    def analyze_business_impact(self, location: str, climate_analysis: str, user_query: str) -> str:
        business_queries = [
            f"supply chain risk climate business continuity {location}",
            f"operational resilience climate adaptation {location}",
            f"financial impact climate change business {location}",
            f"risk management climate hazards enterprise {location}"
        ]
        all_docs = []
        if self.retriever:
            for q in business_queries:
                docs = self.retriever.invoke(q)
                all_docs.extend(docs[:2])

        context = self._build_business_context(all_docs)
        prompt = self._build_risk_prompt(location, climate_analysis, user_query, context)
        enhanced_params = {
            "decoding_method": "greedy",
            "max_new_tokens": 2500,
            "temperature": 0.8,
            "stop_sequences": ["\n\n\n"]
        }
        return self.model.generate_text(prompt=prompt, params=enhanced_params).strip()

    def _build_business_context(self, docs: List) -> str:
        if not docs:
            return "No specific business documents found; use general best practices for climate risk."
        parts = ["--- BUSINESS RISK DOCUMENTS ---"]
        for i, doc in enumerate(docs[:8], 1):
            source = doc.metadata.get("source", f"Source {i}")
            content = doc.page_content[:600] + "..."
            parts.append(f"\nDocument {i}: {source}\nContent: {content}")
        return "\n".join(parts)

    def _build_risk_prompt(self, location: str, climate_analysis: str, user_query: str, context: str) -> str:
        return f"""You are a Senior Business Continuity Consultant.

            LOCATION: {location}
            USER QUESTION: {user_query}

            CLIMATE ANALYSIS:
            {climate_analysis}

            BUSINESS CONTEXT:
            {context}

            Provide a detailed operational impact analysis, financial impact assessment, strategic mitigation framework 
            (immediate to long-term), implementation roadmap, strategic recommendations, and plan evaluation. 
            Include specific examples, timelines, and financial estimates.

            BUSINESS IMPACT ANALYSIS:"""


class ClimateRiskChatbot:
    def __init__(self):
        self.model = setup_watsonx_model()
        self.serper = SerperSearchService()
        self.location_extractor = LocationExtractor(self.model)

        embedding_fn = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        try:
            self.climate_db = Chroma(
                persist_directory=Config.CLIMATE_DB_DIR,
                embedding_function=embedding_fn
            )
            self.business_db = Chroma(
                persist_directory=Config.BUSINESS_DB_DIR,
                embedding_function=embedding_fn
            )
        except Exception:
            self.climate_db = None
            self.business_db = None

        self.climate_agent = ClimateAgent(
            self.climate_db.as_retriever() if self.climate_db else None,
            self.serper,
            self.model
        )
        self.risk_agent = BusinessRiskAgent(
            self.business_db.as_retriever() if self.business_db else None,
            self.model
        )

    def process_query(self, user_query: str) -> str:
        # 1. Extract location via LLM
        location = self.location_extractor.extract_location(user_query)

        # 2. Climate analysis
        climate_results = self.climate_agent.analyze_climate_risks(location, user_query)
        climate_analysis = climate_results["analysis"]

        # 3. Business risk analysis
        business_analysis = self.risk_agent.analyze_business_impact(
            location, climate_analysis, user_query
        )

        # 4. Final response
        final_response = self._create_final_response(
            location, climate_analysis, business_analysis
        )
        return final_response

    def _create_final_response(self, location: str, climate_analysis: str,
                               business_analysis: str) -> str:
        """
        Generate a response structured into:
        - Current Conditions
        - Historic Trends
        - Future Predictions
        - Risk Assessment
        - Economic Impact
        - Summary & Recommendations
        """
        summary_prompt = f"""You are a Climate Risk Advisor.

            LOCATION: {location}

            CLIMATE ANALYSIS:
            {climate_analysis}

            BUSINESS ANALYSIS:
            {business_analysis}

            Produce a response with these sections:
            1. Current Conditions
            2. Historic Trends
            3. Future Predictions
            4. Risk Assessment
            5. Economic Impact
            6. Summary & Recommendations

            For each section, provide concise but informative paragraphs.
            In the Summary & Recommendations section, include actionable steps and strategic advice tailored to the user's needs."""


        enhanced_params = {
            "decoding_method": "greedy",
            "max_new_tokens": 1800,
            "temperature": 0.75,
            "stop_sequences": ["\n\n\n"]
        }

        try:
            response_text = self.model.generate_text(
                prompt=summary_prompt, params=enhanced_params
            ).strip()
        except Exception:
            # Fallback static structure if generation fails
            response_text = """1. Current Conditions:
                - Overview of today's climate hazards and ongoing trends.

                2. Historic Trends:
                - Summary of how these climate factors have evolved over the past decades.

                3. Future Predictions:
                - Projections for temperature changes, sea level rise, extreme events.

                4. Risk Assessment:
                - Identification and evaluation of key vulnerabilities and threats.

                5. Economic Impact:
                - Analysis of potential financial losses, supply chain disruptions, and operational costs.

                6. Summary & Recommendations:
                - Executive summary highlighting critical points and recommended actions to mitigate risks,
                including timeline, stakeholder roles, and resource considerations."""

        return response_text

def main():
    print("CLIMATE RISK ASSESSMENT CHATBOT")
    print("Type 'exit' to quit\n")

    chatbot = ClimateRiskChatbot()
    while True:
        user_input = input("Your Question: ").strip()
        if user_input.lower() in ("exit", "quit", "bye"):
            print("\n👋 Session complete.")
            break
        if not user_input:
            continue
        response = chatbot.process_query(user_input)
        print(f"\n{response}\n")
        print("-" * 80)

if __name__ == "__main__":
    main()
