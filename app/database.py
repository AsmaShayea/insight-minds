from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import logging
from .config import MONGO_URI  # Import MongoDB URI from config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database():
    """
    Create a new MongoDB client and connect to the server.
    Return the database object after successfully connecting.
    """
    try:
        client = MongoClient("mongodb+srv://asma:Sami8407@insightsmindscluster0.34evged.mongodb.net/?retryWrites=true&w=majority&appName=InsightsMindsCluster0", server_api=ServerApi('1'))
        client.admin.command('ping')  # Ping MongoDB to confirm a successful connection
        logger.info("Pinged your deployment. Successfully connected to MongoDB!")
        
        # Connect to the desired database
        db = client['insight_minds']
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return None

# Initialize collections
db = get_database()
if db is not None:
    reviews_collection = db['reviews']
    aspects_collection = db['aspects']
    business_collection = db['business']
    errors_log_collection = db['errors_log']
else:
    reviews_collection = None
    aspects_collection = None
    business_collection = None
    errors_log_collection = None

# Add MongoDB connection teardown
def close_database_connection():
    if db is not None:
        db.client.close()
        logger.info("Closed MongoDB connection.")
