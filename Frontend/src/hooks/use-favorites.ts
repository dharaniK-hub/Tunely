import { useState, useEffect, useCallback } from "react";
import { fetchUserFavorites, addUserFavorite, removeUserFavorite } from "@/lib/api";

export interface Favorite {
  id: string;
  artist: string;
  title: string;
  language: string;
  addedAt: number;
}

export function useFavorites() {
  const [favorites, setFavorites] = useState<Favorite[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [isFetching, setIsFetching] = useState(false);

  // Load favorites from the backend on mount
  const loadFavorites = useCallback(async () => {
    const token = localStorage.getItem("tunely_token");
    if (!token) {
      setLoaded(true);
      return;
    }
    setIsFetching(true);
    try {
      const backendFavs = await fetchUserFavorites();
      const mapped: Favorite[] = backendFavs.map((f) => ({
        id: f.id,
        artist: f.artist,
        title: f.title,
        language: f.language,
        addedAt: typeof f.addedAt === "number" ? f.addedAt : Date.now(),
      }));
      setFavorites(mapped);
    } catch (err) {
      console.error("Failed to load favorites from backend:", err);
    } finally {
      setIsFetching(false);
      setLoaded(true);
    }
  }, []);

  useEffect(() => {
    loadFavorites();
  }, [loadFavorites]);

  const getFavId = (artist: string, title: string) => `${artist}|${title}`.toLowerCase();

  const addFavorite = async (artist: string, title: string, language: string): Promise<boolean> => {
    const id = getFavId(artist, title);
    const exists = favorites.some((fav) => fav.id === id);
    if (exists) return false;

    // Optimistic update
    const newFav: Favorite = { id, artist, title, language, addedAt: Date.now() };
    setFavorites((prev) => [...prev, newFav]);

    try {
      await addUserFavorite(artist, title, language);
      return true;
    } catch (err) {
      // Rollback on failure
      console.error("Failed to save favorite to backend:", err);
      setFavorites((prev) => prev.filter((f) => f.id !== id));
      return false;
    }
  };

  const removeFavorite = async (artist: string, title: string) => {
    const id = getFavId(artist, title);
    // Optimistic update
    setFavorites((prev) => prev.filter((fav) => fav.id !== id));

    try {
      await removeUserFavorite(artist, title);
    } catch (err) {
      console.error("Failed to remove favorite from backend:", err);
      // Reload to get accurate state from server
      loadFavorites();
    }
  };

  const isFavorite = (artist: string, title: string): boolean => {
    const id = getFavId(artist, title);
    return favorites.some((fav) => fav.id === id);
  };

  const clearAll = async () => {
    const previous = [...favorites];
    setFavorites([]);
    try {
      // Remove each from backend
      await Promise.all(previous.map((f) => removeUserFavorite(f.artist, f.title)));
    } catch (err) {
      console.error("Failed to clear all favorites:", err);
      loadFavorites();
    }
  };

  return {
    favorites,
    addFavorite,
    removeFavorite,
    isFavorite,
    clearAll,
    loaded,
    isFetching,
    refresh: loadFavorites,
  };
}
