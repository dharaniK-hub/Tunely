const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("tunely_token");
  return token ? { "Authorization": `Bearer ${token}` } : {};
}

export async function fetchLyrics(artist: string, title: string): Promise<string> {
  const res = await fetch(
    `${API_BASE_URL}/lyrics?artist=${encodeURIComponent(artist)}&title=${encodeURIComponent(title)}`,
    { headers: getAuthHeaders() }
  );
  if (!res.ok) {
    throw new Error("Lyrics not found. Please check the artist and song title.");
  }
  const data = await res.json();
  if (!data.lyrics) {
    throw new Error("No lyrics available for this song.");
  }
  return data.lyrics.trim();
}

export async function detectLanguage(text: string): Promise<{ languages: string[]; primary: string }> {
  try {
    // Send the full text for more accurate detection
    const res = await fetch(`${API_BASE_URL}/detect`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        ...getAuthHeaders()
      },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error();
    const data = await res.json();
    return {
      languages: data.languages || [data.language || "auto"],
      primary: data.primary_language || data.language || "auto",
    };
  } catch {
    return { languages: ["auto"], primary: "auto" };
  }
}

export async function translateText(
  text: string,
  source: string = "auto",
  target: string = "en"
): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/translate`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify({
      text,
      source: source === "auto" ? "auto" : source,
      target,
    }),
  });

  if (!res.ok) {
    throw new Error("Translation service unavailable. Please try again later.");
  }

  const data = await res.json();
  return data.translatedText;
}

const LANGUAGE_NAMES: Record<string, string> = {
  en: "English", es: "Spanish", fr: "French", de: "German",
  it: "Italian", pt: "Portuguese", ja: "Japanese", ko: "Korean",
  zh: "Chinese", ar: "Arabic", ru: "Russian", hi: "Hindi",
  nl: "Dutch", sv: "Swedish", pl: "Polish", tr: "Turkish",
  si: "Sinhala",
  auto: "Unknown",
};

export function getLanguageName(code: string | undefined | null): string {
  if (!code) return "Unknown";
  return LANGUAGE_NAMES[code] || code.toUpperCase();
}

// Extract romanization from mixed-script lyrics (e.g., Korean + romanization)
export function extractRomanization(text: string): string {
  // Check if text has Korean characters
  const hasKorean = /[\uac00-\ud7af\u1100-\u11ff]/.test(text);
  
  if (!hasKorean) {
    return text; // If no Korean, return as-is
  }
  
  // Extract only ASCII letters, numbers, spaces, and punctuation
  const lines = text.split('\n');
  const romanizedLines = lines
    .map(line => {
      // Keep only ASCII characters and common punctuation/spaces
      return line
        .split('')
        .filter(c => /^[a-zA-Z0-9\s.,!?:;'"()\-]$/.test(c))
        .join('')
        .replace(/\s+/g, ' ')
        .trim();
    })
    .filter(line => line.length > 0); // Remove empty lines
  
  return romanizedLines.join('\n');
}

export interface TimestampLine {
  text: string;
  start_time: number;
  end_time: number;
  translated_text?: string | null;
}

export interface LyricsTimestampsData {
  song_id: string;
  artist: string;
  title: string;
  language: string;
  lines: TimestampLine[];
  duration_ms: number;
}

export async function fetchLyricsTimestamps(artist: string, title: string): Promise<LyricsTimestampsData> {
  const res = await fetch(
    `${API_BASE_URL}/v3/lyrics/timestamps?artist=${encodeURIComponent(artist)}&title=${encodeURIComponent(title)}`,
    { headers: getAuthHeaders() }
  );
  if (!res.ok) {
    throw new Error("Lyrics timestamps not available. Fallback to standard translation.");
  }
  const data = await res.json();
  if (data.error) {
    throw new Error(data.error);
  }
  return data.data;
}

export interface SpotifyTrack {
  id: string;
  name: string;
  artist: string;
  album: string;
  duration_ms: number;
  image_url?: string;
  preview_url?: string;
  spotify_uri?: string;
}

export async function searchSpotifyTrack(artist: string, title: string): Promise<SpotifyTrack | null> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/v3/spotify/search?artist=${encodeURIComponent(artist)}&title=${encodeURIComponent(title)}`,
      { 
        method: "POST",
        headers: getAuthHeaders()
      }
    );
    if (!res.ok) return null;
    const data = await res.json();
    if (data.success && data.track) {
      return data.track;
    }
    return null;
  } catch (err) {
    console.error("Spotify search failed:", err);
    return null;
  }
}

