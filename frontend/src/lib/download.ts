import { api } from "@/api/client";

/**
 * Fetch a binary resource with the JWT auth header and trigger a browser download.
 * Because the SPA uses Bearer tokens (not cookies), we can't just
 * window.open() the URL — the request would be unauthenticated.
 */

export async function downloadBlob(
  url: string,
  filename: string,
  mimeType: string = "application/octet-stream"
): Promise<void> {
  const path = url.replace(/^\/api\/v1/, "");
  const response = await api.get(path, { responseType: "blob" });
  const blob = new Blob([response.data], { type: mimeType });
  const objectUrl = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
}

export async function downloadPdf(url: string, filename: string) {
  return downloadBlob(url, filename, "application/pdf");
}
