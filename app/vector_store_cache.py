from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from app.database import get_database
from datetime import datetime

class VectorStoreCache:
    _retrievers = {}  # Dictionary to store retrievers by business_id
    _last_update_times = {}  # Dictionary to store the last update times by business_id
    _embeddings = None  # Shared embeddings instance across all business_ids
    _documents_cache = {}  # Dictionary to store documents by business_id


    @classmethod
    def clear_cache_for_business(cls, business_id):
        """Clear the cache for a specific business_id."""
        if business_id in cls._retrievers:
            del cls._retrievers[business_id]
        if business_id in cls._documents_cache:
            del cls._documents_cache[business_id]
        if business_id in cls._last_update_times:
            del cls._last_update_times[business_id]
        print(f"Cache cleared for business_id: {business_id}")

    @classmethod
    def clear_all_cache(cls):
        """Clear all cached retrievers, documents, and update times."""
        cls._retrievers.clear()
        cls._documents_cache.clear()
        cls._last_update_times.clear()
        print("All cache cleared")

    @classmethod
    def get_embeddings(cls):
        """Returns HuggingFace embeddings, cached after the first use."""
        if cls._embeddings is None:
            cls._embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/LaBSE")
        return cls._embeddings

    @classmethod
    def get_retriever(cls, business_id, process):
        print("get us iddddddddd1111")
        """Returns the retriever for Chroma vector store, cached per business_id, and updates if new reviews are found."""
        if business_id not in cls._retrievers or cls._check_new_reviews(business_id):
            print("get us iddddddddd222",process)
            # Fetch documents based on the process and business_id
            if process == "generate_reply":
                print("get us iddddddddd33")
                replies_data = cls._process_owner_reply(business_id)
                print("get us iddddddddd555")
                print("replies_data",replies_data)
                documents = [
                    f"Review: {review['review_text']} Reply: {review['owner_answer']}" 
                    for review in replies_data
                ]
                print("documents",documents)
            elif process == "text_summary":
                VectorStoreCache.clear_cache_for_business(business_id)
                retrieved_data = cls._process_aspect_summary(business_id)
                print("retrieved_data", retrieved_data)
                documents = [
                    f"Aspect: {data['aspect']}\nSentiment: {data['sentiment']}\nOpinions: {', '.join(data['all_opinions'])}" 
                    for data in retrieved_data
                ]

            print("documents", documents)
            # Create a new Chroma vector store with the documents for this business_id
            vector_store = Chroma.from_texts(documents, cls.get_embeddings())
            cls._retrievers[business_id] = vector_store.as_retriever()  # Cache the retriever for this business_id
        return cls._retrievers[business_id]

    @classmethod
    def _process_owner_reply(cls, business_id):
        """Fetches review data for a specific business_id from the MongoDB collection."""
        reviews_collection = get_database()['reviews']
        print("review123")
        return list(reviews_collection.find(
            {"business_id": business_id, "owner_answer": {"$exists": True, "$ne": "", "$type": "string"}},
            {"_id": 0}
        ))

    @classmethod
    def _process_aspect_summary(cls, business_id):
        """Fetch common aspects and opinions for a specific business_id."""
        common_aspects = cls._get_common_aspects_and_reviews(business_id)
        positive_aspects = [entry for entry in common_aspects if entry['_id']['polarity'] == 'positive'][:3]
        negative_aspects = [entry for entry in common_aspects if entry['_id']['polarity'] == 'negative'][:3]

        retrieved_data = []
        for aspect_entry in positive_aspects + negative_aspects:
            aspect = aspect_entry['_id']['aspect']
            root_aspect = aspect_entry['_id']['root_aspect']
            sentiment = aspect_entry['_id']['polarity']
            all_opinions = aspect_entry['all_opinions']
            flattened_opinions = [opinion for sublist in all_opinions for opinion in sublist]

            retrieved_data.append({
                'aspect': aspect,
                'root_aspect': root_aspect,
                'sentiment': sentiment,
                'count': aspect_entry['count'],
                'all_opinions': flattened_opinions,
            })
        return retrieved_data

    @classmethod
    def _get_common_aspects_and_reviews(cls, business_id):
        """Aggregate common aspects for a specific business_id."""
        aspects_collection = get_database()['aspects']
        pipeline = [
            {"$match": {"business_id": business_id}},  # Filter by business_id
            {"$group": {
                "_id": {"aspect": "$aspect", "root_aspect": "$root_aspect", "polarity": "$polarity"},
                "count": {"$sum": 1},
                "all_opinions": {"$push": "$opinions"}
            }},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1}}
        ]
        return list(aspects_collection.aggregate(pipeline))

    @classmethod
    def _check_new_reviews(cls, business_id):
        """Check if new reviews have been added for a specific business_id."""
        reviews_collection = get_database()['reviews']
        latest_review = reviews_collection.find_one({"business_id": business_id}, sort=[("review_datetime_utc", -1)])
        if not latest_review:
            return False

        latest_review_time = latest_review.get('review_datetime_utc', None)
        if business_id not in cls._last_update_times or (latest_review_time and latest_review_time > cls._last_update_times[business_id]):
            cls._last_update_times[business_id] = latest_review_time
            return True

        return False
