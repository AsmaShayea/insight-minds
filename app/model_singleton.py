# File: app/model_singleton.py

from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.foundation_models.extensions.langchain import WatsonxLLM
import os

class ModelSingleton:
    _instance = None
    _model = None

    @staticmethod
    def get_instance():
        """Returns the singleton instance of the WatsonxLLM model."""
        if ModelSingleton._instance is None:
            model = ModelSingleton.get_model()
            ModelSingleton._instance = WatsonxLLM(model=model)
        
        return ModelSingleton._instance

    @staticmethod
    def get_model():
        """Returns the model object, initializing it if necessary."""
        if ModelSingleton._model is None:
            model_id = "sdaia/allam-1-13b-instruct"
            credentials = { 
                "url": os.getenv("WATSONX_URL", "https://eu-de.ml.cloud.ibm.com"), 
                "apikey": os.getenv("WATSONX_APIKEY", "Zrf8P_lX5EMBsrySSLlEmTRnIZZgZYfTeBreQ-aG43kD")
            }
            gen_parms = { 
                "DECODING_METHOD": "greedy", 
                "MIN_NEW_TOKENS": 1, 
                "MAX_NEW_TOKENS": 1500
            }
            project_id = os.getenv("WATSONX_PROJECT_ID", "94747490-17e0-4527-b930-c84d83e45349")
            
            # Initialize the model
            ModelSingleton._model = Model(model_id, credentials, gen_parms, project_id)
        
        return ModelSingleton._model

    @staticmethod
    def reset_instance():
        """Allows resetting the model or WatsonxLLM instance (if needed for reinitialization)."""
        ModelSingleton._instance = None
        ModelSingleton._model = None
