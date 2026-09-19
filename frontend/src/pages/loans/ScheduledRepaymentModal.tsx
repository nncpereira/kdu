import { FormEvent, useEffect, useState } from "react";
import { toast } from "sonner";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { scheduledRepayment, Loan } from "@/api/loans";
import { formatMoney } from "@/lib/format";

interface Props {
  loan: Loan | null;
  open: boolean;
  onClose: () => void;
}

export function ScheduledRepaymentModal({ loan, open, onClose }: Props) {
  const qc = useQueryClient();
  const [cashAmount, setCashAmount] = useState("0.00");
  const [scheduledPrincipal, setScheduledPrincipal] = useState("0.00");
  const [paymentDate, setPaymentDate] = useState(
    new Date().toISOString().slice(0, 10)
  );
  const [error, setError] = useState<string | null>(null);

  // Pre-compute the interest due and pre-fill cash = interest + scheduled principal
  const interestDue = loan
    ? parseFloat(loan.principal_outstanding) * parseFloat(loan.monthly_rate)
    : 0;

  useEffect(() => {
    if (open && loan) {
      const suggestedPrincipal =
        parseFloat(loan.principal_original) / loan.term_months;
      setScheduledPrincipal(suggestedPrincipal.toFixed(2));
      setCashAmount(
        (interestDue + suggestedPrincipal).toFixed(2)
      );
      setPaymentDate(new Date().toISOString().slice(0, 10));
      setError(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, loan]);

  const mutation = useMutation({
    mutationFn: () =>
      scheduledRepayment(loan!.id, {
        cash_amount: cashAmount,
        scheduled_principal: scheduledPrincipal,
        payment_date: paymentDate,
      }),
    onSuccess: () => {
      toast.success("Installment submitted for approval.");
      qc.invalidateQueries({ queryKey: ["loan", loan!.id] });
      qc.invalidateQueries({ queryKey: ["loans"] });
      qc.invalidateQueries({ queryKey: ["repayments", loan!.id] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      onClose();
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Action failed.");
      const detail = err?.response?.data?.detail;
      if (typeof detail === "string" && detail.includes("INSUFFICIENT")) {
        setError(
          `Cash received must cover the interest due ($${formatMoney(
            interestDue.toFixed(2)
          )}).`
        );
      } else {
        setError(detail ?? "Repayment failed.");
      }
    },
  });

  if (!loan) return null;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    await mutation.mutateAsync();
  }

  // Live waterfall preview
  const cashNum = parseFloat(cashAmount) || 0;
  const principalNum = parseFloat(scheduledPrincipal) || 0;
  const interestPortion = Math.min(cashNum, interestDue);
  const remaining = cashNum - interestPortion;
  const principalPortion = Math.min(remaining, principalNum);
  const savingsPortion = Math.max(0, remaining - principalPortion);
  const obligatoryPortion = Math.min(savingsPortion, 20);
  const voluntaryPortion = savingsPortion - obligatoryPortion;
  const insufficient = cashNum < interestDue;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Record Scheduled Installment"
      size="md"
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="bg-gray-50 rounded p-3 text-sm">
          <p className="font-medium">{loan.member_number}</p>
          <p className="text-gray-500">
            Outstanding: ${formatMoney(loan.principal_outstanding)} · Rate:{" "}
            {formatMoney((parseFloat(loan.monthly_rate) * 100).toFixed(2))}%/mo
          </p>
          <p className="text-gray-500">
            Interest due this month: ${formatMoney(interestDue.toFixed(2))}
          </p>
        </div>

        <div className="bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded p-3">
          Waterfall: interest → principal → obligatory savings (max $20) →
          voluntary savings. If cash is less than the interest due, the
          transaction is rejected.
        </div>

        <Input
          label="Cash Received (USD)"
          type="number"
          step="0.01"
          min="0.01"
          value={cashAmount}
          onChange={(e) => setCashAmount(e.target.value)}
          required
        />

        <Input
          label="Scheduled Principal (USD)"
          type="number"
          step="0.01"
          min="0"
          value={scheduledPrincipal}
          onChange={(e) => setScheduledPrincipal(e.target.value)}
        />

        <Input
          label="Payment Date"
          type="date"
          value={paymentDate}
          onChange={(e) => setPaymentDate(e.target.value)}
        />

        <div className="bg-gray-50 border border-gray-200 rounded p-3 text-xs space-y-1">
          <p className="font-medium text-gray-700 mb-2">Waterfall preview</p>
          <Row label="Interest" value={interestPortion} />
          <Row label="Principal" value={principalPortion} />
          <Row label="Obligatory savings" value={obligatoryPortion} />
          <Row label="Voluntary savings" value={voluntaryPortion} />
        </div>

        {insufficient && (
          <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-xs rounded p-3">
            Cash received is less than the interest due. Use the Manual
            Repayment mode instead.
          </div>
        )}

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
            disabled={insufficient}
          >
            Submit Installment
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function Row({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium">${formatMoney(value.toFixed(2))}</span>
    </div>
  );
}