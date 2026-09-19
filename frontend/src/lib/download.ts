import { api } from "@/api/client";

/**
 * Fetch a binary resource with the JWT auth header and trigger a browser download.
 * Because the SPA uses Bearer tokens (not cookies), we can't just
 * window.open() the URL — the request would be unauthenticated.
 */
export async function downloadPdf(url: string, filename: string): Promise<void> {
  const response = await api.get(url, { responseType: "blob" });

  const blob = new Blob([response.data], { type: "application/pdf" });
  const objectUrl = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  // Give the browser a tick to start the download before revoking.
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
}