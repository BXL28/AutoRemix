import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

# Initialize Spotipy client
auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

def search_track(query: str, limit: int = 5):
    """
    Search for a track by name and return the top match(es).
    """
    try:
        results = sp.search(q=query, type='track', limit=limit)
        return results['tracks']['items']
    except Exception as e:
        print(f"Error searching Spotify for {query}: {e}")
        return []

def get_track_audio_features(track_id: str):
    """
    Get audio features (BPM, key, mode, danceability, etc.) for a specific track.
    """
    try:
        features = sp.audio_features(track_id)
        if features and len(features) > 0 and features[0]:
            f = features[0]
            # Map key integer to standard musical key (0 = C, 1 = C#/Db, 2 = D, etc.)
            key_mapping = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            musical_key = key_mapping[f['key']] if 0 <= f['key'] <= 11 else "Unknown"
            
            # Map mode integer to Major/Minor
            mode = "Major" if f['mode'] == 1 else "Minor"
            
            return {
                "bpm": round(f['tempo']),
                "key": f"{musical_key} {mode}",
                "danceability": f['danceability'],
                "energy": f['energy']
            }
        return None
    except spotipy.SpotifyException as e:
        print(f"Spotify API Error fetching audio features for track {track_id}: {e.http_status} - {e.msg}")
        return None
    except Exception as e:
        print(f"General Error fetching audio features for track {track_id}: {e}")
        return None

def get_track_genre_from_artist(track_id: str):
    """
    Spotify doesn't provide genre directly on the track, it provides it on the artist.
    """
    try:
        track = sp.track(track_id)
        artist_id = track['artists'][0]['id']
        artist = sp.artist(artist_id)
        genres = artist.get('genres', [])
        return genres[0] if genres else "Unknown"
    except Exception as e:
        print(f"Error fetching artist genres for track {track_id}: {e}")
        return "Unknown"

# Test execution
if __name__ == "__main__":
    print("Testing Spotify Integration...")
    tracks = search_track("Blinding Lights")
    if tracks:
        print(f"Found track: {tracks[0]['name']} by {tracks[0]['artists'][0]['name']}")
        track_id = tracks[0]['id']
        
        features = get_track_audio_features(track_id)
        print(f"Features: {features}")
        
        genre = get_track_genre_from_artist(track_id)
        print(f"Primary Genre: {genre}")
