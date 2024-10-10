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
def getOveralSentiment():
    # Initialize counters
    positive_count = 0
    negative_count = 0
    total_count = 0

    aspects_data = aspects_collection.find({
    "polarity": { 
        "$nin": ["mixed", "neutral"] 
    }
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



def group_aspects_and_calculate_sentiments():
    # Step 1: Group by original_aspect and count occurrences
    aspects_data = aspects_collection.find({
    "polarity": { 
        "$nin": ["mixed", "neutral"] 
    }
    })

    aspect_count = defaultdict(int)
    aspect_sentiments = defaultdict(lambda: {'positive': 0, 'negative': 0})
    
    # Group aspects and count occurrences
    for aspect in aspects_data:
        original_aspect = aspect['original_aspect']
        polarity = aspect['polarity']
        
        # Increment the count for each original_aspect
        aspect_count[original_aspect] += 1
        
        # Track sentiment counts for each original_aspect
        aspect_sentiments[original_aspect][polarity] += 1
    
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



def get_top_aspects_and_opinions():
    # Step 1: Group aspects by polarity, and collect counts and opinions
    aspects_data = aspects_collection.find({"polarity": {"$nin": ["mixed", "neutral"]}})

    positive_aspects = defaultdict(int)
    negative_aspects = defaultdict(int)
    positive_opinions = defaultdict(list)
    negative_opinions = defaultdict(list)

    # Group aspects by polarity
    for aspect in aspects_data:
        original_aspect = aspect['original_aspect']
        polarity = aspect['polarity']

        # Append opinions (if available) for each aspect
        if 'opinions' in aspect:
            opinions = aspect['opinions']

            if polarity == "positive":
                positive_aspects[original_aspect] += 1
                text = ', '.join([f"{item}" for item in opinions])
                # positive_opinions[original_aspect].extend(text)
                positive_opinions[original_aspect].append(text)
            elif polarity == "negative":
                negative_aspects[original_aspect] += 1
                text = ', '.join([f"{item}" for item in opinions])
                # negative_opinions[original_aspect].extend(text)
                negative_opinions[original_aspect].append(text)

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


def get_aspect_counts_by_month():

    # Fetch all reviews and aspects
    reviews_data = list(reviews_collection.find({}))
    aspects_data = list(aspects_collection.find({"polarity": {"$nin": ["mixed", "neutral"]}}))

    # Convert the data to Pandas DataFrames
    reviews_df = pd.DataFrame(reviews_data)
    aspects_df = pd.DataFrame(aspects_data)

    # Convert the review datetime to a proper datetime format (handling different formats)
    reviews_df['review_datetime_utc'] = pd.to_datetime(reviews_df['review_datetime_utc'], errors='coerce')

    # Extract month and year
    reviews_df['month'] = reviews_df['review_datetime_utc'].dt.strftime('%B')  # Month name
    reviews_df['year'] = reviews_df['review_datetime_utc'].dt.year

    # Merge aspects with reviews on 'review_id'
    merged_df = pd.merge(aspects_df, reviews_df[['review_id', 'review_datetime_utc', 'month', 'year']], on='review_id')

    # Filter out mixed or neutral polarity aspects
    filtered_df = merged_df[merged_df['polarity'].isin(['positive', 'negative'])]

    # Group by year, month, and polarity, then count occurrences
    grouped = filtered_df.groupby(['year', 'month', 'polarity']).size().unstack(fill_value=0).reset_index()

    # Prepare the JSON response
    result = []
    for _, row in grouped.iterrows():
        result.append({
            "year": int(row['year']),
            "month": row['month'],
            "positive_count": int(row.get('positive', 0)),  # Get positive count or default to 0
            "negative_count": int(row.get('negative', 0))   # Get negative count or default to 0
        })

    # Directly return the JSON response
    return result

# # Call the function (for testing purposes)
# json_result = get_aspect_counts_by_month()
# print(json_result)

# def get_aspect_category_sentiment_analysis():
#     # Step 1: Initialize containers to store counts for each category
#     category_counts = defaultdict(lambda: {'positive': 0, 'negative': 0, 'total': 0})

#     # Step 2: Fetch data from the collection and group by category
#     aspects_data = aspects_collection.find({
#         "polarity": {"$nin": ["mixed", "neutral"]}  # Exclude mixed and neutral
#     })

#     for aspect in aspects_data:
#         category = aspect['category']  # Assuming 'category' field exists
#         polarity = aspect['polarity']

#         # Update counts for the category
#         if polarity == 'positive':
#             category_counts[category]['positive'] += 1
#         elif polarity == 'negative':
#             category_counts[category]['negative'] += 1

#         # Update total count for the category
#         category_counts[category]['total'] += 1

#     # Step 3: Calculate percentages and prepare the result
#     results = []
#     for category, counts in category_counts.items():
#         total = counts['total']
#         positive_count = counts['positive']
#         negative_count = counts['negative']

#         positive_percentage = (positive_count / total) * 100 if total > 0 else 0
#         negative_percentage = (negative_count / total) * 100 if total > 0 else 0

#         results.append({
#             'category': category,
#             'positive_count': positive_count,
#             'positive_percentage': round(positive_percentage, 2),
#             'negative_count': negative_count,
#             'negative_percentage': round(negative_percentage, 2),
#             'total_reviews': total
#         })

#     # Step 4: Return the final grouped results
#     return results

# #1- Calculate Average Sentiment
# # Get all aspects related to reviews
# aspects = aspects_collection.find()
# polarity_scores = []

# for aspect in aspects:
#     # Convert polarity_score to float
#     polarity_score = float(aspect["polarity_score"].replace("+", ""))
#     # print(polarity_score)
#     polarity_scores.append(polarity_score)

# # Calculate average sentiment
# average_sentiment_score = np.mean(polarity_scores)

# if(average_sentiment_score > 0.50):
#     average_sentiment = "positive"
# elif(average_sentiment_score < 0.50):
#     average_sentiment = "negative"
# else:
#     average_sentiment = "neutral"
    
# print(f"Average Sentiment Score: {average_sentiment_score:.2f}")
# print(f"Average Sentiment: {average_sentiment}")


# # Retrieve reviews with their associated aspect sentiments
# reviews = reviews_collection.find()
# sentiments_over_time = []

# for review in reviews:
#     review_date = pd.to_datetime(review["review_datetime_utc"], format="%m/%d/%Y %H:%M:%S")
#     review_id = review["review_id"]

#     # Find aspects for this review
#     aspects_for_review = aspects_collection.find({"review_id": review_id})
    
#     # Calculate average polarity score for this review
#     review_polarity_scores = [float(aspect["polarity_score"].replace("+", "")) for aspect in aspects_for_review]
#     if review_polarity_scores:
#         average_review_sentiment = np.mean(review_polarity_scores)
#         sentiments_over_time.append((review_date, average_review_sentiment))

# # Create a DataFrame for plotting
# sentiment_df = pd.DataFrame(sentiments_over_time, columns=["date", "sentiment"])
# sentiment_df.set_index("date", inplace=True)

# # Resample by day and calculate the mean sentiment
# daily_sentiment = sentiment_df.resample("D").mean()

# # Plotting
# plt.figure(figsize=(12, 6))
# plt.plot(daily_sentiment.index, daily_sentiment["sentiment"], marker='o')
# plt.title("Average Sentiment Over Time")
# plt.xlabel("Date")
# plt.ylabel("Average Sentiment Score")
# plt.grid()
# plt.xticks(rotation=45)
# plt.tight_layout()
# plt.show()



# # 2- Track Sentiment Over Time


# # Retrieve reviews with their associated aspect sentiments
# reviews = reviews_collection.find()
# sentiments_over_time = []

# for review in reviews:
#     review_date = pd.to_datetime(review["review_datetime_utc"], format="%m/%d/%Y %H:%M:%S")
#     review_id = review["review_id"]

#     # Find aspects for this review
#     aspects_for_review = aspects_collection.find({"review_id": review_id})
    
#     # Calculate average polarity score for this review
#     review_polarity_scores = [float(aspect["polarity_score"].replace("+", "")) for aspect in aspects_for_review]
#     if review_polarity_scores:
#         average_review_sentiment = np.mean(review_polarity_scores)

#         # Categorize sentiment
#         if average_review_sentiment > 0.1:  # Adjust threshold as necessary
#             sentiment_category = 'positive'
#         elif average_review_sentiment < -0.1:  # Adjust threshold as necessary
#             sentiment_category = 'negative'
#         else:
#             sentiment_category = 'neutral'
        
#         sentiments_over_time.append((review_date, sentiment_category))

# # Create a DataFrame for sentiment counts
# sentiment_df = pd.DataFrame(sentiments_over_time, columns=["date", "sentiment"])
# sentiment_df.set_index("date", inplace=True)

# # Count occurrences of each sentiment per month
# monthly_sentiment_counts = sentiment_df.groupby([sentiment_df.index.to_period("M"), 'sentiment']).size().unstack(fill_value=0)

# # Plotting
# plt.figure(figsize=(12, 6))
# monthly_sentiment_counts.plot(kind='line', marker='o', color=['green', 'red', 'gray'])  # Green for positive, Red for negative, Gray for neutral
# plt.title("Monthly Sentiment Change")
# plt.xlabel("Month")
# plt.ylabel("Count of Sentiments")
# plt.grid()
# plt.xticks(rotation=45)
# plt.legend(title='Sentiment', labels=['Positive', 'Negative', 'Neutral'])
# plt.tight_layout()
# plt.show()