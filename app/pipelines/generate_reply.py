from bson.objectid import ObjectId
from app.model_manager import ModelSingleton
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from app.database_manager import get_mongo_connection
import re
from datetime import datetime

# Initialize the embeddings and vector store once
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/LaBSE")
vector_store = None
reviews_collection = get_mongo_connection()['reviews']
business_collection = get_mongo_connection()['business']

def process_aspects():
    # Fetch replies from MongoDB
    replies_data = list(reviews_collection.find({
        "owner_answer": {"$exists": True, "$ne": "", "$type": "string"}
    }, {"_id": 0}))

    return replies_data

def setup_summary_vector_store():
    global vector_store
    if vector_store is None:
        replies_data = process_aspects()
        documents = [
            f"Review: {review['review_text']} Reply: {review['owner_answer']}" 
            for review in replies_data
        ]
        vector_store = Chroma.from_texts(documents, embeddings)  
    return vector_store.as_retriever()

async def generate_reply(review_id):
    try:
        review = reviews_collection.find_one({"_id": ObjectId(review_id)})
        business = business_collection.find_one({"_id": ObjectId(review['business_id'])})
        
        retriever = setup_summary_vector_store()
        
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

        qa = RetrievalQA.from_chain_type(llm=ModelSingleton.get_instance(), chain_type="stuff", retriever=retriever)
        response = qa.run(prompt_template)
        
        return response[:100]  # Limit response length to 100 characters

    except Exception as e:
        return {"error": str(e)}

