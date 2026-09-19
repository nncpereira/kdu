import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { deposit } from "@/api/savings";
import { formatMoney } from "@/lib/format";
import { MemberPicker } from "./MemberPicker";
import { toast } from "sonner";

interface Props {
  open: boolean;
  onClose: () => void;
  presetMemberId?: string;
}

export function DepositModal({ open, onClose, presetMemberId }: Props) {
  const qc = useQueryClient();
  const [memberId, setMemberId] = useState(presetMemberId ?? "");
  const [amount, setAmount] = useState("1000.00");
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => deposit(memberId, amount),
    onSuccess: () => {
      toast.success("Deposit submitted for approval.");
      qc.invalidateQueries({ queryKey: ["savings"] });
      qc.invalidateQueries({ queryKey: ["members"] });
      qc.invalidateQueries({ queryKey: ["member"] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      setError(null);
      setMemberId(presetMemberId ?? "");
      setAmount("1000.00");
      onClose();
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail ?? err?.response?.data?.fields?.amount?.[0] ?? "Deposit failed.";
      toast.error(detail);
      setError(detail);
    },
  });

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!memberId) {
      setError("Please select a member.");
      return;
    }
    await mutation.mutateAsync();
  }

  return (
    <Modal open={open} onClose={onClose} title="Record Deposit" size="md">
      <form onSubmit={onSubmit} className="space-y-4">
        <MemberPicker
          value={memberId}
          onChange={(id) => setMemberId(id)}
        />

        <Input
          label="Amount (USD)"
          type="number"
          step="0.01"
          min="0.01"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
        />

        <div className="bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded p-3">
          <p className="font-medium mb-1">Deposit split</p>
          <p>
            The first ${formatMoney("20.00")} each month goes to obligatory
            savings (Kapital Sosial). The remainder goes to voluntary deposits.
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
          <Button type="submit" loading={mutation.isPending}>
            Submit Deposit
          </Button>
        </div>
      </form>
    </Modal>
  );
}
