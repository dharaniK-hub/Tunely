/**
 * Popup Script - Handles the extension popup UI
 */

const statusElem = document.getElementById('status');
const currentTrackElem = document.getElementById('current-track');

function renderCurrentTrack(track) {
  if (!track || (!track.artist && !track.title)) {
    currentTrackElem.innerHTML = '<p class="placeholder">No track detected</p>';
    return;
  }

  const statusText = track.isPlaying ? 'Playing now' : 'Paused';
  currentTrackElem.innerHTML = `
    <div class="track-meta">
      <p class="track-status">${statusText}</p>
      <h4>${track.title || 'Unknown title'}</h4>
      <p>${track.artist || 'Unknown artist'}</p>
    </div>
  `;
}

function loadCurrentTrack() {
  chrome.storage.local.get(['currentTrack'], (result) => {
    renderCurrentTrack(result.currentTrack);
  });

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs[0];
    if (!tab || !tab.url || !tab.url.includes('open.spotify.com')) {
      return;
    }

    chrome.tabs.sendMessage(tab.id, { action: 'getCurrentTrack' }, (response) => {
      if (chrome.runtime.lastError || !response || !response.success) {
        return;
      }

      renderCurrentTrack(response.data);
    });
  });
}

// Load settings on popup open
chrome.storage.sync.get(null, (settings) => {
  document.getElementById('enabled-toggle').checked = settings.enabled ?? true;
  document.getElementById('auto-translate-toggle').checked = settings.autoTranslate ?? true;
  document.getElementById('sync-lyrics-toggle').checked = settings.syncLyrics ?? true;
  document.getElementById('target-lang').value = settings.targetLanguage ?? 'en';
  document.getElementById('theme').value = settings.theme ?? 'dark';
});

loadCurrentTrack();

chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName !== 'local' || !changes.currentTrack) {
    return;
  }

  renderCurrentTrack(changes.currentTrack.newValue);
});

// Save settings when changed
document.getElementById('enabled-toggle').addEventListener('change', (e) => {
  chrome.storage.sync.set({ enabled: e.target.checked });
  updateStatus('Settings saved');
});

document.getElementById('auto-translate-toggle').addEventListener('change', (e) => {
  chrome.storage.sync.set({ autoTranslate: e.target.checked });
  updateStatus('Settings saved');
});

document.getElementById('sync-lyrics-toggle').addEventListener('change', (e) => {
  chrome.storage.sync.set({ syncLyrics: e.target.checked });
  updateStatus('Settings saved');
});

document.getElementById('target-lang').addEventListener('change', (e) => {
  chrome.storage.sync.set({ targetLanguage: e.target.value });
  updateStatus('Target language updated');
});

document.getElementById('theme').addEventListener('change', (e) => {
  chrome.storage.sync.set({ theme: e.target.value });
  document.documentElement.setAttribute('data-theme', e.target.value);
  updateStatus('Theme updated');
});

// Show lyrics button
document.getElementById('show-lyrics-btn').addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.tabs.sendMessage(tabs[0].id, { action: 'showLyrics' }, (response) => {
        if (chrome.runtime.lastError) {
          updateStatus('Open open.spotify.com first');
          return;
        }

        if (!response || !response.success) {
          updateStatus(response?.error || 'No track detected yet');
          return;
        }

        updateStatus('Showing lyrics...');
      });
    }
  });
});

// Settings button
document.getElementById('settings-btn').addEventListener('click', () => {
  chrome.runtime.openOptionsPage();
});

// Update status message
function updateStatus(message) {
  statusElem.textContent = message;
  statusElem.style.opacity = '1';
  setTimeout(() => {
    statusElem.style.opacity = '0';
  }, 2000);
}

console.log('[Tunely] Popup script loaded');
