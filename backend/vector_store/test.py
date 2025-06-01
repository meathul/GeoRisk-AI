import os
import re
import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# ─── IBM Watsonx & Vectorstore imports ─────────────────────────────────────
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# ─── ENVIRONMENT SETUP ───────────────────────────────────────────────────────
load_dotenv()

WATSONX_URL    = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WATSONX_APIKEY = os.getenv("WATSONX_AI_API", "")
WATSONX_PID    = os.getenv("PROJECT_ID", "")

# ─── VECTOR STORES ─────────────────────────────────────────────────────────
CLIMATE_SCIENCE_CHROMA_DIR = "climate_chroma_db"  
BUSINESS_RISK_CHROMA_DIR = "risk_chroma_db"    

# ─── WEATHER API ─────────────────────────────────────────────────────────
VISUAL_CROSSING_API_KEY = os.getenv("VISUAL_CROSSING_API")

# ─── MODEL PARAMETERS ─────────────────────────────────────────────────────────
GEN_PARAMS = {
    GenParams.DECODING_METHOD: "greedy",
    GenParams.MAX_NEW_TOKENS: 1200,
    GenParams.TEMPERATURE: 0.7,
    GenParams.STOP_SEQUENCES: ["\n\n"]
}

model = ModelInference(
    model_id="meta-llama/llama-3-3-70b-instruct",
    params=GEN_PARAMS,
    credentials={ "url": WATSONX_URL, "apikey": WATSONX_APIKEY },
    project_id=WATSONX_PID
)


class ClimateAnalysis(BaseModel):
    """Structured output from Climate Agent"""
    location: str
    current_conditions: str
    historical_trends: str
    future_projections: str
    key_hazards: List[str]
    confidence_level: str


class RiskAnalysis(BaseModel):
    """Structured output from Risk Agent"""
    business_impacts: List[str]
    financial_estimates: str
    mitigation_strategies: List[str]
    priority_actions: List[str]
    risk_score: float


class EnhancedState:
    """Enhanced conversation state with agent outputs"""
    def __init__(self):
        self.messages = []
        self.location: Optional[str] = None
        self.climate_analysis: Optional[ClimateAnalysis] = None
        self.risk_analysis: Optional[RiskAnalysis] = None
        self.raw_weather_data: Optional[str] = None
        self.api_available: bool = True


class LocationExtractor:
    """Enhanced location extraction with validation"""
    
    @staticmethod
    def extract_location(text: str) -> Tuple[str, float]:
        """
        Extract location and return confidence score
        Returns: (location, confidence_score)
        """
        patterns = [
            (r"(?:in|at|for(?:\s+our)?)\s+([A-Z][a-zA-Z\s]+(?:,\s*[A-Z]{2})?)", 0.9),
            (r"(?:our|the)\s+([A-Z][a-zA-Z\s]+)\s+(?:facility|distribution|center|plant|warehouse)", 0.8),
            (r"([A-Z][a-zA-Z\s]+)\s+(?:facility|distribution|center|plant|warehouse)", 0.7),
            (r"([A-Z][a-zA-Z\s]+(?:,\s*[A-Z]{2})?)", 0.5)
        ]
        
        for pattern, confidence in patterns:
            match = re.search(pattern, text)
            if match:
                location = match.group(1).strip()
                # Clean up location
                location_parts = location.split()
                if len(location_parts) > 3:
                    location = " ".join(location_parts[:3])
                return location, confidence
        
        return "New York, NY", 0.3 


