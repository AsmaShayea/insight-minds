from fastapi import Body, FastAPI, HTTPException, BackgroundTasks
from time import sleep
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware
from fastapi.responses import JSONResponse
from bson.objectid import ObjectId
from pydantic import BaseModel
from .database import get_database
from .insights import getOveralSentiment, group_aspects_and_calculate_sentiments, get_top_aspects_and_opinions, get_aspect_counts_by_month
# from .pipelines.insights_extractions import generate_insights_text
from .pipelines.generate_reply import generate_reply, get_instance, correct_reply
from .processing_text import wrap_words_with_span
from .pipelines.extract_aspects import extract_save_aspects, handele_reviews_asepct_tags
from bson import ObjectId
import math
from typing import Optional
from .get_google_id import process_url

app = FastAPI()

# Add the CORS middleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from all domains
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

# Initialize database collections
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



#### 1- First API (Add new business data with scrape reviews from ggogle busines , extract aspect and opinions) Started
task_status = {}

#create busines accoint in db
def create_new_business():

    business_data = {
        "progress_status": "scrapping_reviews"
    }
    
    obj_business_id = business_collection.insert_one(business_data).inserted_id
    business_id = str(obj_business_id)

    
    return business_id

# do task at background
def background_task(business_id, google_id):

    task_status[business_id] = "running"
    try:
        # Extract aspects, polarity, opinions 
        extract_save_aspects(business_id, google_id)  

        print(f"Scraping for business {business_id}")
        task_status[business_id] = "completed"

    except Exception as e:

        task_status[business_id] = "failed"
        print(f"Error in task {business_id}: {e}")


# Start the background task
def start_task(background_tasks: BackgroundTasks, google_id: Optional[str] = None, url: Optional[str] = None):

    if not google_id:
        #extract gogle id from google map link
        google_id = process_url(url)

    existing_business = business_collection.find_one({"google_id": google_id})
    if existing_business:
        business_id = str(existing_business["_id"])  # Converts ObjectId to string

    else:
        business_id = create_new_business()

    background_tasks.add_task(background_task, business_id, google_id)
    return {"status": "started", "business_id":business_id,"message": f"Business {google_id} started scraping {url}"}


class BusinessRequest(BaseModel):
    google_id: Optional[str] = None
    url: Optional[str] = None

@app.post("/scrape-extract-aspects")
async def add_new_business(background_tasks: BackgroundTasks, request: BusinessRequest):

    response = start_task(background_tasks, request.google_id, request.url)
    return response

#### 1- First API (Add new business data with scrape reviews from ggogle busines , extract aspect and opinions) End



#### 2- Second API (Get all business list) Started

# Helper function to serialize ObjectId to string and show only specific fields
def serialize_business_data(business):
    return {
        "id": str(business["_id"]),  # Convert ObjectId to string
        "category": business.get("category"),
        "name": business.get("name"),
        "logo": business.get("logo"),
        "progress_status": business.get("progress_status"),
        "is_my_business": business.get("is_my_business")  # Include is_my_business
    }

