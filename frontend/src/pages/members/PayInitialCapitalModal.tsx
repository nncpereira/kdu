import { FormEvent, useState } from "react";
import { toast } from "sonner";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { payInitialCapital } from "@/api/members";
import type { Member } from "@/api/members";

interface Props {
  member: Member | null;
  open: boolean;
  onClose: () => void;
}

const STANDARD_CAPITAL = "150.00";
const STANDARD_FIRST_MONTH_SAVINGS = "20.00";
const STANDARD_ENTRANCE_FEE = "5.00";
const STANDARD_TOTAL = "175.00";

export function PayInitialCapitalModal({ member, open, onClose }: Props) {
  const qc = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      payInitialCapital(member!.id, {
        amount: STANDARD_CAPITAL,
        first_month_savings: STANDARD_FIRST_MONTH_SAVINGS,
        entrance_fee: STANDARD_ENTRANCE_FEE,
      }),
    onSuccess: () => {
      toast.success("Initial payment submitted for approval.");
      qc.invalidateQueries({ queryKey: ["members"] });
      qc.invalidateQueries({ queryKey: ["member", member!.id] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      setError(null);
      onClose();
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Action failed.");
      setError(err?.response?.data?.detail ?? "Payment failed.");
    },
  });

  if (!member) return null;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    await mutation.mutateAsync();
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

        <div className="border border-gray-200 rounded p-3 space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Principal savings (capital)</span>
            <span className="font-medium">${STANDARD_CAPITAL}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">First month's mandatory savings</span>
            <span className="font-medium">${STANDARD_FIRST_MONTH_SAVINGS}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Entrance / admin / booklet fee</span>
            <span className="font-medium">${STANDARD_ENTRANCE_FEE}</span>
          </div>
          <div className="flex justify-between pt-2 border-t border-gray-200 font-semibold">
            <span>Total cash due upfront</span>
            <span>${STANDARD_TOTAL}</span>
          </div>
        </div>
        <p className="text-xs text-gray-500">
          Confirms the member has brought the standard ${STANDARD_TOTAL} cash
          due at signup. This creates a Maker-Checker-Certifier pipeline; the
          member is activated after all three stages.
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
            Confirm Payment Received
          </Button>
        </div>
      </form>
    </Modal>
  );
}
