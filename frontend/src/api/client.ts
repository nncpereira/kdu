import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { tokenStore } from "@/lib/storage";

const baseURL = import.meta.env.VITE_API_BASE || "/api/v1";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStore.getAccess();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let queue: ((token: string) => void)[] = [];

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original: any = error.config;
    if (
      error.response?.status === 401 &&
      !original._retry &&
      tokenStore.getRefresh()
    ) {
      original._retry = true;

      if (isRefreshing) {
        return new Promise((resolve) => {
          queue.push((token: string) => {
            original.headers.Authorization = `Bearer ${token}`;
            resolve(api(original));
          });
        });
      }

      isRefreshing = true;
      try {
        const refresh = tokenStore.getRefresh()!;
        const resp = await axios.post(`${baseURL}/auth/token/refresh/`, {
          refresh,
        });
        const newAccess: string = resp.data.access;
        tokenStore.set(newAccess, refresh);

        queue.forEach((cb) => cb(newAccess));
        queue = [];

        original.headers.Authorization = `Bearer ${newAccess}`;
        return api(original);
      } catch (e) {
        tokenStore.clear();
        window.location.href = "/login";
        return Promise.reject(e);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);