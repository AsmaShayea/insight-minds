from bson.objectid import ObjectId
from app.model_singleton import ModelSingleton  # For handling MongoDB ObjectId
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from app.database import get_database
import re
from datetime import datetime

# Get the most common positive and negative aspects separately, along with their sentiment and associated reviews
def get_common_aspects_and_reviews():
    aspects_collection = get_database()['aspects']
    # Step 1: Find aspects that are repeated more than 3 times, grouped by aspect, root_aspect, and polarity
    pipeline = [
        {"$group": {
            "_id": {"aspect": "$aspect", "root_aspect": "$root_aspect", "polarity": "$polarity"},  # Group by aspect, root_aspect, and polarity
            "count": {"$sum": 1},  # Count occurrences
            "all_opinions": {"$push": "$opinions"}  # Collect associated opinions into an array
        }},
        {"$match": {"count": {"$gt": 3}}},  # Keep only aspects mentioned more than 3 times
        {"$sort": {"count": -1}}  # Sort by count in descending order
    ]
    
    common_aspects = list(aspects_collection.aggregate(pipeline))
    
    return common_aspects

# Step 3: Retrieve the reviews for these aspects
def process_aspects():
    common_aspects = get_common_aspects_and_reviews()
    positive_aspects = [entry for entry in common_aspects if entry['_id']['polarity'] == 'positive'][:3]  # Top 3 positive aspects
    negative_aspects = [entry for entry in common_aspects if entry['_id']['polarity'] == 'negative'][:3]  # Top 3 negative aspects

    retrieved_data = []
    for aspect_entry in positive_aspects + negative_aspects:
        aspect = aspect_entry['_id']['aspect']
        root_aspect = aspect_entry['_id']['root_aspect']  # Retrieve root_aspect
        sentiment = aspect_entry['_id']['polarity']
        all_opinions = aspect_entry['all_opinions']  # Get all collected opinions arrays
        
        # Flatten the list of lists for opinions (since opinions are stored as arrays within arrays)
        flattened_opinions = [opinion for sublist in all_opinions for opinion in sublist]
        
        # Add to the final retrieved data structure
        retrieved_data.append({
            'aspect': aspect,
            'root_aspect': root_aspect,
            'sentiment': sentiment,
            'count': aspect_entry['count'],  # Add the count of the aspect
            'all_opinions': flattened_opinions,  # Store all consolidated opinions in the final structure
        })
    return retrieved_data

# Prepare summary prompt based on retrieved data
def prepare_summary_prompt(business_id):

    business = get_database()['business'].find_one({"_id": ObjectId(business_id)})
    # Check if the business exists
    if not business:
        return "Business not found."

    # Prepare the prompt template
    prompt_template = f"""You are a Customer Experience Analyst. Based on the user opinions and aspects about a business, You will provide in Arabic language:
        1- الملخص: Start by summarizing both the positive and negative feedback from the user review about the business in overall without mention it as points. Mention in overall what people liked, disliked and how these opinions reflect the overall customer experience.
        2- توصيات: Provide practical recommendations based on positive and negative aspects in overall that could help enhance service and customer experience, focusing on tangible improvements.
        3- أفكار: Suggest new innovative and unique ideas to strengthen the business's position and attract more customers, highlighting new aspects that could be explored with avoiding repeated suggestions.

        Consider the details of the business as follows:
        Name: {business['name']}
        Category: {business['category']}
        Type: {business['type']}
        Subtypes: {business['subtypes']}
        """
  
    return prompt_template

# Setup the embeddings and vector store for the summary task
def setup_summary_vector_store():
    retrieved_data = process_aspects()

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/LaBSE")
    documents = [
        f"Aspect: {data['aspect']}\nSentiment: {data['sentiment']}\nOpinions: {', '.join(data['all_opinions'])}" 
        for data in retrieved_data
    ]
    vector_store = Chroma.from_texts(documents, embeddings)
    return vector_store

# Generate insights text from the processed aspects
# Generate insights text from the processed aspects
def generate_insights_text(business_id):
    # Create the vector store from the retrieved data
    summary_vector_store = setup_summary_vector_store()
    retriever = summary_vector_store.as_retriever()

    # Prepare summary prompt using retrieved data
    summary_prompt = prepare_summary_prompt(business_id)

    # Initialize the RetrievalQA chain
    qa = RetrievalQA.from_chain_type(llm=ModelSingleton.get_instance(), chain_type="stuff", retriever=retriever)

    # Run the query and get insights
    response = qa.run(summary_prompt)

    # Define regex patterns to extract sections
    summary_pattern = r"الملخص:\n\n(.*?)\n\n2- توصيات"
    recommendations_pattern = r"2- توصيات:\n\n(.*?)\n\n3- أفكار"
    ideas_pattern = r"3- أفكار:\n\n(.*)"

    # Extract sections
    summary_match = re.search(summary_pattern, response, re.DOTALL)
    recommendations_match = re.search(recommendations_pattern, response, re.DOTALL)
    ideas_match = re.search(ideas_pattern, response, re.DOTALL)

    # Replace newlines with <br> tags if sections are found
    extracted_data = {
        "summary": summary_match.group(1).strip().replace('\n', '<br>') if summary_match else "",
        "recommendations": recommendations_match.group(1).strip().replace('\n', '<br>') if recommendations_match else "",
        "ideas": ideas_match.group(1).strip().replace('\n', '<br>') if ideas_match else ""
    }

    current_datetime = datetime.now()

    insights_data = {
        "business_id": business_id,
        "data": extracted_data,
        "extraction_date": current_datetime,
    }

    try:
        insights_collection = get_database()['insights']
        
        # Insert the data
        insights_id = insights_collection.insert_one(insights_data).inserted_id
        
        # Convert ObjectId to string before using it in responses or logs
        insights_id_str = str(insights_id)
        
        print(f"Inserted document ID: {insights_id_str}")

    except Exception as e:
        print(f"Error occurred: {e}")
        return {"error": str(e)}
    
    # Create JSON object with catchy headings
    extracted_data = {
        "summary": f"""
            <h3><strong>تجربة العملاء: تقييم شامل لنمط نمق كافيه</strong></h3>
            {extracted_data['summary'].replace('\n', '<br>')}
        """,
        "recommendations": f"""
            <h3><strong>تحسينات مقترحة: خطوات لتعزيز تجربة العملاء في نمق كافيه</strong></h3>
            {extracted_data['recommendations'].replace('\n', '<br>')}
        """,
        "ideas": f"""
            <h3><strong>أفكار مبتكرة: كيف يمكن أن نجذب المزيد من الزبائن إلى نمق كافيه؟</strong></h3>
            {extracted_data['ideas'].replace('\n', '<br>')}
        """
    }
    # Return the response as JSON-compatible dictionary
    return {
        "insights_id": insights_id_str,
        "business_id": business_id,
        "data": extracted_data,
        "extraction_date": current_datetime
    }