import { useState } from "react";

function App() {
  const [city, setCity] = useState("");
  const [mood, setMood] = useState("");
  const [embedUrl, setEmbedUrl] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!city || !mood) return;

    setLoading(true);
    setEmbedUrl(""); 

    try {
      const res = await fetch("http://localhost:5001/generate-playlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ city, mood }),
      });
      const data = await res.json();
      if (data.embed_url) setEmbedUrl(data.embed_url);
    } catch (err) {
      console.error("Błąd przy pobieraniu playlisty:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #c39aff, #7c4dff)",
        padding: "2rem",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "1rem",
          width: "90%",
          maxWidth: "400px",
          background: "rgba(255, 255, 255, 0.15)",
          backdropFilter: "blur(10px)",
          borderRadius: "24px",
          padding: "2rem",
          boxShadow: "0 8px 30px rgba(0,0,0,0.3)",
        }}
      >
        <input
          type="text"
          placeholder="Miasto"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          style={{
            padding: "1rem",
            borderRadius: "12px",
            border: "none",
            outline: "none",
            fontSize: "1rem",
            background: "rgba(255,255,255,0.3)",
            color: "#fff",
            fontWeight: "bold",
            textAlign: "center",
          }}
        />
        <input
          type="text"
          placeholder="Nastrój"
          value={mood}
          onChange={(e) => setMood(e.target.value)}
          style={{
            padding: "1rem",
            borderRadius: "12px",
            border: "none",
            outline: "none",
            fontSize: "1rem",
            background: "rgba(255,255,255,0.3)",
            color: "#fff",
            fontWeight: "bold",
            textAlign: "center",
          }}
        />
        <button
          type="submit"
          style={{
            padding: "1rem",
            borderRadius: "12px",
            border: "none",
            backgroundColor: "rgba(255,255,255,0.4)",
            fontWeight: "bold",
            cursor: "pointer",
            color: "#7c4dff",
            transition: "0.3s",
          }}
        >
          {loading ? "Ładowanie..." : "Generuj playlistę"}
        </button>
      </form>

      {embedUrl && (
        <iframe
          src={embedUrl}
          width="300"
          height="380"
          frameBorder="0"
          allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
          style={{
            marginTop: "2rem",
            borderRadius: "24px",
            boxShadow: "0 10px 40px rgba(0,0,0,0.35)",
            backdropFilter: "blur(10px)",
          }}
        ></iframe>
      )}
    </div>
  );
}

export default App;

