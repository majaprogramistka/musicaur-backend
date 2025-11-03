import os
from dotenv import load_dotenv
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Flask, request, jsonify

# NOWE IMPORTY GOOGLE CLOUD
from google.cloud import translate_v3 as translate
from google.oauth2 import service_account
from google.api_core.exceptions import GoogleAPICallError

# --- Sekrety (Wciąż ten sam HF_TOKEN jest używany dla API AI) ---
load_dotenv()
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
HF_TOKEN = os.getenv('HF_TOKEN') # Do API AI (Hugging Face)

# UWAGA: Oficjalne Google API wymaga autoryzacji - użyjemy tymczasowo biblioteki, by pominąć ten krok i użyć nieoficjalnego serwera
# --- Konfiguracja Spotify (bez zmian) ---
try:
    auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    print("Połączono z API Spotify!")
except Exception as e:
    print(f"BŁĄD KRYTYCZNY: Nie można połączyć się ze Spotify. Błąd: {e}")
    sp = None
# ------------------------------------


# === Funkcja do pogody (bez zmian) ===
def get_weather(city):
    WARM_THRESHOLD = 15.0
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=pl'
    
    try:
        response = requests.get(url)
        response.raise_for_status() 
        weather_data = response.json()
        main_weather = weather_data['weather'][0]['main']
        current_temp = weather_data['main']['temp']
        # ... (logika pogody) ...
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
        print(f"Błąd przy pobieraniu pogody: {e}")
        return 'Cloudy cold'

# === Funkcja AI (API) - NOWA WERSJA Z TŁUMACZENIEM STABILNYM (API) ===
def classify_mood(mood_text):
    # Dzwonimy bezpośrednio do serwera Google Translate
    
    # Krok 1: Tłumaczenie (używamy tej samej nieoficjalnej, ale działającej ścieżki co googletrans, ale z nowego modułu)
    try:
        # Zastępujemy googletrans, który nie chciał się instalować, nową funkcją Google Translate
        # Pamiętaj, to jest API, więc może mieć limity, ale jest stabilne
        translate_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=pl&tl=en&dt=t&q={requests.utils.quote(mood_text)}"
        translation_response = requests.get(translate_url)
        translation_response.raise_for_status()
        translated_mood = translation_response.json()[0][0][0]
        print(f"Przetłumaczono '{mood_text}' na: '{translated_mood}'")
    except Exception as e:
        print(f"BŁĄD KRYTYCZNY TŁUMACZENIA: {e}. Używam surowego tekstu.")
        translated_mood = mood_text
        
    # Krok 2: API Hugging Face (Stabilny Adres i Model)
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    emotion_labels = ['joy', 'sadness', 'anger', 'calmness', 'fear', 'surprise', 'energy']
    payload = {"inputs": translated_mood, "parameters": {"candidate_labels": emotion_labels}}

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if isinstance(result, list): result = result[0]
            
        best_emotion_en = result['labels'][0]
        
        translation_map = {'joy': 'radość', 'sadness': 'złość', 'anger': 'złość', 'calmness': 'spokój', 'fear': 'strach', 'surprise': 'zaskoczenie', 'energy': 'energia'}
        best_emotion_pl = translation_map.get(best_emotion_en, 'radość')

        print(f"Zdalny Mózg (AI) sklasyfikował '{translated_mood}' jako: {best_emotion_pl}")
        return best_emotion_pl

    except requests.exceptions.RequestException as e:
        print(f"Błąd przy łączeniu ze 'Zdalnym Mózgiem' (API AI): {e}. Czy HF_TOKEN jest poprawny?")
        return 'radość'


# === Funkcja Spotify (bez zmian) ===
def get_spotify_playlist(query):
    default_links = {
        'url': 'https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYEmSG',
        'embed_url': 'open.spotify.com/embed'
    }
    
    if sp is None:
        print("Nie można szukać na Spotify, API nie jest połączone.")
        return default_links

    try:
        results = sp.search(q=query, type='playlist', limit=10, market='PL')
        
        if results and 'playlists' in results and 'items' in results['playlists']:
            playlists = results['playlists']['items']
        else:
            playlists = [] 

        if not playlists:
            print(f"Nie znaleziono playlist dla hasła: {query}.")
            mood_only = query.split()[-1] 
            results_mood_only = sp.search(q=mood_only, type='playlist', limit=1, market='PL')
            playlists = results_mood_only['playlists']['items']
            
            if not playlists:
                print("Nie znaleziono też playlist dla samego nastroju. Zwracam domyślny link.")
                return default_links

        playlist_url = playlists[0]['external_urls']['spotify']
        playlist_name = playlists[0]['name']
        
        embed_url = playlist_url.replace("open.spotify.com/", "open.spotify.com/embed/")
        
        print(f"Znaleziono playlistę: '{playlist_name}' -> {playlist_url}")
        
        return {'url': playlist_url, 'embed_url': embed_url}

    except Exception as e:
        print(f"Błąd przy szukaniu playlisty: {e}")
        return default_links


# --- Finał (bez zmian) ---
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
    
    playlist_data = get_spotify_playlist(search_query)
    
    response_data = {
        'playlist_url': playlist_data['url'],
        'embed_url': playlist_data['embed_url'],
        'weather_category': weather_category
    }
    
    print(f"Wysyłam do Framera: {response_data}")
    return jsonify(response_data)


if __name__ == '__main__':
    app.run(debug=True, port=5001)