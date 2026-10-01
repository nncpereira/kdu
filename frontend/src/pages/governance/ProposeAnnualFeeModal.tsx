import { FormEvent, useState } from "react";
import { toast } from "sonner";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { proposeChange } from "@/api/governance";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function ProposeAnnualFeeModal({ open, onClose }: Props) {
  const qc = useQueryClient();
  const [fee, setFee] = useState("20.00");
  const [effectiveFrom, setEffectiveFrom] = useState(() => {
    const y = new Date().getFullYear();
    return `${y + 1}-01-01`;
  });
  const [error, setError] = useState<string | null>(null);

  const feeAmount = parseFloat(fee);
  const isValid = !Number.isNaN(feeAmount) && feeAmount >= 0;

  const mutation = useMutation({
    mutationFn: () =>
      proposeChange({
        parameter_key: "shu_annual_fee",
        proposed_value: fee,
        effective_from: effectiveFrom,
      }),
    onSuccess: () => {
      toast.success("Annual fee proposed. Awaiting approval.");
      qc.invalidateQueries({ queryKey: ["governance"] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      onClose();
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Action failed.");
      setError(err?.response?.data?.detail ?? "Proposal failed.");
    },
  });

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!isValid) {
      setError("Enter a non-negative dollar amount.");
      return;
    }
    await mutation.mutateAsync();
  }

  return (
    <Modal open={open} onClose={onClose} title="Propose Annual Fee" size="sm">
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded p-3">
          <p>
            A flat amount deducted from each member's SHU payout, floored at
            $0 — a member whose payout is smaller than the fee simply
            receives $0 rather than owing the difference.
          </p>
        </div>

        <Input
          label="Annual Fee ($)"
          type="number"
          step="0.01"
          min="0"
          value={fee}
          onChange={(e) => setFee(e.target.value)}
        />

        <Input
          label="Effective From"
          type="date"
          value={effectiveFrom}
          onChange={(e) => setEffectiveFrom(e.target.value)}
        />

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded px-3 py-2">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-4 border-t border-gray-200">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending} disabled={!isValid}>
            Propose Change
          </Button>
        </div>
      </form>
    </Modal>
  );
}
