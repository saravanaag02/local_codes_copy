import os
import requests
import base64
from dotenv import load_dotenv
from tqdm import tqdm 
from pymongo import MongoClient
import json
from bson import ObjectId
load_dotenv()

mongo_url = os.getenv("mongo_url", None)
if mongo_url is None:
    raise ValueError("Mongo url not found in .env")

api_key = os.getenv("api_key", None)
if api_key is None:
    raise ValueError("api key not found in .env")


def encode_image(image_path):

    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def call_google_vision_api(encoded_image, api_key):
    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    payload = {
        "requests": [
            {
                "image": {"content": encoded_image},
                "features": [{"type": "TEXT_DETECTION"}],  # OCR on an image
                # "encodingType": "UTF8"
            }
        ]
    }
    response = requests.post(url, json=payload)
    return response.json()

def extract_text_from_image(response):

    if "responses" in response and response["responses"]:
        annotations = response["responses"][0].get("textAnnotations", [])
        if annotations:
            return annotations[0]["description"]
    return ""

def save_extracted_text(text, output_folder, file_name):
    os.makedirs(output_folder, exist_ok=True)
    text_file_path = os.path.join(output_folder, f"{file_name}_gt.txt")

    with open(text_file_path, "w", encoding="utf-8") as text_file:
        text_file.write(text)

def process_image(file_path, api_key):
    """Processes an image: extracts text and saves it to a file."""
    if not os.path.isfile(file_path) or not file_path.lower().endswith((".png", ".jpg", ".jpeg")):
        print(f"Skipping non-image file: {file_path}")
        return {"error":"file not image"}, "file error"

    print(f"Processing: {file_path}")

    # Get necessary paths
    images_dir_path = os.path.dirname(file_path)
    output_folder = os.path.join(images_dir_path, "ground_truth")
    file_name = os.path.splitext(os.path.basename(file_path))[0]

    # Perform OCR
    encoded_image = encode_image(file_path)
    response = call_google_vision_api(encoded_image, api_key)
    

    extracted_text = extract_text_from_image(response)
    save_extracted_text(extracted_text.strip(), output_folder, file_name)

    return response,extracted_text


        
if __name__ == "__main__":
    
    db_name = "ml_data_labelling"
    coll_name = "ocr"
    client = MongoClient(mongo_url)
    db = client[db_name]
    coll = db[coll_name]

    # docs = coll.find({"ocr_status":{"$exists":False}})
    docs = coll.find({'text':{'$eq':""},'ocr_response':{'$eq':""}})

    # docs = coll.find({"_id":ObjectId("67ce95765bd049e754d9cf78")})

    # count = coll.count_documents({"ocr_status":{"$exists":False}})
    count = coll.count_documents({'text':{'$eq':""},'ocr_response':{'$eq':""}})

    
    for doc in tqdm(docs,total=count):
        image_path = doc["file_path"]
        ocr_response,ocr_text = process_image(image_path,api_key)
        # print("ocr_text",ocr_text)
        # print("ocr_response",ocr_response)
        if ocr_response == {'error': 'file not image'}:
            print("file error")
            coll.update_one({"_id": doc["_id"]}, {'$set': {'text': '', 'ocr_response': ocr_response, "ocr_status": "File error"}})

        elif isinstance(ocr_response.get("responses"), list) and isinstance(ocr_text, str):
            # print("hi")
            coll.update_one({"_id": doc["_id"]}, {'$set': {'text': ocr_text, 'ocr_response': ocr_response["responses"], "ocr_status": "completed"}})

        elif isinstance(ocr_response.get("error"), dict) and isinstance(ocr_text, str):
            print("eooro")
            coll.update_one({"_id": doc["_id"]}, {'$set': {'text': ocr_text, 'ocr_response': ocr_response["error"], "ocr_status": "error"}})
        # break

        

    



