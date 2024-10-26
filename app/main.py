from fastapi import Body, FastAPI, HTTPException, BackgroundTasks
from time import sleep
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware
from fastapi.responses import JSONResponse
from bson.objectid import ObjectId
from .database import get_database
from .insights import getOveralSentiment, group_aspects_and_calculate_sentiments, get_top_aspects_and_opinions, get_aspect_counts_by_month
from .pipelines.insights_extractions import generate_insights_text
from .pipelines.generate_reply import generate_reply, get_instance, correct_reply
from .processing_text import wrap_words_with_span
from .pipelines.extract_aspects import extract_save_aspects, handele_reviews_asepct_tags
from bson import ObjectId
from .scrape_save_reviews import create_new_business
import math
from typing import Optional

app = FastAPI()

# Define the origins that are allowed to make requests to your API
origins = [
    "https://blogapp556.herokuapp.com",  # Your Next.js app's domain
    "http://localhost:3000",  # Local development domain for Next.js
    "http://16.171.196.223:3000",
    "http://insights-mind-7646dfe71e1b.herokuapp.com",
]

# Add the CORS middleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from specified domains
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

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


task_status = {}

# Define your background task function
def background_task(business_id: str, url: Optional[str] = None):

    task_status[business_id] = "running"
    try:

        extract_save_aspects(business_id, url)  # Simulate a long-running task

        # Simulate a background task (e.g., scraping)
        print(f"Scraping {url} for business {business_id}")
        task_status[business_id] = "completed"

    except Exception as e:
        # Mark task as failed if an error occurs
        task_status[business_id] = "failed"
        print(f"Error in task {business_id}: {e}")

# Endpoint to start the background task
@app.post("/scrape-extract-aspects")
async def start_task(background_tasks: BackgroundTasks, url: Optional[str] = None):
    business_id = create_new_business()  # Simulate creating a new business
   
    # Start the background task
    background_tasks.add_task(background_task, business_id, url)
    
    # Return immediate response
    return {"message": f"Business {business_id} started scraping {url}"}

# Endpoint to start the background task
@app.post("/scrape-extract-aspects/{business_id}")
async def complete_task(background_tasks: BackgroundTasks, business_id: str, url: Optional[str] = None):
    # Start the background task
    background_tasks.add_task(background_task, business_id, url)
    
    # Return immediate response
    return {"message": f"Business {business_id} started scraping {url}"}

# Endpoint to check task status
@app.get("/get-business-data/{business_id}")
async def get_business_data(business_id: str):

    business_data = business_collection.find_one({"_id": ObjectId(business_id)})

    if not business_data.get('progress_status'):
        raise HTTPException(status_code=404, detail="Business not found")
    
    if(business_data['progress_status'] == "completed"):

        return {
            "progress_status": "active",
            "business_data": {
                "id": str(business_data["_id"]),  # Convert ObjectId to string
                "category": business_data['category'],
                "name": business_data['name'],
                "logo": business_data['logo'],
                "progress_status": business_data['progress_status']
            }
        }

    else:

        status = task_status.get(business_id, "not found")

        if(status == "failed"):
            return {
                "progress_status": "error",
                "message": "Task stopped for unrecognized error",
                "progress_percentage": 0
            }

        else:
            # Check if the task is completed
            total_reviews = reviews_collection.count_documents({"business_id": business_id})
            analyzed_reviews = reviews_collection.count_documents({"business_id": business_id,"is_analyzed": "true"})
        

            # Extracting the results
            if total_reviews > 0:
                progress_percentage = math.floor((analyzed_reviews / total_reviews) * 100)
            else:
                progress_percentage = 0


            return {
                "progress_status": "in_progress",
                "message": "",
                "progress_percentage": progress_percentage
            }


# Helper function to serialize ObjectId to string and show only specific fields
def serialize_business_data(business):
    return {
        "id": str(business["_id"]),  # Convert ObjectId to string
        "category": business.get("category"),
        "name": business.get("name"),
        "logo": business.get("logo"),
        "progress_status": business.get("progress_status")
    }

