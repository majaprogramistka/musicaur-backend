import os
from dotenv import load_dotenv
import requests
import spotipy 
from spotipy.oauth2 import SpotifyClientCredentials 
from flask import Flask, request, jsonify

load_dotenv()


WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')


SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

try:
    auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID,
                                            client_secret=SPOTIPY_CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    print("Połączono z API Spotify!")
except Exception as e:
    print(f"BŁĄD KRYTYCZNY: Nie można połączyć się ze Spotify. Sprawdź klucze API. Błąd: {e}")
    sp = None



def get_weather(city):
    WARM_THRESHOLD = 15.0
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=pl'
    
    try:
        response = requests.get(url)
        response.raise_for_status() 
        weather_data = response.json()
        main_weather = weather_data['weather'][0]['main']
        current_temp = weather_data['main']['temp']
        print(f"Pogoda z API: {main_weather}, Temperatura: {current_temp}°C")
        
        if main_weather == 'Clear':
            return 'sunny warm' if current_temp >= WARM_THRESHOLD else 'sunny cold'
        elif main_weather == 'Clouds':
            return 'cloudy warm' if current_temp >= WARM_THRESHOLD else 'cloudy cold'
        elif main_weather in ['Rain', 'Drizzle']:
            return 'raining'
        elif main_weather == 'Snow':
            return 'snow'
        elif main_weather == 'Thunderstorm':
            return 'storm'
        else:
            return 'cloudy cold' if current_temp < WARM_THRESHOLD else 'cloudy warm'

    except requests.exceptions.RequestException as e:
        print(f"Błąd przy pobieraniu pogody: {e}")
        if "401" in str(e):
            print("BŁĄD KRYTYCZNY: Twój klucz API pogody jest nieprawidłowy lub jeszcze nieaktywny.")
        return 'cloudy cold'

# === NASZA NOWA, LEKKA FUNKCJA AI (API) ===

# Pobieramy nasz sekretny token do AI
HF_TOKEN = os.getenv('HF_TOKEN')

def classify_mood(mood_text):
    """
    Ta funkcja dzwoni do "Zdalnego Mózgu" (Hugging Face API),
    aby sklasyfikować nastrój.
    """
    # Używamy tego samego modelu, który działał, ale teraz "zdalnie"
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}

    emotion_labels = ['radość', 'smutek', 'złość', 'spokój', 'strach', 'zaskoczenie', 'energia']

    # Przygotowujemy "ładunek" dla API
    payload = {
        "inputs": mood_text,
        "parameters": {"candidate_labels": emotion_labels},
    }

    try:
        # Wysyłamy zapytanie POST do "Zdalnego Mózgu"
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status() # Sprawdź, czy nie ma błędu

        result = response.json()

        # Zwraca on listę etykiet i wyników, bierzemy tę z najwyższym wynikiem
        best_emotion = result['labels'][0]
        print(f"Zdalny Mózg (AI) sklasyfikował '{mood_text}' jako: {best_emotion}")
        return best_emotion

    except requests.exceptions.RequestException as e:
        print(f"Błąd przy łączeniu ze 'Zdalnym Mózgiem' (API AI): {e}")
        # Jeśli API AI zawiedzie, zwróćmy domyślną emocję
        return 'radość'

# ==================================================

def get_spotify_playlist(query):
    """
    Szuka na Spotify playlisty pasującej do naszego hasła (np. "storm złość").
    """
    if sp is None:
        print("Nie można szukać na Spotify, API nie jest połączone.")
        return 'http://googleusercontent.com/spotify.com/5' # Zapasowy link

    try:
        results = sp.search(q=query, type='playlist', limit=10, market='PL')
        
        playlists = results['playlists']['items']
        
        if not playlists:
            print(f"Nie znaleziono playlist dla hasła: {query}. Próbuję szukać dla samego nastroju: {query.split()[1]}")
            results_mood_only = sp.search(q=query.split()[1], type='playlist', limit=1, market='PL')
            playlists = results_mood_only['playlists']['items']
            
            if not playlists:
                print("Nie znaleziono też playlist dla samego nastroju. Zwracam domyślny link.")
                return 'https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYEmSG'

        # Bierzemy pierwszą playlistę z wyników
        playlist_url = playlists[0]['external_urls']['spotify']
        playlist_name = playlists[0]['name']
        
        print(f"Znaleziono playlistę: '{playlist_name}' -> {playlist_url}")
        return playlist_url

    except Exception as e:
        print(f"Błąd przy szukaniu playlisty: {e}")
        return 'https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYEmSG'


app = Flask(__name__)

@app.route('/generate-playlist', methods=['POST'])
def generate_playlist():
    
    print("\n--- NOWE ZAPYTANIE ---")
    data = request.json
    city = data.get('city')
    mood = data.get('mood')

    weather_category = get_weather(city)
    
    emotion_category = classify_mood(mood)
    
    search_query = f"{weather_category} {emotion_category}"
    print(f"Tworzę hasło do Spotify: '{search_query}'")
    
    playlist_link = get_spotify_playlist(search_query)
    
    response_data = {
        'playlist_url': playlist_link
    }
    
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
