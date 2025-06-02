import os
from datetime import datetime

from langchain.memory import ConversationBufferMemory
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from .agents.watsonx_model import setup_watsonx_model
from .tools.search_tool import SerperSearchService
from .tools.location_extractor import LocationExtractor
from .agents.climate_agent import ClimateAgent
from .agents.business_agent import BusinessRiskAgent
from .settings.config import Config

class ClimateRiskChatbot:
    def __init__(self):
        # LLM setup
        self.model = setup_watsonx_model()
        self.serper = SerperSearchService()
        self.location_extractor = LocationExtractor(self.model)

        # Simple in-memory history: list of (user_query, bot_response) tuples
        self.history = []
        # Track the last non-Global location seen
        self.last_location = None

        # Chroma DB retrievers
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
        # 1. Classification prompt
        classification_prompt = (
            "Classify the following user input.\n"
            "If it is only a casual greeting (e.g., 'hello', 'hi'), respond with 'GREETING'.\n"
            "If it is only a farewell (e.g., 'bye', 'goodbye'), respond with 'FAREWELL'.\n"
            "Otherwise, respond with 'OTHER'.\n\n"
            f"User: {user_query}\n\n"
            "Classification:"
        )
        classification_params = {
            "decoding_method": "greedy",
            "max_new_tokens": 10,
            "temperature": 0.0,
            "stop_sequences": ["\n"]
        }
        classification = self.model.generate_text(
            prompt=classification_prompt, params=classification_params
        ).strip().upper()

        # 2. Handle GREETING
        if classification == "GREETING":
            return (
                "<hello>"
                "Hello! I am your Climate Risk Advisor Bot. "
                "I use a Retrieval-Augmented Generation (RAG) approach, combining on-demand real-time search, "
                "a local climate knowledge base, and IBM Watsonx AI to deliver tailored insights. "
                "You can ask me questions like:\n"
                "- 'What climate risks threaten our Chicago warehouse?'\n"
                "- 'How will sea-level rise affect our coastal plant?'\n"
                "Feel free to start with any location or say 'Global' to get a worldwide overview."
                "</hello>"
            )

        # 3. Handle FAREWELL
        if classification == "FAREWELL":
            return "<bye>Goodbye! If you have more climate risk questions later, just let me know.</bye>"

        loc_candidate = self.location_extractor.extract_location(user_query).strip()

        if loc_candidate.lower() == "global":
            if self.last_location:
                location = self.last_location
            else:
                location = "Global"
                self.last_location = None
        else:
            location = loc_candidate
            self.last_location = loc_candidate

        if self.history:
            history_lines = []
            for past_user, past_bot in self.history:
                history_lines.append(f"User: {past_user}")
                history_lines.append(f"Bot: {past_bot}")
            combined_input = "\n".join(history_lines) + "\nUser: " + user_query
        else:
            combined_input = user_query

        climate_results = self.climate_agent.analyze_climate_risks(location, combined_input)
        climate_analysis = climate_results["analysis"]

        business_analysis = self.risk_agent.analyze_business_impact(
            location, climate_analysis, combined_input
        )

        final_response = self._create_tagged_response(
            location, climate_analysis, business_analysis
        )

        self.history.append((user_query, final_response))

        return final_response

    def _create_tagged_response(self, location: str, climate_analysis: str,
                                business_analysis: str) -> str:
        prompt = (
            f"You are a C-suite Climate Risk Advisor.\n\n"
            f"LOCATION: {location}\n\n"
            f"CLIMATE ANALYSIS:\n{climate_analysis}\n\n"
            f"BUSINESS ANALYSIS:\n{business_analysis}\n\n"
            "Generate the output using exactly these tags and no additional text:\n"
            "<current> (current conditions) </current>\n"
            "<history> (historic trends) </history>\n"
            "<future> (future predictions) </future>\n"
            "<risk> (risk assessment) </risk>\n"
            "<economy> (economic impact) </economy>\n"
            "<summary> (final summary with recommendations) </summary>\n"
            "Ensure each section’s content is placed between its opening and closing tags. "
            "Do not include any explanation outside the tags.\n\n"
            "Here is what to generate:\n"
            "<current>\n"
            "  "
        )

        enhanced_params = {
            "decoding_method": "greedy",
            "max_new_tokens": 2000,
            "temperature": 0.75,
            "stop_sequences": ["</summary>"]
        }

        try:
            response_text = self.model.generate_text(prompt=prompt, params=enhanced_params).strip()
        except Exception:
            response_text = (
                "<current>\n"
                "Placeholder current conditions\n"
                "</current>\n"
                "<history>\n"
                "Placeholder historic trends\n"
                "</history>\n"
                "<future>\n"
                "Placeholder future predictions\n"
                "</future>\n"
                "<risk>\n"
                "Placeholder risk assessment\n"
                "</risk>\n"
                "<economy>\n"
                "Placeholder economic impact\n"
                "</economy>\n"
                "<summary>\n"
                "Placeholder summary with recommendations\n"
                "</summary>"
            )

        return response_text
