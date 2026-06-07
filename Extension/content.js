/**
 * Content Script for Spotify - Injects Tunely lyrics panel
 */

console.log('[Tunely] Content script loaded on Spotify');

let currentTrack = { artist: null, title: null, id: null };
let currentLyrics = "";
let translatedLyrics = "";

function persistTrackState() {
  chrome.storage.local.set({
    currentTrack: { ...currentTrack, isPlaying: isPlaying },
    currentLyrics,
    translatedLyrics,
    updatedAt: Date.now(),
  });
}

// ... [Keep your existing chrome.runtime.onMessage listeners here] ...

async function fetchAndDisplayLyrics(artist, title) {
  try {
    const settings = await new Promise((resolve) => chrome.runtime.sendMessage({ action: 'getSettings' }, resolve));
    if (!settings.data || !settings.data.enabled) return;

    const response = await new Promise((resolve) => chrome.runtime.sendMessage({ action: 'fetchLyrics', artist, title }, resolve));
    if (!response.success) return;

    // 1. Set currentLyrics to the source
    currentLyrics = response.data.lyrics;
    // 2. Set translatedLyrics to a loading state or default initially
    translatedLyrics = "Translating..."; 

    if (settings.data.autoTranslate) {
      const langResponse = await new Promise((resolve) => chrome.runtime.sendMessage({ action: 'detectLanguage', text: currentLyrics }, resolve));
      const targetLang = settings.data.targetLanguage || 'en';

      if (langResponse.data.primary_language !== targetLang) {
        const transResponse = await new Promise((resolve) => chrome.runtime.sendMessage({
          action: 'translateText',
          text: currentLyrics,
          source: langResponse.data.primary_language,
          target: targetLang
        }, resolve));
        
        if (transResponse.success) {
          translatedLyrics = transResponse.data.translatedText;
        } else {
          translatedLyrics = "Translation failed.";
        }
      } else {
        translatedLyrics = currentLyrics;
      }
    } else {
      translatedLyrics = currentLyrics;
    }
    
    displayLyricsPanel();
    persistTrackState();
  } catch (error) {
    console.error('[Tunely] Error in fetchAndDisplayLyrics:', error);
  }
}

function displayLyricsPanel() {
  const existing = document.getElementById('tunely-lyrics-panel');
  if (existing) existing.remove();

  const panel = document.createElement('div');
  panel.id = 'tunely-lyrics-panel';
  panel.className = 'tunely-panel';
  
  // Use unique classes for original vs translated to ensure they style correctly
  panel.innerHTML = `
    <div class="tunely-lyrics-container">
      <div class="tunely-lyrics-column">
        <h3>Original</h3>
        <div class="tunely-lyrics-text original-view">${currentLyrics.replace(/\n/g, '<br>')}</div>
      </div>
      <div class="tunely-lyrics-column">
        <h3>Translation</h3>
        <div class="tunely-lyrics-text translated-view">${translatedLyrics.replace(/\n/g, '<br>')}</div>
      </div>
    </div>
    <div class="tunely-panel-controls">
      <button id="tunely-close-btn">Close</button>
    </div>
  `;

  document.body.appendChild(panel);
  panel.querySelector('#tunely-close-btn').addEventListener('click', () => panel.remove());
}

// ... (existing code)

async function fetchAndDisplayLyrics(artist, title) {
  try {
    const settings = await new Promise((resolve) => chrome.runtime.sendMessage({ action: 'getSettings' }, resolve));
    if (!settings.data || !settings.data.enabled) return;

    const response = await new Promise((resolve) => chrome.runtime.sendMessage({ action: 'fetchLyrics', artist, title }, resolve));

    // IMPROVED ERROR HANDLING
    if (!response.success || !response.data.lyrics) {
      console.warn('[Tunely] Lyrics not found in database');
      displayLyricsPanel(true); // true indicates error state
      return;
    }

    currentLyrics = response.data.lyrics;
    // ... (keep the rest of translation logic)
    
    displayLyricsPanel(false);
    persistTrackState();
  } catch (error) {
    console.error('[Tunely] Error in fetchAndDisplayLyrics:', error);
  }
}

function displayLyricsPanel(isError = false) {
  const existing = document.getElementById('tunely-lyrics-panel');
  if (existing) existing.remove();

  const panel = document.createElement('div');
  panel.id = 'tunely-lyrics-panel';
  panel.className = 'tunely-panel';
  
  // Dynamic message based on error state
  const lyricsContent = isError 
    ? '<p class="error-msg">Lyrics not found in database for this track.</p>' 
    : `<div class="tunely-lyrics-text original-view">${currentLyrics.replace(/\n/g, '<br>')}</div>`;

  panel.innerHTML = `
    <div class="tunely-lyrics-container">
      <div class="tunely-lyrics-column">
        <h3>Original</h3>
        ${lyricsContent}
      </div>
      <div class="tunely-lyrics-column">
        <h3>Translation</h3>
        <div class="tunely-lyrics-text translated-view">
          ${isError ? '-' : translatedLyrics.replace(/\n/g, '<br>')}
        </div>
      </div>
    </div>
    <div class="tunely-panel-controls">
      <button id="tunely-close-btn">Close</button>
    </div>
  `;

  document.body.appendChild(panel);
  panel.querySelector('#tunely-close-btn').addEventListener('click', () => panel.remove());
}