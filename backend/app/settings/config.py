import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    WATSONX_APIKEY = os.getenv("WATSONX_AI_API", "")
    WATSONX_PROJECT_ID = os.getenv("PROJECT_ID", "")
    SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
    CLIMATE_DB_DIR = ".../vector_store/climate_chroma_db"
    BUSINESS_DB_DIR = ".../vector_store/risk_chroma_db"
