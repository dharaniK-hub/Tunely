import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const MockFacebookLogin = () => {
  const [showCustomForm, setShowCustomForm] = useState(false);
  const [customName, setCustomName] = useState("");
  const [customEmail, setCustomEmail] = useState("");

  const handleSelectAccount = (email: string, oauthId: string, name: string) => {
    if (window.opener) {
      window.opener.postMessage(
        {
          type: "MOCK_OAUTH_SUCCESS",
          provider: "Facebook",
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

    const randomId = "fb" + Math.floor(Math.random() * 100000000);
    handleSelectAccount(customEmail, randomId, customName);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f0f2f5] text-[#1c1e21] font-sans p-4">
      <div className="w-full max-w-[400px] bg-white rounded-lg border border-[#dddfe2] shadow-md overflow-hidden flex flex-col">
        
        {/* Facebook Blue Header Bar */}
        <div className="bg-[#1877f2] py-4 px-6 flex items-center justify-between text-white">
          <span className="font-bold text-lg tracking-tight">facebook</span>
          <span className="text-xs opacity-80">Mock Auth</span>
        </div>

        <div className="p-6 flex flex-col items-center">
          {/* FB Icon */}
          <svg className="w-10 h-10 text-[#1877f2] fill-current mb-4" viewBox="0 0 24 24">
            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
          </svg>

          {!showCustomForm ? (
            <>
              <h2 className="text-lg font-bold text-center mb-1 text-[#1c1e21]">
                Log in to Tunely
              </h2>
              <p className="text-xs text-[#606770] text-center mb-6">
                To continue, select your Facebook profile below
              </p>

              {/* Profiles List */}
              <div className="w-full space-y-2 mb-6">
                
                {/* Profile 1 */}
                <button
                  onClick={() => handleSelectAccount("jane.smith@facebook.com", "fb88372648", "Jane Smith")}
                  className="w-full flex items-center gap-3.5 p-3 rounded-lg border border-[#dadde1] hover:bg-[#f5f6f7] transition-colors text-left group"
                >
                  <div className="w-10 h-10 rounded-full bg-[#e7f3ff] text-[#1877f2] flex items-center justify-center text-sm font-bold">
                    JS
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-[#1c1e21] group-hover:underline">
                      Jane Smith
                    </p>
                    <p className="text-xs text-[#606770]">jane.smith@facebook.com</p>
                  </div>
                  <span className="text-xs font-semibold text-[#1877f2]">Select</span>
                </button>

                {/* Profile 2 */}
                <button
                  onClick={() => handleSelectAccount("robert.jones@facebook.com", "fb99023847", "Bob Jones")}
                  className="w-full flex items-center gap-3.5 p-3 rounded-lg border border-[#dadde1] hover:bg-[#f5f6f7] transition-colors text-left group"
                >
                  <div className="w-10 h-10 rounded-full bg-[#e7f3ff] text-[#1877f2] flex items-center justify-center text-sm font-bold">
                    BJ
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-[#1c1e21] group-hover:underline">
                      Bob Jones
                    </p>
                    <p className="text-xs text-[#606770]">robert.jones@facebook.com</p>
                  </div>
                  <span className="text-xs font-semibold text-[#1877f2]">Select</span>
                </button>

                {/* Login as Another Profile */}
                <button
                  onClick={() => setShowCustomForm(true)}
                  className="w-full text-center py-2.5 rounded-lg border border-dashed border-[#dadde1] hover:bg-[#f5f6f7] transition-colors text-xs font-bold text-[#1877f2] mt-2"
                >
                  Log in as another user
                </button>
              </div>
            </>
          ) : (
            <form onSubmit={handleCustomSubmit} className="w-full flex flex-col">
              <h2 className="text-lg font-bold text-center mb-1 text-[#1c1e21]">
                Facebook Login
              </h2>
              <p className="text-xs text-[#606770] text-center mb-6">
                Enter your Facebook account details
              </p>

              <div className="space-y-3 mb-6">
                <Input
                  type="text"
                  placeholder="Profile Name"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  className="h-10 border-[#dddfe2] focus-visible:ring-[#1877f2] text-xs text-[#1c1e21]"
                  required
                />
                <Input
                  type="email"
                  placeholder="Email or Mobile"
                  value={customEmail}
                  onChange={(e) => setCustomEmail(e.target.value)}
                  className="h-10 border-[#dddfe2] focus-visible:ring-[#1877f2] text-xs text-[#1c1e21]"
                  required
                />
              </div>

              <div className="flex justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setShowCustomForm(false)}
                  className="text-xs font-bold text-[#606770] hover:bg-[#e4e6eb] py-2 px-4 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <Button
                  type="submit"
                  className="bg-[#1877f2] hover:bg-[#166fe5] text-white px-5 h-9 rounded-lg font-bold text-xs"
                >
                  Log In
                </Button>
              </div>
            </form>
          )}

          <div className="w-full border-t border-[#e5e5e5] pt-4 mt-2 text-[10px] text-[#606770] text-center leading-normal">
            By logging in, Tunely will receive access to your public profile and email address.
          </div>
        </div>
      </div>
    </div>
  );
};

export default MockFacebookLogin;