@app.get("/get-business-data")
async def get_businesses_data():
    try:
        # Fetch only required fields from the business collection
        business_data = [
            serialize_business_data(business) 
            for business in business_collection.find({}, {"_id": 1, "category":1, "name": 1, "logo": 1, "progress_status": 1, "is_my_business": 1})
        ]

        if not business_data:
            raise HTTPException(status_code=404, detail="No businesses found")

        # Split data into "my_business" and "other_business" based on "is_my_business" value
        my_business = [business for business in business_data if business.get("is_my_business") == "true"]
        other_business = [business for business in business_data if business.get("is_my_business") != "true"]
        
        return {
            "progress_status": "active",
            "data": {
                "my_business": my_business,
                "other_business": other_business
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
#### Second API (Get all business list) End




#### 3- Third API (Get a business data and insights) Started
# Check business loading data status
def business_loading_status(business_id: str):

    business_data = business_collection.find_one({"_id": ObjectId(business_id)})


    if not business_data.get('progress_status'):
        raise HTTPException(status_code=404, detail="Business not found")

    if(business_data['progress_status'] == "completed"):
        progress_status = "active"
        progress_message =  "Request successful"
        progress_percentage = 100
        
    else:
        status = task_status.get(business_id, "not found")

        if(status == "failed"):

            progress_status = "error"
            progress_message =  "Task stopped for unrecognized error"
            progress_percentage = 0

        else:
            # Check if the task is completed
            total_reviews = reviews_collection.count_documents({"business_id": business_id}) + 1
            analyzed_reviews = reviews_collection.count_documents({"business_id": business_id,"is_analyzed": "true"})
        

            # Extracting the results
            if total_reviews > 0:
                progress_percentage = math.floor((analyzed_reviews / total_reviews) * 100)
            else:
                progress_percentage = 0

            progress_status = "in_progress"
            progress_message =  "data in progress and please chaek later"
            progress_percentage = progress_percentage

    return progress_status, progress_message, progress_percentage



# check if busines loadind is done, get all reviews and insight to show in dashboard
@app.get('/insights/{business_id}')
def getInsights(business_id: str):
    
    #check loaded statud that started at background is done
    progress_status, progress_message, progress_percentage = business_loading_status(business_id)
    data = None

    if(progress_status == "active"):
        data = {
            "overal_sentiment": getOveralSentiment(business_id),
            "most_popular_aspects": group_aspects_and_calculate_sentiments(business_id),
            "topicOpinions": get_top_aspects_and_opinions(business_id),
            "get_aspect_counts_by_month": get_aspect_counts_by_month(business_id),
            "overall_review_tone": { ##Future Work
                "Happy": 20,
                "Angry": 10,
                "Satisfied": 30,
                "Disappointed": 10,
                "Excited": 30
            },
            "get_category_sentiment": [ ##Future Work
                {"category": "Product", "positive": 50, "negative": 50},
                {"category": "Service", "positive": 80, "negative": 20},
                {"category": "Place", "positive": 90, "negative": 10},
                {"category": "Price", "positive": 30, "negative": 70}
            ]
        }

    result = JSONResponse(content={
        "status": 200,
        "progress_status": progress_status,
        "message": progress_message,
        "progress_percentage" : progress_percentage,
        "data": data
    })
    return result
#### Third API (Get a business data and insights) End


#### 4- Fourth API (Get all business reviews) Started
@app.get('/reviews/{business_id}')
def get_reviews(business_id: str):
    # Get business details
    business = business_collection.find_one({"_id": ObjectId(business_id)})
    if not business:
        return {"error": business_id}
    
    # Get reviews for the business (limit to 50 reviews - for test)
    reviews = list(reviews_collection.find({"business_id": business_id}).limit(50))

    positive_reviews = []
    negative_reviews = []
    neutral_reviews = []

    for review in reviews:
        # Get all aspects for the review
        aspects = list(aspects_collection.find({"review_id": review['review_id']}))
        review_text = review['review_text']
        aspect_details = []
        
        for aspect in aspects:
            aspect_str = aspect['aspect']
            polarity_score = aspect['polarity_score']
            polarity = aspect['polarity']

         

            # Show just positive and negative aspects
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
            "clean_review_text": review.get('review_text', ""),          # Default to empty string if not found
            "review_text": review.get('review_aspects_text', ""),
            "owner_reply": review.get('owner_answer', ""),                # Handle missing 'owner_reply'
            "rating": rating,
            "name": review.get('author_name', "Anonymous"),              # Default name if missing
            "image": review.get('author_logo', "https://i.ibb.co/0Bsq8MC/user-image.png"),   
            "date": review.get('review_datetime_utc', None),             # None if date is missing
            "review_type": review_type,
            "tokenized_review": review.get('tokenized_review', []),      # Default to empty list if missing
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
#### Fourth API (Get all business reviews) End


#### 5- Fifth API (Generate a reply for a review) Started
@app.get("/get-reply/{review_id}")
async def get_reply(review_id: str):
    try:
        reply = generate_reply(review_id)
        if reply:
            return {"reply": reply}
        else:
            raise HTTPException(status_code=404, detail="Review not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
#### Fifth API (Generate a reply for a review) End


#### 6- Sixth API (Correct current review) Started
# Define a Pydantic model for the input
class ReplyRequest(BaseModel):
    reply_text: str
    
@app.post("/correct-reply")
async def correct_reply_endpoint(request: ReplyRequest):
    """Endpoint to correct a business owner's reply."""
    corrected_reply = correct_reply(request.reply_text)  # Access reply_text from the Pydantic model
    return {"corrected_reply": corrected_reply}
#### Sixth API (Correct current review) End


#### Seventh API (Get Text Summary insights, recommendation, ideas) Started
@app.get("/generate-text-insights/{business_id}")
async def generate_insights(business_id: str):
    """
    Endpoint to run the pipeline for generating business insights.
    """
    insights_collection = get_database()['insights']  # Ensure this references the correct collection

    # Fetch the insights document if it is already exists
    insights = insights_collection.find_one({"business_id": business_id})

    # if insights is None:
    #     print("No insights found for the given business ID.")
    #     try:
    #         # Generate and insert insights data if none exist
    #         generate_insights_text(business_id)
    #         # Re-fetch the inserted insights document to get the _id
    #         insights = insights_collection.find_one({"business_id": business_id})

    #         if insights is None:
    #             return {"status": "error", "message": "Failed to insert or retrieve new insights."}

    #     except Exception as e:
    #         return {"status": "error", "message": str(e)}


    # Format the response with headings
    extracted_data = {
        "summary": "<h3><strong>ملخص تجربة العملاء</strong></h3>" + insights['data']['summary'].strip().replace('\n', '<br>'),
        "recommendations": "<h3><strong>توصيات</strong></h3>" + insights['data']['recommendations'].strip().replace('\n', '<br>'),
        "ideas": "<h3><strong>أفكار مبتكرة</strong></h3>" + insights['data']['ideas'].strip().replace('\n', '<br>')
    }

    # Return the response with insights_id and business_id
    return {
        "status": "success", 
        "insights_id": str(insights['_id']),  # Convert ObjectId to string for JSON serialization
        "business_id": insights['business_id'],
        "data": extracted_data
    }
#### Seventh API (Get Text Summary insights) End
