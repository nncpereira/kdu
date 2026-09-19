import { api } from "./client";

export type Role =
  | "MAKER"
  | "CHECKER"
  | "CERTIFIER"
  | "SUPERADMIN"
  | "MEMBER"
  | "BOARD"
  | "AUDITOR";

export interface Profile {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  must_change_password: boolean;
  created_at: string;
}

export interface StaffUser {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  must_change_password: boolean;
  is_active: boolean;
  last_login: string | null;
  created_at: string;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface CreateStaffPayload {
  username: string;
  password: string;
  role: Role;
  email?: string;
  first_name?: string;
  last_name?: string;
}

// ====================================================================
// Auth
// ====================================================================
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

// ====================================================================
// Superadmin staff management
// ====================================================================
export async function listStaff(): Promise<StaffUser[]> {
  const { data } = await api.get<StaffUser[]>("/users/");
  return data;
}

export async function createStaff(
  payload: CreateStaffPayload
): Promise<StaffUser> {
  const { data } = await api.post<StaffUser>("/users/", payload);
  return data;
}

export async function disableStaff(id: string): Promise<StaffUser> {
  const { data } = await api.post<StaffUser>(`/users/${id}/disable/`);
  return data;
}

export async function enableStaff(id: string): Promise<StaffUser> {
  const { data } = await api.post<StaffUser>(`/users/${id}/enable/`);
  return data;
}

export async function resetStaffPassword(
  id: string
): Promise<{ detail: string; temporary_password: string }> {
  const { data } = await api.post<{ detail: string; temporary_password: string }>(
    `/users/${id}/reset-password/`
  );
  return data;
}

export async function updateStaff(
  id: string,
  payload: { first_name?: string; last_name?: string; email?: string }
): Promise<StaffUser> {
  const { data } = await api.patch<StaffUser>(`/users/${id}/`, payload);
  return data;
}

export async function updateMyProfile(payload: {
  first_name?: string;
  last_name?: string;
  email?: string;
}): Promise<Profile> {
  const { data } = await api.patch<Profile>("/users/me/", payload);
  return data;
}