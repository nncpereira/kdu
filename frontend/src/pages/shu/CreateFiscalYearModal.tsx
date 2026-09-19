import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { createFiscalYear } from "@/api/shu";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function CreateFiscalYearModal({ open, onClose }: Props) {
  const qc = useQueryClient();
  const currentYear = new Date().getFullYear();
  const [startYear, setStartYear] = useState(String(currentYear));
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => {
      const y = parseInt(startYear, 10);
      return createFiscalYear({
        year_start: `${y}-07-01`,
        year_end: `${y + 1}-06-30`,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["shu", "fiscal-years"] });
      onClose();
    },
    onError: (err: any) => {
      setError(err?.response?.data?.detail ?? "Failed to create fiscal year.");
    },
  });

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    await mutation.mutateAsync();
  }

  const y = parseInt(startYear, 10) || 0;

  return (
    <Modal open={open} onClose={onClose} title="Create Fiscal Year" size="sm">
      <form onSubmit={onSubmit} className="space-y-4">
        <Input
          label="Starting Year"
          type="number"
          min="2000"
          max="2100"
          value={startYear}
          onChange={(e) => setStartYear(e.target.value)}
          required
        />
        <div className="bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded p-3">
          This creates a fiscal year running from{" "}
          <strong>{y}-07-01</strong> to <strong>{y + 1}-06-30</strong>. The
          system will compute net surplus, social capital, and accumulated legal
          reserve automatically from the ledger.
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded px-3 py-2">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-4 border-t border-gray-200">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending}>
            Create
          </Button>
        </div>
      </form>
    </Modal>
  );
}