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
    def get_retriever(cls, documents):
        """Returns the retriever for Chroma vector store, cached after first use, 
        and updates if new reviews are found."""
        ##
        # if cls._retriever is None or cls._check_new_reviews():

            # if(process == "generate_reply"):
            #     replies_data = cls._process_owner_reply()
            #     documents = [
            #         f"Review: {review['review_text']} Reply: {review['owner_answer']}" 
            #         for review in replies_data
            #     ]
            # elif(process == "text_summary"):
            #     # retrieved_data = cls._process_aspect_summary()
            #     documents = [
            #         f"Aspect: {data['aspect']}\nSentiment: {data['sentiment']}\nOpinions: {', '.join(data['all_opinions'])}" 
            #         for data in retrieved_data
            #     ]

        vector_store = Chroma.from_texts(documents, cls.get_embeddings())
        cls._retriever = vector_store.as_retriever()
        return cls._retriever

    # @classmethod
    # def _process_owner_reply(cls):
    #     """Fetches review data from the MongoDB collection."""
    #     reviews_collection = get_database()['reviews']
    #     return list(reviews_collection.find({"owner_answer": {"$exists": True, "$ne": "", "$type": "string"}}, {"_id": 0}))
    

    # # Get the most common positive and negative aspects separately, along with their sentiment and associated reviews
    # def _get_common_aspects_and_reviews():
    #     aspects_collection = get_database()['aspects']
    #     # Step 1: Find aspects that are repeated more than 3 times, grouped by aspect, root_aspect, and polarity
    #     pipeline = [
    #         {"$group": {
    #             "_id": {"aspect": "$aspect", "root_aspect": "$root_aspect", "polarity": "$polarity"},  # Group by aspect, root_aspect, and polarity
    #             "count": {"$sum": 1},  # Count occurrences
    #             "all_opinions": {"$push": "$opinions"}  # Collect associated opinions into an array
    #         }},
    #         {"$match": {"count": {"$gt": 3}}},  # Keep only aspects mentioned more than 3 times
    #         {"$sort": {"count": -1}}  # Sort by count in descending order
    #     ]
    #     common_aspects = list(aspects_collection.aggregate(pipeline))
    
    #     return common_aspects

    # @classmethod
    # def _process_aspect_summary(cls):
    #     common_aspects = cls._get_common_aspects_and_reviews()
    #     positive_aspects = [entry for entry in common_aspects if entry['_id']['polarity'] == 'positive'][:3]  # Top 3 positive aspects
    #     negative_aspects = [entry for entry in common_aspects if entry['_id']['polarity'] == 'negative'][:3]  # Top 3 negative aspects

    #     retrieved_data = []
    #     for aspect_entry in positive_aspects + negative_aspects:
    #         aspect = aspect_entry['_id']['aspect']
    #         root_aspect = aspect_entry['_id']['root_aspect']  # Retrieve root_aspect
    #         sentiment = aspect_entry['_id']['polarity']
    #         all_opinions = aspect_entry['all_opinions']  # Get all collected opinions arrays
            
    #         # Flatten the list of lists for opinions (since opinions are stored as arrays within arrays)
    #         flattened_opinions = [opinion for sublist in all_opinions for opinion in sublist]
            
    #         # Add to the final retrieved data structure
    #         retrieved_data.append({
    #             'aspect': aspect,
    #             'root_aspect': root_aspect,
    #             'sentiment': sentiment,
    #             'count': aspect_entry['count'],  # Add the count of the aspect
    #             'all_opinions': flattened_opinions,  # Store all consolidated opinions in the final structure
    #         })
    #     return retrieved_data


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
