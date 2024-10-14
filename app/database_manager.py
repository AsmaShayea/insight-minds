from pymongo import MongoClient

def get_mongo_connection(db_name='insight_minds'):
    client = MongoClient('mongodb://localhost:27017/')
    return client[db_name]
