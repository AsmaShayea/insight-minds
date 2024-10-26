
from app.database import get_database
from app.processing_text import preprocess_arabic_text, extract_aspect_data, get_original_token, get_root_word
import json
from app.model_singleton import ModelSingleton
from app.scrape_save_reviews import scrape_reviews
from bson.objectid import ObjectId

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


prompt_template = """
You are an advanced AI model specialized in extracting aspects and determining sentiment polarities from customer reviews.

Follow these steps for the task:
1- Preprocess the text by normalizing, removing stopwords, and lemmatizing the words.
2- Extract all aspects (nouns) mentioned in the review. No aspect with same polarity will be repeatead in two items.
3- Assign a sentiment polarity for each aspect as one of the following: positive, negative, or neutral with adding the polarity score.
4- For mixed polarity (both positive and negative sentiments), split the aspect into two entries with the same name but different sentiments.
5- If there is a duplicated aspect, **merge the data** by combining their descriptions and averaging the polarity score while avoiding any repeated information.
6- For each aspect, extract unique opinion terms which are the relevant adjectives with their corresponding nouns to form a description or their opinion for the aspect. Do not duplicate any opinion term.
7- Provide the output in the exact format shown in the examples below, without any explanations, translation, or additional.
8- Check that output is in JSON format, and it is an array of objects. The array must start with "[" and end with "]", and each object must start with "{" and end with "}", separated by commas ",".
9- Do not show me the traslation or how/what you are doing just show me the output and it's just one output do not repeat or duplicate.
10- Review your result before show it.
11- once you retrievied "Outpu:" started with "[" and closed with "]", stop here and do not generating more.

------------

Example 1:
Input: "المكان كسر الصورة النمطية عن باقي الأماكن.
        المكان واسع جداً وشرح بالرغم الزحمة ما شاء الله
        إلا انه هادي ورايق جداً
        تعامل الموظفين رائع وخدمتهم سريعة، تنوع في المنيو يحير ومختلف👌🏻
        كيكة الشوكولاته تفوز بـ ألذ وأفضل كيكة
        فعلاً اسم على مسمى مليانة شوكولاته وطرية وهشة.
        اكثر من تجربة وكل مره تكون أفضل وأجمل
        المُلاحظة الوحيدة، القهوة ما تكون بنفس المستوى
        مره واو، مره عادية.
        عدا ذلك مُمتاز"
Output: 
[
    {
        "aspect": "المكان",
        "polarity": "positive",
        "polarity_score": "+0.80",
        "opinions": ["واسع", "شرح", "هادي", "رايق"]
    },
    {
        "aspect": "تعامل الموظفين",
        "polarity": "positive",
        "polarity_score": "+0.90",
        "opinions": ["تعامل رائع"]
    },
    {
        "aspect": "خدمتهم",
        "polarity": "positive",
        "polarity_score": "+0.85",
        "opinions": ["سريعة"]
    },
    {
        "aspect": "المنيو",
        "polarity": "positive",
        "polarity_score": "+0.80",
        "opinions": ["تنوع", "مختلف"]
    },
    {
        "aspect": "كيكة الشوكولاته",
        "polarity": "positive",
        "polarity_score": "+0.95",
        "opinions": ["ألذ", "أفضل", "مليانة شوكولاته", "طرية", "هشة"]
    },
    {
        "aspect": "القهوة",
        "polarity": "positive",
        "polarity_score": "+0.90",
        "opinions": ["واو"]
     },
    {
        "aspect": "القهوة",
        "polarity": "neutral",
        "polarity_score": "-0.50",
        "opinions": ["عادية"]
     }
]
Example1_end


Example 2:
Input: "هاذي أول زيارة لي لـ الكوفي ، أخذت قهوة اليوم - أثيوبي (ساخن) ، القهوه رايقه وفيها شويه مراره ، بس مراره القهوه المطلوب ، القهوه أعطيها 10/9 ، وطلبت حلى نمق ، تجي كيكه ومعها ايسكريم الكيكه عادية مافيها شيء زود ، وتقييمي لها 10/6 ، الكوفي شرح وفيه جلسات فوق للعوائل وجلسات داخل حلوه وعددها كويس ، الملاحظة بسيطه ، الكيكة تقديمها في علبه كرتونيه وتحتها ورق ماكانت فكره حلوه الورق يتفتت مع الايسكريم ويدخل مع الكيكه وتبلش فيه ، وبالنسبه للموظفين جداً بشوشين."
Output: 
[
    {
        "aspect": "القهوi",
        "polarity": "positive",
        "polarity_score": "+0.90",
        "opinions": ["رايقه", "مراره"]
    },
    {
        "aspect": "حلى نمق",
        "polarity": "negative",
        "polarity_score": "-0.50",
        "opinions": ["عادي", "مافيها شيء زود"]
    },
    {
        "aspect": "الكوفي",
        "polarity": "positive",
        "polarity_score": "+0.85",
        "opinions": ["شرح", "جلسات فوق للعوائل", "جلسات داخل", "عددها كويس"]
    },
    {
        "aspect": "الكيكة",
        "polarity": "negative",
        "polarity_score": "-0.65",
        "opinions": ["تقديمها في علبة كرتونية", "تحتها ورق"]
    },
    {
        "aspect": "للموظفين",
        "polarity": "positive",
        "polarity_score": "+0.95",
        "opinions": ["بشوشين"]
    }
]
Example2_end


Example 3:
Input: "اسبوع ومو اول تعامل معاه تفصيل ثياب اولادي بكل المناسبات من هالمحل يفصلون وهم مرتاحين انه مراح يعدلون عليه سعره شوي غالي بالنسبه للخياطين بس يستاهل 👍🏻 …"
Output:
[
    {
        "aspect": "تفصيل ثياب",
        "polarity": "positive",
        "polarity_score": "+0.85",
        "opinions": ["مناسب للمناسبات", "مريح"]
    },
    {
        "aspect": "سعره",
        "polarity": "negative",
        "polarity_score": "-0.65",
        "opinions": ["غالي"]
    },
    {
        "aspect": "هالمحل",
        "polarity": "positive",
        "polarity_score": "+0.75",
        "opinions": ["يستاهل"]
    }
]
Example3_end

------------

Now, Extract the unique aspects with its sentiment ploarity, ploarity score and opinion terms from the following review:
 %s

"""

