import { useState, useEffect, useRef } from "react";
import { 
  Play, 
  Pause, 
  RotateCcw, 
  SkipBack, 
  SkipForward, 
  Music, 
  Globe, 
  Sparkles, 
  Volume2, 
  VolumeX, 
  ChevronLeft 
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  fetchLyricsTimestamps, 
  translateText, 
  searchSpotifyTrack, 
  getLanguageName, 
  SUPPORTED_LANGUAGES,
  TimestampLine,
  SpotifyTrack
} from "@/lib/api";
import { toast } from "@/hooks/use-toast";

function romanizeKoreanChar(char: string): string {
  const code = char.charCodeAt(0);
  if (code >= 0xAC00 && code <= 0xD7A3) {
    const S = code - 0xAC00;
    const I = Math.floor(S / 588);
    const V = Math.floor((S % 588) / 28);
    const F = S % 28;

    const initials = ['g', 'kk', 'n', 'd', 'tt', 'r', 'm', 'b', 'pp', 's', 'ss', '', 'j', 'jj', 'ch', 'k', 't', 'p', 'h'];
    const vowels = ['a', 'ae', 'ya', 'yae', 'eo', 'e', 'yeo', 'ye', 'o', 'wa', 'wae', 'oe', 'yo', 'u', 'wo', 'we', 'wi', 'yu', 'eu', 'ui', 'i'];
    const finals = ['', 'g', 'kk', 'gs', 'n', 'nj', 'nh', 'd', 'l', 'lg', 'lm', 'lb', 'ls', 'lt', 'lp', 'lh', 'm', 'b', 'bs', 's', 'ss', 'ng', 'j', 'ch', 'k', 't', 'p', 'h'];

    return initials[I] + vowels[V] + finals[F];
  }
  return char;
}

function romanizeText(text: string): string {
  if (!text) return "";
  const romanized = text.split('').map(romanizeKoreanChar).join('');
  return romanized.charAt(0).toUpperCase() + romanized.slice(1);
}

interface SyncedLyricsPlayerProps {
  artist: string;
  title: string;
  initialTargetLang?: string;
  onBack: () => void;
}

