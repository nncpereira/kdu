import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { rejectActor, PipelineActor } from "@/api/pipeline";
import { formatMoney } from "@/lib/format";

interface Props {
  actor: PipelineActor | null;
  open: boolean;
  onClose: () => void;
}

export function RejectConfirmModal({ actor, open, onClose }: Props) {
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
    mutationFn: () => rejectActor(actor!.id, reason),
    onSuccess: () => {
      toast.success("Transaction rejected. The Maker has been notified.");
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["notifications"] });
      onClose();
    },
    onError: (err: any) => {
      toast.error(
        err?.response?.data?.detail ?? "Failed to reject transaction."
      );
    },
  });

  if (!actor) return null;

  const summary = actor.target_summary;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (reason.trim().length < 5) {
      setError("Please provide a reason of at least 5 characters.");
      return;
    }
    await mutation.mutateAsync();
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Confirm Rejection"
      size="md"
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="bg-yellow-50 border-l-4 border-yellow-500 px-4 py-3 rounded">
          <p className="text-sm font-semibold text-yellow-800">
            The Maker will see your reason
          </p>
          <p className="text-xs text-yellow-700 mt-1">
            The transaction will return to the Maker with your note. They can
            correct it and resubmit, or abandon it. Nothing posts to the ledger.
          </p>
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded p-4 space-y-2 text-sm">
          <DetailRow label="Type" value={actor.transaction_type.replace("_", " ")} />
          <DetailRow
            label="Description"
            value={summary?.label ?? "(no description)"}
          />
          {summary?.amount && (
            <DetailRow
              label="Amount"
              value={`$${formatMoney(summary.amount)}`}
            />
          )}
          <DetailRow label="Maker" value={actor.maker_username} />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Reason for rejection *
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={4}
            placeholder="e.g. Amount does not match the deposit slip, please verify and resubmit."
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            autoFocus
          />
          <p className="text-xs text-gray-500 mt-1">
            Minimum 5 characters. Be specific — this is what the Maker will see.
          </p>
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
          <Button
            type="submit"
            variant="danger"
            loading={mutation.isPending}
            disabled={reason.trim().length < 5}
          >
            Yes, Reject
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-gray-500 shrink-0">{label}</span>
      <span className="text-gray-800 text-right truncate">{value}</span>
    </div>
  );
}