class WeatherService:
    """Enhanced weather data fetching with error handling"""
    
    @staticmethod
    def get_extended_forecast(location: str) -> Dict:
        """Get 7-day forecast and historical context with graceful error handling"""
        if not VISUAL_CROSSING_API_KEY:
            return {"error": "api_unavailable", "message": "Weather API not configured"}
        
        loc_encoded = location.replace(" ", "%20")
        
        # Current + 7-day forecast
        url = (
            f"https://weather.visualcrossing.com/VisualCrossingWebServices/"
            f"rest/services/timeline/{loc_encoded}"
            f"?unitGroup=us&key={VISUAL_CROSSING_API_KEY}&contentType=json&include=days"
        )
        
        try:
            response = urllib.request.urlopen(url)
            data = json.load(response)
            
            return {
                "current": data.get("days", [{}])[0],
                "forecast": data.get("days", [])[:7],
                "location_resolved": data.get("resolvedAddress", location),
                "success": True
            }
        except Exception as e:
            return {
                "error": "api_error", 
                "message": f"Unable to fetch current weather data",
                "success": False
            }


class ClimateAgent:
    """Agent focused on climate science and environmental conditions"""
    
    def __init__(self, climate_retriever):
        self.retriever = climate_retriever
    
    def analyze_climate(self, state: EnhancedState) -> EnhancedState:
        """
        Comprehensive climate analysis combining:
        1. Current weather conditions (when available)
        2. Historical climate trends (from documents)
        3. Future climate projections
        4. Key hazard identification
        """
        user_query = state.messages[-1]["content"]
        location = state.location
        
        # 1. Attempt to get weather data
        weather_data = WeatherService.get_extended_forecast(location)
        weather_available = weather_data.get("success", False)
        
        # 2. Retrieve climate science documents
        climate_query = f"climate change impacts {location} temperature precipitation extreme weather"
        docs = self.retriever.invoke(climate_query)
        
        # Build context from retrieved docs
        climate_context = self._build_climate_context(docs[:4])
        
        # 3. Generate comprehensive climate analysis
        prompt = self._build_climate_prompt(user_query, location, weather_data, climate_context, weather_available)
        
        response = model.generate_text(prompt=prompt).strip()
        
        # Format the response into structured points
        formatted_response = self._format_climate_response(response, location, weather_available)
        
        # Store structured analysis
        state.climate_analysis = self._parse_climate_response(response, location)
        if weather_available:
            state.raw_weather_data = json.dumps(weather_data, indent=2)
        
        # Add to conversation
        state.messages.append({
            "role": "assistant", 
            "content": formatted_response,
            "agent": "climate"
        })
        
        return state
    
    def _build_climate_context(self, docs) -> str:
        """Build climate science context from retrieved documents"""
        if not docs:
            return "No specific climate science data retrieved from knowledge base."
        
        context_parts = []
        for doc in docs:
            source = doc.metadata.get("source", "Climate Research Document")
            content = doc.page_content.replace("\n", " ")[:400] + "..."
            context_parts.append(f"From {source}: {content}")
        
        return "\n\n".join(context_parts)
    
    def _build_climate_prompt(self, user_query: str, location: str, weather_data: Dict, context: str, weather_available: bool) -> str:
        """Build comprehensive climate analysis prompt"""
        weather_section = ""
        if weather_available:
            weather_section = f"""
            CURRENT WEATHER DATA AVAILABLE:
            {json.dumps(weather_data, indent=2)}
            """
        else:
            weather_section = "CURRENT WEATHER DATA: Not available - focus on historical and projected climate patterns."
        
        return f"""You are a Climate Science Advisor providing comprehensive environmental analysis.

            LOCATION: {location}

            {weather_section}

            CLIMATE SCIENCE CONTEXT FROM KNOWLEDGE BASE:
            {context}

            USER QUERY: {user_query}

            Based on the available information, provide a structured climate analysis. Format your response as clear, numbered points under these sections:

            CURRENT CONDITIONS:
            - List current weather and short-term outlook if data available
            - If no current data available, note this and focus on typical seasonal patterns

            HISTORICAL CLIMATE TRENDS:
            - Key long-term climate patterns for this region
            - Notable changes observed over past decades
            - Include sources when referencing specific data

            FUTURE CLIMATE PROJECTIONS:
            - Expected changes in next 10-30 years
            - Temperature and precipitation trends
            - Cite sources for projections

            KEY CLIMATE HAZARDS:
            - List top 3-5 climate risks specific to this location
            - Rank by likelihood and potential severity
            - Include both gradual changes and extreme events

            CONFIDENCE ASSESSMENT:
            - Rate confidence in projections (High/Medium/Low)
            - Note any data limitations or uncertainties

            Format each section with clear bullet points. Be specific and actionable while maintaining scientific accuracy.

            RESPONSE:"""
    
    def _format_climate_response(self, response: str, location: str, weather_available: bool) -> str:
        """Format the response with better structure and human-like language"""
        header = f"CLIMATE ANALYSIS FOR {location.upper()}\n\n"
        
        if not weather_available:
            disclaimer = "Note: Based on available climate research data and historical patterns.\n\n"
            return header + disclaimer + response
        
        return header + response
    
    def _parse_climate_response(self, response: str, location: str) -> ClimateAnalysis:
        """Parse response into structured format"""
        # Simple parsing - could be enhanced with more sophisticated NLP
        hazards = []
        response_lower = response.lower()
        
        hazard_keywords = {
            "flooding": ["flood", "flooding", "storm surge", "heavy rain"],
            "extreme_heat": ["heat", "temperature", "heat wave", "extreme heat"],
            "storms": ["hurricane", "storm", "wind", "tornado", "cyclone"],
            "sea_level_rise": ["sea level", "coastal", "rising waters"],
            "drought": ["drought", "water shortage", "dry conditions"],
            "wildfire": ["fire", "wildfire", "burning"]
        }
        
        for hazard, keywords in hazard_keywords.items():
            if any(keyword in response_lower for keyword in keywords):
                hazards.append(hazard)
        
        return ClimateAnalysis(
            location=location,
            current_conditions="Extracted from analysis",
            historical_trends="Based on available climate data",
            future_projections="Derived from climate models and research", 
            key_hazards=hazards[:5],  # Limit to top 5
            confidence_level="moderate"
        )


