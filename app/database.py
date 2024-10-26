from pymongo import MongoClient
from pymongo.server_api import ServerApi
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB client at the global level to reuse it
client = MongoClient(
    "mongodb+srv://asma:Sami8407@insightsmindscluster0.34evged.mongodb.net/?retryWrites=true&w=majority&appName=InsightsMindsCluster0",
    server_api=ServerApi('1'),
    maxPoolSize=50,   # Pool size to handle multiple requests
    minPoolSize=10,   # Maintain some connections ready
    socketTimeoutMS=5000
)

def get_database():
    """
    Return the MongoDB database object after successfully connecting.
    """
    try:
        # Ping MongoDB to confirm connection
        client.admin.command('ping')
        logger.info("Pinged your deployment. Successfully connected to MongoDB!")
        
        # Return the connected database
        db = client['insight_minds']
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return None

# Close MongoDB connection
def close_database_connection():
    if client is not None:
        client.close()
        logger.info("Closed MongoDB connection.")
