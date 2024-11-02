import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt
from .database import get_database
from bson.objectid import ObjectId
from collections import defaultdict, Counter
# Initialize collections

db = get_database()
if db is not None:
    reviews_collection = db['reviews']
    aspects_collection = db['aspects']
    business_collection = db['business']
    errors_log_collection = db['errors_log']
else:
    reviews_collection = None
    aspects_collection = None
    business_collection = None
    errors_log_collection = None


# Helper function to calculate sentiment percentages (from the previous code)
def calculate_sentiment_percentage(positive_count, negative_count, total_count):
    
    # Initial percentage calculation (with rounding)
    positive_percentage = round((positive_count / total_count) * 100)
    negative_percentage = round((negative_count / total_count) * 100)
    # neutral_percentage = round((neutral_count / total_count) * 100)
    
    # Ensure total is 100 by adjusting the largest value
    total_percentage = positive_percentage + negative_percentage
    if total_percentage != 100:
        # Find the category with the largest percentage and adjust it
        max_percentage = max(positive_percentage, negative_percentage)
        
        if max_percentage == positive_percentage:
            positive_percentage += 100 - total_percentage
        elif max_percentage == negative_percentage:
            negative_percentage += 100 - total_percentage
        # else:
        #     neutral_percentage += 100 - total_percentage
    
    return positive_percentage, negative_percentage


#1- Calculate overall sentiment polarity
def getOveralSentiment(business_id):
    # Initialize counters
    positive_count = 0
    negative_count = 0
    total_count = 0

    aspects_data = aspects_collection.find({
    "polarity": { 
        "$nin": ["mixed", "neutral"]
    },
    "business_id": business_id  # Add this filter to match the specific business_id
    })

    # Iterate over each document in the aspects collection
    for aspect in aspects_data:
        polarity = aspect['polarity']
        
        # Increment based on polarity
        if polarity == "positive":
            positive_count += 1
            total_count += 1
        elif polarity == "negative":
            negative_count += 1
            total_count += 1

        
    total_count = positive_count + negative_count

    positive_percentage, negative_percentage = calculate_sentiment_percentage(positive_count, negative_count, total_count)
    overal_sentiment = {
        "total": {"count": total_count, "percentage": "100"},
        "positive": {"count": positive_count, "percentage": positive_percentage},
        "negative": {"count": negative_count, "percentage": negative_percentage}
    }

    return overal_sentiment



def group_aspects_and_calculate_sentiments(business_id):
    # Step 1: Group by root_aspect and count occurrences
    aspects_data = aspects_collection.find({
    "polarity": { 
        "$nin": ["mixed", "neutral"]
    },
    "business_id": business_id  # Add this filter to match the specific business_id
    })

    aspect_count = defaultdict(int)
    aspect_sentiments = defaultdict(lambda: {'positive': 0, 'negative': 0})
    
    # Group aspects and count occurrences
    for aspect in aspects_data:
        print("aspect_id",aspect['_id'])

        root_aspect = aspect['root_aspect']
        polarity = aspect['polarity']
        
        # Increment the count for each root_aspect
        aspect_count[root_aspect] += 1
        
        # Track sentiment counts for each root_aspect
        aspect_sentiments[root_aspect][polarity] += 1
    
    # Step 2: Find the top 4 most popular aspects based on count
    most_popular_aspects = Counter(aspect_count).most_common(4)

    
    # Step 3: Calculate sentiment percentages for each of the top 4 aspects
    results = []
    for aspect, count in most_popular_aspects:
        positive_count = aspect_sentiments[aspect]['positive']
        negative_count = aspect_sentiments[aspect]['negative']
        
        total_count = positive_count + negative_count
        
        # Calculate percentages and ensure they sum to 100
        positive_percentage, negative_percentage = calculate_sentiment_percentage(
            positive_count, negative_count, total_count
        )
        
        # Store the results for each aspect
        results.append({
            'aspect': aspect,
            "total": {"count": total_count, "percentage": "100"},
            "positive": {"count": positive_count, "percentage": positive_percentage},
            "negative": {"count": negative_count, "percentage": negative_percentage}
        })
    
    return results



