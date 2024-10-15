from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware
from fastapi.responses import JSONResponse
from bson.objectid import ObjectId
from .database import get_database
from .insights import getOveralSentiment, group_aspects_and_calculate_sentiments, get_top_aspects_and_opinions, get_aspect_counts_by_month
from .pipelines.insights_extractions import generate_insights_text
from .pipelines.generate_reply import generate_reply
from .global_methods import wrap_words_with_span
app = FastAPI()

# Define the origins that are allowed to make requests to your API
origins = [
    "https://blogapp556.herokuapp.com",  # Your Next.js app's domain
    "http://localhost:3000",  # Local development domain for Next.js
]

# Add the CORS middleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows requests from specified domains
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

from bson import ObjectId

def serialize_doc(doc):
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, dict):
        return {k: serialize_doc(v) for k, v in doc.items()}
    return doc

# Initialize collections
db = get_database()
if db is not None:
    reviews_collection = db['reviews']
    aspects_collection = db['aspects']
    business_collection = db['business']
    insights_collection = db['insights']
    errors_log_collection = db['errors_log']
else:
    reviews_collection = None
    aspects_collection = None
    business_collection = None
    insights_collection = None
    errors_log_collection = None

# Sample root endpoint
@app.get("/")
def read_root():
    return {"Hello": "World13"}


# Get reply
@app.get("/get-reply/{review_id}")
async def get_reply(review_id: str):
    reply = generate_reply(review_id)
    return {"reply": reply}
    

@app.get("/generate-text-insights/{business_id}")
async def generate_insights(business_id: str):
    """
    Endpoint to run the pipeline for generating business insights.
    """
    try:
        response = generate_insights_text(business_id)  # Call the run_pipeline function
        return {"status": "success", "data": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}


#get insights
@app.get("/get-last-insight")
async def get_latest_insights():
    # Get the last document based on the extraction_date
    last_document = insights_collection.find().limit(1)
    
    # Convert the cursor to a list and check if there's a document
    last_insight = list(last_document)
    
    if last_insight:
        return {
            "id" : str(last_insight[0]['_id']),
            "data": last_insight[0]['data']
        }
    
    return JSONResponse(content={"message": "No insights found."}, status_code=404)

#get insights
@app.get("/get-business-details/{business_id}")
async def get_business_details(business_id):
    # Get the last document based on the extraction_date
    business_data = business_collection.find_one({"_id": ObjectId(business_id)})
    
    # Convert the cursor to a list and check if there's a document
    
    return {
        "id" : str(business_data['_id']),
        "name": business_data['name'],
        "full_address": business_data['full_address'],
        "city": business_data['city'],
        "description": business_data['description'],
        "logo": business_data['logo'],
        "category": business_data['category'],
        "type": business_data['type'],
        "subtypes": business_data['subtypes']

    }
    

# Get All Reviews
@app.get('/reviews/{business_id}')
def get_reviews(business_id: str):
    # Get business details
    business = business_collection.find_one({"_id": ObjectId(business_id)})
    if not business:
        return {"error": "Business not found"}
    
    # Get reviews for the business (limit to 50 reviews)
    reviews = list(reviews_collection.find({"business_id": business_id}).limit(50))

    # Initialize arrays for different review types
    positive_reviews = []
    negative_reviews = []
    neutral_reviews = []

    for review in reviews:
        # Get aspects for the review
        aspects = list(aspects_collection.find({"review_id": review['review_id']}))
        review_text = review['review_text']
        aspect_details = []
        
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
                highlighted_aspect = aspect_str

            # Replace the aspect in the review text
            review_text = review_text.replace(aspect_str, highlighted_aspect)

            # Add the aspect details to the list
            if polarity in ["positive", "negative"]:
                aspect_details.append({
                    "aspect": aspect_str,
                    "polarity_score": polarity_score,
                    "polarity": polarity
                })

        # Classify the review based on its rating
        rating = review['review_rating']
        if rating >= 4:
            review_type = 'Positive'
        elif rating == 3:
            review_type = 'Neutral'
        else:
            review_type = 'Negative'

        review_data = {
            "id": str(review['_id']),
            "review_text": review_text,
            "rating": rating,
            "name": review['author_name'],
            "logo": review['author_logo'],
            "image": "https://i.ibb.co/0Bsq8MC/user-image.png",
            "date": review['review_datetime_utc'],
            "review_type": review_type,
            "tokenized_review": wrap_words_with_span(review_text),
            "aspects": aspect_details
        }

        if review_type == 'Positive':
            positive_reviews.append(review_data)
        elif review_type == 'Negative':
            negative_reviews.append(review_data)
        else:
            neutral_reviews.append(review_data)

    result = JSONResponse(content={
        "status": 200,
        "message": "Request successful",
        "data": {
            "positive_reviews": positive_reviews[:10],  # Max 10 positive reviews
            "negative_reviews": negative_reviews[:10],  # Max 10 negative reviews
            "neutral_reviews": neutral_reviews[:10]     # Max 10 neutral reviews
        }
    })
    return result

@app.get('/insights/{business_id}')
def getInsights():
    result = JSONResponse(content={
        "status": 200,
        "message": "Request successful",
        "data": {
            "overal_sentiment": getOveralSentiment(),
            "most_popular_aspects": group_aspects_and_calculate_sentiments(),
            "topicOpinions": get_top_aspects_and_opinions(),
            "get_aspect_counts_by_month": get_aspect_counts_by_month(),
            "overall_review_tone": {
                "Happy": 20,
                "Angry": 10,
                "Satisfied": 30,
                "Disappointed": 10,
                "Excited": 30
            },
            "get_category_sentiment": [
                {"category": "Product", "positive": 50, "negative": 50},
                {"category": "Service", "positive": 80, "negative": 20},
                {"category": "Place", "positive": 90, "negative": 10},
                {"category": "Price", "positive": 30, "negative": 70}
            ]
        }
    })
    return result



#Realtime Scrape & get insights
# Sample scrape reviews endpoint
@app.get("/scrape-reviews")
def scrape_google_reviews():
    return {"Hello": "World15"}
