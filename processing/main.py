from dotenv import load_dotenv
from typing import Literal
from pydantic import BaseModel, Field
import os
import urllib.request
import json

from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

# Vector store integration
from langchain_community.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

# Set parameters and credentials
parameters = {
    GenParams.DECODING_METHOD: "greedy",
    GenParams.MAX_NEW_TOKENS: 500,
    GenParams.TEMPERATURE: 0.7,
    GenParams.STOP_SEQUENCES: ["\n\n"]
}

credentials = {
    "url": os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
    "apikey": os.getenv("WATSONX_API_KEY")
}

model = ModelInference(
    model_id="meta-llama/llama-3-3-70b-instruct",
    params=parameters,
    credentials=credentials,
    project_id=os.getenv("WATSONX_PROJECT_ID")
)

# Initialize vector store
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = Chroma(
    persist_directory="processing/chroma_store",
    embedding_function=embedding_function
)
retriever = vector_store.as_retriever()

# Fetch weather forecast from Visual Crossing API
def get_climate_forecast(location="New York"):
    location_encoded = location.replace(" ", "%20")
    api_key = "3J9L4GZZVSM2782DZUSXL2NYD"
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location_encoded}?unitGroup=us&key={api_key}&contentType=json"
    
    try:
        result_bytes = urllib.request.urlopen(url)
        json_data = json.load(result_bytes)
        first_day = json_data.get("days", [{}])[0]
        forecast = f"Date: {first_day.get('datetime')}, Temp: {first_day.get('temp')}°F, Conditions: {first_day.get('conditions')}"
        return forecast
    except Exception as e:
        return f"Unable to fetch climate forecast: {e}"

class QueryClassifier(BaseModel):
    query_type: Literal["climate", "risk"] = Field(
        ..., description="Classify whether the user message requires real-time climate data or long-term risk analysis."
    )

class State:
    def __init__(self):
        self.messages = []
        self.message_type = None
        self.next = None
        self.forecast_data = None

class ChatbotFlow:
    def __init__(self):
        pass

    def classify_message(self, state):
        last_message = state.messages[-1]
        classification_prompt = f"""
Classify the user message as either:
- 'climate': if it asks about current or forecast weather.
- 'risk': if it asks about long-term climate threats to assets.

User message: {last_message['content']}
Classification:"""
        response = model.generate_text(prompt=classification_prompt)
        message_type = response.strip().lower()
        state.message_type = "climate" if "climate" in message_type else "risk"
        return state

    def router(self, state):
        if state.message_type == "climate":
            state.next = "climate_agent"
        else:
            state.next = "risk_agent"
        return state

    def climate_agent(self, state):
        forecast = get_climate_forecast()
        state.forecast_data = forecast

        prompt = f"""You are a weather assistant. The user is asking about climate conditions.
Forecast: {forecast}

User: {state.messages[-1]['content']}
Response:"""
        response = model.generate_text(prompt=prompt)
        state.messages.append({"role": "assistant", "content": response.strip()})
        return state

    def risk_agent(self, state):
        forecast = state.forecast_data or get_climate_forecast()
        user_query = state.messages[-1]['content']

        # Retrieve context from ChromaDB
        docs = retriever.get_relevant_documents(user_query)
        context = "\n\n".join([doc.page_content for doc in docs[:3]]) if docs else "No relevant context found."

        prompt = f"""You are a climate risk advisor.

Recent forecast data: {forecast}

Use the following relevant data extracted from trusted documents:
{context}

User question: {user_query}

Give a detailed risk assessment with references to both the forecast and retrieved data.
Response:"""

        response = model.generate_text(prompt=prompt)
        state.messages.append({"role": "assistant", "content": response.strip()})
        return state

    def invoke(self, state):
        state = self.classify_message(state)
        state = self.router(state)

        if state.next == "climate_agent":
            state = self.climate_agent(state)
        else:
            state = self.risk_agent(state)

        return state

def run_chatbot():
    chatbot = ChatbotFlow()
    state = State()

    while True:
        user_input = input("Message: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        state.messages.append({"role": "user", "content": user_input})
        state = chatbot.invoke(state)

        last_message = state.messages[-1]
        if last_message.get("role") == "assistant":
            print(f"AI: {last_message['content']}")

if __name__ == "__main__":
    run_chatbot()
