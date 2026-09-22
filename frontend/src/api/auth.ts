import { api, refreshAccessToken } from "./client";
import { tokenStore } from "@/lib/storage";

export interface Profile {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: "MAKER" | "CHECKER" | "CERTIFIER" | "SUPERADMIN" | "MEMBER" | "BOARD" | "AUDITOR";
  must_change_password: boolean;
  created_at: string;
}

// Login returns only the access token; refresh is in an HttpOnly cookie.
export async function login(username: string, password: string): Promise<void> {
  const { data } = await api.post<{ access: string }>("/auth/token/", {
    username,
    password,
  });
  tokenStore.setAccess(data.access);
}

export async function getProfile(): Promise<Profile> {
  const { data } = await api.get<Profile>("/users/me/");
  return data;
}

export async function changePassword(
  oldPassword: string,
  newPassword: string
): Promise<void> {
  await api.post("/users/me/change-password/", {
    old_password: oldPassword,
    new_password: newPassword,
  });
}

export async function logout(): Promise<void> {
  try {
    await api.post("/auth/logout/");
  } catch {
    // Ignore network errors; local state is cleared regardless.
  }
  tokenStore.clear();
}

export { refreshAccessToken };