import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Copy, Check, Sparkles } from "lucide-react";
import { useState } from "react";
import { getLanguageName } from "@/lib/api";

interface LyricsDisplayProps {
  artist: string;
  title: string;
  original: string;
  translated: string;
  languages: string[];
  targetLang?: string;
  onBack: () => void;
  onSyncPlay?: () => void;
}

const LyricsDisplay = ({
  artist,
  title,
  original,
  translated,
  languages,
  targetLang = "en",
  onBack,
  onSyncPlay
}: LyricsDisplayProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(translated);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-full animate-fade-in space-y-6">
      {/* Header and Control Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4 bg-secondary/35 border border-border/40 rounded-xl p-4">
        <div className="flex items-center gap-3 w-full md:w-auto">
          <Button
            variant="ghost"
            onClick={onBack}
            className="gap-2 text-sm font-semibold text-muted-foreground hover:text-foreground h-10 px-3"
          >
            <ArrowLeft className="h-4.5 w-4.5" />
            Back
          </Button>
          <div className="h-6 w-[1px] bg-border/60 mx-1 hidden md:block" />
          <div className="text-left">
            <h2 className="text-lg font-black text-foreground truncate max-w-[200px] md:max-w-[300px]">
              {title}
            </h2>
            <p className="text-sm text-muted-foreground/80 truncate max-w-[150px] md:max-w-[200px] mt-0.5">
              {artist}
            </p>
          </div>
        </div>

        {/* Badges and Mode Actions */}
        <div className="flex flex-wrap items-center gap-4 w-full md:w-auto justify-end">
          <div className="flex items-center gap-1.5 bg-secondary/50 rounded-xl p-1.5 border border-border/40 text-sm">
            <span className="text-muted-foreground px-1.5 font-semibold">Source:</span>
            {languages && languages.length > 0 ? (
              languages.map((lang) => (
                <Badge
                  key={lang}
                  className="bg-primary/20 hover:bg-primary/30 text-primary border-primary/30 select-none text-xs font-bold py-0.5 px-2.5 rounded-lg"
                >
                  {getLanguageName(lang)}
                </Badge>
              ))
            ) : (
              <Badge variant="outline" className="text-xs rounded-lg">
                Unknown
              </Badge>
            )}
          </div>

          {onSyncPlay && (
            <Button
              onClick={onSyncPlay}
              className="gap-2 bg-gradient-to-r from-primary to-accent hover:opacity-90 text-primary-foreground font-bold shadow-lg hover:shadow-primary/20 text-sm py-2 px-4 h-10 rounded-lg"
            >
              <Sparkles className="h-4 w-4 fill-current animate-pulse" />
              Sync Karaoke Player
            </Button>
          )}
        </div>
      </div>

      {/* Lyrics Panels Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Left: Original Lyrics */}
        <div className="glass-card rounded-xl overflow-hidden shadow-xl">
          <div className="bg-secondary/40 border-b border-border/40 px-5 py-3 flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Original Lyrics
            </h3>
            <span className="text-[10px] text-muted-foreground/60">
              {original.split("\n").filter(Boolean).length} lines
            </span>
          </div>
          <div className="p-6 select-text">
            <pre className="whitespace-pre-wrap font-sans text-sm md:text-[15px] leading-8 text-foreground/95 font-medium tracking-normal antialiased">
              {original}
            </pre>
          </div>
        </div>

        {/* Right: Translated Lyrics */}
        <div className="glass-card rounded-xl overflow-hidden shadow-xl">
          <div className="bg-secondary/40 border-b border-border/40 px-5 py-3 flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              {getLanguageName(targetLang)} Translation
            </h3>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleCopy}
              className="h-7 w-7 text-muted-foreground hover:text-foreground"
              title="Copy translation"
            >
              {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
          <div className="p-6 select-text">
            <pre className="whitespace-pre-wrap font-sans text-sm md:text-[15px] leading-8 text-foreground/95 font-medium tracking-normal antialiased">
              {translated}
            </pre>
          </div>
        </div>

      </div>
    </div>
  );
};

export default LyricsDisplay;
