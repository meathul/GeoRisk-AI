import os
import re
import json
import urllib.request

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Literal, Optional

# ─── IBM Watsonx & Vectorstore imports ─────────────────────────────────────
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ─── ENVIRONMENT SETUP ───────────────────────────────────────────────────────
load_dotenv()  


WATSONX_URL    = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WATSONX_APIKEY = os.getenv("WATSONX_AI_API", "")
WATSONX_PID    = os.getenv("PROJECT_ID", "")

# ─── LOCATION FOR YOUR PREBUILT CHROMA VECTOR STORE ─────────────────────────
#   Assume you have already run your ingestion pipeline on your climate PDFs
#   and persisted a single Chroma store under this directory. 
CLIMATE_CHROMA_DIR = "chroma_store"

# ─── WEATHER FORECAST API (Visual Crossing) ─────────────────────────────────
VISUAL_CROSSING_API_KEY = os.getenv("VISUAL_CROSSING_API")


# ─── MODEL PARAMETERS FOR WATSONx Llama-3 ────────────────────────────────────
GEN_PARAMS = {
    GenParams.DECODING_METHOD: "greedy",
    GenParams.MAX_NEW_TOKENS: 1000,
    GenParams.TEMPERATURE: 0.7,
    GenParams.STOP_SEQUENCES: ["\n\n"]
}

# Initialize the Watsonx foundation model (Llama-3 70B Instruct)
model = ModelInference(
    model_id="meta-llama/llama-3-3-70b-instruct",
    params=GEN_PARAMS,
    credentials={ "url": WATSONX_URL, "apikey": WATSONX_APIKEY },
    project_id=WATSONX_PID
)


# ─── AUXILIARY FUNCTIONS ─────────────────────────────────────────────────────

