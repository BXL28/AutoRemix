import { useState, useEffect } from 'react';
import './App.css';

// Simple SVG Icons
const SearchIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg>
);
const SparklesIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="url(#gradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <defs>
      <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#8a2be2" />
        <stop offset="100%" stopColor="#ff007f" />
      </linearGradient>
    </defs>
    <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path><path d="M5 3v4"></path><path d="M19 17v4"></path><path d="M3 5h4"></path><path d="M17 19h4"></path>
  </svg>
);
const PlayIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="6 3 20 12 6 21 6 3"></polygon></svg>
);
const DownloadIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" x2="12" y1="15" y2="3"></line></svg>
);

const API_BASE = "http://localhost:8000/api";

function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  
  const [selectedBaseTrack, setSelectedBaseTrack] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [isRecommending, setIsRecommending] = useState(false);
  
  const [selectedRemixTrack, setSelectedRemixTrack] = useState(null);
  const [isMixing, setIsMixing] = useState(false);
  const [mixResult, setMixResult] = useState(null);

  // Search input debounce and API call
  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (searchQuery.trim().length > 2) {
        setIsSearching(true);
        try {
          const res = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: searchQuery })
          });
          const data = await res.json();
          setSearchResults(data.results || []);
        } catch (error) {
          console.error("Search failed", error);
        } finally {
          setIsSearching(false);
        }
      } else {
        setSearchResults([]);
      }
    }, 500);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery]);

  // Fetch recommendations when base track is selected
  const handleSelectBaseTrack = async (track) => {
    setSelectedBaseTrack(track);
    setSearchResults([]);
    setSearchQuery('');
    setRecommendations([]);
    setSelectedRemixTrack(null);
    setIsRecommending(true);
    
    // Defaulting genre heavily as Spotify API didn't reliably return it on tracks
    // LangGraph prompt will try to deduce it if we pass "Unknown"
    
    try {
      const res = await fetch(`${API_BASE}/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          title: track.title, 
          artist: track.artist, 
          genre: "Unknown" 
        })
      });
      const data = await res.json();
      setRecommendations(data.recommendations || []);
    } catch (error) {
      console.error("Recommendation failed", error);
    } finally {
      setIsRecommending(false);
    }
  };

  const handleGenerateRemix = async () => {
    if (!selectedBaseTrack || !selectedRemixTrack) return;
    
    setIsMixing(true);
    setMixResult(null);
    try {
      const res = await fetch(`${API_BASE}/remix`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          base_title: selectedBaseTrack.title,
          base_artist: selectedBaseTrack.artist,
          remix_title: selectedRemixTrack.title,
          remix_artist: selectedRemixTrack.artist,
          target_bpm: parseInt(selectedRemixTrack.bpm) || 120
        })
      });
      const data = await res.json();
      if(res.ok) {
        setMixResult(data.file);
      } else {
        alert("Error generating remix: " + (data.detail || "Unknown error"));
      }
    } catch (error) {
      console.error("Remix failed", error);
      alert("Failed to reach server during remix generation.");
    } finally {
      setIsMixing(false);
    }
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '3rem' }}>
      
      {/* Header */}
      <header className="flex-col gap-sm" style={{ textAlign: 'center', marginTop: '2rem' }}>
        <div className="flex-center gap-sm">
          <SparklesIcon />
          <h1 className="gradient-text">AutoRemix</h1>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>
          AI-powered song matching and mixing
        </p>
      </header>

      {/* Main Content Area */}
      <main style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: '2rem' }}>
        
        {/* Left Column: Search & Base Track */}
        <section className="glass-panel flex-col gap-md" style={{ padding: '2rem' }}>
          <h2>1. Choose Base Track</h2>
          <div className="input-group">
            <span className="input-icon left"><SearchIcon /></span>
            <input 
              type="text" 
              className="input-field has-icon-left" 
              placeholder="Search Spotify..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {isSearching && <span className="input-icon right animate-spin">🌀</span>}
          </div>
          
          {/* Search Dropdown / Results */}
          {searchResults.length > 0 && searchQuery && (
            <div className="flex-col gap-sm" style={{ marginTop: '0.5rem', maxHeight: '200px', overflowY: 'auto' }}>
              {searchResults.map(track => (
                <div key={track.id} className="track-card" onClick={() => handleSelectBaseTrack(track)} style={{ padding: '0.5rem' }}>
                   {track.art ? <img src={track.art} alt="art" className="track-art" style={{ width: 40, height: 40 }} /> : <div className="track-art-placeholder" style={{ width: 40, height: 40 }}>🎵</div>}
                   <div className="track-info">
                     <div className="track-title" style={{ fontSize: '0.9rem' }}>{track.title}</div>
                     <div className="track-artist" style={{ fontSize: '0.75rem' }}>{track.artist}</div>
                   </div>
                </div>
              ))}
            </div>
          )}
          
          <div style={{ marginTop: '1rem' }}>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '1rem', color: 'var(--text-secondary)' }}>Selected Track</h3>
            {selectedBaseTrack ? (
              <div className="track-card selected" style={{ cursor: 'default' }}>
                {selectedBaseTrack.art ? <img src={selectedBaseTrack.art} alt="art" className="track-art" /> : <div className="track-art-placeholder" style={{ width: 56, height: 56 }}>🎵</div>}
                <div className="track-info">
                  <div className="track-title">{selectedBaseTrack.title}</div>
                  <div className="track-artist">{selectedBaseTrack.artist}</div>
                  <button className="badge" style={{ marginTop: '0.5rem', alignSelf: 'flex-start', border: 'none', cursor: 'pointer' }} onClick={() => setSelectedBaseTrack(null)}>✕ Change</button>
                </div>
              </div>
            ) : (
              <div className="glass-panel flex-center" style={{ height: '100px', borderStyle: 'dashed', opacity: 0.6 }}>
                <p>Search and select a track to begin</p>
              </div>
            )}
          </div>
        </section>

        {/* Right Column: AI Recommendations */}
        <section className="glass-panel flex-col gap-md" style={{ padding: '2rem', position: 'relative' }}>
          <div className="flex-row gap-sm" style={{ alignItems: 'center' }}>
            <h2 className="gradient-text">2. AI Matches</h2>
            <SparklesIcon />
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            LangGraph suggests these tracks based on tempo, key, and genre compatibility.
          </p>
          
          <div className="flex-col gap-sm" style={{ marginTop: '1rem' }}>
            {recommendations.map((track, i) => (
              <div 
                key={i} 
                className={`track-card ${selectedRemixTrack === track ? 'selected' : ''}`}
                onClick={() => setSelectedRemixTrack(track)}
                style={{ flexDirection: 'column', alignItems: 'flex-start' }}
              >
                <div className="flex-row gap-sm" style={{ width: '100%', alignItems: 'center' }}>
                  <div className="track-art-placeholder" style={{ width: 40, height: 40, fontSize: '1.2rem' }}>✨</div>
                  <div className="track-info">
                    <div className="track-title">{track.title}</div>
                    <div className="track-artist">{track.artist}</div>
                    <div className="track-meta">
                      <span className="badge">{track.bpm} BPM</span>
                      <span className="badge">{track.genre}</span>
                    </div>
                  </div>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem', fontStyle: 'italic' }}>
                  "{track.reason}"
                </div>
              </div>
            ))}
          </div>

          {/* Loading Overlays */}
          {!selectedBaseTrack && (
            <div className="glass-panel flex-center flex-col gap-sm" style={{ position: 'absolute', inset: 0, zIndex: 10, background: 'rgba(10, 10, 15, 0.8)' }}>
              <p style={{ color: 'var(--text-muted)' }}>Waiting for Base Track</p>
            </div>
          )}
          {isRecommending && (
            <div className="glass-panel flex-center flex-col gap-sm" style={{ position: 'absolute', inset: 0, zIndex: 10, background: 'rgba(10, 10, 15, 0.8)' }}>
              <div className="animate-spin" style={{ fontSize: '2rem' }}>🌀</div>
              <p className="gradient-text animate-pulse">Gemini evaluates musical theory...</p>
            </div>
          )}
        </section>
      </main>

      {/* Bottom Area: Controls & Player */}
      <section className="glass-panel flex-col gap-md" style={{ padding: '2rem' }}>
        <div className="flex-row" style={{ justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2>3. Create Remix</h2>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
              Downloads via RapidAPI and mixes via Pedalboard/Librosa.
            </p>
          </div>
          
          <button 
            className="btn btn-primary" 
            disabled={!selectedBaseTrack || !selectedRemixTrack || isMixing}
            onClick={handleGenerateRemix}
            style={{ 
              opacity: (!selectedBaseTrack || !selectedRemixTrack || isMixing) ? 0.5 : 1,
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            {isMixing ? 'Mixing Audio (May take a minute)...' : 'Generate Full Remix'}
          </button>
        </div>

        {/* Player */}
        {mixResult ? (
          <div className="glass-panel flex-row gap-md" style={{ padding: '1rem', marginTop: '1rem', alignItems: 'center', background: 'var(--bg-secondary)', border: '1px solid var(--accent-primary)' }}>
            <button className="btn btn-primary btn-icon-only">
              <PlayIcon />
            </button>
            <div className="flex-col" style={{ flexGrow: 1, gap: '0.5rem' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Ready: {mixResult}</div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Playback requires static file serving from FastAPI, demo mock visual shown.</p>
            </div>
            <button className="btn btn-glass">
              <DownloadIcon /> Save
            </button>
          </div>
        ) : (
          <div className="glass-panel flex-center" style={{ padding: '2rem', marginTop: '1rem', background: 'var(--bg-secondary)', opacity: 0.5 }}>
             <p>Your mixed audio will appear here</p>
          </div>
        )}
      </section>

    </div>
  );
}

export default App;
