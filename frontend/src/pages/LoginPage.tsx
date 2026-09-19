import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/auth/useAuth";
import { Button } from "@/components/Button";
import { Logo } from "@/components/Logo";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Invalid username or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
      <div className="relative w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
          <div className="bg-brand-700 px-8 pt-10 pb-8 text-center">
            <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-white shadow-inner">
              <Logo size={84} />
            </div>
            <h1 className="mt-5 text-xl font-bold text-white tracking-tight">
              Koperativa Dezenvolvimentu Umanu
            </h1>
            <p className="text-brand-100 text-xs mt-1 uppercase tracking-widest">
              KDU · Cooperative Core
            </p>
          </div>

          {/* Form */}
          <form onSubmit={onSubmit} className="px-8 py-8 space-y-5">
            {error && (
              <div className="bg-red-50 border-l-4 border-red-500 text-red-700 px-4 py-3 rounded text-sm">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoFocus
                autoComplete="username"
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition"
              />
            </div>

            <Button
              type="submit"
              loading={loading}
              className="w-full py-2.5 rounded-lg"
            >
              Sign In
            </Button>

            <p className="text-xs text-center text-gray-500 pt-2">
              Access is monitored. Contact a Superadmin if you need an account.
            </p>
          </form>
        </div>

        <p className="text-center text-xs text-white/70 mt-6">
          DL 16/2004 as amended by DL 76/2022
        </p>
      </div>
    </div>
  );
}
