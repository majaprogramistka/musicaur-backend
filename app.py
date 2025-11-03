import os
from dotenv import load_dotenv
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Flask, request, jsonify

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
        print(f"🌤 Pogoda w {city}: {main_weather}, {current_temp}°C")

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

# === NOWA wersja klasyfikacji nastroju (bez AI, PL+EN) ===
def classify_mood(mood_text):
    """
    Lekka klasyfikacja nastroju (PL + EN) bez zewnętrznych API ani modeli ML.
    """
    text = mood_text.lower().strip()
    
    emotion_keywords = {
        'radość': [
            "szczęśliw", "radoś", "zadowol", "uśmiech", "super", "ekstra", "fajnie", "dobry humor",
            "happy", "joy", "glad", "smile", "cheerful", "excited", "great", "awesome", "fantastic"
        ],
        'smutek': [
            "smutn", "przygnęb", "zdołowan", "depresyj", "płacz", "nieszczęśliw",
            "sad", "unhappy", "depressed", "cry", "miserable", "down"
        ],
        'złość': [
            "zły", "wkurz", "zdenerw", "wściek", "agresywn", "frustrac",
            "angry", "mad", "furious", "annoyed", "irritated", "frustrated"
        ],
        'strach': [
            "boję", "strach", "przeraż", "lęk", "niepew", "panik",
            "afraid", "scared", "terrified", "fear", "panic", "nervous", "anxious"
        ],
        'zaskoczenie': [
            "zaskocz", "wow", "niespodzi", "szok",
            "surprised", "astonished", "amazed", "shocked", "wow", "unexpected"
        ],
        'spokój': [
            "spokoj", "wyluz", "zrelaks", "harmon", "luźn",
            "calm", "relaxed", "peaceful", "chill", "serene", "balanced"
        ],
        'energia': [
            "pełen energ", "motywac", "podekscytow", "aktywn", "żywioł",
            "energetic", "motivated", "hyped", "active", "driven", "powerful"
        ]
    }
    
    for emotion, keywords in emotion_keywords.items():
        if any(word in text for word in keywords):
            print(f"🧠 Zidentyfikowano emocję: '{emotion}' (dopasowano słowo kluczowe).")
            return emotion

    print("😐 Nie znaleziono emocji, zwracam 'spokój' jako neutralny stan.")
    return "spokój"

# === Spotify ===
def get_spotify_playlist(query):
    default_links = {
        'url': 'https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYEmSG',
        'embed_url': 'open.spotify.com/embed'
    }

    if sp is None:
        print("⚠️ Spotify API niepołączone, zwracam domyślną playlistę.")
        return default_links

    try:
        results = sp.search(q=query, type='playlist', limit=10, market='PL')
        if results and 'playlists' in results and 'items' in results['playlists']:
            playlists = results['playlists']['items']
        else:
            playlists = []

        if not playlists:
            print(f"Nie znaleziono playlisty dla: {query}. Próbuję uprościć zapytanie...")
            mood_only = query.split()[-1]
            results_mood_only = sp.search(q=mood_only, type='playlist', limit=1, market='PL')
            playlists = results_mood_only['playlists']['items']

            if not playlists:
                print("Nie znaleziono żadnej playlisty – zwracam domyślną.")
                return default_links

        playlist_url = playlists[0]['external_urls']['spotify']
        playlist_name = playlists[0]['name']
        embed_url = playlist_url.replace("open.spotify.com/", "open.spotify.com/embed/")

        print(f"🎵 Znaleziono playlistę: '{playlist_name}' → {playlist_url}")
        return {'url': playlist_url, 'embed_url': embed_url}

    except Exception as e:
        print(f"❌ Błąd przy szukaniu playlisty: {e}")
        return default_links

# === Flask app ===
app = Flask(__name__)

@app.route('/generate-playlist', methods=['POST'])
def generate_playlist():
    print("\n--- 🪩 NOWE ZAPYTANIE ---")
    data = request.json
    city = data.get('city')
    mood = data.get('mood')

    weather_category = get_weather(city)
    emotion_category = classify_mood(mood)
    
    search_query = f"{weather_category} {emotion_category}"
    print(f"🔍 Tworzę zapytanie do Spotify: '{search_query}'")
    
    playlist_data = get_spotify_playlist(search_query)
    
    response_data = {
        'playlist_url': playlist_data['url'],
        'embed_url': playlist_data['embed_url'],
        'weather_category': weather_category,
        'emotion_category': emotion_category
    }
    
    print(f"✅ Wysyłam do Framera: {response_data}")
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
