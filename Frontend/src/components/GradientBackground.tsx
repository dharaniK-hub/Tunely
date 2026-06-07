const GradientBackground = () => (
  <div className="fixed inset-0 -z-10 overflow-hidden">
    {/* Base dark blue background */}
    <div className="absolute inset-0 bg-[#020d1e]" />
    
    {/* Vibrant Cyan Blob (blob-1) */}
    <div
      className="blob-1 absolute -top-40 -left-40 h-[650px] w-[650px] rounded-full opacity-55 blur-[120px]"
      style={{ background: "radial-gradient(circle, hsl(185, 90%, 45%) 0%, hsl(190, 85%, 35%) 100%)" }}
    />
    
    {/* Royal Blue Blob (blob-2) */}
    <div
      className="blob-2 absolute top-1/4 -right-20 h-[550px] w-[550px] rounded-full opacity-50 blur-[110px]"
      style={{ background: "radial-gradient(circle, hsl(215, 90%, 50%) 0%, hsl(220, 85%, 40%) 100%)" }}
    />
    
    {/* Emerald Green Blob (blob-3) */}
    <div
      className="blob-3 absolute -bottom-30 left-1/4 h-[700px] w-[700px] rounded-full opacity-45 blur-[130px]"
      style={{ background: "radial-gradient(circle, hsl(150, 80%, 42%) 0%, hsl(165, 85%, 33%) 100%)" }}
    />
    
    {/* Ambient light overlay */}
    <div className="absolute inset-0 bg-black/10 backdrop-blur-[2px]" />
  </div>
);

export default GradientBackground;
