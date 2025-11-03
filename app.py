import os
import random
from dotenv import load_dotenv
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Flask, request, jsonify
from flask_cors import CORS

# === Load env variables ===
load_dotenv()
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

# === Spotify setup ===
try:
    auth_manager = SpotifyClientCredentials(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    print("✅ Connected to Spotify API!")
except Exception as e:
    print(f"⚠️ Spotify connection error: {e}")
    sp = None

# === Flask app ===
app = Flask(__name__)
CORS(app)

# === Weather ===
def get_weather(city):
    WARM_THRESHOLD = 15.0
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=pl'
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        main_weather = data['weather'][0]['main']
        temp = data['main']['temp']

        if main_weather == 'Clear':
            return 'Mega sunny Hot' if temp >= WARM_THRESHOLD else 'Sunny cold'
        elif main_weather == 'Clouds':
            return 'Cloudy warm' if temp >= WARM_THRESHOLD else 'Cloudy cold'
        elif main_weather in ['Rain', 'Drizzle']:
            return 'Raining'
        elif main_weather == 'Snow':
            return 'Snow'
        elif main_weather == 'Thunderstorm':
            return 'Storm'
        else:
            return 'Cloudy warm' if temp >= WARM_THRESHOLD else 'Cloudy cold'
    except:
        return 'Cloudy cold'

# === Mood classification ===
emotion_keywords = {
    'radość': ["szczęśliw","radoś","zadowol","uśmiech","super","fajnie","happy","joy","smile","cheerful","awesome"],
    'smutek': ["smutn","przygnęb","płacz","sad","unhappy","depressed","cry"],
    'złość': ["zły","wkurz","wściek","angry","mad","furious"],
    'strach': ["boję","strach","lęk","afraid","scared","fear"],
    'zaskoczenie': ["zaskocz","wow","niespodzi","surprised","amazed","shocked"],
    'spokój': ["spokoj","wyluz","calm","relaxed","peaceful"],
    'energia': ["pełen energ","motywac","aktywn","energetic","active","powerful"]
}

def classify_mood(text):
    text = text.lower().strip()
    for emotion, keywords in emotion_keywords.items():
        if any(word in text for word in keywords):
            return emotion
    return "spokój"

# === Spotify playlist fetch ===
def get_spotify_playlist(query):
    default = {
        'url': 'https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYEmSG',
        'embed_url': 'https://open.spotify.com/embed/playlist/37i9dQZF1DXcBWIGoYEmSG'
    }

    if sp is None:
        return default

    try:
        results = sp.search(q=query, type='playlist', limit=10, market='PL')
        playlists = results.get('playlists', {}).get('items', [])

        if not playlists:
            # Spróbuj użyć tylko nastroju
            mood_only = query.split()[-1]
            results_mood_only = sp.search(q=mood_only, type='playlist', limit=5, market='PL')
            playlists = results_mood_only.get('playlists', {}).get('items', [])

        if not playlists:
            return default

        chosen = random.choice(playlists)
        url = chosen['external_urls']['spotify']
        embed_url = url.replace("open.spotify.com/", "open.spotify.com/embed/")
        return {'url': url, 'embed_url': embed_url}

    except Exception as e:
        print(f"❌ Spotify fetch error: {e}")
        return default

# === Flask endpoint ===
@app.route('/generate-playlist', methods=['POST'])
def generate_playlist():
    data = request.json
    city = data.get('city', '')
    mood = data.get('mood', '')

    weather_cat = get_weather(city)
    emotion_cat = classify_mood(mood)
    search_query = f"{weather_cat} {emotion_cat}"

    playlist_data = get_spotify_playlist(search_query)

    return jsonify({
        'playlist_url': playlist_data['url'],
        'embed_url': playlist_data['embed_url']
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)
