import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

import { 
  Search, 
  Music, 
  Heart, 
  Sparkles, 
  Settings as SettingsIcon, 
  Trash2, 
  Info,
  Globe,
  Plus,
  User,
  Lock,
  LogOut
} from "lucide-react";
import GradientBackground from "@/components/GradientBackground";
import LyricsDisplay from "@/components/LyricsDisplay";
import FavoritesList from "@/components/FavoritesList";
import SyncedLyricsPlayer from "@/components/SyncedLyricsPlayer";
import { 
  fetchLyrics, 
  detectLanguage, 
  translateText, 
  SUPPORTED_LANGUAGES, 
  getLanguageName,
  logoutUser,
  changePassword 
} from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { useFavorites } from "@/hooks/use-favorites";

const Index = () => {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState<any>(null);
  
  // Account settings states
  const [showAccountMenu, setShowAccountMenu] = useState(false);
  const [showChangePasswordModal, setShowChangePasswordModal] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);

  // Session enforcement & user loading
  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem("tunely_token");
      const userStr = localStorage.getItem("tunely_user");
      if (!token || !userStr) {
        navigate("/login");
      } else {
        try {
          setCurrentUser(JSON.parse(userStr));
        } catch {
          navigate("/login");
        }
      }
    };

    checkAuth();
    window.addEventListener("auth-changed", checkAuth);
    return () => window.removeEventListener("auth-changed", checkAuth);
  }, [navigate]);

  const handleLogout = async () => {
    setShowAccountMenu(false);
    try {
      await logoutUser();
      toast({
        title: "Logged out successfully!",
        description: "Goodbye!",
      });
      navigate("/login");
    } catch (err: any) {
      toast({
        title: "Logout failed",
        description: err.message || "An unexpected error occurred",
        variant: "destructive",
      });
    }
  };

  const handleChangePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast({
        title: "Passwords do not match",
        description: "Please confirm your new password correctly.",
        variant: "destructive",
      });
      return;
    }

    setChangingPassword(true);
    try {
      await changePassword(currentPassword, newPassword);
      toast({
        title: "Password updated successfully!",
        description: "Your credentials have been updated.",
      });
      setShowChangePasswordModal(false);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      toast({
        title: "Failed to change password",
        description: err.message || "Could not change password",
        variant: "destructive",
      });
    } finally {
      setChangingPassword(false);
    }
  };

  const [artist, setArtist] = useState("");
  const [songTitle, setSongTitle] = useState("");
  const [targetLang, setTargetLang] = useState(() => {
    try { return localStorage.getItem("tunely_target_lang") || "en"; } catch { return "en"; }
  });
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("search");
  
  // Translation Search Result State
  const [result, setResult] = useState<{
    original: string;
    translated: string;
    languages: string[];
    targetLanguage: string;
  } | null>(null);

  // Active song loaded in the Synced Player
  const [syncPlayerSong, setSyncPlayerSong] = useState<{
    artist: string;
    title: string;
    targetLang: string;
  } | null>(null);

  const { favorites, addFavorite, removeFavorite, isFavorite, clearAll, isFetching } = useFavorites();

  const handleSearch = async (overrideArtist?: string, overrideTitle?: string) => {
    const searchArtist = overrideArtist || artist;
    const searchTitle = overrideTitle || songTitle;

    if (!searchArtist.trim() || !searchTitle.trim()) {
      toast({
        title: "Please enter both artist and song title",
        variant: "destructive",
      });
      return;
    }

    // Set search inputs to matching overrides if any (e.g. from favorites click)
    if (overrideArtist) setArtist(overrideArtist);
    if (overrideTitle) setSongTitle(overrideTitle);

    setLoading(true);
    setResult(null);

    try {
      const lyrics = await fetchLyrics(searchArtist, searchTitle);
      const langDetection = await detectLanguage(lyrics);

      const sourceLang = langDetection.primary && langDetection.primary !== targetLang
        ? langDetection.primary
        : "auto";

      let translated = await translateText(lyrics, sourceLang, targetLang);

      if (translated.trim() === lyrics.trim() && sourceLang !== "auto") {
        translated = await translateText(lyrics, "auto", targetLang);
      }

      setResult({
        original: lyrics,
        translated,
        languages: langDetection.languages,
        targetLanguage: targetLang,
      });

      // Automatically pre-load song metadata into synced player state
      setSyncPlayerSong({
        artist: searchArtist,
        title: searchTitle,
        targetLang: targetLang
      });

    } catch (err: any) {
      toast({
        title: "Error fetching lyrics",
        description: err.message || "Something went wrong",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAddFavorite = async () => {
    if (!artist.trim() || !songTitle.trim() || !result) return;
    
    // Use first detected language or auto
    const primaryLang = result.languages[0] || "auto";
    const added = await addFavorite(artist, songTitle, primaryLang);
    
    if (added) {
      toast({
        title: "Added to favorites!",
        description: `"${songTitle}" by ${artist}`,
      });
    } else {
      toast({
        title: "Could not add favorite",
        description: "This song may already be saved, or there was a server error.",
        variant: "destructive",
      });
    }
  };

  const handleRemoveFavoriteClick = async (favArtist: string, favTitle: string) => {
    await removeFavorite(favArtist, favTitle);
    toast({
      title: "Removed from favorites",
      description: `"${favTitle}" by ${favArtist}`,
    });
  };

  const handleSelectFavorite = (favArtist: string, favTitle: string) => {
    setActiveTab("search");
    handleSearch(favArtist, favTitle);
  };

  const handleClearAllFavorites = () => {
    clearAll();
    toast({
      title: "Favorites cleared",
      description: "All songs have been removed from your favorites list.",
    });
  };

  return (
    <div className="relative min-h-screen flex flex-col bg-transparent text-foreground select-none">
      <GradientBackground />

      {/* Modern Dashboard Header */}
      <header className="sticky top-0 z-40 w-full border-b border-border/40 bg-background/40 backdrop-blur-xl">
        <div className="max-w-[1440px] mx-auto px-6 md:px-8 h-18 flex items-center justify-between py-3">
          
          {/* Logo */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => {
            setResult(null);
            setArtist("");
            setSongTitle("");
            setActiveTab("search");
          }}>
            <div className="flex items-center justify-center w-10.5 h-10.5 rounded-xl bg-gradient-to-r from-primary to-accent shadow-md">
              <Music className="h-5 w-5 text-white" />
            </div>
            <span className="text-2xl font-black bg-gradient-to-r from-primary via-accent to-emerald-400 bg-clip-text text-transparent tracking-tight">
              Tunely
            </span>
          </div>

          {/* Navigation and Account Control Container */}
          <div className="flex items-center gap-4">
            {/* Navigation Tabs (Horizontal Pill Switcher) */}
            <div className="bg-secondary/40 border border-border/40 p-1 rounded-xl flex items-center h-11 select-none">
              <button
                onClick={() => setActiveTab("search")}
                className={`flex items-center gap-2 px-4 py-1.5 text-sm font-semibold rounded-lg transition-all ${
                  activeTab === "search"
                    ? "bg-secondary text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Search className="h-4 w-4" />
                Search
              </button>
              <button
                onClick={() => setActiveTab("favorites")}
                className={`flex items-center gap-2 px-4 py-1.5 text-sm font-semibold rounded-lg transition-all ${
                  activeTab === "favorites"
                    ? "bg-secondary text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Heart className="h-4 w-4" />
                Favorites
              </button>
              <button
                onClick={() => setActiveTab("synced")}
                className={`flex items-center gap-2 px-4 py-1.5 text-sm font-semibold rounded-lg transition-all ${
                  activeTab === "synced"
                    ? "bg-secondary text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Sparkles className="h-4 w-4" />
                Synced Player
              </button>
              <button
                onClick={() => setActiveTab("settings")}
                className={`flex items-center gap-2 px-4 py-1.5 text-sm font-semibold rounded-lg transition-all ${
                  activeTab === "settings"
                    ? "bg-secondary text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <SettingsIcon className="h-4 w-4" />
                Settings
              </button>
            </div>

            {/* User Greeting & Account Menu */}
            {currentUser && (
              <div className="flex items-center gap-3.5 pl-4 border-l border-border/40 h-8">
                {/* Account Button */}
                <div className="relative">
                  <Button
                    onClick={() => setShowAccountMenu(!showAccountMenu)}
                    className="flex items-center gap-2 h-9 px-3 rounded-lg bg-secondary hover:bg-secondary/80 border border-border/40 text-foreground font-bold text-xs"
                  >
                    <User className="h-4 w-4 text-primary" />
                    Account
                  </Button>
                  
                  {/* Account Menu Dropdown Card */}
                  {showAccountMenu && (
                    <>
                      {/* Click outside trigger overlay */}
                      <div 
                        className="fixed inset-0 z-40" 
                        onClick={() => setShowAccountMenu(false)}
                      />
                      <div className="absolute right-0 mt-2 w-56 glass-card rounded-xl border border-white/10 shadow-2xl p-2 bg-background/95 backdrop-blur-2xl z-50 animate-in fade-in duration-200">
                        {/* Menu Header with User Info */}
                        <div className="px-3 py-2 border-b border-border/30 mb-1">
                          <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Signed in as</p>
                          <p className="text-xs font-bold truncate text-foreground">{currentUser.username}</p>
                          <p className="text-[10px] text-muted-foreground truncate">{currentUser.email || "No email"}</p>
                        </div>
                        
                        {/* Menu Items */}
                        <button
                          onClick={() => {
                            setShowAccountMenu(false);
                            setShowChangePasswordModal(true);
                          }}
                          className="w-full text-left px-3 py-2 text-xs font-semibold rounded-lg hover:bg-secondary/60 text-foreground transition-colors flex items-center gap-2"
                        >
                          <Lock className="h-3.5 w-3.5 text-primary" />
                          Change Password
                        </button>
                        
                        <button
                          onClick={handleLogout}
                          className="w-full text-left px-3 py-2 text-xs font-semibold rounded-lg hover:bg-destructive/10 text-destructive transition-colors flex items-center gap-2"
                        >
                          <LogOut className="h-3.5 w-3.5" />
                          Log Out
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Viewport Content Container */}
      <main className="flex-1 max-w-[1440px] w-full mx-auto px-6 md:px-8 py-8">
        
        {/* TABS CONTAINER */}
        <div className="w-full">
          
          {/* TAB 1: SEARCH & STATIC LYRICS */}
          {activeTab === "search" && (
            <div className="w-full">
              {!result && !loading && (
                <div className="w-full max-w-md mx-auto px-4 text-center animate-fade-in pt-12">
                  <div className="mb-10 select-none">
                    {/* Premium Gradient Logo */}
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-primary via-accent to-emerald-400 shadow-xl shadow-primary/10 border border-white/20 mb-6 transition-transform hover:scale-105 duration-300">
                      <Music className="h-10 w-10 text-white" />
                    </div>
                    


                    {/* Title */}
                    <h1 className="text-3xl sm:text-4.5xl font-black tracking-tight text-foreground mb-3 leading-none">
                      Lyrics <span className="bg-gradient-to-r from-primary via-accent to-emerald-400 bg-clip-text text-transparent">Translation</span>
                    </h1>

                    {/* Subtitle */}
                    <p className="text-xs sm:text-sm text-muted-foreground/90 max-w-sm mx-auto font-medium leading-relaxed">
                      Your premium music lyrics translator and synchronizer. Search any song to extract original lyrics and translate them instantly.
                    </p>
                  </div>

                  <div className="glass-card rounded-2xl p-6 space-y-4 shadow-xl border border-border/30">
                    <div className="space-y-3">
                      <Input
                        placeholder="Artist name (e.g. Shakira, BTS)"
                        value={artist}
                        onChange={(e) => setArtist(e.target.value)}
                        className="bg-secondary/40 border-border/50 h-11 focus-visible:ring-primary"
                        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                      />
                      <Input
                        placeholder="Song title (e.g. Hips Don't Lie, Dynamite)"
                        value={songTitle}
                        onChange={(e) => setSongTitle(e.target.value)}
                        className="bg-secondary/40 border-border/50 h-11 focus-visible:ring-primary"
                        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                      />
                    </div>

                    <div className="flex items-center gap-3 bg-secondary/30 border border-border/40 rounded-lg px-3 py-2">
                      <Globe className="h-4 w-4 text-primary shrink-0" />
                      <span className="text-xs text-muted-foreground font-semibold">Translate to:</span>
                      <select
                        value={targetLang}
                        onChange={(e) => { setTargetLang(e.target.value); try { localStorage.setItem("tunely_target_lang", e.target.value); } catch {} }}
                        className="bg-transparent text-xs text-foreground focus:outline-none ml-auto cursor-pointer font-bold"
                      >
                        {SUPPORTED_LANGUAGES.map((lang) => (
                          <option key={lang.code} value={lang.code} className="bg-background">
                            {lang.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <Button
                      onClick={() => handleSearch()}
                      className="w-full gap-2 h-11 bg-gradient-to-r from-primary to-accent hover:opacity-90 text-primary-foreground font-semibold shadow-lg hover:shadow-primary/10 transition-all"
                    >
                      <Search className="h-4 w-4" />
                      Search & Translate
                    </Button>
                  </div>
                </div>
              )}

              {loading && (
                <div className="w-full pt-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {[0, 1].map((i) => (
                      <div key={i} className="glass-card rounded-xl p-6 space-y-3 border border-border/30">
                        <Skeleton className="h-4 w-28 bg-muted" />
                        {Array.from({ length: 9 }).map((_, j) => (
                          <Skeleton
                            key={j}
                            className="h-4 bg-muted"
                            style={{ width: `${60 + Math.random() * 40}%` }}
                          />
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result && (
                <div className="space-y-4">
                  <div className="flex justify-end items-center">
                    <Button
                      variant="outline"
                      onClick={handleAddFavorite}
                      className={`gap-2 text-sm font-semibold h-10 px-4 rounded-lg transition-all ${
                        isFavorite(artist, songTitle) 
                          ? "bg-primary/20 hover:bg-primary/30 text-primary border-primary/40" 
                          : "hover:bg-secondary"
                      }`}
                    >
                      <Heart className={`h-4 w-4 ${isFavorite(artist, songTitle) ? "fill-current" : ""}`} />
                      {isFavorite(artist, songTitle) ? "Saved to Favorites" : "Add to Favorites"}
                    </Button>
                  </div>

                  <LyricsDisplay
                    artist={artist}
                    title={songTitle}
                    original={result.original}
                    translated={result.translated}
                    languages={result.languages}
                    targetLang={result.targetLanguage}
                    onBack={() => setResult(null)}
                    onSyncPlay={() => setActiveTab("synced")}
                  />
                </div>
              )}
            </div>
          )}

          {/* TAB 2: FAVORITES LIST */}
          {activeTab === "favorites" && (
            <div className="w-full animate-fade-in">
              <div className="flex items-center justify-between mb-6 border-b border-border/40 pb-4">
                <div>
                  <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                    <Heart className="h-5 w-5 text-primary fill-current" /> Favorite Songs
                  </h2>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Your collection of saved tracks and translations
                  </p>
                </div>

                {favorites.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleClearAllFavorites}
                    className="text-destructive hover:text-destructive hover:bg-destructive/10 gap-1.5 text-xs font-semibold"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Clear All
                  </Button>
                )}
              </div>

              {isFetching && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-2">
                  {[1,2,3].map(i => (
                    <div key={i} className="glass-card rounded-xl p-5 border border-border/30 space-y-3 animate-pulse">
                      <div className="h-4 bg-muted/60 rounded w-3/4" />
                      <div className="h-3 bg-muted/40 rounded w-1/2" />
                      <div className="h-3 bg-muted/30 rounded w-1/4" />
                    </div>
                  ))}
                </div>
              )}

              <FavoritesList
                favorites={favorites}
                onSelectFavorite={handleSelectFavorite}
                onRemoveFavorite={handleRemoveFavoriteClick}
              />
            </div>
          )}

          {/* TAB 3: SYNCED PLAYBACK PLAYER */}
          {activeTab === "synced" && (
            <div className="w-full">
              {syncPlayerSong ? (
                <SyncedLyricsPlayer
                  artist={syncPlayerSong.artist}
                  title={syncPlayerSong.title}
                  initialTargetLang={syncPlayerSong.targetLang}
                  onBack={() => {
                    // Go back to static lyrics search result if it matches current player
                    if (result && artist === syncPlayerSong.artist && songTitle === syncPlayerSong.title) {
                      setActiveTab("search");
                    } else {
                      setSyncPlayerSong(null);
                      setActiveTab("search");
                    }
                  }}
                />
              ) : (
                <div className="w-full max-w-md mx-auto text-center px-4 py-16 animate-fade-in">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-secondary/80 border border-border/40 mb-4 text-muted-foreground shadow-md">
                    <Sparkles className="h-8 w-8 text-primary" />
                  </div>
                  <h2 className="text-2xl font-bold text-foreground">No song playing</h2>
                  <p className="text-sm text-muted-foreground mt-2 max-w-xs mx-auto leading-relaxed">
                    Search for a song in the Search tab first, then click "Sync Karaoke Player" to sync lyrics!
                  </p>
                  <Button
                    onClick={() => setActiveTab("search")}
                    className="mt-6 gap-2 bg-gradient-to-r from-primary to-accent text-primary-foreground font-semibold"
                  >
                    Go to Search
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: APP SETTINGS */}
          {activeTab === "settings" && (
            <div className="w-full max-w-2xl mx-auto px-4 animate-fade-in space-y-6">
              <div className="border-b border-border/40 pb-4">
                <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                  <SettingsIcon className="h-5 w-5 text-primary" /> Settings
                </h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Configure preferences for your lyrics translator application
                </p>
              </div>

              <div className="space-y-4">
                {/* Default translation settings */}
                <div className="glass-card rounded-xl p-5 border border-border/40 space-y-4">
                  <h3 className="text-sm font-bold text-foreground flex items-center gap-2 border-b border-border/20 pb-2">
                    <Globe className="h-4 w-4 text-primary" /> Translation Settings
                  </h3>
                  
                  <div className="flex items-center justify-between text-sm">
                    <div className="space-y-0.5">
                      <p className="font-semibold text-foreground">Default Target Language</p>
                      <p className="text-xs text-muted-foreground">The language used when loading a new song translation.</p>
                    </div>
                    <select
                      value={targetLang}
                      onChange={(e) => { setTargetLang(e.target.value); try { localStorage.setItem("tunely_target_lang", e.target.value); } catch {} }}
                      className="bg-secondary/60 text-xs border border-border/60 rounded-md px-2.5 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer font-semibold"
                    >
                      {SUPPORTED_LANGUAGES.map((lang) => (
                        <option key={lang.code} value={lang.code}>
                          {lang.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Storage and caching */}
                <div className="glass-card rounded-xl p-5 border border-border/40 space-y-4">
                  <h3 className="text-sm font-bold text-foreground flex items-center gap-2 border-b border-border/20 pb-2">
                    <Trash2 className="h-4 w-4 text-primary" /> Storage & Reset
                  </h3>
                  
                  <div className="flex items-center justify-between text-sm">
                    <div className="space-y-0.5">
                      <p className="font-semibold text-foreground">Clear Saved Favorites</p>
                      <p className="text-xs text-muted-foreground">Permanently delete all songs in your favorites list ({favorites.length} saved).</p>
                    </div>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={handleClearAllFavorites}
                      disabled={favorites.length === 0}
                      className="font-semibold"
                    >
                      Clear Favorites
                    </Button>
                  </div>
                </div>

                {/* Info and help section */}
                <div className="glass-card rounded-xl p-5 border border-border/40 space-y-4">
                  <h3 className="text-sm font-bold text-foreground flex items-center gap-2 border-b border-border/20 pb-2">
                    <Info className="h-4 w-4 text-primary" /> About Tunely
                  </h3>
                  <div className="text-xs text-muted-foreground space-y-2.5 leading-relaxed">
                    <p>
                      <strong>Tunely</strong> is an intelligent lyrics search and translator application. It uses a FastAPI backend that aggregates lyrics, detects language structures, and provides real-time translations using high-speed translation models.
                    </p>
                    <p>
                      <strong>Sync Player:</strong> By using the timestamp generation engine in the backend, Tunely simulates a fully-fledged media player matching Spotify or Apple Music, scrolling lines dynamically to help you read and learn foreign languages in real time.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>
      </main>

      {/* Simple Footer */}
      <footer className="border-t border-border/30 bg-background/30 py-4 text-center text-xs text-muted-foreground">
        <p>&copy; {new Date().getFullYear()} Tunely. Created with care.</p>
      </footer>

      {/* Change Password Dialog Modal */}
      {showChangePasswordModal && (
        <div className="fixed inset-0 bg-background/60 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-[400px] glass-card rounded-2xl border border-white/10 shadow-2xl p-6 bg-background/30 backdrop-blur-2xl transition-all duration-300 animate-in zoom-in-95 duration-200">
            
            <h3 className="text-xl font-black tracking-tight text-center mb-6 text-foreground">
              Change Password
            </h3>
            
            <form onSubmit={handleChangePasswordSubmit} className="space-y-4">
              {/* Skip current password input if user has oauth_provider */}
              {!currentUser?.oauth_provider && (
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-muted-foreground/80 tracking-wide uppercase">
                    Current Password
                  </label>
                  <Input
                    type="password"
                    placeholder="••••••••"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    className="bg-secondary/40 border-border/50 h-10 focus-visible:ring-primary font-medium text-sm text-foreground"
                    required
                  />
                </div>
              )}
              
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-muted-foreground/80 tracking-wide uppercase">
                  New Password
                </label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="bg-secondary/40 border-border/50 h-10 focus-visible:ring-primary font-medium text-sm text-foreground"
                  required
                />
              </div>
              
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-muted-foreground/80 tracking-wide uppercase">
                  Confirm New Password
                </label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="bg-secondary/40 border-border/50 h-10 focus-visible:ring-primary font-medium text-sm text-foreground"
                  required
                />
              </div>
              
              <div className="flex justify-end gap-2.5 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowChangePasswordModal(false);
                    setCurrentPassword("");
                    setNewPassword("");
                    setConfirmPassword("");
                  }}
                  className="h-10 border-border/50 font-semibold text-xs"
                  disabled={changingPassword}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="h-10 bg-gradient-to-r from-primary to-accent text-primary-foreground font-semibold shadow-lg hover:shadow-primary/10 transition-all text-xs"
                  disabled={changingPassword}
                >
                  {changingPassword ? "Updating..." : "Update Password"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Index;