def augment(prompt_template, review_text):
    return prompt_template % review_text


def clean_result(input_value):
    # Function to remove undesired substrings
    def remove_undesired(text):
        # Remove all instances of "Place_" and replace underscores with spaces
        cleaned_text = re.sub(r"Place_", "", text)  # Remove "Place_"
        cleaned_text = re.sub(r"NOT_", "", text)  # Remove "Place_"
        cleaned_text = cleaned_text.replace("_", " ")  # Replace remaining underscores with spaces
        return cleaned_text.strip()
    
    # Check if the input is a list (array)
    if isinstance(input_value, list):
        # Apply the cleaning function to each element in the list
        return [remove_undesired(item) for item in input_value if isinstance(item, str)]
    
    # If the input is a single string, clean it directly
    elif isinstance(input_value, str):
        return remove_undesired(input_value)
    
    # Return None or input as-is if it's neither string nor list
    return input_value


# Save apects for each review to DB
def save_aspects_data(reviews, business_id):
    count = 0
    categpries_list = "(Price, Product, Service, Staff, Place)"

    for review in reviews:
        count = count + 1
        print(count)

        review_txt = review['review_text']
        review_id = review['review_id']
        existing_aspect_review = aspects_collection.find_one({"review_id": review_id})
        is_review_analyzed = "false"
        
        if not existing_aspect_review:
            print(review_id)
            print(review_txt)
            cleaned_review, token_mapping = preprocess_arabic_text(review_txt)

            llm_model = ModelSingleton.get_model()
            response = llm_model.generate(augment( prompt_template, cleaned_review))
            
            # print(pretty(response))
            generated_text = response['results'][0]['generated_text']
            print(generated_text)
            print('---')
            try:
                aspect_data_list = extract_aspect_data(generated_text)
                for aspect in aspect_data_list:
                    aspect_value = get_original_token(aspect["aspect"], token_mapping)
                    print("old",aspect["aspect"])
                    print("new",aspect_value)

                    root_aspect = get_root_word(aspect_value)
                    existing_aspects = aspects_collection.find_one({
                        "root_aspect": root_aspect,
                        "polarity": aspect["polarity"],
                        "review_id": review_id,
                    })
                    if not existing_aspects:
                        aspect_data = {
                            "review_id": review_id,
                            "business_id": review['business_id'],
                            "aspect": clean_result(aspect_value),
                            "root_aspect": root_aspect,
                            "polarity": aspect["polarity"],
                            "polarity_score": aspect["polarity_score"],
                            # "category": aspect["category"],
                            "opinions": clean_result(aspect["opinions"]),
                        }
                        
                        aspect_id = aspects_collection.insert_one(aspect_data).inserted_id
                        print(f"Added review with review_id {aspect_id} to the database.")


                    else:
                        print(f"Review with review_id {aspect['aspect']} already exists in the database.")
    
            except json.JSONDecodeError as e:
                print(review['review_id'])
                existing_error_review = errors_log_collection.find_one({"review_id": review_id})
        
                if not existing_error_review:
                    error_data = {
                        "review_id": review_id,
                        "type": "prompt_result",
                        "response": response,
                    }
                    error_id = errors_log_collection.insert_one(error_data).inserted_id
                print(f"Error parsing JSON: {e}")

            business_collection.update_one(
                {"_id": ObjectId(business_id)},  # Filter by _id or use other unique field
                {"$set": {"progress_status": "Completed"}}  # Set the new progress status
            )
        else:
            print('done')

        if is_review_analyzed == "false":
            reviews_collection.update_one(
                {"review_id": review_id},  # Match the review by review_id
                {"$set": {"is_analyzed": "true"}}  # Set is_analyzed to True
            )
            is_review_analyzed = "true"



def extract_save_aspects(business_id, url):

    business_reviews = reviews_collection.count_documents({"business_id": business_id})

    if(business_reviews == 0):
        business_id = scrape_reviews(business_id, url)

    # business_id = "66eb726e1b898c92f06c243f"  # Replace with the actual business ID
    # Find all reviews for the specific business_id
    print("hi2 bbbbbbbbb")
    reviews = reviews_collection.find({"business_id": business_id})

    save_aspects_data(reviews, business_id)
