import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST")
from youtubesearchpython import VideosSearch

def search_youtube_video(query: str) -> str:
    """Search YouTube for a query and return the first video ID matching the query using youtube-search-python."""
    print(f"Searching YouTube for: {query}")
    try:
        videos_search = VideosSearch(query, limit=1)
        results = videos_search.result()
        
        if results and results.get("result") and len(results["result"]) > 0:
            video_id = results["result"][0]["id"]
            print(f"Found YouTube Video ID: {video_id}")
            return video_id
        else:
            print("No YouTube video found.")
            return None
    except Exception as e:
        print(f"Error searching YouTube: {e}")
        return None

def download_mp3(video_id: str, output_path: str) -> str:
    """Download MP3 using the specified RapidAPI service."""
    if not video_id:
        return None
        
    url = f"https://{RAPIDAPI_HOST}/get_mp3_download_link/{video_id}"
    
    querystring = {
        "quality": "low",
        "wait_until_the_file_is_ready": "true"
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }
    
    print(f"Requesting MP3 conversion from RapidAPI for video: {video_id}")
    try:
        import time
        max_retries = 20
        for attempt in range(max_retries):
            response = requests.get(url, headers=headers, params=querystring)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(f"HTTPError: {e}")
                print(f"Response Content: {response.text}")
                raise

            data = response.json()
            raw_text = response.text
            
            # API returns: {"comment": "The file will soon be ready...", "msg": "{...}"}
            # Or {"msg": "in queue..."}
            msg = data.get("msg")
            
            if msg == "in queue..." or "will soon be ready" in str(data.get("comment", "")):
                print(f"[{attempt+1}/{max_retries}] API is processing the video, waiting 4 seconds...")
                time.sleep(4)
                continue
                
            # If done, msg is a stringified python dictionary containing dlink
            download_url = None
            if msg and isinstance(msg, str) and "dlink" in msg:
                import ast
                try:
                    parsed_msg = ast.literal_eval(msg)
                    download_url = parsed_msg.get("dlink")
                except:
                    pass
                    
            if not download_url and data.get("dlink"):
                download_url = data.get("dlink")
            
            if download_url:
                print(f"Got download link: {download_url}. Downloading file...")
                
                # Download the actual file
                file_response = requests.get(download_url)
                file_response.raise_for_status()
                
                with open(output_path, "wb") as f:
                    f.write(file_response.content)
                
                print(f"Successfully saved to {output_path}")
                return output_path
            else:
                print(f"Unexpected RapidAPI response format or still waiting: {data}")
                time.sleep(4)
                
        print("RapidAPI timed out waiting for the video to process.")
        return None
            
    except Exception as e:
        import traceback
        print(f"Error calling RapidAPI or downloading file: {e}")
        traceback.print_exc()
        return None

# Test execution (will only run if called directly)
if __name__ == "__main__":
    test_query = "The Weeknd Blinding Lights Official Audio"
    vid_id = search_youtube_video(test_query)
    if vid_id:
        os.makedirs("downloads", exist_ok=True)
        download_mp3(vid_id, f"downloads/{vid_id}.mp3")
