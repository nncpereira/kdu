import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { Input, Select } from "@/components/Input";
import { recordExpense } from "@/api/expenses";
import { formatMoney } from "@/lib/format";
import { toast } from "sonner";

interface Props {
  open: boolean;
  onClose: () => void;
}

const EXPENSE_ACCOUNTS = [
  { code: "5101", name: "AGM Expense" },
  { code: "5102", name: "Salaries Expense" },
  { code: "5103", name: "Utilities Expense" },
  { code: "5104", name: "Office Supplies Expense" },
];

const MAX_SIZE = 5 * 1024 * 1024;
const ALLOWED = ".pdf,.jpg,.jpeg,.png,.webp";

export function RecordExpenseModal({ open, onClose }: Props) {
  const qc = useQueryClient();
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [accountCode, setAccountCode] = useState("5101");
  const [paymentDate, setPaymentDate] = useState(
    new Date().toISOString().slice(0, 10)
  );
  const [receipt, setReceipt] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setDescription("");
      setAmount("");
      setAccountCode("5101");
      setPaymentDate(new Date().toISOString().slice(0, 10));
      setReceipt(null);
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
        receipt,
      }),
    onSuccess: () => {
      toast.success("Expense submitted for approval.");
      qc.invalidateQueries({ queryKey: ["expenses"] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      onClose();
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail;
      const fieldErr = err?.response?.data?.fields;
      const message = typeof detail === "string" ? detail : fieldErr?.receipt?.[0] ?? fieldErr?.amount?.[0] ?? "Failed to record expense.";
      toast.error(message);
      setError(message);
    },
  });

  function onFileChange(e: ChangeEvent<HTMLInputElement>) {
    setError(null);
    const file = e.target.files?.[0] ?? null;

    if (!file) {
      setReceipt(null);
      return;
    }

    if (file.size > MAX_SIZE) {
      setError(
        `File too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum 5 MB.`
      );
      e.target.value = "";
      setReceipt(null);
      return;
    }

    setReceipt(file);
  }

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

        {/* Receipt */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Receipt (optional)
          </label>
          <div className="border border-dashed border-gray-300 rounded px-3 py-4 text-sm bg-gray-50">
            {!receipt ? (
              <>
                <input
                  type="file"
                  accept={ALLOWED}
                  onChange={onFileChange}
                  className="block w-full text-sm text-gray-600 file:mr-3 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:font-medium file:bg-brand-600 file:text-white hover:file:bg-brand-700 file:cursor-pointer"
                />
                <p className="text-xs text-gray-500 mt-2">
                  PDF, JPG, PNG, or WEBP. Max 5 MB.
                </p>
              </>
            ) : (
              <div className="flex items-center justify-between">
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">
                    {receipt.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {(receipt.size / 1024).toFixed(0)} KB
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setReceipt(null)}
                  className="text-xs text-red-600 hover:underline ml-3"
                >
                  Remove
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded p-3">
          <p className="font-medium mb-1">Double-entry posting</p>
          <p>
            Debit{" "}
            <span className="font-mono">{accountCode}</span> —{" "}
            {formatMoney(amount || "0")} · Credit{" "}
            <span className="font-mono">1001</span> Cash
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
