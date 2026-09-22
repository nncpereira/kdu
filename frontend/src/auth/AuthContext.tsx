import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  ReactNode,
} from "react";
import {
  login as apiLogin,
  logout as apiLogout,
  getProfile,
  refreshAccessToken,
  Profile,
} from "@/api/auth";
import { tokenStore } from "@/lib/storage";

interface AuthContextValue {
  profile: Profile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<Profile>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount: try to refresh using the HttpOnly cookie.
  // If the cookie is valid → new access token → fetch profile.
  // If not → user is unauthenticated.
  useEffect(() => {
    (async () => {
      try {
        await refreshAccessToken();
        const p = await getProfile();
        setProfile(p);
      } catch {
        tokenStore.clear();
        setProfile(null);
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  const refreshProfile = useCallback(async () => {
    const p = await getProfile();
    setProfile(p);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    await apiLogin(username, password);
    const p = await getProfile();
    setProfile(p);
    return p;
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    setProfile(null);
  }, []);

  const value = useMemo(
    () => ({
      profile,
      isLoading,
      isAuthenticated: !!profile,
      login,
      logout,
      refreshProfile,
    }),
    [profile, isLoading, login, logout, refreshProfile]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}