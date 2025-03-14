from indicnlp.tokenize import sentence_tokenize
import os
from pymongo import MongoClient
from tqdm import tqdm
from dotenv import load_dotenv
load_dotenv()

mongo_url = os.getenv("mongo_url")
if not mongo_url:
    raise ValueError("MongoDB URL not found in .env")


def extract_first_n_sentences(text:str, lang:str, n:int=2) ->str:

    try:
        sentences = sentence_tokenize.sentence_split(text, lang)
        # print(sentences)
        # print(len(sentences))
        return " ".join(sentences[:n+1]),"completed"
    except Exception as e:
        return str(e),"error"


if __name__ == "__main__":

    client = MongoClient(mongo_url)
    db = client["ml_data_labelling"]
    coll = db["translation_labelling_data"]
    
    # docs = coll.find({'_id':"96656477-2df8-4bd3-979d-d7078ae63eda"}) # urudu
    # docs = coll.find({'_id':"3b073c5c-1445-4a59-971a-f903e3a67fee"}) # arabic
    # docs = coll.find({'_id':"7714262c-f13a-415c-b014-9097e80035b4"}) # hindi
    # docs = coll.find({'_id':"a7de67ba-d80c-4e27-abb7-108da70602a4"}) # marthi

    docs = coll.find({"lang": "ar" ,"sentence_extracted_status":{"$exists":False}})
    count = coll.count_documents({"lang": "ar" ,"sentence_extracted_status":{"$exists":False}})

    for doc in tqdm(docs,total=count):
        # print(doc['_id'])
        text = doc['text']
        lang = doc['lang']
        # print("actual text :", text)

        sentence_extracted,status = extract_first_n_sentences(text,lang)
        coll.update_one({"_id": doc["_id"]}, {'$set': {'sentence_extracted': sentence_extracted, "sentence_extracted_status": status}})
        # print(doc["_id"])
        # break