export default function SyncedLyricsPlayer({
  artist,
  title,
  initialTargetLang = "en",
  onBack
}: SyncedLyricsPlayerProps) {
  const [loading, setLoading] = useState(true);
  const [translating, setTranslating] = useState(false);
  const [lyricsData, setLyricsData] = useState<{
    language: string;
    lines: TimestampLine[];
    duration_ms: number;
  } | null>(null);
  
  const [spotifyTrack, setSpotifyTrack] = useState<SpotifyTrack | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [targetLang, setTargetLang] = useState(initialTargetLang);
  const [fontSize, setFontSize] = useState<"sm" | "base" | "lg" | "xl">("lg");
  const [showTranslation, setShowTranslation] = useState(true);
  const [volume, setVolume] = useState(0.8);
  const [audioMuted, setAudioMuted] = useState(false);
  
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const lineRefs = useRef<(HTMLDivElement | null)[]>([]);
  // Track current time in a ref so simulation effect doesn't get stale
  const currentTimeRef = useRef(0);

  // 1. Fetch Lyrics Timestamps and Spotify Metadata
  useEffect(() => {
    let cancelled = false;
    
    async function loadData() {
      setLoading(true);
      setCurrentTime(0);
      currentTimeRef.current = 0;
      setIsPlaying(false);
      
      try {
        const trackPromise = searchSpotifyTrack(artist, title);
        const timestampsPromise = fetchLyricsTimestamps(artist, title);
        
        const [track, timestamps] = await Promise.all([
          trackPromise,
          timestampsPromise
        ]);
        
        if (cancelled) return;
        
        setSpotifyTrack(track);
        
        // Translate the lines immediately
        setTranslating(true);
        const lang = timestamps.language || "auto";
        const originalText = timestamps.lines.map(l => l.text).join("\n");
        const translatedText = await translateText(originalText, lang, initialTargetLang);
        
        if (cancelled) return;
        
        const translatedLines = translatedText.split("\n");
        
        const linesWithTranslation = timestamps.lines.map((line, idx) => ({
          ...line,
          translated_text: translatedLines[idx] || line.translated_text || ""
        }));

        setLyricsData({
          language: timestamps.language,
          duration_ms: timestamps.duration_ms,
          lines: linesWithTranslation
        });
      } catch (err: any) {
        if (!cancelled) {
          toast({
            title: "Player Load Error",
            description: err.message || "Failed to load synced lyrics.",
            variant: "destructive"
          });
          onBack();
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
          setTranslating(false);
        }
      }
    }
    
    loadData();
    return () => { cancelled = true; };
  }, [artist, title]);

  // 2. Translate lyrics when target language changes (after initial load)
  useEffect(() => {
    if (!lyricsData || loading) return;
    
    let cancelled = false;
    
    async function performTranslation() {
      setTranslating(true);
      try {
        const originalText = lyricsData!.lines.map(l => l.text).join("\n");
        const translatedText = await translateText(originalText, lyricsData!.language || "auto", targetLang);
        
        if (cancelled) return;
        
        const translatedLines = translatedText.split("\n");
        
        setLyricsData(prev => {
          if (!prev) return null;
          return {
            ...prev,
            lines: prev.lines.map((line, idx) => ({
              ...line,
              translated_text: translatedLines[idx] || ""
            }))
          };
        });
      } catch (err: any) {
        if (!cancelled) {
          toast({
            title: "Translation Error",
            description: "Failed to update lyrics translation.",
            variant: "destructive"
          });
        }
      } finally {
        if (!cancelled) setTranslating(false);
      }
    }
    
    performTranslation();
    return () => { cancelled = true; };
  }, [targetLang]); // eslint-disable-line react-hooks/exhaustive-deps

  const isSpotifyPreview = !!(spotifyTrack?.preview_url && !spotifyTrack?.id.includes("_"));

  const durationMs = isSpotifyPreview 
    ? 30000 // Spotify preview is always 30s
    : (lyricsData?.duration_ms || spotifyTrack?.duration_ms || 180000);

  // 3. Audio / Simulation Playback Loop
  useEffect(() => {
    if (!isPlaying) return;

    const audio = audioRef.current;
    if (isSpotifyPreview && audio) {
      // Audio-driven playback: sync state from the audio element
      audio.volume = audioMuted ? 0 : volume;
      audio.play().catch(() => {
        setIsPlaying(false);
      });

      const interval = setInterval(() => {
        setCurrentTime(audio.currentTime * 1000);
        currentTimeRef.current = audio.currentTime * 1000;
      }, 33);

      return () => {
        clearInterval(interval);
      };
    }

    // Simulation-driven playback (no audio preview available)
    const startWallTime = Date.now() - currentTimeRef.current;
    const interval = setInterval(() => {
      const elapsed = Date.now() - startWallTime;
      if (elapsed >= durationMs) {
        setCurrentTime(durationMs);
        currentTimeRef.current = durationMs;
        setIsPlaying(false);
        clearInterval(interval);
      } else {
        setCurrentTime(elapsed);
        currentTimeRef.current = elapsed;
      }
    }, 33); // ~30 FPS

    return () => clearInterval(interval);
  }, [isPlaying, isSpotifyPreview, durationMs, audioMuted, volume]);

  // 4. Sync HTML Audio element state with React state
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) {
      audio.play().catch(() => setIsPlaying(false));
    } else {
      audio.pause();
    }
  }, [isPlaying]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.volume = audioMuted ? 0 : volume;
  }, [audioMuted, volume]);

  const handleAudioTimeUpdate = () => {
    const audio = audioRef.current;
    if (!audio) return;
    setCurrentTime(audio.currentTime * 1000);
    currentTimeRef.current = audio.currentTime * 1000;
  };

  const handleAudioEnded = () => {
    setIsPlaying(false);
    setCurrentTime(0);
    currentTimeRef.current = 0;
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
    }
  };

  // 5. Detect current active lyric line
  const activeLineIndex = lyricsData?.lines.findIndex((line, idx) => {
    const nextLine = lyricsData.lines[idx + 1];
    // Map full song timestamps to preview duration if playing preview
    const scale = isSpotifyPreview && lyricsData?.duration_ms
      ? (30000 / lyricsData.duration_ms) 
      : 1;
    
    const start = line.start_time * scale;
    const end = nextLine ? (nextLine.start_time * scale) : (durationMs);
    
    return currentTime >= start && currentTime < end;
  }) ?? -1;

  // 6. Smooth scrolling to center active line
  useEffect(() => {
    if (activeLineIndex !== -1 && lineRefs.current[activeLineIndex]) {
      lineRefs.current[activeLineIndex]?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [activeLineIndex]);

  // Format milliseconds to MM:SS
  const formatTime = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };

  const handleProgressChange = (values: number[]) => {
    const newTime = values[0];
    setCurrentTime(newTime);
    currentTimeRef.current = newTime;
    if (audioRef.current && isSpotifyPreview) {
      audioRef.current.currentTime = newTime / 1000;
    }
  };

  const handleTogglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const handleRestart = () => {
    setCurrentTime(0);
    currentTimeRef.current = 0;
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
    }
  };

  const skipTime = (amountMs: number) => {
    const newTime = Math.max(0, Math.min(durationMs, currentTimeRef.current + amountMs));
    setCurrentTime(newTime);
    currentTimeRef.current = newTime;
    if (audioRef.current && isSpotifyPreview) {
      audioRef.current.currentTime = newTime / 1000;
    }
  };

  const fontSizes = {
    sm: "text-xs md:text-sm",
    base: "text-sm md:text-base",
    lg: "text-base md:text-lg",
    xl: "text-lg md:text-xl"
  };

  const transFontSizes = {
    sm: "text-[10px] md:text-xs",
    base: "text-xs md:text-sm",
    lg: "text-sm md:text-base",
    xl: "text-base md:text-lg"
  };

  if (loading) {
    return (
      <div className="w-full py-8 space-y-6">
        <div className="flex items-center gap-2">
          <Skeleton className="h-8 w-24 bg-muted/60" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-5 space-y-6">
            <Skeleton className="aspect-square w-full rounded-2xl bg-muted/60" />
            <Skeleton className="h-24 w-full rounded-xl bg-muted/60" />
          </div>
          <div className="lg:col-span-7">
            <Skeleton className="h-[450px] w-full rounded-2xl bg-muted/60" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full py-6">
      {/* Hidden audio element for preview */}
      {spotifyTrack?.preview_url && (
        <audio
          ref={audioRef}
          src={spotifyTrack.preview_url}
          onTimeUpdate={handleAudioTimeUpdate}
          onEnded={handleAudioEnded}
        />
      )}

      {/* Back Button */}
      <div className="flex items-center justify-between mb-6">
        <Button 
          variant="ghost" 
          onClick={onBack} 
          className="gap-2 text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="h-4 w-4" />
          Back to Search
        </Button>
        <Badge className="bg-primary/20 text-primary border-primary/30">
          Sync Player Mode
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* LEFT COLUMN: Player Card & Controls */}
        <div className="lg:col-span-5 space-y-6">
          <div className="glass-card rounded-2xl p-6 flex flex-col items-center text-center relative overflow-hidden shadow-2xl">
            {/* Spinning Record / Album Art */}
            <div className="relative group mb-6">
              {spotifyTrack?.image_url ? (
                <img
                  src={spotifyTrack.image_url}
                  alt={spotifyTrack.album || "Album cover"}
                  className={`w-64 h-64 rounded-full object-cover border-4 border-border shadow-2xl transition-transform duration-1000 ${
                    isPlaying ? "animate-[spin_8s_linear_infinite]" : ""
                  }`}
                />
              ) : (
                <div className={`w-64 h-64 rounded-full bg-secondary/80 flex items-center justify-center border-4 border-border shadow-2xl ${
                  isPlaying ? "animate-[spin_8s_linear_infinite]" : ""
                }`}>
                  <Music className="h-24 w-24 text-muted-foreground" />
                </div>
              )}
              {/* Spindle hole in center */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-background border-4 border-border" />
            </div>

            {/* Song Metadata */}
            <div className="w-full">
              <h2 className="text-xl font-bold text-foreground truncate px-2">{title}</h2>
              <p className="text-muted-foreground text-sm font-medium truncate mt-1">{artist}</p>
              {spotifyTrack?.album && (
                <p className="text-muted-foreground/60 text-xs truncate mt-1">
                  Album: {spotifyTrack.album}
                </p>
              )}
            </div>

            {/* Playback Progress Slider */}
            <div className="w-full mt-6 space-y-2">
              <Slider
                value={[currentTime]}
                max={durationMs}
                step={50}
                onValueChange={handleProgressChange}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(durationMs)}</span>
              </div>
            </div>

            {/* Audio Controls */}
            <div className="flex items-center gap-4 mt-4">
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={handleRestart}
                className="h-10 w-10 text-muted-foreground hover:text-foreground"
                title="Restart"
              >
                <RotateCcw className="h-5 w-5" />
              </Button>

              <Button 
                variant="ghost" 
                size="icon" 
                onClick={() => skipTime(-5000)}
                className="h-10 w-10 text-muted-foreground hover:text-foreground"
                title="Back 5s"
              >
                <SkipBack className="h-5 w-5" />
              </Button>

              <Button
                onClick={handleTogglePlay}
                size="icon"
                className="h-14 w-14 rounded-full bg-gradient-to-r from-primary to-accent hover:opacity-90 text-primary-foreground shadow-lg hover:shadow-primary/25 transition-all"
              >
                {isPlaying ? (
                  <Pause className="h-6 w-6 fill-current" />
                ) : (
                  <Play className="h-6 w-6 fill-current translate-x-0.5" />
                )}
              </Button>

              <Button 
                variant="ghost" 
                size="icon" 
                onClick={() => skipTime(5000)}
                className="h-10 w-10 text-muted-foreground hover:text-foreground"
                title="Forward 5s"
              >
                <SkipForward className="h-5 w-5" />
              </Button>

              {/* Mute toggle button */}
              {spotifyTrack?.preview_url ? (
                <Button 
                  variant="ghost" 
                  size="icon" 
                  onClick={() => setAudioMuted(!audioMuted)}
                  className={`h-10 w-10 ${audioMuted ? "text-destructive" : "text-muted-foreground hover:text-foreground"}`}
                  title={audioMuted ? "Unmute" : "Mute"}
                >
                  {audioMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
                </Button>
              ) : (
                <div className="w-10 h-10" />
              )}
            </div>

            {/* Volume Slider (only when audio preview is available) */}
            {spotifyTrack?.preview_url && !audioMuted && (
              <div className="w-full mt-4 flex items-center gap-3 px-2">
                <VolumeX className="h-3.5 w-3.5 text-muted-foreground/60 shrink-0" />
                <Slider
                  value={[volume]}
                  min={0}
                  max={1}
                  step={0.02}
                  onValueChange={(vals) => setVolume(vals[0])}
                  className="w-full"
                />
                <Volume2 className="h-3.5 w-3.5 text-muted-foreground/60 shrink-0" />
              </div>
            )}
          </div>

          {/* Quick Customization Options */}
          <div className="glass-card rounded-2xl p-5 space-y-4 shadow-xl">
            {/* Target Language Dropdown */}
            <div className="flex items-center justify-between gap-4">
              <span className="text-sm font-semibold flex items-center gap-2 text-muted-foreground">
                <Globe className="h-4 w-4 text-primary" /> Translation:
              </span>
              <div className="flex items-center gap-2">
                {translating && (
                  <span className="text-[10px] text-primary animate-pulse font-semibold">Translating...</span>
                )}
                <select
                  value={targetLang}
                  onChange={(e) => setTargetLang(e.target.value)}
                  disabled={translating}
                  className="bg-secondary/60 text-sm border border-border/60 rounded-md px-2 py-1 text-foreground focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
                >
                  {SUPPORTED_LANGUAGES.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Show/Hide Translation */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-muted-foreground">Show translation overlay:</span>
              <Button
                variant={showTranslation ? "default" : "outline"}
                size="sm"
                onClick={() => setShowTranslation(!showTranslation)}
                className={showTranslation ? "bg-primary/20 text-primary hover:bg-primary/30 border border-primary/40" : ""}
              >
                {showTranslation ? "Enabled" : "Disabled"}
              </Button>
            </div>

            {/* Font Size Selector */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-muted-foreground">Font Size:</span>
              <div className="flex gap-1 bg-secondary/50 rounded-lg p-0.5 border border-border/40">
                {(["sm", "base", "lg", "xl"] as const).map((sz) => (
                  <Button
                    key={sz}
                    variant={fontSize === sz ? "default" : "ghost"}
                    size="xs"
                    onClick={() => setFontSize(sz)}
                    className={`h-7 px-2.5 text-xs font-bold uppercase rounded-md ${
                      fontSize === sz 
                        ? "bg-gradient-to-r from-primary to-accent text-primary-foreground shadow" 
                        : "text-muted-foreground"
                    }`}
                  >
                    {sz}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Scrolling Synced Lyrics */}
        <div className="lg:col-span-7 flex flex-col h-[520px] lg:h-[620px] glass-card rounded-2xl overflow-hidden shadow-2xl relative">
          
          {/* Header */}
          <div className="bg-secondary/40 border-b border-border/50 px-6 py-3 flex items-center justify-between z-10">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Music className="h-3.5 w-3.5" /> Lyrics Sync
            </span>
            <Badge variant="outline" className="text-xs bg-secondary/60">
              Detected language: {getLanguageName(lyricsData?.language)}
            </Badge>
          </div>

          {/* Fade overlays for smooth visuals */}
          <div className="absolute top-12 left-0 right-0 h-8 bg-gradient-to-b from-card to-transparent pointer-events-none z-10" />
          <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-card to-transparent pointer-events-none z-10" />

          {/* Translating overlay shown during re-translation */}
          {translating && lyricsData && lyricsData.lines.length > 0 && (
            <div className="absolute inset-0 z-20 flex items-center justify-center bg-background/50 backdrop-blur-sm pointer-events-none">
              <div className="flex flex-col items-center gap-2 text-muted-foreground">
                <Sparkles className="h-6 w-6 text-primary animate-pulse" />
                <p className="text-xs font-semibold">Updating translation...</p>
              </div>
            </div>
          )}

          {/* Lyrics list */}
          <div 
            ref={scrollContainerRef}
            className="flex-1 overflow-y-auto px-6 py-12 space-y-6 scrollbar-thin select-none"
            style={{
              scrollPaddingTop: "40%",
              scrollPaddingBottom: "40%"
            }}
          >
            {translating && (!lyricsData || lyricsData.lines.length === 0) ? (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground space-y-3">
                <Sparkles className="h-8 w-8 text-primary animate-pulse" />
                <p className="text-sm">Translating synced lines...</p>
              </div>
            ) : lyricsData?.lines.map((line, idx) => {
              const isActive = idx === activeLineIndex;
              const isPast = idx < activeLineIndex;
              
              return (
                <div
                  key={idx}
                  ref={(el) => (lineRefs.current[idx] = el)}
                  onClick={() => {
                    const scale = isSpotifyPreview && lyricsData?.duration_ms 
                      ? (30000 / lyricsData.duration_ms) 
                      : 1;
                    handleProgressChange([line.start_time * scale]);
                  }}
                  className={`group rounded-xl p-3 transition-all duration-300 cursor-pointer ${
                    isActive 
                      ? "bg-primary/10 border-l-4 border-primary shadow-[0_0_15px_rgba(0,255,220,0.15)] scale-102" 
                      : "hover:bg-secondary/30 border-l-4 border-transparent"
                  }`}
                >
                  {/* Original line */}
                  <p 
                    className={`font-semibold transition-all duration-300 leading-relaxed ${
                      fontSizes[fontSize]
                    } ${
                      isActive 
                        ? "text-transparent bg-gradient-to-r from-primary via-accent to-blue-400 bg-clip-text font-bold" 
                        : isPast 
                          ? "text-foreground/50 font-normal" 
                          : "text-foreground/80 font-normal"
                    }`}
                  >
                    {lyricsData?.language === "ko" ? romanizeText(line.text) : line.text}
                  </p>
                  
                  {/* Translation overlay */}
                  {showTranslation && line.translated_text && (
                    <p 
                      className={`mt-1 font-medium transition-all duration-300 leading-relaxed ${
                        transFontSizes[fontSize]
                      } ${
                        isActive 
                          ? "text-foreground/90 font-bold" 
                          : "text-muted-foreground/45"
                      }`}
                    >
                      {line.translated_text}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}
