import { FormEvent, useEffect, useState } from "react";
import { toast } from "sonner";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { originateLoan } from "@/api/loans";
import { formatMoney } from "@/lib/format";
import { MemberPicker } from "../savings/MemberPicker";

interface Props {
  open: boolean;
  onClose: () => void;
  presetMemberId?: string;
}

export function OriginateLoanModal({ open, onClose, presetMemberId }: Props) {
  const qc = useQueryClient();
  const [memberId, setMemberId] = useState(presetMemberId ?? "");
  const [principal, setPrincipal] = useState("1000.00");
  const [termMonths, setTermMonths] = useState("12");
  const [ratePct, setRatePct] = useState("2.00"); // displayed as percent, sent as decimal
  const [purpose, setPurpose] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Reset form when modal reopens with a new preset
  useEffect(() => {
    if (open) {
      setMemberId(presetMemberId ?? "");
      setPrincipal("1000.00");
      setTermMonths("12");
      setRatePct("2.00");
      setPurpose("");
      setError(null);
    }
  }, [open, presetMemberId]);

  const mutation = useMutation({
    mutationFn: () =>
      originateLoan({
        member: memberId,
        principal,
        term_months: parseInt(termMonths, 10),
        monthly_rate: (parseFloat(ratePct) / 100).toFixed(4),
        purpose,
      }),
    onSuccess: (loan) => {
      toast.success("Loan created. Awaiting approval.");
      qc.invalidateQueries({ queryKey: ["loans"] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      onClose();
      // Optional: navigate to detail
      window.location.href = `/loans/${loan.id}`;
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Action failed.");
      setError(
        err?.response?.data?.detail ??
          err?.response?.data?.fields?.principal?.[0] ??
          "Failed to originate loan."
      );
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

  // Live preview calculation
  const principalNum = parseFloat(principal) || 0;
  const rateDecimal = (parseFloat(ratePct) || 0) / 100;
  const monthlyInterest = principalNum * rateDecimal;

  return (
    <Modal open={open} onClose={onClose} title="Originate Loan" size="md">
      <form onSubmit={onSubmit} className="space-y-4">
        <MemberPicker value={memberId} onChange={(id) => setMemberId(id)} />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Principal (USD)"
            type="number"
            step="0.01"
            min="1"
            value={principal}
            onChange={(e) => setPrincipal(e.target.value)}
            required
          />
          <Input
            label="Term (months)"
            type="number"
            min="1"
            max="60"
            value={termMonths}
            onChange={(e) => setTermMonths(e.target.value)}
            required
          />
        </div>

        <Input
          label="Monthly Interest Rate (%)"
          type="number"
          step="0.01"
          min="1"
          max="2"
          value={ratePct}
          onChange={(e) => setRatePct(e.target.value)}
          required
        />
        <p className="text-xs text-gray-500 -mt-2">
          AGM-approved range is 1.00% – 2.00% per month.
        </p>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Purpose (optional)
          </label>
          <input
            type="text"
            value={purpose}
            onChange={(e) => setPurpose(e.target.value)}
            placeholder="e.g. working capital, farming inputs"
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        <div className="bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded p-3 space-y-1">
          <p className="font-medium">Preview</p>
          <p>
            Principal: ${formatMoney(principalNum.toFixed(2))} · Term:{" "}
            {termMonths} months · Rate: {ratePct}% per month
          </p>
          <p>
            First-month interest: ${formatMoney(monthlyInterest.toFixed(2))}
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
            Create Loan
          </Button>
        </div>
      </form>
    </Modal>
  );
}