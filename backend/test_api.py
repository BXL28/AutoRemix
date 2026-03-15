import os
from dotenv import load_dotenv
import requests
import ast

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")

url = f"https://{RAPIDAPI_HOST}/get_mp3_download_link/fHI8X4OXluQ"
querystring = {"quality": "low", "wait_until_the_file_is_ready": "true"}
headers = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers, params=querystring)
raw_text = response.text
print("Raw text:", raw_text)

try:
    # RapidAPI sometimes returns a stringified python dictionary like "{'dlink': '...'}"
    data = ast.literal_eval(raw_text)
    print("Parsed data:", dict(data))
    print("DLINK:", data.get("dlink"))
except Exception as e:
    print("Error parsing:", e)
