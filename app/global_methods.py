# def get_common_aspects_and_reviews(aspects_collection):
#     # Step 1: Find aspects that are repeated more than 3 times, grouped by aspect, original_aspect, and polarity
#     pipeline = [
#         {"$group": {
#             "_id": {"aspect": "$aspect", "original_aspect": "$original_aspect", "polarity": "$polarity"},  # Group by aspect, original_aspect, and polarity
#             "count": {"$sum": 1},  # Count occurrences
#             "all_opinions": {"$push": "$opinions"}  # Collect associated opinions into an array
#         }},
#         {"$match": {"count": {"$gt": 3}}},  # Keep only aspects mentioned more than 3 times
#         {"$sort": {"count": -1}}  # Sort by count in descending order
#     ]
    
#     common_aspects = list(aspects_collection.aggregate(pipeline))
    
#     # Step 2: Split aspects into positive and negative categories
#     positive_aspects = [entry for entry in common_aspects if entry['_id']['polarity'] == 'positive'][:3]  # Top 3 positive aspects
#     negative_aspects = [entry for entry in common_aspects if entry['_id']['polarity'] == 'negative'][:3]  # Top 3 negative aspects
    
#     retrieved_data = []
#     for aspect_entry in positive_aspects + negative_aspects:
#         aspect = aspect_entry['_id']['aspect']
#         original_aspect = aspect_entry['_id']['original_aspect']  # Retrieve original_aspect
#         sentiment = aspect_entry['_id']['polarity']
#         all_opinions = aspect_entry['all_opinions']  # Get all collected opinions arrays
        
#         # Flatten the list of lists for opinions (since opinions are stored as arrays within arrays)
#         flattened_opinions = [opinion for sublist in all_opinions for opinion in sublist]
        
#         # Add to the final retrieved data structure
#         retrieved_data.append({
#             'original_aspect': original_aspect,
#             'sentiment': sentiment,
#             'all_opinions': flattened_opinions,  # Store all consolidated opinions in the final structure
#         })
#     return retrieved_data


import re

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
