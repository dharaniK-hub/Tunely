import { Heart, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Favorite } from "@/hooks/use-favorites";
import { getLanguageName } from "@/lib/api";

interface FavoritesListProps {
  favorites: Favorite[];
  onSelectFavorite: (artist: string, title: string) => void;
  onRemoveFavorite: (artist: string, title: string) => void;
}

const FavoritesList = ({
  favorites,
  onSelectFavorite,
  onRemoveFavorite,
}: FavoritesListProps) => {
  if (favorites.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Heart className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>No favorites yet. Add your first favorite song!</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {favorites.map((fav) => (
        <div
          key={fav.id}
          className="glass-card rounded-lg p-4 flex flex-col justify-between hover:bg-secondary/40 transition-colors cursor-pointer"
          onClick={() => onSelectFavorite(fav.artist, fav.title)}
        >
          <div>
            <h3 className="font-semibold text-foreground truncate">
              {fav.title}
            </h3>
            <p className="text-sm text-muted-foreground truncate">
              {fav.artist}
            </p>
          </div>
          <div className="flex items-center justify-between mt-4">
            <Badge variant="outline" className="text-xs">
              {getLanguageName(fav.language)}
            </Badge>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-destructive hover:text-destructive/80"
              onClick={(e) => {
                e.stopPropagation();
                onRemoveFavorite(fav.artist, fav.title);
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default FavoritesList;