def extract_location(text: str) -> str:
    """
    Attempt to pull a city/region name from the user query.
    Look for patterns like "in {City}" or "for our {City} distribution center".
    Falls back to "New York" if no location is found.
    """
    # Example pattern: "in Chicago", "for our Miami plant", "at Houston distribution center"
    patterns = [
        r"(?:in|at|for(?:\s+our)?)\s+([A-Z][a-zA-Z\s]+)",
        r"(?:our|the)\s+([A-Z][a-zA-Z\s]+)\s+(?:facility|distribution|center|plant)"
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            candidate = match.group(1).strip()
            # Simple cleanup: if more than two words, cut off unneeded trailing words
            return candidate.split()[:3] if len(candidate.split()) > 3 else candidate
    # Default
    return "New York"


def get_climate_forecast(location: str = "New York") -> str:
    """
    Fetches the current-day forecast for `location` from Visual Crossing API.
    Returns a short string: "Date: YYYY-MM-DD, Temp: XX°F, Conditions: …"
    """
    loc_encoded = location.replace(" ", "%20")
    url = (
        f"https://weather.visualcrossing.com/VisualCrossingWebServices/"
        f"rest/services/timeline/{loc_encoded}"
        f"?unitGroup=us&key={VISUAL_CROSSING_API_KEY}&contentType=json"
    )
    try:
        response = urllib.request.urlopen(url)
        data = json.load(response)
        first_day = data.get("days", [{}])[0]
        return (
            f"Date: {first_day.get('datetime', 'N/A')}, "
            f"Temp: {first_day.get('temp', 'N/A')}°F, "
            f"Conditions: {first_day.get('conditions', 'N/A')}"
        )
    except Exception as e:
        return f"Unable to fetch forecast for {location}: {e}"


# ─── DATA MODEL FOR CLASSIFICATION (OPTIONAL) ─────────────────────────────────
class QueryClassifier(BaseModel):
    """
    A placeholder schema—if you want to validate payloads or integrate with a typed system.
    In this implementation, we do a simple string match instead of using this.
    """
    query_type: Literal["climate", "risk"] = Field(
        ..., description="Either 'climate' (short-term forecast) or 'risk' (long-term risk)."
    )


# ─── CHATBOT STATE & FLOW ────────────────────────────────────────────────────
class State:
    """
    Holds the conversation state. 
    - messages: list of dicts with {"role": "user"/"assistant", "content": str}
    - message_type: "climate" or "risk"
    - forecast_data: cached forecast string if available
    """
    def __init__(self):
        self.messages = []
        self.message_type: Optional[str] = None
        self.forecast_data: Optional[str] = None


class ChatbotFlow:
    def __init__(self, retriever):
        self.retriever = retriever

    def classify_message(self, state: State) -> State:
        """
        Use a short prompt to decide whether the user is asking for a short-term forecast
        or for a longer-term, document-backed risk assessment.
        """
        last_msg = state.messages[-1]["content"]
        prompt = (
            "Classify this user message into exactly one of:\n"
            "  - 'climate'  (if they want a short-term weather forecast)\n"
            "  - 'risk'     (if they want a long-term, document-backed climate risk analysis)\n"
            f"User message: {last_msg}\n"
            "Classification (just output 'climate' or 'risk'):"
        )

        resp = model.generate_text(prompt=prompt).strip().lower()
        # If the model returns anything containing "climate", treat as climate; else risk.
        if "climate" in resp:
            state.message_type = "climate"
        else:
            state.message_type = "risk"
        return state

    def climate_agent(self, state: State) -> State:
        """
        Handles short-term weather queries:
         - Extract location
         - Fetch forecast
         - Ask the LLM to rephrase/provide a friendly weather answer
        """
        user_query = state.messages[-1]["content"]
        location = extract_location(user_query)
        forecast = get_climate_forecast(location)
        state.forecast_data = forecast  # cache for later if needed

        prompt = (
            "You are a helpful Weather Assistant. Provide a brief, friendly answer.\n"
            f"Location: {location}\n"
            f"Forecast Info: {forecast}\n"
            f"User question: {user_query}\n"
            "Response:"
        )
        resp = model.generate_text(prompt=prompt).strip()
        state.messages.append({"role": "assistant", "content": resp})
        return state

    def risk_agent(self, state: State) -> State:
        """
        Handles long-term climate risk queries:
         - Extract location (for both forecast & retrieval context)
         - Fetch forecast if not yet fetched
         - Retrieve top-3 relevant document excerpts from Chroma
         - Build a supply-chain-focused prompt with citations/formatting guidelines
         - Generate a multi-part answer: Risks, Business Impact, Mitigations
        """
        user_query = state.messages[-1]["content"]
        location = extract_location(user_query)

        # 1. Short-term forecast (if not already available)
        if not state.forecast_data:
            state.forecast_data = get_climate_forecast(location)
        forecast = state.forecast_data

        # 2. Retrieve relevant documents from Chroma
        docs = self.retriever.get_relevant_documents(user_query)
        if docs:
            # We assume each document chunk has metadata like "source" (e.g., "IPCC_AR6", "WEF_GR2025")
            context_snippets = []
            for doc in docs[:3]:
                src = doc.metadata.get("source", "Unknown Source")
                snippet = doc.page_content.replace("\n", " ").strip()
                context_snippets.append(f"{src}: {snippet}")
            context = "\n\n".join(context_snippets)
        else:
            context = "No relevant document context found."

        # 3. Build the supply-chain/operations prompt
        prompt = (
            "You are a Climate Risk Advisor specialized in Supply-Chain & Operations for industrial facilities.\n"
            f"Facility Location: {location}\n\n"
            "A) Short-Term Forecast Data (Visual Crossing):\n"
            f"{forecast}\n\n"
            "B) Relevant Excerpts from Trusted Climate-Risk Documents:\n"
            f"{context}\n\n"
            "C) Guidelines for your response:\n"
            "  1. Focus specifically on physical climate hazards that threaten operations at the facility (e.g., floods, storms, heatwaves, sea-level rise).\n"
            "  2. Structure your answer in three sections:\n"
            "     • Risks: Describe each concrete hazard and timeline (e.g., “50% chance of 100-year flood by 2030…”).\n"
            "     • Business Impact: Explain how those hazards disrupt supply chain or facility (e.g., “Delayed shipments, higher insurance costs…”).\n"
            "     • Suggested Mitigations: Offer practical, actionable steps (e.g., “Elevate warehouse floor by 1 ft, secure backup power generator…”).\n"
            "  3. Whenever you reference a retrieved excerpt, include a citation in brackets like [IPCC_AR6_2023, Section 4.2].\n\n"
            f"User question: {user_query}\n\n"
            "Response (follow the Risks / Impact / Mitigations format, with citations):"
        )

        resp = model.generate_text(prompt=prompt).strip()
        state.messages.append({"role": "assistant", "content": resp})
        return state

    def invoke(self, state: State) -> State:
        """
        1. Classify user message (“climate” vs. “risk”)
        2. Route to the appropriate agent
        """
        state = self.classify_message(state)
        if state.message_type == "climate":
            return self.climate_agent(state)
        else:
            return self.risk_agent(state)


def run_chatbot():
    """
    Main loop: keep reading user input, updating state, and printing assistant responses.
    Type “exit” to quit.
    """
    # 1. Initialize Vector Store & Retriever
    embedding_fn = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectordb = Chroma(
        persist_directory=CLIMATE_CHROMA_DIR,
        embedding_function=embedding_fn
    )
    retriever = vectordb.as_retriever()

    # 2. Initialize State & Flow
    chatbot = ChatbotFlow(retriever=retriever)
    state = State()

    print("Climate Risk Assessment Chatbot (type 'exit' to quit)\n")
    while True:
        user_input = input("User: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("Assistant: Goodbye!")
            break

        # Append user message
        state.messages.append({"role": "user", "content": user_input})

        # Generate assistant response
        state = chatbot.invoke(state)

        # Print the last assistant message
        last_assistant = state.messages[-1]
        if last_assistant["role"] == "assistant":
            print(f"Assistant: {last_assistant['content']}\n")


if __name__ == "__main__":
    run_chatbot()
