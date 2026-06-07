import { useState, useEffect } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { loginUser, signupUser, oauthLogin } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import GradientBackground from "@/components/GradientBackground";
import { 
  Music, 
  User, 
  Lock, 
  Mail, 
  Eye, 
  EyeOff, 
  ArrowRight
} from "lucide-react";

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const isLoginMode = location.pathname !== "/create-account";

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  // Clear fields on view toggle/path change
  useEffect(() => {
    setUsername("");
    setPassword("");
    setEmail("");
  }, [location.pathname]);



  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim() || (!isLoginMode && !email.trim())) {
      toast({
        title: "Please fill in all required fields",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      if (isLoginMode) {
        const res = await loginUser(username, password);
        if (res.token) {
          localStorage.setItem("tunely_token", res.token);
          localStorage.setItem("tunely_user", JSON.stringify(res.user));
          window.dispatchEvent(new Event("auth-changed"));
          toast({
            title: "Logged in successfully!",
            description: `Welcome back, ${res.user?.username}!`,
          });
          navigate("/");
        }
      } else {
        await signupUser(username, password, email);
        toast({
          title: "Account created successfully!",
          description: "Please log in using your new credentials.",
        });
        navigate("/login");
      }
    } catch (err: any) {
      toast({
        title: isLoginMode ? "Login Failed" : "Registration Failed",
        description: err.message || "An unexpected error occurred",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };



  return (
    <div className="relative min-h-screen flex items-center justify-center bg-transparent text-foreground select-none px-4 py-12">
      <GradientBackground />

      <div className="w-full max-w-[440px] z-10 space-y-6">
        
        {/* Brand Logo & Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-r from-primary to-accent shadow-lg animate-pulse">
            <Music className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-3xl font-black tracking-tight bg-gradient-to-r from-primary via-accent to-emerald-400 bg-clip-text text-transparent">
            Tunely
          </h1>
          <p className="text-sm text-muted-foreground max-w-xs mx-auto">
            Your premium music lyrics translator and synchronizer
          </p>
        </div>

        {/* Main Authentication Card */}
        <div className="glass-card rounded-2xl border border-white/10 shadow-2xl p-8 bg-background/30 backdrop-blur-2xl transition-all duration-300">
          
          {/* Header Title */}
          <h2 className="text-2xl font-black tracking-tight text-center mb-6 text-foreground">
            {isLoginMode ? "Log In" : "Create an Account"}
          </h2>

          <form onSubmit={handleCredentialsSubmit} className="space-y-4">
            
            {/* Username Field */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-muted-foreground/80 tracking-wide uppercase">
                Username
              </label>
              <div className="relative">
                <User className="absolute left-3.5 top-3.5 h-4 w-4 text-muted-foreground/50" />
                <Input
                  type="text"
                  placeholder="e.g. music_lover"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="pl-10.5 bg-secondary/40 border-border/50 h-11 focus-visible:ring-primary font-medium text-sm"
                  required
                />
              </div>
            </div>

            {/* Email Field (Signup only) */}
            {!isLoginMode && (
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-muted-foreground/80 tracking-wide uppercase">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-3.5 h-4 w-4 text-muted-foreground/50" />
                  <Input
                    type="email"
                    placeholder="e.g. user@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-10.5 bg-secondary/40 border-border/50 h-11 focus-visible:ring-primary font-medium text-sm"
                    required
                  />
                </div>
              </div>
            )}

            {/* Password Field */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-muted-foreground/80 tracking-wide uppercase">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3.5 h-4 w-4 text-muted-foreground/50" />
                <Input
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10.5 pr-10 bg-secondary/40 border-border/50 h-11 focus-visible:ring-primary font-medium text-sm"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3.5 h-4 w-4 text-muted-foreground/50 hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={loading}
              className="w-full gap-2 h-11 mt-2 bg-gradient-to-r from-primary to-accent hover:opacity-90 text-primary-foreground font-semibold shadow-lg hover:shadow-primary/10 transition-all text-sm"
            >
              {isLoginMode ? "Log In" : "Create Account"}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </form>

          {/* Switch page link */}
          <div className="text-center mt-4.5">
            {isLoginMode ? (
              <span className="text-xs text-muted-foreground">
                New to Tunely?{" "}
                <Link to="/create-account" className="text-primary hover:underline font-bold">
                  Create an Account
                </Link>
              </span>
            ) : (
              <span className="text-xs text-muted-foreground">
                Already have an account?{" "}
                <Link to="/login" className="text-primary hover:underline font-bold">
                  Log In
                </Link>
              </span>
            )}
          </div>



        </div>
      </div>
    </div>
  );
};

export default Login;
