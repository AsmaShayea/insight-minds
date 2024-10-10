prompt_template = """
You are an advanced AI model specialized in extracting aspects and determining sentiment polarities from Arabic customer reviews.

------------
First: Before analyze and extract the sentiment, preprocess the arabic text by doing: normalize, remove arabic stopwords, and lemmatizing the words.
Second: The result must be an array of objects. Each object contains the six following fields:
1.aspect: Extract all aspects (nouns) mentioned in the review. 
2.lemmi_aspect: Lemmatize the aspect and add it as lemmi_aspect.
3.polarity: considering the three following points:
    - Assign a sentiment polarity for each aspect as one of the following: positive, negative, neutral, or mixed.
    - For mixed polarity (both positive and negative sentiments), split the aspect into two entries with the same name but different sentiments.
    - If there is a duplicated aspect with the same polarity, **merge the data** by combining their descriptions and averaging the polarity score while avoiding any repeated information.
4.polarity_score: set the polarity score.
5.description: Extract relevant adjectives or descriptive phrases characterizing the aspect. Ensure there are no duplicate strings and that all entries are relevant to the aspect, avoiding mere nouns or product names. Focus only on features or qualities of the aspect.
6.phrases: For the aspect, extract the **unique** related phrases without duplicating. Each phrase should appear **only once**. Aim to make these phrases as short as possible, without repeated or duplicated words.

Important Notes:
- Ensure the output starts with "Output:" followed by an array of objects exactly as the output at the examples provided.
- Do not add any repeated or other arrays and do not add any explanations.
- In the `phrases` array, ensure **no repeated** or **duplicated** phrases appear.

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
        "lemmi_aspect": "مكان",
        "polarity": "positive",
        "polarity_score": "+0.80",
        "description": ["واسع", "شرح", "هادي", "رايق"],
        "phrases": [
            "المكان واسع جداً وشرح بالرغم الزحمة ما شاء الله إلا انه هادي ورايق جداً"
        ]
    },
    {
        "aspect": "تعامل الموظفين",
        "lemmi_aspect": "تعامل الموظفين",
        "polarity": "positive",
        "polarity_score": "+0.90",
        "description": ["تعامل رائع"],
        "phrases": [
            "تعامل الموظفين رائع"
        ]
    },
    {
        "aspect": "خدمة",
        "lemmi_aspect": "خدمه",
        "polarity": "positive",
        "polarity_score": "+0.85",
        "description": ["سريعة"],
        "phrases":  [
            "خدمتهم سريعة"
        ]
    },
    {
        "aspect": "المنيو",
        "lemmi_aspect": "منيو",
        "polarity": "positive",
        "polarity_score": "+0.80",
        "description": ["تنوع", "مختلف"],
        "phrases": [
            "تنوع في المنيو يحير ومختلف"
        ]
    },
    {
        "aspect": "كيكة الشوكولاتة",
        "lemmi_aspect": "كيكه الشوكولاته",
        "polarity": "positive",
        "polarity_score": "+0.95",
        "description": ["ألذ", "أفضل", "مليانة شوكولاته", "طرية", "هشة"],
        "phrases": [
            "كيكة الشوكولاته تفوز بـ ألذ وأفضل كيكة",
            "فعلاً اسم على مسمى مليانة شوكولاته وطرية وهشة"
        ]
    },
    {
        "aspect": "القهوة",
        "lemmi_aspect": "قهوه",
        "polarity": "mixed",
        "polarity_score": "+0.10",
        "description": ["واو", "عادية"],
        "phrases": [
            "القهوة ما تكون بنفس المستوى مره واو، مره عادية."
        ]
    }
]


Example 2:
Input: "هاذي أول زيارة لي لـ الكوفي ، أخذت قهوة اليوم - أثيوبي (ساخن) ، القهوه رايقه وفيها شويه مراره ، بس مراره القهوه المطلوب ، القهوه أعطيها 10/9 ، وطلبت حلى نمق ، تجي كيكه ومعها ايسكريم الكيكه عادية مافيها شيء زود ، وتقييمي لها 10/6 ، الكوفي شرح وفيه جلسات فوق للعوائل وجلسات داخل حلوه وعددها كويس ، الملاحظة بسيطه ، الكيكة تقديمها في علبه كرتونيه وتحتها ورق ماكانت فكره حلوه الورق يتفتت مع الايسكريم ويدخل مع الكيكه وتبلش فيه ، وبالنسبه للموظفين جداً بشوشين."
Output: 
[
    {
        "aspect": "القهوة",
        "lemmi_aspect": "قهوه",
        "polarity": "positive",
        "polarity_score": "+0.75",
        "description": ["رايقه", "مراره"],
        "phrases": [
            "القهوه رايقه وفيها شويه مراره",
            "مراره القهوه المطلوب",
        ]
    },
    {
        "aspect": "حلى نمق",
        "lemmi_aspect": "حلى نمق",
        "polarity": "negative",
        "polarity_score": "-0.60",
        "description": ["عادي", "مافيها شيء زود"],
        "phrases":  [
            "الكيكه عادية مافيها شيء زود"
        ]
    },
    {
        "aspect": "الكوفي",
        "lemmi_aspect": "كوفي",
        "polarity": "positive",
        "polarity_score": "+0.80",
        "description": ["شرح", "جلسات فوق للعوائل", "جلسات داخل", "عددها كويس"],
        "phrases": [
            "الكوفي شرح وفيه جلسات فوق للعوائل",
            "جلسات داخل حلوه وعددها كويس"
        ]
    },
    {
        "aspect": "الكيكة",
        "lemmi_aspect": "كيكه",
        "polarity": "negative",
        "polarity_score": "-0.70",
        "description": ["تقديمها في علبة كرتونية", "تحتها ورق"],
        "phrases": [
            "الكيكة تقديمها في علبه كرتونيه وتحتها ورق",
        ]
    },
    {
        "aspect": "الموظفين",
        "lemmi_aspect": "موظفين",
        "polarity": "positive",
        "polarity_score": "+0.85",
        "description": ["بشوشين"],
        "phrases": [
            "الموظفين جداً بشوشين"
        ]
    }
]


Example 3:
Input: "اسبوع ومو اول تعامل معاه تفصيل ثياب اولادي بكل المناسبات من هالمحل يفصلون وهم مرتاحين انه مراح يعدلون عليه سعره شوي غالي بالنسبه للخياطين بس يستاهل 👍🏻 …"
Output:
[
   {
        "aspect": "تفصيل الثياب",
        "lemmi_aspect": "تفصيل الثياب",
        "polarity": "positive",
        "polarity_score": "+0.85",
        "description": ["مناسب للمناسبات", "مريح"],
        "phrases": [
            "تفصيل ثياب اولادي بكل المناسبات",
            "يفصلون وهم مرتاحين انه مراح يعدلون عليه"
        ]
    },
    {
        "aspect": "السعر",
        "lemmi_aspect": "سعر",
        "polarity": "negative",
        "polarity_score": "-0.65",
        "description": ["غالي"],
        "phrases": [
            "سعره شوي غالي بالنسبه للخياطين"
        ]
    },
    {
        "aspect": "المحل",
        "lemmi_aspect": "محل",
        "polarity": "positive",
        "polarity_score": "+0.75",
        "description": ["يستاهل"],
        "phrases": [
            "المحل يستاهل"
        ]
    }
]

------------

Now,Extract the aspects with its sentiment ploarity and its score, description and phrase from the following review:
%s

"""

