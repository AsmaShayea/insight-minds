
import nltk
from nltk.corpus import stopwords
from camel_tools.utils.normalize import normalize_alef_maksura_ar, normalize_alef_ar, normalize_teh_marbuta_ar
from camel_tools.utils.dediac import dediac_ar
from camel_tools.morphology.database import MorphologyDB
from camel_tools.morphology.analyzer import Analyzer
import re
from camel_tools.tokenizers.word import simple_word_tokenize
from camel_tools.disambig.mle import MLEDisambiguator
import string
import json

nltk.download('stopwords')

# Initialize resources
db = MorphologyDB.builtin_db()
analyzer = Analyzer(db)
stop_words = set(stopwords.words())  # Faster look-up with set
negation_words = {'لا', 'لم', 'ما', 'لن'}
important_stopwords = {'المكان', 'مكان'}

# Example Arabic stopwords
stop_words = stopwords.words()


def clean_result(input_value):
    # Function to remove undesired substrings
    def remove_undesired(text):
        cleaned_text = re.sub(r"Place_", "", text)  # Remove "Place_"
        cleaned_text = re.sub(r"NOT_", "", text)  # Remove "Place_"
        cleaned_text = cleaned_text.replace("_", " ")  # Replace remaining underscores with spaces
        cleaned_text = re.sub(r'[.,،؛:;"\'؛:]', '', cleaned_text)
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
    
# Combined Preprocessing Function
def preprocess_arabic_text(text):
    # Initial cleanup of spaces
    text = text.replace('\n', ' ').replace('\r', ' ')
    # Replace multiple spaces with a single space
    text = re.sub(' +', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)  # Removes all punctuation

    
    # Tokenization
    tokens = simple_word_tokenize(text)

    text = clean_text(text)
    
    processed_tokens = []
    token_mapping = []  # To store original-to-processed token mapping

    # Negation state tracking
    negation_active = False

    for token in tokens:
        original_token = token  # Preserve original token for mapping

        # Step 1: Normalization
        # Normalize alef variants to 'ا'
        token = normalize_alef_ar(token)
        # Normalize alef maksura 'ى' to yeh 'ي'
        token = normalize_alef_maksura_ar(token)   
        # Normalize teh marbuta 'ة' to heh 'ه'
        token = normalize_teh_marbuta_ar(token)
        # Normalize teh marbuta 'ة' to heh 'ه'
        token = normalize_teh_marbuta_ar(token)
        
        # Step 2: Remove diacritics (Tashkeel)
        token = dediac_ar(token)
    

        # Step 4: Lemmatization
        lemmas = {analysis['lex'] for analysis in analyzer.analyze(token)}
        if lemmas:
            lemmitized_token = dediac_ar(list(lemmas)[0])  # Take the first lemma if available
        else:
            lemmitized_token = token
    

        # Step 4: Lemmatization
        lemmas = {analysis['lex'] for analysis in analyzer.analyze(token)}
        if lemmas:
            lemmitized_token = dediac_ar(list(lemmas)[0])  # Take the first lemma if available


        # Step 4: Negation Handling
        if lemmitized_token in negation_words:
            negation_word = token
            negation_active = True
            continue  # Skip adding the negation word itself

        if negation_active:
            original_token = negation_word + token
            token = f'NOT_{token}'
            negation_active = False  # Reset negation status


        # Step 5: Stopword Removal (skip if a stopword)
        if lemmitized_token in stop_words:
            continue

        # Step 7: Specific Word Handling
        if lemmitized_token in important_stopwords:
            token = f'Place_{token}'


    
        # Add the processed token to the final list and mapp


        # Step 4: Negation Handling
        if lemmitized_token in negation_words:
            negation_word = token
            negation_active = True
            continue  # Skip adding the negation word itself

        if negation_active:
            original_token = negation_word + token
            token = f'NOT_{token}'
            negation_active = False  # Reset negation status


        # Step 5: Stopword Removal (skip if a stopword)
        if lemmitized_token in stop_words:
            continue

        # Step 7: Specific Word Handling
        if lemmitized_token in important_stopwords:
            token = f'Place_{token}'


    
        # Add the processed token to the final list and mapping
        processed_tokens.append(token)
        token_mapping.append((original_token, token))

    # Join the processed tokens into a single string
    preprocessed_text = ' '.join(processed_tokens)

    return preprocessed_text, token_mapping

def get_original_token(processed_token, token_mapping):
    # Tokenize the processed token
    tokens = simple_word_tokenize(processed_token)
    original_tokens = []

    # Search for each token in the token mapping
    for token in tokens:
        found = False
        for original, processed in token_mapping:
            if processed == token:
                original_tokens.append(original)
                found = True
                break
        if not found:
            original_tokens.append(token)  # Keep the token as is if not found in mapping

    # Join the original tokens back into a single string
    return ' '.join(original_tokens)






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

# Step 2: Tokenization
def tokenize_text(text):
    tokens = simple_word_tokenize(text)
    return tokens

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