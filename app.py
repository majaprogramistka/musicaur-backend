import os
from dotenv import load_dotenv
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Flask, request, jsonify
from flask_cors import CORS
from urllib.parse import urlparse

# === Ładowanie sekretów z .env ===
load_dotenv()
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

# --- Konfiguracja Spotify ---
try:
    auth_manager = SpotifyClientCredentials(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    print("✅ Połączono z API Spotify!")
except Exception as e:
    print(f"⚠️ BŁĄD: Nie można połączyć się ze Spotify: {e}")
    sp = None

# === Flask app ===
app = Flask(__name__)
CORS(app)

# === Pogoda ===
def get_weather(city):
    WARM_THRESHOLD = 15.0
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=pl'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        weather_data = response.json()
        main_weather = weather_data['weather'][0]['main']
        current_temp = weather_data['main']['temp']

        if main_weather == 'Clear':
            return 'Mega sunny Hot' if current_temp >= WARM_THRESHOLD else 'Sunny cold'
        elif main_weather == 'Clouds':
            return 'Cloudy warm' if current_temp >= WARM_THRESHOLD else 'Cloudy cold'
        elif main_weather in ['Rain', 'Drizzle']:
            return 'Raining'
        elif main_weather == 'Snow':
            return 'Snow'
        elif main_weather == 'Thunderstorm':
            return 'Storm'
        else:
            return 'Cloudy cold' if current_temp < WARM_THRESHOLD else 'Cloudy warm'

    except requests.exceptions.RequestException as e:
        print(f"❌ Błąd przy pobieraniu pogody: {e}")
        return 'Cloudy cold'

# === Klasyfikacja nastroju ===
emotion_keywords = {
    'radość': [
        "szczęśliw", "radoś", "zadowol", "uśmiech", "super", "ekstra", "fajnie", "dobry humor", "wesoł", "pozytyw", "entuzj", "szczęście",
        "happy", "joy", "glad", "smile", "cheerful", "excited", "great", "awesome", "fantastic", "joyful", "elated"
    ],
    'smutek': [
        "smutn", "przygnęb", "zdołowan", "depresyj", "płacz", "nieszczęśliw", "przykro", "załam", "żal", "tęskn", "cierpi", "smutek",
        "sad", "unhappy", "depressed", "cry", "miserable", "down", "gloomy", "melancholy", "heartbroken"
    ],
    'złość': [
        "zły", "wkurz", "zdenerw", "wściek", "agresywn", "frustrac", "gniew", "irytac", "niezadowol", "furia",
        "angry", "mad", "furious", "annoyed", "irritated", "frustrated", "rage", "resentful"
    ],
    'strach': [
        "boję", "strach", "przeraż", "lęk", "niepew", "panik", "obaw", "strasz", "nerw", "stres",
        "afraid", "scared", "terrified", "fear", "panic", "nervous", "anxious", "worried", "frightened"
    ],
    'zaskoczenie': [
        "zaskocz", "wow", "niespodzi", "szok", "zdum", "ogłup", "zadziw",
        "surprised", "astonished", "amazed", "shocked", "wow", "unexpected", "stunned"
    ],
    'spokój': [
        "spokoj", "wyluz", "zrelaks", "harmon", "luźn", "cisz", "relaks", "pokój", "wycisz",
        "calm", "relaxed", "peaceful", "chill", "serene", "balanced", "tranquil"
    ],
    'energia': [
        "pełen energ", "motywac", "podekscytow", "aktywn", "żywioł", "energicz", "radosn", "żywy", "szybki",
        "energetic", "motivated", "hyped", "active", "driven", "powerful", "lively", "excited"
    ]
}

def classify_mood(mood_text):
    text = mood_text.lower().strip()
    for emotion, keywords in emotion_keywords.items():
        if any(word in text for word in keywords):
            return emotion
    return "spokój"

# === Spotify ===
def get_spotify_playlist(query):
    default_links = {
        'url': 'https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYEmSG',
        'embed_url': 'https://open.spotify.com/embed/playlist/37i9dQZF1DXcBWIGoYEmSG'
    }

    if sp is None:
        return default_links

    try:
        results = sp.search(q=query, type='playlist', limit=10, market='PL')
        playlists = results.get('playlists', {}).get('items', [])

        if not playlists:
            # fallback: tylko nastrój
            mood_only = query.split()[-1]
            results_mood_only = sp.search(q=mood_only, type='playlist', limit=5, market='PL')
            playlists = results_mood_only.get('playlists', {}).get('items', [])

            if not playlists:
                return default_links

        playlist_url = playlists[0]['external_urls']['spotify']

        # poprawny embed URL
        parsed = urlparse(playlist_url)
        path_parts = parsed.path.split('/')
        if len(path_parts) >= 3:
            embed_url = f"https://open.spotify.com/embed/{path_parts[1]}/{path_parts[2]}"
        else:
            embed_url = playlist_url  # fallback

        return {'url': playlist_url, 'embed_url': embed_url}

    except Exception as e:
        print(f"❌ Błąd przy szukaniu playlisty: {e}")
        return default_links

# === Endpoint Flask ===
@app.route('/generate-playlist', methods=['POST'])
def generate_playlist():
    data = request.json
    city = data.get('city')
    mood = data.get('mood')

    weather_category = get_weather(city)
    emotion_category = classify_mood(mood)
    
    search_query = f"{weather_category} {emotion_category}"
    print(f"🔍 Query Spotify: {search_query}")  # logowanie dla debug

    playlist_data = get_spotify_playlist(search_query)
    
    response_data = {
        'playlist_url': playlist_data['url'],
        'embed_url': playlist_data['embed_url'],
        'weather_category': weather_category,
        'emotion_category': emotion_category
    }
    
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
