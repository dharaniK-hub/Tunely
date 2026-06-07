import { useLocation, Link } from "react-router-dom";
import { useEffect } from "react";
import { AlertCircle, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import GradientBackground from "@/components/GradientBackground";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center py-12 px-4 select-none">
      <GradientBackground />

      <div className="w-full max-w-md mx-auto text-center animate-fade-in">
        <div className="glass-card rounded-2xl p-8 border border-border/30 shadow-2xl flex flex-col items-center">
          
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-destructive/10 border border-destructive/20 mb-6 shadow-inner">
            <AlertCircle className="h-8 w-8 text-destructive" />
          </div>

          <h1 className="text-6xl font-black bg-gradient-to-r from-red-400 via-primary to-accent bg-clip-text text-transparent tracking-tight mb-2">
            404
          </h1>
          
          <h2 className="text-xl font-bold text-foreground">Oops! Page not found</h2>
          
          <p className="mt-3 text-muted-foreground text-sm leading-relaxed max-w-xs">
            We couldn't find the page you were looking for at <code className="bg-secondary/60 px-1.5 py-0.5 rounded text-xs text-foreground font-mono">{location.pathname}</code>.
          </p>

          <Button 
            asChild
            className="mt-8 gap-2 bg-gradient-to-r from-primary to-accent hover:opacity-90 text-primary-foreground font-semibold shadow-lg hover:shadow-primary/10 transition-all w-full h-11"
          >
            <Link to="/">
              <Home className="h-4 w-4" />
              Return to Tunely
            </Link>
          </Button>

        </div>
      </div>
    </div>
  );
};

export default NotFound;
