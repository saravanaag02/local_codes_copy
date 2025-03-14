import requests
import os
from pymongo import MongoClient
from tqdm import tqdm
from dotenv import load_dotenv
load_dotenv()

mongo_url = os.getenv("sarvagya_url")
if not mongo_url:
    raise ValueError("MongoDB URL not found in .env")

client = MongoClient(mongo_url)
db = client["ml_data_labelling"]
coll = db["ner_labelling_data"]

api_key = os.getenv("api_key", None)
if api_key is None:
    raise ValueError("API key not found in .env")

# Function to call Google Cloud NER API
def call_google_ner(text, api_key=api_key):
    url = f"https://language.googleapis.com/v2/documents:analyzeEntities?key={api_key}"
    
    payload = {
        "document": {
            "type": "PLAIN_TEXT",
            "content": text
        },
        "encodingType": "UTF8"
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    
    # Debugging: Print response status and text if there's an issue
    if response.status_code != 200:
        # print("Error:", response.status_code, response.text)
        return {"error": response.status_code,"error_message":response.text} ,"error"

    return response.json(),"sucess"

if __name__ == "__main__":
        
    docs = coll.find({"ner_status":{"$exists":False}})
    count = coll.count_documents({"ner_status":{"$exists":False}})

    for doc in tqdm(docs,total=count):
        text = doc['text']
        ner_response,status = call_google_ner(text)
        try:
            if status == "sucess":
                coll.update_one({"_id":doc['_id']},{'$set':{"ner_response":ner_response,"ner_status":"completed"}})
            else:
                coll.update_one({"_id":doc['_id']},{'$set':{"ner_response":ner_response,"ner_status":status}})
            # break
        except Exception as e:
            print("Error :",e)
