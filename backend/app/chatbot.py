import os
from datetime import datetime

from .agents.watsonx_model import setup_watsonx_model
from .tools.search_tool import SerperSearchService
from .tools.location_extractor import LocationExtractor
from .agents.climate_agent import ClimateAgent
from .agents.business_agent import BusinessRiskAgent
from .settings.config import Config
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

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
        location = self.location_extractor.extract_location(user_query)

        climate_results = self.climate_agent.analyze_climate_risks(location, user_query)
        climate_analysis = climate_results["analysis"]

        business_analysis = self.risk_agent.analyze_business_impact(
            location, climate_analysis, user_query
        )

        final_response = self._create_final_response(
            location, climate_analysis, business_analysis
        )
        return final_response

    def _create_final_response(self, location: str, climate_analysis: str,
                               business_analysis: str) -> str:
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
