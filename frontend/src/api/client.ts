import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { tokenStore } from "@/lib/storage";

const baseURL = import.meta.env.VITE_API_BASE || "/api/v1";

export const api = axios.create({
  baseURL,
  withCredentials: true,                // send cookies with every request
  headers: { "Content-Type": "application/json" },
});

// Attach access token (from memory) to every request.
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStore.getAccess();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Single in-flight refresh promise — dedupes concurrent 401s.
let refreshPromise: Promise<string> | null = null;

export async function refreshAccessToken(): Promise<string> {
  const resp = await axios.post(
    `${baseURL}/auth/token/refresh/`,
    {},
    { withCredentials: true }
  );
  const newAccess: string = resp.data.access;
  tokenStore.setAccess(newAccess);
  return newAccess;
}

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original: any = error.config;

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;

      // If a refresh is already in flight, wait for it.
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
      }

      try {
        const newAccess = await refreshPromise;
        original.headers.Authorization = `Bearer ${newAccess}`;
        return api(original);
      } catch (refreshErr) {
        tokenStore.clear();
        if (!window.location.pathname.startsWith("/login")) {
          window.location.href = "/login";
        }
        return Promise.reject(refreshErr);
      }
    }

    return Promise.reject(error);
  }
);