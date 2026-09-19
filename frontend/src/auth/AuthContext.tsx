import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  ReactNode,
} from "react";
import { login as apiLogin, getProfile, Profile } from "@/api/auth";
import { tokenStore } from "@/lib/storage";

interface AuthContextValue {
  profile: Profile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshProfile = useCallback(async () => {
    if (!tokenStore.getAccess()) {
      setProfile(null);
      return;
    }
    const p = await getProfile();
    setProfile(p);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        await refreshProfile();
      } catch {
        tokenStore.clear();
        setProfile(null);
      } finally {
        setIsLoading(false);
      }
    })();
  }, [refreshProfile]);

  const login = useCallback(
    async (username: string, password: string) => {
      const tokens = await apiLogin(username, password);
      tokenStore.set(tokens.access, tokens.refresh);
      await refreshProfile();
    },
    [refreshProfile]
  );

  const logout = useCallback(() => {
    tokenStore.clear();
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