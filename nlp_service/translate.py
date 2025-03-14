import os
import uuid
import json
import base64
import requests
from pymongo import MongoClient
from tqdm import tqdm
from dotenv import load_dotenv  

# Load environment variables
load_dotenv()


# MongoDB Connection
mongo_url = os.getenv("mongo_url")
if not mongo_url:
    raise ValueError("MongoDB URL not found in .env")


# Google Vision API Key
api_key = os.getenv("api_key")
if not api_key:
    raise ValueError("MongoDB URL not found in .env")


def call_google_translate_api(text: str,target: str='en',API_KEY=api_key) -> dict:
    

    url = f"https://translation.googleapis.com/language/translate/v2"
    
    params = {
        "q": text,
        "target": target,
        "format": "text",
        "key": API_KEY
    }
    try:
        response = requests.post(url, params=params)
        response = response.json()
        # print(response)
        return response, "completed"
    except Exception as e:  
        return str(e), "error"
    

if __name__ == "__main__":

    client = MongoClient(mongo_url)
    db = client["ml_data_labelling"]
    coll = db["translation_labelling_data"]
    
        
    docs = coll.find({"sentence_extracted_status":{"$exists":True},"translation_status":{"$exists":False}})
    count = coll.count_documents({"sentence_extracted_status":{"$exists":True},"translation_status":{"$exists":False}})

    for doc in tqdm(docs,total=count):
        text = doc['text']
        translation_response,status = call_google_translate_api(text)
        # print(translation_response)

        coll.update_one({"_id": doc["_id"]}, {'$set': {'translation_response': translation_response, "translation_status": status}})

        # break

    