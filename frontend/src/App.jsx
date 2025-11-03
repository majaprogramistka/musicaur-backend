import { useState } from 'react';

function App() {
  const [city, setCity] = useState('');
  const [mood, setMood] = useState('');
  const [playlist, setPlaylist] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastQuery, setLastQuery] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:5001/generate-playlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ city, mood }),
      });

      if (!response.ok) throw new Error('Błąd w komunikacji z backendem');

      const data = await response.json();
      setPlaylist(data);
      setLastQuery(`${data.weather_category} ${data.emotion_category}`);
    } catch (err) {
      console.error(err);
      setError('Nie udało się pobrać playlisty');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '2rem',
      background: 'linear-gradient(135deg, #c1b3ff, #8e70f0, #b19cff)',
      backgroundSize: '400% 400%',
      animation: 'gradient 15s ease infinite',
      fontFamily: 'Arial, sans-serif',
      color: '#fff'
    }}>
      <style>{`
        @keyframes gradient {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }

        .container {
          display: flex;
          flex-direction: column;
          align-items: center;
          width: 100%;
          max-width: 700px;
        }

        .form-container, .playlist-container {
          width: 100%;
          margin-top: 1rem;
        }

        input::placeholder {
          color: rgba(255, 255, 255, 0.8);
        }

        @media (max-width: 768px) {
          .form-container, .playlist-container {
            width: 90%;
          }
        }
      `}</style>

      <div className="container">
        <h1 style={{
          fontSize: '2.8rem',
          marginBottom: '2rem',
          textAlign: 'center',
          textShadow: '2px 2px 10px rgba(0,0,0,0.3)'
        }}>🎵 Musicaur</h1>

        <form onSubmit={handleSubmit} className="form-container" style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '1rem',
          background: 'rgba(255,255,255,0.12)',
          padding: '2rem',
          borderRadius: '50px',
          boxShadow: '0 10px 30px rgba(0,0,0,0.4)',
          backdropFilter: 'blur(20px)'
        }}>
          <input
            type="text"
            placeholder="Miasto"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            style={{
              padding: '1rem',
              borderRadius: '30px',
              border: 'none',
              outline: 'none',
              width: '100%',
              fontSize: '1rem',
              textAlign: 'center',
              background: 'rgba(255,255,255,0.2)',
              color: '#fff',
              boxShadow: 'inset 0 4px 12px rgba(0,0,0,0.25)'
            }}
          />
          <input
            type="text"
            placeholder="Nastrój"
            value={mood}
            onChange={(e) => setMood(e.target.value)}
            style={{
              padding: '1rem',
              borderRadius: '30px',
              border: 'none',
              outline: 'none',
              width: '100%',
              fontSize: '1rem',
              textAlign: 'center',
              background: 'rgba(255,255,255,0.2)',
              color: '#fff',
              boxShadow: 'inset 0 4px 12px rgba(0,0,0,0.25)'
            }}
          />
          <button type="submit" style={{
            padding: '1rem 2rem',
            borderRadius: '40px',
            border: 'none',
            background: 'rgba(255, 111, 244, 0.85)',
            color: '#fff',
            fontSize: '1.2rem',
            cursor: 'pointer',
            boxShadow: '0 8px 25px rgba(0,0,0,0.4)',
            transition: 'all 0.3s ease'
          }}
          onMouseOver={e => e.target.style.transform = 'scale(1.05)'}
          onMouseOut={e => e.target.style.transform = 'scale(1)'}
          >
            Generuj
          </button>
        </form>

        {loading && <p style={{ marginTop: '1rem' }}>Ładowanie playlisty… ⏳</p>}
        {error && <p style={{ marginTop: '1rem', color: '#ffaaaa' }}>{error}</p>}

        {playlist && (
          <div className="playlist-container" style={{
            marginTop: '2rem',
            background: 'rgba(255,255,255,0.15)',
            padding: '2rem',
            borderRadius: '50px',
            boxShadow: '0 10px 30px rgba(0,0,0,0.4)',
            backdropFilter: 'blur(25px)'
          }}>
            <h2>Twoja playlista:</h2>
            <p>🎵 Kategorie: {playlist.weather_category}, {playlist.emotion_category}</p>
            <p style={{fontSize: '0.9rem', opacity: 0.8}}>Query: {lastQuery}</p>
            <iframe
              src={playlist.embed_url}
              width="100%"
              height="380"
              frameBorder="0"
              allow="encrypted-media"
              title="Spotify Playlist"
              style={{ borderRadius: '30px', marginTop: '1rem' }}
            ></iframe>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
