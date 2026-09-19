import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { withdraw, getVoluntaryBalance } from "@/api/savings";
import { formatMoney } from "@/lib/format";
import { MemberPicker } from "./MemberPicker";
import { toast } from "sonner";

interface Props {
  open: boolean;
  onClose: () => void;
  presetMemberId?: string;
}

export function WithdrawModal({ open, onClose, presetMemberId }: Props) {
  const qc = useQueryClient();
  const [memberId, setMemberId] = useState(presetMemberId ?? "");
  const [amount, setAmount] = useState("");
  const [error, setError] = useState<string | null>(null);

  const balanceQuery = useQuery({
    queryKey: ["savings", "voluntary", memberId],
    queryFn: () => getVoluntaryBalance(memberId),
    enabled: !!memberId,
  });

  // Reset amount when switching member
  useEffect(() => {
    setAmount("");
  }, [memberId]);

  const mutation = useMutation({
    mutationFn: () => withdraw(memberId, amount),
    onSuccess: () => {
      toast.success("Withdrawal submitted for approval.");
      qc.invalidateQueries({ queryKey: ["savings"] });
      qc.invalidateQueries({ queryKey: ["members"] });
      qc.invalidateQueries({ queryKey: ["member"] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      setError(null);
      setMemberId(presetMemberId ?? "");
      setAmount("");
      onClose();
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail;
      if (typeof detail === "string" && detail.includes("Insufficient")) {
        toast.error("Insufficient voluntary balance for this withdrawal.");
        setError("Insufficient voluntary balance for this withdrawal.");
      } else {
        toast.error(detail ?? "Withdrawal failed.");
        setError(detail ?? "Withdrawal failed.");
      }
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

  const available = balanceQuery.data?.balance_available ?? "0.00";
  const held = balanceQuery.data?.balance_held_pipeline ?? "0.00";
  const availableNum = parseFloat(available) - parseFloat(held);

  return (
    <Modal open={open} onClose={onClose} title="Record Withdrawal" size="md">
      <form onSubmit={onSubmit} className="space-y-4">
        <MemberPicker
          value={memberId}
          onChange={(id) => setMemberId(id)}
        />

        {memberId && balanceQuery.data && (
          <div className="bg-gray-50 border border-gray-200 rounded p-3 text-sm space-y-1">
            <p>
              <span className="text-gray-500">Available:</span>{" "}
              <span className="font-medium text-green-700">
                ${formatMoney(available)}
              </span>
            </p>
            {parseFloat(held) > 0 && (
              <p>
                <span className="text-gray-500">Held in pending:</span>{" "}
                <span className="font-medium text-yellow-700">
                  ${formatMoney(held)}
                </span>
              </p>
            )}
            <p className="text-xs text-gray-500">
              Withdrawals come from voluntary deposits only. Obligatory
              (Kapital Sosial) savings cannot be withdrawn while a member is
              active.
            </p>
          </div>
        )}

        <Input
          label="Amount (USD)"
          type="number"
          step="0.01"
          min="0.01"
          max={availableNum > 0 ? availableNum.toFixed(2) : undefined}
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
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
          <Button
            type="submit"
            loading={mutation.isPending}
            disabled={availableNum <= 0}
          >
            Submit Withdrawal
          </Button>
        </div>
      </form>
    </Modal>
  );
}