def get_top_aspects_and_opinions(business_id):
    # Step 1: Group aspects by polarity, and collect counts and opinions
    aspects_data = aspects_collection.find({
        "polarity": { 
            "$nin": ["mixed", "neutral"]
        },
        "business_id": business_id  # Add this filter to match the specific business_id
        })

    positive_aspects = defaultdict(int)
    negative_aspects = defaultdict(int)
    positive_opinions = defaultdict(list)
    negative_opinions = defaultdict(list)

    # Group aspects by polarity
    for aspect in aspects_data:
        root_aspect = aspect['root_aspect']
        polarity = aspect['polarity']

        # Append opinions (if available) for each aspect
        if 'opinions' in aspect:
            opinions = aspect['opinions']

            if polarity == "positive":
                positive_aspects[root_aspect] += 1
                text = ', '.join([f"{item}" for item in opinions])
                # positive_opinions[root_aspect].extend(text)
                positive_opinions[root_aspect].append(text)
            elif polarity == "negative":
                negative_aspects[root_aspect] += 1
                text = ', '.join([f"{item}" for item in opinions])
                # negative_opinions[root_aspect].extend(text)
                negative_opinions[root_aspect].append(text)

    # Step 2: Find the top 3 most popular positive and negative aspects
    top_positive_aspects = Counter(positive_aspects).most_common(3)
    top_negative_aspects = Counter(negative_aspects).most_common(3)

    # Step 3: Format results with aspect name, count, and opinions
    positive_results = [
        {
            'aspect': aspect,
            'count': count,
            'opinions': positive_opinions[aspect]
        }
        for aspect, count in top_positive_aspects
    ]

    negative_results = [
        {
            'aspect': aspect,
            'count': count,
            'opinions': negative_opinions[aspect]
        }
        for aspect, count in top_negative_aspects
    ]

    # Step 4: Return both positive and negative results
    return {
        'top_positive_aspects': positive_results,
        'top_negative_aspects': negative_results
    }


def get_aspect_counts_by_month(business_id):
    # Fetch all reviews and aspects
    reviews_data = list(reviews_collection.find({
        "business_id": business_id  # Filter by business_id
    }))

    aspects_data = list(aspects_collection.find({
        "polarity": {"$nin": ["mixed", "neutral"]},  # Filter by polarity
        "business_id": business_id                    # Filter by business_id
    }))

    # Convert the data to Pandas DataFrames
    reviews_df = pd.DataFrame(reviews_data)
    aspects_df = pd.DataFrame(aspects_data)

    # Convert the review datetime to a proper datetime format (handling different formats)
    reviews_df['review_datetime_utc'] = pd.to_datetime(reviews_df['review_datetime_utc'], errors='coerce')

    # Extract month and year
    reviews_df['month'] = reviews_df['review_datetime_utc'].dt.month  # Month as integer
    reviews_df['year'] = reviews_df['review_datetime_utc'].dt.year

    # Merge aspects with reviews on 'review_id'
    merged_df = pd.merge(aspects_df, reviews_df[['review_id', 'review_datetime_utc', 'month', 'year']], on='review_id')

    # Filter out mixed or neutral polarity aspects
    filtered_df = merged_df[merged_df['polarity'].isin(['positive', 'negative'])]

    # Group by year, month, and polarity, then count occurrences
    grouped = filtered_df.groupby(['year', 'month', 'polarity']).size().unstack(fill_value=0).reset_index()

    # Define month order in Arabic
    month_order = {
        1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل', 5: 'مايو', 6: 'يونيو',
        7: 'يوليو', 8: 'أغسطس', 9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
    }
    grouped['month_name'] = grouped['month'].map(month_order)

    # Sort by year and month using month as numeric order
    grouped = grouped.sort_values(by=['year', 'month'])

    # Prepare the JSON response
    result = []
    for _, row in grouped.iterrows():
        result.append({
            "year": int(row['year']),
            "month": row['month_name'],  # Use the Arabic month name
            "positive_count": int(row.get('positive', 0)),  # Get positive count or default to 0
            "negative_count": int(row.get('negative', 0))   # Get negative count or default to 0
        })

    # Directly return the JSON response
    return result
