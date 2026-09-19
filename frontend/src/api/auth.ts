import { api } from "./client";

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface Profile {
  id: string;
  username: string;
  email: string;
  role:
    | "MAKER"
    | "CHECKER"
    | "CERTIFIER"
    | "SUPERADMIN"
    | "MEMBER"
    | "BOARD"
    | "AUDITOR";
  must_change_password: boolean;
  created_at: string;
}

export async function login(
  username: string,
  password: string
): Promise<TokenPair> {
  const { data } = await api.post<TokenPair>("/auth/token/", {
    username,
    password,
  });
  return data;
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