## Auto Lyrics Translator — V1 MVP

### Overview

A beautiful lyrics translation app with animated purple/pink/blue gradients. Users search for a song, see original lyrics, and get an English translation — all from the browser.

### Design

- **Dark background** with animated moving gradient blobs (purple `#8B5CF6`, hot pink `#EC4899`, electric blue `#3B82F6`)
- Glassmorphism cards for content areas
- Smooth animations and transitions throughout
- Clean, modern typography

### Pages & Components

**1. Home / Search Page**

- Large centered search with two fields: **Artist** and **Song Title**
- Animated gradient background with floating blobs
- App logo/title "Tunely" with subtle glow effect
- Search button triggers lyrics fetch

**2. Results View**

- Two-column layout: **Original lyrics** (left) | **Translated lyrics** (right)
- Language badge showing detected source language
- Loading skeleton while fetching/translating
- "Back to search" button
- Copy-to-clipboard for translated lyrics

### API Integration

- **Lyrics**: `lyrics.ovh` public API (no key needed) — called directly from browser
- **Translation**: `LibreTranslate` public instance — called directly from browser
- **Language detection**: Done via LibreTranslate's detect endpoint

### Flow

1. User enters artist + song title → hits Search
2. App fetches lyrics from lyrics.ovh
3. App detects language via LibreTranslate
4. App translates lyrics line-by-line to English
5. Results displayed side-by-side with smooth fade-in
