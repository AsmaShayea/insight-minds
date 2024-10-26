import nltk
from nltk.corpus import stopwords
from camel_tools.utils.normalize import normalize_alef_maksura_ar
from camel_tools.utils.normalize import normalize_alef_ar
from camel_tools.utils.normalize import normalize_teh_marbuta_ar
from camel_tools.utils.dediac import dediac_ar
from camel_tools.morphology.database import MorphologyDB
from camel_tools.morphology.analyzer import Analyzer
import string
import re
from camel_tools.tokenizers.word import simple_word_tokenize
from camel_tools.disambig.mle import MLEDisambiguator
from camel_tools.utils.dediac import dediac_ar
import json

nltk.download('stopwords')

db = MorphologyDB.builtin_db()
analyzer = Analyzer(db)

# Example Arabic stopwords
stop_words = stopwords.words()

# Step 1: Normalization
def normalize_text(text):
    # Normalize alef variants to 'ا'
    text = normalize_alef_ar(text)
    # Normalize alef maksura 'ى' to yeh 'ي'
    text = normalize_alef_maksura_ar(text)   
    # Normalize teh marbuta 'ة' to heh 'ه'
    text = normalize_teh_marbuta_ar(text)
    # Normalize teh marbuta 'ة' to heh 'ه'
    text = normalize_teh_marbuta_ar(text)
    return text

# Step 1: Normalization
def normalize_token(tokens):
    normalized_tokens = []
    for token in tokens:
        token = normalize_text(token)
        normalized_tokens.append(token)
    return normalized_tokens
    
# Step 2: Tokenization
def tokenize_text(text):
    tokens = simple_word_tokenize(text)
    return tokens

# Step 3: Cleaning (Remove elongations, special characters, numbers, punctuation)
def clean_text(tokens):
    cleaned_tokens = []
    for token in tokens:
        # Preserve "لام الشمسية" and proper names like "الله"
        if not re.match(r'^(الل|اللّ|لل|ال[^\u0627-\u063a])', token):
            # Remove elongation (e.g., جمييييل => جميل), but do not shorten valid names
             token = re.sub(r'(.)\1{2,}', r'\1', token)

        # Remove non-Arabic characters, punctuation, and numbers
        token = re.sub(r'[^\u0600-\u06FF]', '', token)
            
        cleaned_tokens.append(token)
    
    return cleaned_tokens

def remove_tashkeel(tokens):
    new_tokens = []
    for token in tokens:
        token = dediac_ar(token)
        new_tokens.append(token)
    return new_tokens

# Step 4: Stopword Removal (replace stopwords with empty string)
def remove_stopwords(tokens):
    return [token if token not in stop_words else "" for token in tokens]

# Step 5: Lemmatization using Analyzer
def lemmatize_tokens(tokens):
    token_original_mapping = []  # Dictionary to hold token-original pairs
    
    for token in tokens:
        
        analyses = analyzer.analyze(token)  # Analyze the word
        
        # Collect unique lemmas from the analysis
        lemmas = set()  # Use a set to avoid duplicates
        for analysis in analyses:
            lemmas.add(analysis['lex'])  # 'lex' key contains the lemma

        # If lemmas exist, add the first lemma to lemmatized tokens
        if lemmas:
            lemmatized_token = list(lemmas)[0]  # Use the first lemma
            # lemmatized_token = dediac_ar(lemmatized_token)
            token_original_mapping.append((lemmatized_token, token))

        else:
            token_original_mapping.append((token, token))
        
    return token_original_mapping  # Return the mapping dictionary

#Step 6: Negation Handling
def handle_negation(tokens):
    negation_words = ['لا', 'لم', 'ما', 'لن']
    negation_active = False
    final_tokens = []
    
    for token in tokens:
        if token in negation_words:
            negation_active = True
        else:
            if negation_active:
                token = 'NOT_' + token  # Add a marker for negation
                negation_active = False
            final_tokens.append(token)
    
    return final_tokens

# # Step 6: Negation Handling
# def handle_negation(tokens):
#     negation_words = ['لا', 'لم', 'ما', 'لن']
#     final_tokens = []
    
#     for token in tokens:
#         if token in negation_words:
#             token = 'NOT_'
            
#         final_tokens.append(token)
    
#     return final_tokens

# Step 6: Negation Handling
def handle_specific_words(tokens):
    important_stopword = ["المكان","مكان"]
    final_tokens = []
    
    for token in tokens:
        processed_text = normalize_text(token)
        processed_text = dediac_ar(processed_text)
    
        if processed_text in important_stopword:
            token = 'Place_' + token
        
        final_tokens.append(token)
         
    return final_tokens

# Function to reconstruct text from lemmatized tokens
def reconstruct_text(tokens, token_mapping):
    reconstructed = []

    for token in tokens:
        if "NOT_" in token:
            cleaned_token = token.replace("NOT_", "").strip()
            if any(key == cleaned_token for key, val in token_mapping):
                found_value = next((value for key, value in token_mapping if key == cleaned_token), None)
                token = 'NOT_' + found_value
                reconstructed.append(token)
            else:
                reconstructed.append(token)  # Keep it as is if not found
        elif any(key == token for key, val in token_mapping):
            # token = next((value for key, value in token_mapping if key == token), None)
            # reconstructed.append(token)
  
            # Find the key-value pair where the token matches the key
            key_value_pair = next(((key, value) for key, value in token_mapping if key == token), None)
            
            if key_value_pair:
                key, value = key_value_pair  # Extract both key and value
                token = value  # Replace the token with the corresponding value
                reconstructed.append(token)
                
                # Remove the first occurrence of the key-value pair from token_mapping
                token_mapping.remove(key_value_pair)
        else:
            reconstructed.append(token)  # Keep it as is if not found
    return reconstructed


