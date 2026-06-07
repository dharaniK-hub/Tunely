import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const MockGoogleLogin = () => {
  const [showCustomForm, setShowCustomForm] = useState(false);
  const [customName, setCustomName] = useState("");
  const [customEmail, setCustomEmail] = useState("");

  const handleSelectAccount = (email: string, oauthId: string, name: string) => {
    if (window.opener) {
      window.opener.postMessage(
        {
          type: "MOCK_OAUTH_SUCCESS",
          provider: "Google",
          user: { email, oauthId, name },
        },
        window.location.origin
      );
      window.close();
    } else {
      alert("Error: Parent window not found.");
    }
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customName.trim() || !customEmail.trim()) return;
    
    // Generate a random oauth ID
    const randomId = "g" + Math.floor(Math.random() * 1000000000);
    handleSelectAccount(customEmail, randomId, customName);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f0f4f9] text-[#1f1f1f] font-sans p-4">
      <div className="w-full max-w-[450px] bg-white rounded-3xl border border-[#dadce0] p-10 shadow-sm flex flex-col items-center">
        
        {/* Google Logo */}
        <svg className="w-12 h-12 mb-4" viewBox="0 0 24 24">
          <path
            fill="#4285F4"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          />
          <path
            fill="#34A853"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          />
          <path
            fill="#FBBC05"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
          />
          <path
            fill="#EA4335"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
          />
        </svg>

        {!showCustomForm ? (
          <>
            <h1 className="text-2xl font-normal text-[#1f1f1f] text-center mb-1">
              Choose an account
            </h1>
            <p className="text-sm text-[#444746] text-center mb-6">
              to continue to <span className="font-semibold text-primary">Tunely</span>
            </p>

            {/* Account List */}
            <div className="w-full border-t border-[#e3e3e3] border-b mb-6">
              
              {/* Account 1 */}
              <button
                onClick={() => handleSelectAccount("john.doe@gmail.com", "g102938475", "John Doe")}
                className="w-full flex items-center gap-4 py-3.5 px-2 hover:bg-[#f7f9fc] transition-colors border-b border-[#e3e3e3] text-left group"
              >
                <div className="w-8 h-8 rounded-full bg-[#e8f0fe] text-[#1a73e8] flex items-center justify-center text-xs font-medium">
                  JD
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#1f1f1f] truncate group-hover:text-[#0b57d0]">
                    John Doe
                  </p>
                  <p className="text-xs text-[#444746] truncate">john.doe@gmail.com</p>
                </div>
              </button>

              {/* Account 2 */}
              <button
                onClick={() => handleSelectAccount("alice.wonder@gmail.com", "g987654321", "Alice Wonder")}
                className="w-full flex items-center gap-4 py-3.5 px-2 hover:bg-[#f7f9fc] transition-colors border-b border-[#e3e3e3] text-left group"
              >
                <div className="w-8 h-8 rounded-full bg-[#fce8e6] text-[#c5221f] flex items-center justify-center text-xs font-medium">
                  AW
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#1f1f1f] truncate group-hover:text-[#0b57d0]">
                    Alice Wonder
                  </p>
                  <p className="text-xs text-[#444746] truncate">alice.wonder@gmail.com</p>
                </div>
              </button>

              {/* Use Another Account */}
              <button
                onClick={() => setShowCustomForm(true)}
                className="w-full flex items-center gap-4 py-3.5 px-2 hover:bg-[#f7f9fc] transition-colors text-left group"
              >
                <div className="w-8 h-8 rounded-full border border-[#dadce0] flex items-center justify-center text-xs font-medium text-[#444746]">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <p className="text-sm font-medium text-[#0b57d0] group-hover:text-[#0842a0]">
                  Use another account
                </p>
              </button>
            </div>
          </>
        ) : (
          <form onSubmit={handleCustomSubmit} className="w-full flex flex-col">
            <h1 className="text-2xl font-normal text-[#1f1f1f] text-center mb-1">
              Sign in
            </h1>
            <p className="text-sm text-[#444746] text-center mb-6">
              Use your Google Account
            </p>

            <div className="space-y-4 mb-8">
              <Input
                type="text"
                placeholder="Full Name"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                className="h-12 border-[#dadce0] focus-visible:ring-[#0b57d0] text-sm text-[#1f1f1f] bg-transparent"
                required
              />
              <Input
                type="email"
                placeholder="Email address"
                value={customEmail}
                onChange={(e) => setCustomEmail(e.target.value)}
                className="h-12 border-[#dadce0] focus-visible:ring-[#0b57d0] text-sm text-[#1f1f1f] bg-transparent"
                required
              />
            </div>

            <div className="flex justify-between items-center">
              <button
                type="button"
                onClick={() => setShowCustomForm(false)}
                className="text-sm font-semibold text-[#0b57d0] hover:text-[#0842a0] py-2 px-3 rounded"
              >
                Back
              </button>
              <Button
                type="submit"
                className="bg-[#0b57d0] hover:bg-[#0842a0] text-white px-6 h-10 rounded-full font-semibold text-sm"
              >
                Next
              </Button>
            </div>
          </form>
        )}

        <div className="mt-8 text-xs text-[#5f6368] text-center max-w-xs leading-normal">
          To continue, Google will share your name, email address, and profile picture with Tunely.
        </div>
      </div>
    </div>
  );
};

export default MockGoogleLogin;
