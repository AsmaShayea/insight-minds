from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from a .env file

WATSON_CREDENTIALS = {
    "url": os.getenv("WATSON_URL"),
    "apikey": os.getenv("WATSON_API_KEY"),
}

PROJECT_ID = os.getenv("PROJECT_ID")

OUTSCRAPER_API_KEY = os.getenv("OUTSCRAPER_API_KEY")

MONGO_URI = os.getenv("MONGO_URI")
