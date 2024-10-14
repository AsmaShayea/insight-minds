from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.foundation_models.extensions.langchain import WatsonxLLM

class ModelSingleton:
    _instance = None

    @staticmethod
    def get_instance():
        if ModelSingleton._instance is None:
            model_id = "sdaia/allam-1-13b-instruct"
            credentials = { 
                "url": "https://eu-de.ml.cloud.ibm.com", 
                "apikey": "ltqRXYdJ4roJXzlXAoAkQpoX1HcNbTcrtLOUljZW3PBf"
            }
            gen_parms = { 
                "DECODING_METHOD": "greedy", 
                "MIN_NEW_TOKENS": 1, 
                "MAX_NEW_TOKENS": 1500
            }
            project_id = "f140f90d-331a-4c84-b266-c701f3525ea8"
            
            model = Model(model_id, credentials, gen_parms, project_id)
            ModelSingleton._instance = WatsonxLLM(model=model)
        
        return ModelSingleton._instance
