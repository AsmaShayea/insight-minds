from fastapi import FastAPI
# from .scraping_service import scrape_reviews
from .database import get_database
from fastapi.responses import JSONResponse
from bson.objectid import ObjectId
from .insights import getOveralSentiment, group_aspects_and_calculate_sentiments, get_top_aspects_and_opinions, get_aspect_counts_by_month
from fastapi import BackgroundTasks

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World13"}

@app.get("/scrape-reviews")
def scrape_google_reviews():
    return {"Hello": "World15"}
    # try:
    #     result = scrape_reviews()
    #     return {"status": "success", "data": result}
    # except Exception as e:
    #     return {"status": "error", "message": str(e)}


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





#### Get All Reviews
business_id = "66eb726e1b898c92f06c243f"
#/reviews/66eb726e1b898c92f06c243f
@app.get('/reviews/{business_id}')
async def get_reviews(business_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(long_running_task, business_id)  # Add the long-running task
    return {"message": "Your request is being processed, please check back later."}

def get_relong_running_taskviews(business_id: str):
    # Get business details
    business = business_collection.find_one({"_id": ObjectId(business_id)})

    if not business:
        return {"error": "Business not found"}
    
    # Get reviews for the business
    reviews = list(reviews_collection.find({"business_id": business_id}))


    # Initialize separate arrays for positive, negative, and neutral reviews
    positive_reviews = []
    negative_reviews = []
    neutral_reviews = []

    for review in reviews:
       # Get aspects for the review
        aspects = list(aspects_collection.find({"review_id": review['review_id']}))

        # Prepare the review text with highlighted aspects
        review_text = review['review_text']
        aspect_details = []  # To store aspects and their polarities
        
        for aspect in aspects:
            aspect_str = aspect['aspect']
            polarity_score = aspect['polarity_score']
            polarity = aspect['polarity']

            # Color-code the aspects
            if polarity == 'positive':
                highlighted_aspect = f"<span style='color: green;'>{aspect_str}</span>"
            elif polarity == 'negative':
                highlighted_aspect = f"<span style='color: red;'>{aspect_str}</span>"
            else:
                highlighted_aspect = aspect_str  # Neutral or unspecified polarity

            # Replace the aspect in the review text with the highlighted version
            review_text = review_text.replace(aspect_str, highlighted_aspect)

            if polarity == "positive" or polarity == "negative":
                aspect_details.append({
                    "aspect": aspect_str,
                    "polarity_score": polarity_score,
                    "polarity": polarity
                })

        # Classify the review rating
        rating = review['review_rating']
        if rating >= 4:
            review_type = 'Positive'
        elif rating == 3:
            review_type = 'Neutral'
        else:
            review_type = 'Negative'

        # Prepare the review data
        review_data = {
            "review_text": review_text,  # Use the modified review text
            "rating": rating,
            "name": business['name'],
            "date": review['review_datetime_utc'],
            "review_type": review_type,
            "aspects": aspect_details  # Include aspects and their polarities
        }


        # Append to the appropriate list based on review_type
        if review_type == 'Positive':
            positive_reviews.append(review_data)
        elif review_type == 'Negative':
            negative_reviews.append(review_data)
        else:
            neutral_reviews.append(review_data)

        # Prepare the final response with the separated reviews
        result = JSONResponse(content={
            "status": 200,
            "message": "Request successful",
            "data": {
                "positive_reviews": positive_reviews,
                "negative_reviews": negative_reviews,
                "neutral_reviews": neutral_reviews
            }
        })

    return result


@app.get('/insights/66eb726e1b898c92f06c243f')
def getInsights():
    # Prepare the final response with the separated reviews
    result = JSONResponse(content={
        "status": 200,
        "message": "Request successful",
        "data": {
            "overal_sentiment": getOveralSentiment(),
            "most_popular_aspects": group_aspects_and_calculate_sentiments(),
            "topicOpinions": get_top_aspects_and_opinions(),
            "get_aspect_counts_by_month": get_aspect_counts_by_month(),
            "overall_review_tone": {
                "Happy":"20",
                "Angry":"10",
                "Satisfied":"30",
                "Disappointed":"10",
                "Excited":"30"
                },
            "get_category_sentiment": [
                {
                    "category": "Product",
                    "positive": "50%",
                    "negative": "50%"
                },
                {
                    "category": "Service",
                    "positive": "80%",
                    "negative": "20%"
                },
                {
                    "category": "Place",
                    "positive": "90%",
                    "negative": "10%"
                },
                {
                    "category": "Price",
                    "positive": "30%",
                    "negative": "70%"
                },
            ]
        }
    })

    return result
