# import nltk
# from nltk.corpus import stopwords
# from camel_tools.utils.normalize import normalize_alef_maksura_ar
# from camel_tools.utils.normalize import normalize_alef_ar
# from camel_tools.utils.normalize import normalize_teh_marbuta_ar
# from camel_tools.utils.dediac import dediac_ar
# from camel_tools.morphology.database import MorphologyDB
# from camel_tools.morphology.analyzer import Analyzer
# import string
# import re
# from camel_tools.tokenizers.word import simple_word_tokenize
# from camel_tools.disambig.mle import MLEDisambiguator
# from camel_tools.utils.dediac import dediac_ar

# nltk.download('stopwords')



# db = MorphologyDB.builtin_db()
# analyzer = Analyzer(db)

# # Example Arabic stopwords
# stop_words = stopwords.words()


# # Step 1: Normalization
# def normalize_text(text):
#     # Normalize alef variants to 'ا'
#     text = normalize_alef_ar(text)
#     # Normalize alef maksura 'ى' to yeh 'ي'
#     text = normalize_alef_maksura_ar(text)   
#     # Normalize teh marbuta 'ة' to heh 'ه'
#     text = normalize_teh_marbuta_ar(text)
#     return text

# # Step 2: Tokenization
# def tokenize_text(text):
#     tokens = simple_word_tokenize(text)
#     return tokens

# # Step 3: Cleaning (Remove elongations, special characters, numbers, punctuation)
# def clean_text(tokens):
#     cleaned_tokens = []
#     for token in tokens:
#         # Remove elongation (e.g., جمييييل => جميل)
#         token = re.sub(r'(.)\1+', r'\1', token)
#         # Remove non-Arabic characters, punctuation, and numbers
#         token = re.sub(r'[^\u0600-\u06FF]', '', token)
#         cleaned_tokens.append(token)
#     return cleaned_tokens


# def remove_tashkeel(tokens):
#     new_tokens = []
#     for token in tokens:
#         token = dediac_ar(token)
#         new_tokens.append(token)
#     return new_tokens


# # Step 4: Stopword Removal (replace stopwords with empty string)
# def remove_stopwords(tokens):
#     return [token if token not in stop_words else "" for token in tokens]


# # Step 5: Lemmatization using Analyzer
# def lemmatize_tokens(tokens):
#     token_original_mapping = []  # Dictionary to hold token-original pairs
    
#     for token in tokens:
        
#         analyses = analyzer.analyze(token)  # Analyze the word
        
#         # Collect unique lemmas from the analysis
#         lemmas = set()  # Use a set to avoid duplicates
#         for analysis in analyses:
#             lemmas.add(analysis['lex'])  # 'lex' key contains the lemma

#         # If lemmas exist, add the first lemma to lemmatized tokens
#         if lemmas:
#             lemmatized_token = list(lemmas)[0]  # Use the first lemma
#             token_original_mapping.append((lemmatized_token, token))

#         else:
#             token_original_mapping.append((token, token))
        
#     return token_original_mapping  # Return the mapping dictionary

# # Step 6: Negation Handling
# def handle_negation(tokens):
#     negation_words = ['لا', 'لم', 'ما', 'لن']
#     negation_active = False
#     final_tokens = []
    
#     for token in tokens:
#         if token in negation_words:
#             negation_active = True
#         else:
#             if negation_active:
#                 token = 'NOT_ ' + token  # Add a marker for negation
#                 negation_active = False
#             final_tokens.append(token)
    
#     return final_tokens


# # Function to reconstruct text from lemmatized tokens
# def reconstruct_text(tokens, token_mapping):
#     reconstructed = []
#     for token in tokens:     
#         if "NOT_" in token:
#             cleaned_token = token.replace("NOT_", "").strip()
#             if any(key == cleaned_token for key, val in token_mapping):
#                 found_value = next((value for key, value in token_mapping if key == cleaned_token), None)
#                 original_token = 'NOT_ ' + found_value
#                 reconstructed.append(original_token)
#             else:
#                 reconstructed.append(token)  # Keep it as is if not found
#         elif any(key == token for key, val in token_mapping):
#             found_value = next((value for key, value in token_mapping if key == token), None)
#             reconstructed.append(found_value)
#         else:
#             reconstructed.append(token)  # Keep it as is if not found
#     return reconstructed


# # Combined Preprocessing Function
# def preprocess_arabic_text(text):

#     text = text.replace('\n', ' ').replace('\r', ' ')
#     # Replace multiple spaces with a single space
#     text = re.sub(' +', ' ', text)

#     # Step 1: Normalization
#     text = normalize_text(text)
    
#     # Step 2: Tokenization
#     tokens = tokenize_text(text)
#     print("tokens111: ", len(tokens))

#     # Step 3: Cleaning
#     tokens = clean_text(tokens)
    
#     # remove tashkeel
#     tokens = remove_tashkeel(tokens)

#     # Step 5: Lemmatization
#     # Step 5: Lemmatization
#     token_mapping = lemmatize_tokens(tokens)  # Get the mapping of lemmatized to original tokens    
#     print("tokens333: ", len(tokens))
#     # Use the lemmatized tokens for further processing
#     tokens = [token[0] for token in token_mapping]  # Get only the lemmatized tokens
#     print("tokens444: ", len(tokens))

#     # Step 6: Negation Handling
#     tokens = handle_negation(tokens)

#      # Step 4: Stopword Removal
#     tokens = remove_stopwords(tokens)

#     preprocessed_text = ' '.join(tokens)

    
#     reconstruct_tokens = reconstruct_text(tokens, token_mapping)
#     reconstruct_review = ' '.join(reconstruct_tokens)
#     reconstruct_review = re.sub(r'\s+', ' ', reconstruct_review).strip()


#     return reconstruct_review
