from bson.objectid import ObjectId
from app.model_manager import ModelSingleton  # For handling MongoDB ObjectId
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from app.database_manager import get_mongo_connection
import re
from datetime import datetime

reviews_collection = get_mongo_connection()['reviews']
def process_aspects():
    replies_data =list(reviews_collection.find({
        "owner_answer": {"$exists": True, "$ne": "", "$type": "string"}
    }, {"_id": 0}))

    return replies_data


def setup_summary_vector_store():

    replies_data = process_aspects()

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/LaBSE")
    # documents = [reply['owner_answer'] for reply in replies_data]  # Use owner_answer for embedding
    documents = [
    f"Review: {review['review_text']} Reply: {review['owner_answer']}" 
    for review in replies_data
    ]
    # Create a Chroma vector store from the owner replies
    vector_store = Chroma.from_texts(documents, embeddings)  # Embedding owner_answer instead of review_text
    retriever = vector_store.as_retriever()

    return retriever


def generate_reply(review_id):

    # Fetch the review from the collection
    review = reviews_collection.find_one({"_id": ObjectId(review_id)})
    
    # Check if the review exists
    if not review:
        return f"Review with id {review_id} not found."

    # Check if the review has a business_id field
    if 'business_id' not in review:
        return f"No business_id found in review {review_id}."

    # Fetch the business associated with the review
    business = get_mongo_connection()['business'].find_one({"_id": ObjectId(review['business_id'])})

    # Check if the business exists
    if not business:
        return f"Business with id {review['business_id']} not found."

    # Set up the vector store
    retriever = setup_summary_vector_store()

    # Create the prompt template for generating a reply
    prompt_template = f"""
        Generate a reply from the business owner to the customer review following these steps:

        - Make it as short as possible and directly related to the review, without unnecessary details.
        - Consider that this business is a {business['category']}.
        - The reply should follow the same style that the owner always uses.
        - The response must be related to the review.
        - The reply must be a maximum of 100 characters unless it is important.
        - Reply in the same language as the review, and do not include any text in a different language.
        - Avoid repeating general phrases or adding filler content.
        - Do not add any hashtag or mention
        - Follow the output of the example below.

        Example :
        input: نجمتين لاني فعلا احب قهوتهم خصوصا الفلات وايت وساندوتش الحلومي اللي عندهم ودايم اطلب منهم عن طريق احد تطبيقات التوصيل رغم كثرة الكافيهات القريبه حولي بالدمام … ولكن الطلب الاخير وصلني بطريقه بشعه جدا ماتوقعتها منهم ولا اتوقع انها ترضي ادارة كافيه محترم له سمعته … اين ادارة الجوده … الساندوتش وصلني يابس و محروق واضح بالصور رغم محاولات ازاله الطبقه المحروقه والقهوه وصلت والغطا مش نظيف مشروبي فلات وايت ولا اعلم سبب وجود هذا السائل الاحمر ؟؟!!! … اتمنى من الاداره اتخاذ الاجراءات اللازمه لعدم تكرار هذا مع زبائن اخرين
        output: نحن نقدر تقييمك ونأسف اذا لم تكن راضياً بشكل كامل، سنعمل جاهدين على تحسين خدماتنا. 
        Example_END

        Now generate a short response for the following review:
        {review['review_text']}
        """

    # Initialize the retrieval QA system
    qa = RetrievalQA.from_chain_type(llm=ModelSingleton.get_instance(), chain_type="stuff", retriever=retriever)
    
    # Generate the response
    response = qa.run(prompt_template)

    return response