# def handle_negation(tokens):
#     negation_words = ['لا', 'لم', 'ما', 'لن']
#     negation_word = ""
#     final_tokens = []
#     orig_tokens = []
    
#     for token in tokens:
#         orig_token = token

#         if token in negation_words:
#             negation_word = token
#         else:
#             if negation_word != "":
#                 orig_token = negation_word + " " + token
#                 token = "NOT" + '_' + token  # Add a marker for negation
#                 negation_word = ""
#             final_tokens.append(token)
#             orig_tokens.append(orig_token)
    
#     return final_tokens, orig_tokens
    
# Combined Preprocessing Function
def preprocess_arabic_text(text):

    text = text.replace('\n', ' ').replace('\r', ' ')
    # Replace multiple spaces with a single space
    text = re.sub(' +', ' ', text)

    
    # Step 2: Tokenization
    original_tokens = tokenize_text(text)

    # Step 3: Cleaning
    tokens = clean_text(original_tokens)

    
    # tokens, original_tokens = handle_negation(tokens)

    # Step 1: Normalization
    tokens = normalize_token(tokens)

    # remove tashkeel
    tokens = remove_tashkeel(tokens)

    
    # Step 5: Lemmatization
    token_mapping = lemmatize_tokens(tokens)  # Get the mapping of lemmatized to original tokens  

    # Use the lemmatized tokens for further processing
    tokens = [token[0] for token in token_mapping]  # Get only the lemmatized tokens

    
    # # Step 6: Negation Handling
    tokens = handle_negation(tokens)



    # Step 4: Stopword Removal
    tokens = remove_stopwords(tokens)
    
    preprocessed_text = ' '.join(tokens)
    
    reconstruct_tokens = reconstruct_text(tokens, token_mapping)

    token_mapping = []
    
    # Ensure we map only existing tokens
    for token, original in zip(reconstruct_tokens, original_tokens):
        token_mapping.append((token,original))

    # Step 6: Negation Handling
    reconstruct_tokens = handle_specific_words(reconstruct_tokens)
    # print("token_mapping",token_mapping)
    reconstruct_review = ' '.join(reconstruct_tokens)
    reconstruct_review = re.sub(r'\s+', ' ', reconstruct_review).strip()
    print("reconstruct_review123", reconstruct_review)
    
    return reconstruct_review, token_mapping



#post processing


def wrap_words_with_span(text):
    # Regular expression to match words of 2 or more characters
    words = re.findall(r'\S+', text)  # \S+ matches any sequence of non-whitespace characters

    wrapped_text = ''
    
    for word in words:
        # Use regular expression to remove punctuation from word
        cleaned_word = re.sub(r'[^\w\s]', '', word)

        if len(cleaned_word) > 1:  # Only wrap words that have more than 1 letter
            wrapped_text += f"<span>{word}</span> "
        else:
            wrapped_text += word + ' '

    return wrapped_text.strip()



def get_original_token(text, mapping):
    # Tokenize the input text
    tokenized_text = tokenize_text(text)
    
    # Initialize the replaced_text variable with the original text
    replaced_text = text
    
    if len(tokenized_text) > 1:
        replaced_words = []
        indices = []
        
        for word in tokenized_text:
            # Find the corresponding value for the word in mapping
            found = next(((k, v) for (k, v) in mapping if word == k), None)
            if found is not None:
                replaced_words.append(found[1])  # Append the value (v) to the replaced words
                indices.append(mapping.index(found))  # Get the index in mapping
    
        # Check if indices are in the same order and consecutive
        if all(indices[i] < indices[i + 1] for i in range(len(indices) - 1)):
            print("All words found in the same order in mapping.")
            # Join the replaced words into a single string
            replaced_text = ' '.join(replaced_words)
        else:
            print("Words are not in the same order in mapping.")
    else:
        # Handle case for single word
        for k, v in mapping:
            if tokenized_text[0] == k:
                replaced_text = v  # Replace the single word with its mapped value
                break

    return replaced_text




# Step 5: Lemmatization using Analyzer
def get_root_word(word):
    
    #remove tashkeel
    cleaned_word = dediac_ar(word)

    #noemalize
    cleaned_word = normalize_text(cleaned_word)
    cleaned_word = dediac_ar(cleaned_word)

    #lemmatized
    analyses = analyzer.analyze(word)
    if analyses:
        cleaned_word = analyses[0]['lex']
    
    else:
        # Handle the case where no analysis was found
        cleaned_word = cleaned_word  # Or any fallback mechanism you prefer


    cleaned_word = normalize_text(cleaned_word)
    cleaned_word = dediac_ar(cleaned_word)
    

    return cleaned_word


def extract_aspect_data(generated_text):

    aspect_data_list = []

    # Regular expression to match each aspect object, focusing on "phrases"
    pattern = r'\{\s*"aspect":\s*[^{}]*"opinions":\s*\[[^\]]*\]\s*\}'
    
    # Find all matches
    aspects_data = re.findall(pattern, generated_text, re.DOTALL)

    for aspect_data in aspects_data:
        aspect_data = aspect_data.strip()

        aspect_data_to_save = json.loads(aspect_data)
        aspect_data_list.append(aspect_data_to_save)
    return aspect_data_list