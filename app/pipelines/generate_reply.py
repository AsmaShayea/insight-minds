# File: app/generate_reply.py

from bson.objectid import ObjectId
from langchain.chains import RetrievalQA
from app.vector_store_cache import VectorStoreCache
from app.database import get_database
from app.model_singleton import ModelSingleton

# Fetch the MongoDB collection
reviews_collection = get_database()['reviews']

def get_instance():
    message = ""
    if ModelSingleton._instance is None:
        message = "Initializing WatsonxLLM model..."
        # Initialize the model...
    else:
        message = "Reusing cached WatsonxLLM model..."
    return message

def generate_reply(review_id):
    """Generates a reply based on a review using a cached model and vector store."""
    
    # Fetch the review from the collection
    review = reviews_collection.find_one({"_id": ObjectId(review_id)})
    
    if not review:
        return f"Review with id {review_id} not found."

    if 'business_id' not in review:
        return f"No business_id found in review {review_id}."

    # Fetch business information
    business = get_database()['business'].find_one({"_id": ObjectId(review['business_id'])})

    if not business:
        return f"Business with id {review['business_id']} not found."

    # Use the cached retriever
    retriever = VectorStoreCache.get_retriever()

    # Prepare the prompt for response generation
    prompt_template = f"""
        Generate a reply from the business owner to the customer review following these steps:

        - Make it as short as possible and directly related to the review, without unnecessary details.
        - Consider that this business is a {business['category']}.
        - The reply should follow the same style, words and pahses that the owner always uses.
        - The response must be related to the review.
        - The reply must be a maximum of 200 characters, you can increase it to 300 if there is very important issues need to ecalrify.
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

    # Use the cached WatsonxLLM model
    qa = RetrievalQA.from_chain_type(llm=ModelSingleton.get_instance(), chain_type="stuff", retriever=retriever)
    
    # Generate the response
    response = qa.run(prompt_template)

    return response


def correct_reply(reply_text):

   # Prepare the prompt for response generation
    prompt_template = f"""

    Correct the following text by check any grammer or spelling errors:
    - Ensure that the reply is in the same language as the input_reply.
    - Just correct without any further text.
    - Follow the example format provided below and response with just the output.

    Example:
    input: نحن نقدر تييمك ونوسف اذا لم تكن رضياً بشكل كاملسنعمل جاهدين علي تحسين خدماتنا.
    output: نحن نقدر تقييمك ونأسف إذا لم تكن راضياً بشكل كامل، سنعمل جاهدين على تحسين خدماتنا.
    Example_END

    Now, give the output of correcting the following input:
    input: {reply_text}
    output:
    """

   
    model = ModelSingleton.get_model()
    # Generate the response
    response = model.generate(prompt_template)['results'][0]['generated_text']

    return response
