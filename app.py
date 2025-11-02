import os
from dotenv import load_dotenv
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Flask, request, jsonify

# --- Załaduj sekrety z pliku .env ---
load_dotenv()
# ------------------------------------

# --- Konfiguracje API (wszystkie 3) ---
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
HF_TOKEN = os.getenv('HF_TOKEN')
# ------------------------------------

# --- Konfiguracja Spotify (bez zmian) ---
try:
    auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID,
                                            client_secret=SPOTIPY_CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    print("Połączono z API Spotify!")
except Exception as e:
    print(f"BŁĄD KRYTYCZNY: Nie można połączyć się ze Spotify. Sprawdź klucze API. Błąd: {e}")
    sp = None
# ------------------------------------


# === Funkcja do pogody (ZAKTUALIZOWANA) ===
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
        
        # Logika dopasowana do Twoich 7 kategorii z Figmy
        if main_weather == 'Clear':
            # ZMIANA: Z 'sunny warm' na 'Mega sunny Hot'
            return 'Mega sunny Hot' if current_temp >= WARM_THRESHOLD else 'Sunny cold'
        elif main_weather == 'Clouds':
            return 'Cloudy warm' if current_temp >= WARM_THRESHOLD else 'Cloudy cold'
        elif main_weather in ['Rain', 'Drizzle']:
            return 'Raining' # Zmieniamy 'raining' na 'Raining', żeby pasowało do screena
        elif main_weather == 'Snow':
            return 'Snow' # Zmieniamy 'snow' na 'Snow'
        elif main_weather == 'Thunderstorm':
            return 'Storm' # Zmieniamy 'storm' na 'Storm'
        else:
            return 'Cloudy cold' if current_temp < WARM_THRESHOLD else 'Cloudy warm'

    except requests.exceptions.RequestException as e:
        print(f"Błąd przy pobieraniu pogody: {e}")
        return 'Cloudy cold' # Domyślna bezpieczna kategoria

# === Funkcja AI (API) (bez zmian) ===
def classify_mood(mood_text):
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    emotion_labels = ['radość', 'smutek', 'złość', 'spokój', 'strach', 'zaskoczenie', 'energia']
    payload = {"inputs": mood_text, "parameters": {"candidate_labels": emotion_labels}}

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        best_emotion = result['labels'][0]
        print(f"Zdalny Mózg (AI) sklasyfikował '{mood_text}' jako: {best_emotion}")
        return best_emotion
    except requests.exceptions.RequestException as e:
        print(f"Błąd przy łączeniu ze 'Zdalnym Mózgiem' (API AI): {e}")
        return 'radość'


# === Funkcja Spotify (ZAKTUALIZOWANA) ===
def get_spotify_playlist(query):
    # Zwracamy DWA linki: normalny i do podglądu (embed)
    default_links = {
        'url': 'https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYEmSG',
        'embed_url': 'http://googleusercontent.com/spotify.com/7'
    }
    
    if sp is None:
        print("Nie można szukać na Spotify, API nie jest połączone.")
        return default_links

    try:
        results = sp.search(q=query, type='playlist', limit=10, market='PL')
        playlists = results['playlists']['items']
        
        if not playlists:
            print(f"Nie znaleziono playlist dla hasła: {query}. Próbuję szukać dla samego nastroju.")
            mood_only = query.split()[-1] # Bierzemy ostatnie słowo (emocję)
            results_mood_only = sp.search(q=mood_only, type='playlist', limit=1, market='PL')
            playlists = results_mood_only['playlists']['items']
            
            if not playlists:
                print("Nie znaleziono też playlist dla samego nastroju. Zwracam domyślny link.")
                return default_links

        # Mamy playlistę! Bierzemy pierwszą
        playlist_url = playlists[0]['external_urls']['spotify']
        playlist_name = playlists[0]['name']
        
        # TWORZYMY LINK DO PODGLĄDU (EMBED)
        # Zamieniamy: https://open.spotify.com/playlist/ID
        # Na:         https://open.spotify.com/embed/playlist/ID
        embed_url = playlist_url.replace("open.spotify.com/", "open.spotify.com/embed/")
        
        print(f"Znaleziono playlistę: '{playlist_name}' -> {playlist_url}")
        
        return {
            'url': playlist_url,
            'embed_url': embed_url
        }

    except Exception as e:
        print(f"Błąd przy szukaniu playlisty: {e}")
        return default_links


# --- Nasz główny serwer Flask (WIELKI FINAŁ v2) ---
app = Flask(__name__)

@app.route('/generate-playlist', methods=['POST'])
def generate_playlist():
    
    print("\n--- NOWE ZAPYTANIE ---")
    data = request.json
    city = data.get('city')
    mood = data.get('mood')

    # KROK 1: Pogoda
    weather_category = get_weather(city) # Np. "Mega sunny Hot"
    
    # KROK 2: Emocje
    emotion_category = classify_mood(mood) # Np. "radość"
    
    # KROK 3: Hasło do wyszukiwania
    search_query = f"{weather_category} {emotion_category}"
    print(f"Tworzę hasło do Spotify: '{search_query}'")
    
    # KROK 4: Playlista
    playlist_data = get_spotify_playlist(search_query) # Zwraca {'url': '...', 'embed_url': '...'}
    
    # KROK 5: Zbuduj ostateczną odpowiedź dla Framera
    response_data = {
        'playlist_url': playlist_data['url'],
        'embed_url': playlist_data['embed_url'],
        'weather_category': weather_category  # <-- WYSYŁAMY KATEGORIĘ DO UI!
    }
    
    print(f"Wysyłam do Framera: {response_data}")
    return jsonify(response_data)


# --- Uruchomienie serwera ---
if __name__ == '__main__':
    app.run(debug=True, port=5001)