@app.get("/get-business-data")
async def get_businesses_data():
    try:
        # Fetch only _id, name, and logo fields from the business collection
        business_data = [
            serialize_business_data(business) 
            for business in business_collection.find({}, {"_id": 1, "category":1 , "name": 1, "logo": 1, "progress_status": 1})
        ]
        
        if not business_data:
            raise HTTPException(status_code=404, detail="No businesses found")
        
        return business_data  # FastAPI will convert it to JSON automatically
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# def serialize_doc(doc):
#     if isinstance(doc, ObjectId):
#         return str(doc)
#     if isinstance(doc, dict):
#         return {k: serialize_doc(v) for k, v in doc.items()}
#     return doc


# Sample root endpoint
@app.get("/")
def read_root():
    return {"Hello": "World13"}


@app.get("/check_model_cash")
def get_model_instance():
    msg = get_instance()

    return {"Hello": msg}


@app.post("/correct-reply")
async def correct_reply_endpoint(reply_text: str = Body(...)):
    """Endpoint to correct a business owner's reply."""
    corrected_reply = correct_reply(reply_text)
    return {"corrected_reply": corrected_reply}

# Get reply
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
    

@app.get("/generate-text-insights/{business_id}")
async def generate_insights(business_id: str):
    """
    Endpoint to run the pipeline for generating business insights.
    """
    insights = insights_collection.find_one({"business_id": business_id})

    if insights is None:
        print("No insights found for the given business ID.")
        try:
            response = generate_insights_text(business_id)  # Call the run_pipeline function
            return {"status": "success", "data": response}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    else:
         # Create JSON object with catchy headings
        extracted_data = {
            "summary": {
                "heading": "ملخص تجربة العملاء",
                "content": insights['data']['summary']
            },
            "recommendations": {
                "heading": "توصيات",
                "content": insights['data']['recommendations']
            },
            "ideas": {
                "heading": "أفكار مبتكرة",
                "content": insights['data']['ideas']
            }
        }
        extracted_data = {
            "summary": f"""
                <h3><strong>ملخص تجربة العملاء</strong></h3>
                {insights['data']['summary'].replace('\n', '<br>')}
            """,
            "recommendations": f"""
                <h3><strong>توصيات</strong></h3>
                {insights['data']['recommendations'].replace('\n', '<br>')}
            """,
            "ideas": f"""
                <h3><strong>أفكار مبتكرة</strong></h3>
                {insights['data']['ideas'].replace('\n', '<br>')}
            """
        }
        return {
            "status": "success", 
            "data": {
                "insights_id": str(insights['_id']),  # Convert ObjectId to string for JSON serialization
                "business_id": insights['business_id'],
                "data": extracted_data,
                "extraction_date": insights['extraction_date'],
            }
        }


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
    
@app.get('/chan_rev')
def chan_rev():

    reviews = list(reviews_collection.find())

    handele_reviews_asepct_tags(reviews)

    return{"status":"Done"}


# Get All Reviews
@app.get('/reviews/{business_id}')
def get_reviews(business_id: str):
    # Get business details
    business = business_collection.find_one({"_id": ObjectId(business_id)})
    if not business:
        return {"error": business_id}
    
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

            # # Color-code the aspects
            # if polarity == 'positive':
            #     highlighted_aspect = f"<span style='color: green;'>{aspect_str}</span>"
            # elif polarity == 'negative':
            #     highlighted_aspect = f"<span style='color: red;'>{aspect_str}</span>"
            # else:
            #     highlighted_aspect = aspect_str

            # # Replace the aspect in the review text
            # review_aspects_text = review_text.replace(aspect_str, highlighted_aspect)

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
            "clean_review_text": review['review_text'],
            "review_text": review['review_aspects_text'],
            "rating": rating,
            "name": review['author_name'],
            "logo": review['author_logo'],
            "image": "https://i.ibb.co/0Bsq8MC/user-image.png",
            "date": review['review_datetime_utc'],
            "review_type": review_type,
            "tokenized_review": review['tokenized_review'],
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
