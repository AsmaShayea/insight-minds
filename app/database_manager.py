from pymongo import MongoClient

def get_mongo_connection(db_name='insight_minds'):
    client = MongoClient('mongodb+srv://asma:Sami8407@insightsmindscluster0.34evged.mongodb.net/?retryWrites=true&w=majority&appName=InsightsMindsCluster0')
    return client[db_name]