export interface LanguageOption {
  code: string;
  name: string;
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: "en", name: "English" },
  { code: "es", name: "Spanish" },
  { code: "fr", name: "French" },
  { code: "de", name: "German" },
  { code: "it", name: "Italian" },
  { code: "pt", name: "Portuguese" },
  { code: "ja", name: "Japanese" },
  { code: "ko", name: "Korean" },
  { code: "zh-CN", name: "Chinese (Simplified)" },
  { code: "ru", name: "Russian" },
  { code: "hi", name: "Hindi" },
  { code: "ta", name: "Tamil" },
  { code: "si", name: "Sinhala" },
  { code: "tr", name: "Turkish" },
  { code: "nl", name: "Dutch" },
  { code: "sv", name: "Swedish" },
  { code: "pl", name: "Polish" },
  { code: "ar", name: "Arabic" },
];

// Authentication Types
export interface User {
  id: number;
  username: string;
  email: string | null;
  oauth_provider: string | null;
}

export interface AuthResponse {
  success: boolean;
  message?: string;
  token?: string;
  user?: User;
}

// Helper to extract FastAPI validation errors
function extractErrorMessage(data: any, fallback: string): string {
  if (data?.detail) {
    if (typeof data.detail === "string") {
      return data.detail;
    } else if (Array.isArray(data.detail)) {
      return data.detail.map((err: any) => err.msg.replace(/^Value error, /, '')).join(", ");
    }
  }
  return fallback;
}

// Authentication API Helper Functions
export async function signupUser(username: string, password: string, email?: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, email }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(extractErrorMessage(data, "Signup failed"));
  }
  return data;
}

export async function loginUser(username: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(extractErrorMessage(data, "Login failed"));
  }
  return data;
}

export async function oauthLogin(provider: string, email: string, oauthId: string, username?: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/oauth`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, email, oauth_id: oauthId, username }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(extractErrorMessage(data, "OAuth login failed"));
  }
  return data;
}

export async function logoutUser(): Promise<void> {
  try {
    await fetch(`${API_BASE_URL}/api/auth/logout`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
  } catch (err) {
    console.error("Logout request failed:", err);
  } finally {
    localStorage.removeItem("tunely_token");
    localStorage.removeItem("tunely_user");
  }
}

export async function getCurrentUser(): Promise<User | null> {
  const token = localStorage.getItem("tunely_token");
  if (!token) return null;
  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) {
      localStorage.removeItem("tunely_token");
      localStorage.removeItem("tunely_user");
      return null;
    }
    const data = await res.json();
    return data.user;
  } catch (err) {
    console.error("Fetch current user failed:", err);
    return null;
  }
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/auth/change-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify({ current_password: currentPassword || null, new_password: newPassword })
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(extractErrorMessage(data, "Failed to change password"));
  }
  return await res.json();
}

// User Favorites persisted API Helper Functions
export interface BackendFavorite {
  id: string;
  artist: string;
  title: string;
  language: string;
  addedAt: number;
}

export async function fetchUserFavorites(): Promise<BackendFavorite[]> {
  const res = await fetch(`${API_BASE_URL}/api/favorites`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error("Failed to fetch favorites");
  }
  const data = await res.json();
  return data.favorites || [];
}

export async function addUserFavorite(artist: string, title: string, language: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/favorites`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ artist, title, language }),
  });
  if (!res.ok) {
    throw new Error("Failed to save favorite to database");
  }
}

export async function removeUserFavorite(artist: string, title: string): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/api/favorites?artist=${encodeURIComponent(artist)}&title=${encodeURIComponent(title)}`,
    {
      method: "DELETE",
      headers: getAuthHeaders(),
    }
  );
  if (!res.ok) {
    throw new Error("Failed to delete favorite from database");
  }
}

