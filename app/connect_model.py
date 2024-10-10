import json
from ibm_watson_machine_learning.foundation_models import Model
from .config import WATSON_CREDENTIALS, PROJECT_ID  # Import credentials

def pretty(data):
    return json.dumps(data, indent=4)

model_id = "sdaia/allam-1-13b-instruct"

# Load the model with error handling
try:
    model = Model(model_id, WATSON_CREDENTIALS, {
        "DECODING_METHOD": "greedy",
        "MIN_NEW_TOKENS": 1,
        "MAX_NEW_TOKENS": 1536
    }, PROJECT_ID)
except Exception as e:
    print(f"Error loading model: {e}")
