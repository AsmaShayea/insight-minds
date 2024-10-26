# File: app/vector_store_cache.py

from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from app.database import get_database
from datetime import datetime

class VectorStoreCache:
    _retriever = None
    _embeddings = None
    _last_update_time = None

    @classmethod
    def get_embeddings(cls):
        """Returns HuggingFace embeddings, cached after the first use."""
        if cls._embeddings is None:
            cls._embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/LaBSE")
        return cls._embeddings

    @classmethod
    def get_retriever(cls):
        """Returns the retriever for Chroma vector store, cached after first use, 
        and updates if new reviews are found."""
        if cls._retriever is None or cls._check_new_reviews():
            replies_data = cls._process_aspects()
            documents = [
                f"Review: {review['review_text']} Reply: {review['owner_answer']}" 
                for review in replies_data
            ]
            vector_store = Chroma.from_texts(documents, cls.get_embeddings())
            cls._retriever = vector_store.as_retriever()
        return cls._retriever

    @classmethod
    def _process_aspects(cls):
        """Fetches review data from the MongoDB collection."""
        reviews_collection = get_database()['reviews']
        return list(reviews_collection.find({"owner_answer": {"$exists": True, "$ne": "", "$type": "string"}}, {"_id": 0}))

    @classmethod
    def _check_new_reviews(cls):
        """Check if new reviews have been added to the collection."""
        reviews_collection = get_database()['reviews']

        # Fetch the latest review timestamp
        latest_review = reviews_collection.find_one(sort=[("review_datetime_utc", -1)])
        if not latest_review:
            return False

        latest_review_time = latest_review.get('review_datetime_utc', None)

        # If there's no previous update time, or the latest review is newer, refresh
        if cls._last_update_time is None or (latest_review_time and latest_review_time > cls._last_update_time):
            cls._last_update_time = latest_review_time  # Update the cache timestamp
            return True

        return False
