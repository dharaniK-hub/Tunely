/**
 * Injected Script - Runs in Spotify's context
 */

(function() {
  let lastTrackId = null;

  function monitorPlayerState() {
    try {
      const container = document.querySelector('[data-testid="now-playing-widget"]');
      if (container) {
        const title = container.querySelector('[data-testid="context-item-info-title"]')?.textContent;
        const artist = container.querySelector('[data-testid="context-item-info-subtitles"]')?.textContent;

        if (title && artist) {
          const trackId = `${artist}-${title}`;
          if (trackId !== lastTrackId) {
            lastTrackId = trackId;
            window.postMessage({
              type: 'SPOTIFY_TRACK_CHANGED',
              payload: { artist, title, id: trackId, isPlaying: true }
            }, '*');
          }
        }
      }
      setTimeout(monitorPlayerState, 1000);
    } catch (e) {
      setTimeout(monitorPlayerState, 2000);
    }
  }

  setTimeout(monitorPlayerState, 2000);
})();