class RiskAgent:
    """Agent focused on business risk analysis and mitigation strategies"""
    
    def __init__(self, business_retriever):
        self.retriever = business_retriever
    
    def analyze_risk(self, state: EnhancedState) -> EnhancedState:
        """
        Business risk analysis based on climate analysis:
        1. Translate climate hazards to business impacts
        2. Estimate financial implications
        3. Recommend mitigation strategies
        4. Prioritize actions
        """
        user_query = state.messages[-1]["content"]
        climate_data = state.climate_analysis
        location = state.location
        
        # 1. Retrieve business risk documents
        business_query = f"supply chain risk climate {location} business impact operational resilience"
        docs = self.retriever.invoke(business_query)
        
        business_context = self._build_business_context(docs[:4])
        
        # 2. Generate risk analysis
        prompt = self._build_risk_prompt(user_query, location, climate_data, business_context)
        
        response = model.generate_text(prompt=prompt).strip()
        
        # Format the response
        formatted_response = self._format_risk_response(response, location)
        
        # Store structured analysis
        state.risk_analysis = self._parse_risk_response(response)
        
        # Add to conversation
        state.messages.append({
            "role": "assistant",
            "content": formatted_response,
            "agent": "risk"
        })
        
        return state
    
    def _build_business_context(self, docs) -> str:
        """Build business risk context from retrieved documents"""
        if not docs:
            return "No specific business risk data retrieved from knowledge base."
        
        context_parts = []
        for doc in docs:
            source = doc.metadata.get("source", "Business Risk Report")
            content = doc.page_content.replace("\n", " ")[:400] + "..."
            context_parts.append(f"From {source}: {content}")
        
        return "\n\n".join(context_parts)
    
    def _build_risk_prompt(self, user_query: str, location: str, climate_data: ClimateAnalysis, context: str) -> str:
        """Build comprehensive business risk prompt"""
        return f"""You are a Business Risk Advisor specializing in climate-related operational risks.

            LOCATION: {location}

            IDENTIFIED CLIMATE HAZARDS:
            {', '.join(climate_data.key_hazards) if climate_data.key_hazards else 'General climate risks'}

            BUSINESS RISK CONTEXT FROM KNOWLEDGE BASE:
            {context}

            USER QUERY: {user_query}

            Based on the climate analysis, provide a comprehensive business risk assessment formatted as clear, numbered points:

            OPERATIONAL IMPACTS:
            - How each climate hazard affects day-to-day operations
            - Specific disruptions to facilities, logistics, and workforce
            - Duration and frequency of potential impacts

            FINANCIAL IMPLICATIONS:
            - Estimated direct costs (repairs, downtime, emergency response)
            - Indirect costs (lost productivity, supply chain delays)
            - Insurance considerations and coverage gaps
            - Revenue impact scenarios

            SUPPLY CHAIN VULNERABILITIES:
            - Critical supplier locations at risk
            - Transportation route disruptions
            - Inventory and storage risks
            - Alternative sourcing challenges

            MITIGATION STRATEGIES:
            - Infrastructure improvements and hardening measures
            - Operational procedure changes
            - Supply chain diversification options
            - Emergency response planning

            IMPLEMENTATION PRIORITIES:
            High Priority (Immediate - 0-6 months):
            - Most critical actions with highest ROI

            Medium Priority (6-18 months):
            - Important improvements requiring more planning

            Low Priority (18+ months):
            - Long-term resilience building measures

            ESTIMATED RETURNS:
            - Cost-benefit analysis for key recommendations
            - Payback periods for major investments

            Format with clear bullet points and be specific about timeframes and costs where possible.

            RESPONSE:"""
    
    def _format_risk_response(self, response: str, location: str) -> str:
        """Format the risk response with better structure"""
        header = f"BUSINESS RISK ANALYSIS FOR {location.upper()}\n\n"
        return header + response
    
    def _parse_risk_response(self, response: str) -> RiskAnalysis:
        """Parse response into structured format"""
        # Extract key information from response
        impacts = []
        strategies = []
        priorities = []
        
        response_lower = response.lower()
        
        # Simple keyword extraction
        if "operational" in response_lower:
            impacts.append("Operational disruption")
        if "supply chain" in response_lower:
            impacts.append("Supply chain delays")
        if "financial" in response_lower:
            impacts.append("Financial losses")
        
        if "infrastructure" in response_lower:
            strategies.append("Infrastructure hardening")
        if "diversif" in response_lower:
            strategies.append("Supply diversification")
        if "emergency" in response_lower:
            strategies.append("Emergency planning")
        
        if "high priority" in response_lower:
            priorities.append("Infrastructure assessment")
        if "medium priority" in response_lower:
            priorities.append("Supply chain review")
        
        # Calculate risk score based on number of hazards and impacts
        risk_score = min(10.0, len(impacts) * 2.5 + 2.5)
        
        return RiskAnalysis(
            business_impacts=impacts or ["General operational risks"],
            financial_estimates="Based on analysis of climate impacts",
            mitigation_strategies=strategies or ["Risk assessment and planning"],
            priority_actions=priorities or ["Comprehensive risk evaluation"],
            risk_score=risk_score
        )


