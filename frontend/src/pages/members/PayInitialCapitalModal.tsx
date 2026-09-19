import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { payInitialCapital } from "@/api/members";
import type { Member } from "@/api/members";

interface Props {
  member: Member | null;
  open: boolean;
  onClose: () => void;
}

export function PayInitialCapitalModal({ member, open, onClose }: Props) {
  const qc = useQueryClient();
  const [amount, setAmount] = useState("50.00");
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (amt: string) => payInitialCapital(member!.id, amt),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["members"] });
      qc.invalidateQueries({ queryKey: ["member", member!.id] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      setError(null);
      onClose();
    },
    onError: (err: any) => {
      const detail =
        err?.response?.data?.detail ??
        err?.response?.data?.fields?.amount?.[0] ??
        "Payment failed.";
      setError(detail);
    },
  });

  if (!member) return null;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    await mutation.mutateAsync(amount);
  }

  return (
    <Modal open={open} onClose={onClose} title="Pay Initial Capital" size="sm">
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="bg-gray-50 rounded p-3 text-sm">
          <p className="font-medium">{member.full_name}</p>
          <p className="text-gray-500">{member.membership_number}</p>
          <p className="text-gray-500 mt-1">
            Status: <span className="font-medium">{member.status}</span>
          </p>
        </div>

        <Input
          label="Amount (USD)"
          type="number"
          step="0.01"
          min="50"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
        />
        <p className="text-xs text-gray-500">
          Minimum: $50.00 (DL 76/2022 Art. 19). This creates a Maker-Checker-Certifier
          pipeline; the member is activated after all three stages.
        </p>

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
            Submit Payment
          </Button>
        </div>
      </form>
    </Modal>
  );
}