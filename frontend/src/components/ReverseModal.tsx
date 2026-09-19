import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { createReversal, ReversalSourceType } from "@/api/reversals";
import { toast } from "sonner";

interface Props {
  open: boolean;
  onClose: () => void;
  journalEntryId: string | null;
  sourceType: ReversalSourceType;
  sourceId?: string;
  description?: string;
}

export function ReverseModal({
  open,
  onClose,
  journalEntryId,
  sourceType,
  sourceId,
  description,
}: Props) {
  const qc = useQueryClient();
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setReason("");
      setError(null);
    }
  }, [open]);

  const mutation = useMutation({
    mutationFn: () =>
      createReversal({
        original_journal_entry: journalEntryId!,
        source_type: sourceType,
        source_id: sourceId,
        reason,
      }),
    onSuccess: () => {
      toast.success("Reversal request submitted for approval.");
      // Invalidate everything that might show the reversed record.
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      qc.invalidateQueries({ queryKey: ["savings"] });
      qc.invalidateQueries({ queryKey: ["loans"] });
      qc.invalidateQueries({ queryKey: ["loan"] });
      qc.invalidateQueries({ queryKey: ["expenses"] });
      qc.invalidateQueries({ queryKey: ["reversals"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["reports"] });
      onClose();
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail ?? "Failed to create reversal.";
      toast.error(detail);
      setError(detail);
    },
  });

  if (!journalEntryId) return null;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (reason.trim().length < 5) {
      setError("Please provide a reason (at least 5 characters).");
      return;
    }
    await mutation.mutateAsync();
  }

  return (
    <Modal open={open} onClose={onClose} title="Reverse Transaction" size="md">
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm rounded p-3">
          <p className="font-medium">You are about to reverse a certified entry.</p>
          <p className="text-xs mt-1">
            The original entry will not be deleted. A new offsetting entry will
            be posted once the Checker and Certifier approve. Cached balances
            will be updated automatically.
          </p>
        </div>

        {description && (
          <div className="bg-gray-50 border border-gray-200 rounded p-3 text-sm">
            <p className="text-xs text-gray-500">Original entry</p>
            <p className="font-medium mt-0.5">{description}</p>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Reason for reversal *
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={4}
            placeholder="e.g. Member deposited wrong amount, expense posted to wrong account"
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            required
          />
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
          <Button type="submit" variant="danger" loading={mutation.isPending}>
            Request Reversal
          </Button>
        </div>
      </form>
    </Modal>
  );
}