class EnhancedChatbotFlow:
    """Main orchestrator for the sequential multi-agent system"""
    
    def __init__(self, climate_retriever, business_retriever):
        self.climate_agent = ClimateAgent(climate_retriever)
        self.risk_agent = RiskAgent(business_retriever)
        self.location_extractor = LocationExtractor()
    
    def process_query(self, state: EnhancedState) -> EnhancedState:
        """
        Sequential processing:
        1. Extract location
        2. Climate Agent analysis
        3. Risk Agent analysis
        4. Executive summary
        """
        user_query = state.messages[-1]["content"]
        
        # 1. Extract location
        location, confidence = self.location_extractor.extract_location(user_query)
        state.location = location
        
        if confidence < 0.5:
            # Ask for clarification if location unclear
            clarification = (f"I identified '{location}' as the location, but I'd like to be more precise. "
                           f"Could you please specify the exact city and state/country for your climate risk assessment? "
                           f"This will help me provide more accurate and relevant information.")
            state.messages.append({"role": "assistant", "content": clarification})
            return state
        
        # 2. Climate analysis
        state = self.climate_agent.analyze_climate(state)
        
        # 3. Business risk analysis
        state = self.risk_agent.analyze_risk(state)
        
        # 4. Summary integration
        self._add_executive_summary(state)
        
        return state
    
    def _add_executive_summary(self, state: EnhancedState):
        """Add executive summary combining both analyses"""
        hazards_text = "Various climate risks"
        if state.climate_analysis and state.climate_analysis.key_hazards:
            hazards_text = ', '.join(state.climate_analysis.key_hazards[:3])
        
        risk_score = 7.0
        if state.risk_analysis:
            risk_score = state.risk_analysis.risk_score
        
        priority_count = 3
        if state.risk_analysis and state.risk_analysis.priority_actions:
            priority_count = len(state.risk_analysis.priority_actions)
        
        summary = f"""EXECUTIVE SUMMARY FOR {state.location.upper()}

            KEY FINDINGS:
            • Primary Climate Threats: {hazards_text}
            • Overall Risk Level: {risk_score}/10 ({self._get_risk_level(risk_score)})
            • Immediate Actions Required: {priority_count} high-priority items identified

            NEXT STEPS:
            • Review the detailed climate and business risk analyses above
            • Focus on high-priority mitigation strategies first
            • Develop implementation timeline based on resource availability
            • Consider engaging climate risk specialists for detailed planning

            RECOMMENDATION:
            Begin with the highest-priority actions to build operational resilience while developing longer-term adaptation strategies."""

        state.messages.append({
            "role": "assistant",
            "content": summary,
            "agent": "summary"
        })
    
    def _get_risk_level(self, score: float) -> str:
        """Convert numeric risk score to descriptive level"""
        if score >= 8.0:
            return "High Risk"
        elif score >= 6.0:
            return "Moderate Risk"
        elif score >= 4.0:
            return "Low-Moderate Risk"
        else:
            return "Low Risk"