def augment(prompt_template, review_text):
    return prompt_template % review_text



def extract_aspect_data(generated_text):
    aspect_data_list = []

    # Regular expression to match each aspect object, focusing on "phrases"
    pattern = r'\{\s*"aspect":\s*[^{}]*"phrases":\s*\[[^\]]*\]\s*\}'
    
    # Find all matches
    aspects_data = re.findall(pattern, generated_text, re.DOTALL)

    for aspect_data in aspects_data:
        aspect_data = aspect_data.strip()
        # # Load the aspect_data as a dictionary
        # print("111")
        # print(aspect_data)
        # print("111")
        
        # # Modify the string to make it a valid JSON object
        # valid_json_string = '{' + aspect_data + '}'  
        # Convert the string to a JSON object
        aspect_data_to_save = json.loads(aspect_data)
        aspect_data_list.append(aspect_data_to_save)
    return aspect_data_list


# Save apects for each review to DB
def save_aspects_data(reviews):
    count = 0

    for review in reviews:
        count = count + 1
        print(count)

        review_txt = review['review_text']
        review_id = review['review_id']
        existing_aspect_review = aspects_collection.find_one({"review_id": review_id})
        
        if not existing_aspect_review:
            print(review_txt)
            cleaned_review = preprocess_arabic_text(review_txt)
            response = model.generate(augment( prompt_template, cleaned_review ))
            # print(pretty(response))
            generated_text = response['results'][0]['generated_text']
            print(generated_text)
            print('---')
            # # Remove the 'Output:' part
            # json_string = generated_text.split('Output:')[-1].strip()
            
            # json_string = json_string.replace("'", '"')
    
            # # print(json_string)
    
            # # Find the first closing square bracket "]" and trim the string until there
            # closing_bracket_index = json_string.find(']') + 1  # find index of the first "]" and include it
            # if closing_bracket_index > 0:
            #     json_string = json_string[:closing_bracket_index]
    
            # print(json_string)
            #  Parse the JSON string into a Python object
            try:
                aspect_data_list = extract_aspect_data(generated_text)
                for aspect in aspect_data_list:
                    existing_aspects = aspects_collection.find_one({
                        "lemmi_aspect": aspect['lemmi_aspect'],
                        "review_id": review_id,
                    })
                    if not existing_aspects:
                       
                        
                        aspect_data = {
                            "review_id": review_id,
                            "business_id": review['business_id'],
                            "aspect": aspect["aspect"],
                            "lemmi_aspect": aspect["lemmi_aspect"],
                            "polarity": aspect["polarity"],
                            "polarity_score": aspect["polarity_score"],
                            "description": aspect["description"],
                            "phrases": aspect["phrases"]
                        }
                        
                        aspect_id = aspects_collection.insert_one(aspect_data).inserted_id
                        print(f"Added review with review_id {aspect_id} to the database.")
                    else:
                        print(f"Review with review_id {aspect['aspect']} already exists in the database.")
    
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                print(review['review_id'])
                existing_error_review = errors_log_collection.find_one({"review_id": review_id})
        
                if not existing_error_review:
                    error_data = {
                        "review_id": review_id,
                        "type": "prompt_result",
                        "response": response,
                    }
                    error_id = errors_log_collection.insert_one(error_data).inserted_id
        else:
            print('done')
