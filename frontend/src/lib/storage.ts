/**
 * Access token is held in memory only. It is not persisted to
 * localStorage or sessionStorage, so a page reload discards it.
 * On reload, the AuthContext calls /auth/token/refresh/ and, if the
 * HttpOnly refresh cookie is still valid, obtains a new one.
 */
let accessToken: string | null = null;

export const tokenStore = {
  getAccess: (): string | null => accessToken,
  setAccess: (token: string | null): void => {
    accessToken = token;
  },
  clear: (): void => {
    accessToken = null;
  },
};