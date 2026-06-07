/**
 * Background Service Worker for Tunely Chrome Extension
 * Handles API calls, storage, and inter-tab communication
 */

const API_BASE_URL = 'http://localhost:8000';

// Listen for messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('[Tunely] Message received:', request.action);

  if (request.action === 'fetchLyrics') {
    fetchLyrics(request.artist, request.title)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Keep channel open for async response
  }

  if (request.action === 'detectLanguage') {
    detectLanguage(request.text)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  if (request.action === 'translateText') {
    translateText(request.text, request.source, request.target)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  if (request.action === 'getTimestamps') {
    getTimestamps(request.artist, request.title)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }

  if (request.action === 'saveSettings') {
    chrome.storage.sync.set(request.settings, () => {
      sendResponse({ success: true });
    });
    return true;
  }

  if (request.action === 'getSettings') {
    chrome.storage.sync.get(null, (settings) => {
      sendResponse({ success: true, data: settings });
    });
    return true;
  }
});

// API Functions
async function fetchLyrics(artist, title) {
  const response = await fetch(
    `${API_BASE_URL}/lyrics?artist=${encodeURIComponent(artist)}&title=${encodeURIComponent(title)}`
  );
  if (!response.ok) throw new Error('Failed to fetch lyrics');
  const data = await response.json();
  return data;
}

async function detectLanguage(text) {
  const response = await fetch(`${API_BASE_URL}/detect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });
  if (!response.ok) throw new Error('Failed to detect language');
  return await response.json();
}

async function translateText(text, source = 'auto', target = 'en') {
  const response = await fetch(`${API_BASE_URL}/translate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, source, target })
  });
  if (!response.ok) throw new Error('Failed to translate');
  return await response.json();
}

async function getTimestamps(artist, title) {
  const response = await fetch(
    `${API_BASE_URL}/v3/lyrics/timestamps?artist=${encodeURIComponent(artist)}&title=${encodeURIComponent(title)}`
  );
  if (!response.ok) throw new Error('Failed to get timestamps');
  return await response.json();
}

// Listen for tab changes to potentially inject content
chrome.tabs.onActivated.addListener((activeInfo) => {
  chrome.tabs.get(activeInfo.tabId, (tab) => {
    if (tab.url && tab.url.includes('open.spotify.com')) {
      console.log('[Tunely] Spotify tab activated');
      // Notify content script that tab is active
      chrome.tabs.sendMessage(activeInfo.tabId, { action: 'tabActive' }).catch(() => {
        // Content script might not be injected yet
      });
    }
  });
});

// Initialize extension on install
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('[Tunely] Extension installed');
    // Set default settings
    chrome.storage.sync.set({
      enabled: true,
      autoTranslate: true,
      targetLanguage: 'en',
      syncLyrics: true,
      theme: 'dark'
    });
  }
});

console.log('[Tunely] Background service worker loaded');
