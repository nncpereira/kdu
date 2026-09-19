import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { manualRepayment, Loan } from "@/api/loans";
import { formatMoney } from "@/lib/format";

interface Props {
  loan: Loan | null;
  open: boolean;
  onClose: () => void;
}

export function ManualRepaymentModal({ loan, open, onClose }: Props) {
  const qc = useQueryClient();
  const [principalPaid, setPrincipalPaid] = useState("0.00");
  const [interestPaid, setInterestPaid] = useState("0.00");
  const [paymentDate, setPaymentDate] = useState(
    new Date().toISOString().slice(0, 10)
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && loan) {
      setPrincipalPaid("0.00");
      setInterestPaid("0.00");
      setPaymentDate(new Date().toISOString().slice(0, 10));
      setError(null);
    }
  }, [open, loan]);

  const mutation = useMutation({
    mutationFn: () =>
      manualRepayment(loan!.id, {
        principal_paid: principalPaid,
        interest_paid: interestPaid,
        payment_date: paymentDate,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["loan", loan!.id] });
      qc.invalidateQueries({ queryKey: ["loans"] });
      qc.invalidateQueries({ queryKey: ["repayments", loan!.id] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      onClose();
    },
    onError: (err: any) => {
      setError(err?.response?.data?.detail ?? "Repayment failed.");
    },
  });

  if (!loan) return null;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    await mutation.mutateAsync();
  }

  const total =
    (parseFloat(principalPaid) || 0) + (parseFloat(interestPaid) || 0);

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Record Manual Repayment"
      size="md"
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="bg-gray-50 rounded p-3 text-sm">
          <p className="font-medium">{loan.member_number}</p>
          <p className="text-gray-500">
            Outstanding: ${formatMoney(loan.principal_outstanding)} · Rate:{" "}
            {formatMoney((parseFloat(loan.monthly_rate) * 100).toFixed(2))}%/mo
          </p>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-xs rounded p-3">
          For members with irregular income (market vendors, casual labour).
          Enter whatever they can pay this period. No validation on the interest
          amount — the Checker reviews against the field receipt.
        </div>

        <Input
          label="Principal Paid (USD)"
          type="number"
          step="0.01"
          min="0"
          value={principalPaid}
          onChange={(e) => setPrincipalPaid(e.target.value)}
        />
        <Input
          label="Interest Paid (USD)"
          type="number"
          step="0.01"
          min="0"
          value={interestPaid}
          onChange={(e) => setInterestPaid(e.target.value)}
        />
        <Input
          label="Payment Date"
          type="date"
          value={paymentDate}
          onChange={(e) => setPaymentDate(e.target.value)}
        />

        <div className="bg-blue-50 border border-blue-200 text-blue-800 text-sm rounded p-3">
          <p className="font-medium">
            Total Cash Received: ${formatMoney(total.toFixed(2))}
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
            Submit Repayment
          </Button>
        </div>
      </form>
    </Modal>
  );
}