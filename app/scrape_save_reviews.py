from .database import get_database
from .get_google_id import process_url
from outscraper import ApiClient
from bson.objectid import ObjectId
import re

#scrapping data from google business
api_client = ApiClient(api_key='YWNhNDdkZWJmNzg0NDdiM2EzZDFkZDMxNmZlNDFkMDV8NDBjZGIwMGU4MA')

# Initialize collections
reviews_collection = get_database()['reviews']
aspects_collection = get_database()['aspects']
business_collection = get_database()['business']
insights_collection = get_database()['insights']
errors_log_collection = get_database()['errors_log']


def is_arabic(text):
    # Count Arabic characters
    arabic_count = len(re.findall(r'[\u0600-\u06FF]', text))
    
    # Count English characters (A-Z, a-z)
    english_count = len(re.findall(r'[A-Za-z]', text))
    
    # Check if the text is predominantly Arabic
    if arabic_count > english_count:
        return True
    else:
        return False

def create_new_business():

    business_data = {
        "progress_status": "scrapping_reviews"
    }
    
    business_id = business_collection.insert_one(business_data).inserted_id

    
    return business_id

def scrape_reviews(business_id, url):
    google_id = process_url(url)
    # Scraping Google reviews using the business name and location
    results = api_client.google_maps_reviews(google_id, 
        reviews_limit=5000, 
        ignore_empty=True,
        language='ar'
    )


    # Save business and reviews data into DB
    for place in results:
        # Check if the place already exists in the database by place_id
        existing_business = business_collection.find_one({"google_id": place['google_id']})
        reviews = place['reviews_data']
        
        if not existing_business:

            # If the place doesn't exist, insert it into the database
            business_data = {
                "name": place['name'],
                "place_id": place['place_id'],
                "google_id": place['google_id'],
                "full_address": place['full_address'],
                "country": place['country'],
                "city": place['city'],
                "popular_times": place['popular_times'],
                "logo": place['logo'],
                "description": place['description'],
                "category": place['category'],
                "type": place['type'],
                "subtypes": place['subtypes'],
                "rating": place['rating'],
                "progress_status": "scrapping_reviews",
            }
            # Update the document with a matching place_id
            business_collection.update_one(
                {"_id": ObjectId(business_id)},  # Filter to match the document
                {"$set": business_data},  # Update the document with new data
                upsert=True  # If the document doesn't exist, insert it
            )
            print(f"Added business with business_id {business_id} to the database.")

            
            for review in reviews:

                if is_arabic(review['review_text']):
                    # Check if the place already exists in the database by place_id
                    existing_review = reviews_collection.find_one({"review_id": review['review_id']})
            
                    if not existing_review:
                        review_data = {
                            "review_id": review['review_id'],
                            "business_id": str(business_id),
                            "review_text": review['review_text'],
                            "owner_answer": review['owner_answer'],
                            "review_rating": review['review_rating'],
                            "review_timestamp": review['review_timestamp'],
                            "review_datetime_utc": review['review_datetime_utc'],
                            "review_likes": review['review_likes'],
                            "is_analyzed": "false",
                        }
                        
                        review_id = reviews_collection.insert_one(review_data).inserted_id
                        print(f"Added review with review_id {review['review_id']} to the database.")
                    else:
                        print(f"Review with review_id {review['review_id']} already exists in the database.")

            business_collection.update_one(
                {"_id": ObjectId(business_id)},  # Filter by _id or use other unique field
                {"$set": {"progress_status": "reviews_scrapped_successfully"}}  # Set the new progress status
            )
        
        else:
            print(f"Business with google_id {place['google_id']} already exists in the database.")
            business_id = existing_business['_id']
            print(business_id)

    return business_id

