# import re
# from outscraper import ApiClient
# from .database import business_collection, reviews_collection, errors_log_collection
# from datetime import datetime
# from .config import OUTSCRAPER_API_KEY

# # Scraping data from Google Business
# api_client = ApiClient(api_key=OUTSCRAPER_API_KEY)

# def is_arabic(text):
#     """
#     Determine if the majority of characters in the text are Arabic.
#     """
#     arabic_count = len(re.findall(r'[\u0600-\u06FF]', text))
#     english_count = len(re.findall(r'[A-Za-z]', text))
#     return arabic_count > english_count

# def log_error(error_message):
#     """
#     Log error details to the errors_log collection.
#     """
#     if errors_log_collection:
#         error_data = {
#             "error_message": str(error_message),
#             "timestamp": datetime.utcnow()
#         }
#         errors_log_collection.insert_one(error_data)
#     else:
#         print("Failed to log error to the database.")

# def scrape_reviews():
#     """
#     Scrape Google reviews and save the data into MongoDB collections.
#     """
#     try:
#         results = api_client.google_maps_reviews(
#             'ChIJvQOWKnDpST4RYKCGnwam1GE', 
#             reviews_limit=100000, 
#             ignore_empty=True,
#             language='ar'
#         )

#         # Process each place in the results
#         for place in results:
#             # Check if the place already exists in the database by place_id
#             existing_business = business_collection.find_one({"place_id": place['place_id']})
#             reviews = place['reviews_data']

#             if not existing_business:
#                 # Insert new business into the database
#                 business_data = {
#                     "name": place['name'],
#                     "place_id": place['place_id'],
#                     "google_id": place['google_id'],
#                     "full_address": place['full_address'],
#                     "country": place['country'],
#                     "city": place['city'],
#                     "popular_times": place.get('popular_times', []),
#                     "logo": place['logo'],
#                     "description": place['description'],
#                     "category": place['category'],
#                     "type": place.get('type', ''),
#                     "subtypes": place.get('subtypes', []),
#                     "rating": place['rating'],
#                 }
#                 business_id = business_collection.insert_one(business_data).inserted_id
#                 print(f"Added business with place_id {place['place_id']} to the database.")
#             else:
#                 business_id = existing_business['_id']
#                 print(f"Business with place_id {place['place_id']} already exists in the database.")

#             # Process each review
#             for review in reviews:
#                 if is_arabic(review['review_text']):
#                     # Check if the review already exists in the database by review_id
#                     existing_review = reviews_collection.find_one({"review_id": review['review_id']})
#                     if not existing_review:
#                         review_data = {
#                             "review_id": review['review_id'],
#                             "business_id": str(business_id),
#                             "review_text": review['review_text'],
#                             "owner_answer": review.get('owner_answer', ''),
#                             "review_rating": review['review_rating'],
#                             "review_timestamp": review['review_timestamp'],
#                             "review_datetime_utc": review['review_datetime_utc'],
#                             "review_likes": review['review_likes'],
#                         }
#                         reviews_collection.insert_one(review_data)
#                         print(f"Added review with review_id {review['review_id']} to the database.")
#                     else:
#                         print(f"Review with review_id {review['review_id']} already exists in the database.")
#         return "Scraping and saving reviews completed."
#     except Exception as e:
#         log_error(e)
#         return "Scraping failed."
