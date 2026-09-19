import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { Input, Select } from "@/components/Input";
import { recordExpense } from "@/api/expenses";
import { formatMoney } from "@/lib/format";

interface Props {
  open: boolean;
  onClose: () => void;
}

// Standard expense accounts from the CoA seed.
// In production, load these from /api/v1/admin/coa/ filtered to account_type=EXPENSE.
const EXPENSE_ACCOUNTS = [
  { code: "5101", name: "AGM Expense" },
  { code: "5102", name: "Salaries Expense" },
  { code: "5103", name: "Utilities Expense" },
  { code: "5104", name: "Office Supplies Expense" },
];

export function RecordExpenseModal({ open, onClose }: Props) {
  const qc = useQueryClient();
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [accountCode, setAccountCode] = useState("5101");
  const [paymentDate, setPaymentDate] = useState(
    new Date().toISOString().slice(0, 10)
  );
  const [error, setError] = useState<string | null>(null);

  // Reset form on open
  useEffect(() => {
    if (open) {
      setDescription("");
      setAmount("");
      setAccountCode("5101");
      setPaymentDate(new Date().toISOString().slice(0, 10));
      setError(null);
    }
  }, [open]);

  const mutation = useMutation({
    mutationFn: () =>
      recordExpense({
        description,
        amount,
        expense_account_code: accountCode,
        payment_date: paymentDate,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["expenses"] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      onClose();
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail;
      const fieldErr = err?.response?.data?.fields;
      if (typeof detail === "string") {
        setError(detail);
      } else if (fieldErr?.amount) {
        setError(fieldErr.amount[0]);
      } else if (fieldErr?.expense_account_code) {
        setError(fieldErr.expense_account_code[0]);
      } else {
        setError("Failed to record expense.");
      }
    },
  });

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    await mutation.mutateAsync();
  }

  return (
    <Modal open={open} onClose={onClose} title="Record Expense" size="md">
      <form onSubmit={onSubmit} className="space-y-4">
        <Input
          label="Description *"
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="e.g. AGM venue rental, November electricity bill"
          required
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Amount (USD) *"
            type="number"
            step="0.01"
            min="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
          <Input
            label="Payment Date"
            type="date"
            value={paymentDate}
            onChange={(e) => setPaymentDate(e.target.value)}
          />
        </div>

        <Select
          label="Expense Account *"
          value={accountCode}
          onChange={(e) => setAccountCode(e.target.value)}
        >
          {EXPENSE_ACCOUNTS.map((a) => (
            <option key={a.code} value={a.code}>
              {a.code} — {a.name}
            </option>
          ))}
        </Select>

        <div className="bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded p-3">
          <p className="font-medium mb-1">Double-entry posting</p>
          <p>
            Debit{" "}
            <span className="font-mono">{accountCode}</span> —{" "}
            {formatMoney(amount || "0")} · Credit{" "}
            <span className="font-mono">1001</span> Cash
          </p>
          <p className="mt-1 text-blue-700">
            The expense is recorded in the ledger only after the
            Checker and Certifier approve it through the pipeline.
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
            Submit Expense
          </Button>
        </div>
      </form>
    </Modal>
  );
}