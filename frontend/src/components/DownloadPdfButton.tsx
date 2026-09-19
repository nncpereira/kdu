import { useState } from "react";
import { Button } from "@/components/Button";
import { downloadPdf } from "@/lib/download";

interface Props {
  url: string;
  filename: string;
  disabled?: boolean;
}

export function DownloadPdfButton({ url, filename, disabled }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setLoading(true);
    setError(null);
    try {
      await downloadPdf(url, filename);
    } catch (e: any) {
      setError("Failed to download PDF.");
      // Auto-clear after a few seconds.
      setTimeout(() => setError(null), 4000);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="inline-flex flex-col items-end">
      <Button
        variant="secondary"
        onClick={handleClick}
        loading={loading}
        disabled={disabled}
      >
        Download PDF
      </Button>
      {error && (
        <p className="text-xs text-red-600 mt-1">{error}</p>
      )}
    </div>
  );
}