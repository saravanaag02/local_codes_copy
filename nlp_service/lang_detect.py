import os
from pymongo import MongoClient
from tqdm import tqdm
from dotenv import load_dotenv  
from langdetect import detect


# Load environment variables
load_dotenv()


# MongoDB Connection
mongo_url = os.getenv("mongo_url")
if not mongo_url:
    raise ValueError("MongoDB URL not found in .env")

client = MongoClient(mongo_url)
db = client["ml_data_labelling"]
coll = db["translation_labelling_data"]



if __name__ == "__main__":
        
    docs = coll.find({"lang_detect_status":{"$exists":False}})
    count = coll.count_documents({"lang_detect_status":{"$exists":False}})

    for doc in tqdm(docs,total=count):

        try:
            lang = detect(doc['text'])

            coll.update_one({"_id": doc["_id"]}, {'$set': {'lang': lang, "lang_detect_status": "completed"}})
        except Exception as e:
            coll.update_one({"_id": doc["_id"]}, {'$set': {'lang': "", "lang_detect_status": "error"}})
            

        # break

    