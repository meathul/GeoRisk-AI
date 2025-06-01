import os
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from ..settings.config import Config

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
