from bson.objectid import ObjectId
from app.model_singleton import ModelSingleton  # For handling MongoDB ObjectId
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from app.database import get_database
import re
from datetime import datetime
from app.vector_store_cache import VectorStoreCache



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



# Generate insights text from the processed aspects
# Define regex patterns to extract sections
# summary_pattern = r"الملخص:\n\n(.*?)\n\n2- توصيات"
# recommendations_pattern = r"2- توصيات:\n\n(.*?)\n\n3- أفكار"
# ideas_pattern = r"3- أفكار:\n\n(.*)"
summary_pattern = r"1-\s*الملخص:(.*?)(?:2-\s*توصيات:|3-\s*أفكار:|$)"
recommendations_pattern = r"2-\s*توصيات:(.*?)(?:1-\s*الملخص:|3-\s*أفكار:|$)"
ideas_pattern = r"3-\s*أفكار:(.*?)(?:1-\s*الملخص:|2-\s*توصيات:|$)"


#we used the reviews of most common aspect negative and positive
# To generate text summary of insight and recommendation
def generate_insights_text(business_id):

    summary_prompt = prepare_summary_prompt(business_id)

    # Use the cached retriever
    #we used the reviews of most common aspect negative and positive and also suggest ideas to improve their business
    retriever = VectorStoreCache.get_retriever(business_id,"text_summary")

    # Initialize the RetrievalQA chain
    qa = RetrievalQA.from_chain_type(llm=ModelSingleton.get_instance(), chain_type="stuff", retriever=retriever)


    # Run the query and get insights
    response = qa.run(summary_prompt)

    # Extract sections
    summary_match = re.search(summary_pattern, response, re.DOTALL)
    recommendations_match = re.search(recommendations_pattern, response, re.DOTALL)
    ideas_match = re.search(ideas_pattern, response, re.DOTALL)
    print("0000000")

    # Ensure sections are not empty
    if (summary_match and summary_match.group(1).strip()) or \
       (recommendations_match and recommendations_match.group(1).strip()) or \
       (ideas_match and ideas_match.group(1).strip()):
        
        print("11111111111111")
        
        # Format extracted data with <br> tags replacing newline characters
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

        print("22222222222")

        try:
            insights_collection = get_database()['insights']
            print("4444444444", insights_collection)

            # Insert the data and retrieve the generated _id
            insights_id = insights_collection.insert_one(insights_data).inserted_id
            print("33333333333", insights_id)
            # Ensure the insights_id was created successfully
            if insights_id is None:
                print("Insertion failed, no ID returned.")
            else:
                print(f"Inserted document ID: {str(insights_id)}")

        except Exception as e:
            print(f"An error occurred: {str(e)}")
    else:
        print("No valid data found to insert.")
    