def run_enhanced_chatbot():
    """Main execution loop"""
    # Initialize separate vector stores
    embedding_fn = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    try:
        climate_db = Chroma(
            persist_directory=CLIMATE_SCIENCE_CHROMA_DIR,
            embedding_function=embedding_fn
        )
        business_db = Chroma(
            persist_directory=BUSINESS_RISK_CHROMA_DIR,
            embedding_function=embedding_fn
        )
    except Exception as e:
        print(f"Warning: Vector database initialization issue. Using fallback mode.")
        print(f"Error: {e}")
        return
    
    # Initialize system
    chatbot = EnhancedChatbotFlow(
        climate_retriever=climate_db.as_retriever(),
        business_retriever=business_db.as_retriever()
    )
    
    state = EnhancedState()
    
    print("Climate Risk Assessment System")
    print("=" * 50)
    print("Comprehensive Analysis: Climate Science → Business Risk → Action Plan")
    print("\nExample queries:")
    print("• 'What climate risks affect our Miami distribution center?'")
    print("• 'How might flooding impact our Chicago warehouse operations?'")
    print("• 'What are the long-term climate threats for our Phoenix facility?'")
    print("\nType 'exit' or 'quit' to end the session.\n")
    
    while True:
        user_input = input("User: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("\nClimate risk assessment session complete.")
            print("Stay prepared and resilient!")
            break
        
        if not user_input:
            continue
        
        # Add user message
        state.messages.append({"role": "user", "content": user_input})
        
        # Process through sequential agents
        try:
            state = chatbot.process_query(state)
            
            # Print latest responses (avoid duplicates)
            recent_messages = [msg for msg in state.messages[-4:] if msg["role"] == "assistant"]
            for msg in recent_messages:
                print(f"\n{msg['content']}")
                print("\n" + "=" * 80 + "\n")
                
        except Exception as e:
            print(f"\nI encountered an issue processing your request: {str(e)}")
            print("Please try rephrasing your question or check your system configuration.")
            print()


if __name__ == "__main__":
    run_enhanced_chatbot()