import { useState } from "react";
import { TableSkeleton } from "@/components/Skeleton";
import { useQuery } from "@tanstack/react-query";
import { listExpenses, Expense } from "@/api/expenses";
import { useAuth } from "@/auth/useAuth";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Table } from "@/components/Table";
import { formatMoney, formatDate } from "@/lib/format";
import { RecordExpenseModal } from "./expenses/RecordExpenseModal";
import { ReverseModal } from "@/components/ReverseModal";

const ACCOUNTS = [
  { code: "", name: "All accounts" },
  { code: "5101", name: "AGM Expense" },
  { code: "5102", name: "Salaries Expense" },
  { code: "5103", name: "Utilities Expense" },
  { code: "5104", name: "Office Supplies Expense" },
];

export function ExpensesPage() {
  const { profile } = useAuth();
  const [accountFilter, setAccountFilter] = useState("");
  const [recordOpen, setRecordOpen] = useState(false);
  const [reverseTarget, setReverseTarget] = useState<Expense | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["expenses", { accountFilter }],
    queryFn: () =>
      listExpenses({
        expense_account_code: accountFilter || undefined,
      }),
  });

  const canRecord =
    profile?.role === "MAKER" || profile?.role === "SUPERADMIN";

  const rows: Expense[] = data ?? [];
  const totalAmount = rows.reduce((s, e) => s + parseFloat(e.amount), 0);
  const completedCount = rows.filter((e) => e.status === "COMPLETED").length;
  const pendingCount = rows.filter(
    (e) => e.status === "PENDING_CHECK" || e.status === "PENDING_CERTIFY"
  ).length;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Expenses</h1>
          <p className="text-sm text-gray-500">
            Operating costs and administrative outlays
          </p>
        </div>
        {canRecord && (
          <Button onClick={() => setRecordOpen(true)}>+ Record Expense</Button>
        )}
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card title="Total Expenses">
          <p className="text-2xl font-bold text-red-700">
            ${formatMoney(totalAmount.toFixed(2))}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Across {rows.length} entries
          </p>
        </Card>
        <Card title="Completed">
          <p className="text-2xl font-bold text-green-700">
            {completedCount}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Fully approved and posted to the ledger
          </p>
        </Card>
        <Card title="In Pipeline">
          <p className="text-2xl font-bold text-yellow-700">
            {pendingCount}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Awaiting Checker or Certifier
          </p>
        </Card>
      </div>

      {/* Filter + Table */}
      <Card>
        <div className="flex flex-wrap gap-3 mb-4">
          <select
            value={accountFilter}
            onChange={(e) => setAccountFilter(e.target.value)}
            className="border border-gray-300 rounded px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {ACCOUNTS.map((a) => (
              <option key={a.code} value={a.code}>
                {a.name}
              </option>
            ))}
          </select>
        </div>

        {isLoading && (
          <TableSkeleton rows={5} cols={6} />
        )}
        {isError && (
          <p className="text-sm text-red-600 py-8 text-center">
            Failed to load expenses.
          </p>
        )}

        {!isLoading && !isError && (
          <Table
            headers={[
              "Date",
              "Description",
              "Account",
              "Amount",
              "Receipt",
              "Status",
              "Actions",
            ]}
            empty={rows.length === 0}
          >
            {rows.map((e) => (
              <tr
                key={e.id}
                className="border-b border-gray-100 hover:bg-gray-50"
              >
                <td className="py-2 px-2 text-xs text-gray-500">
                  {formatDate(e.payment_date)}
                </td>
                <td className="py-2 px-2">{e.description}</td>
                <td className="py-2 px-2 font-mono text-xs">
                  {e.expense_account_code}
                </td>
                <td className="py-2 px-2 font-medium">
                  ${formatMoney(e.amount)}
                </td>
                <td className="py-2 px-2">
                  {e.receipt_url ? (
                    <a
                      href={e.receipt_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-brand-600 hover:underline text-xs"
                    >
                      View
                    </a>
                  ) : (
                    <span className="text-xs text-gray-400">—</span>
                  )}
                </td>
                <td className="py-2 px-2">
                  <Badge value={e.status} />
                </td>
                <td className="py-2 px-2">
                  {e.status === "COMPLETED" && e.journal_entry && (
                    <button
                      onClick={() => setReverseTarget(e)}
                      className="text-red-600 hover:underline text-xs"
                    >
                      Reverse
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      <RecordExpenseModal
        open={recordOpen}
        onClose={() => setRecordOpen(false)}
      />
      <ReverseModal
        open={!!reverseTarget}
        onClose={() => setReverseTarget(null)}
        journalEntryId={reverseTarget?.journal_entry ?? null}
        sourceType="EXPENSE"
        sourceId={reverseTarget?.id}
        description={
          reverseTarget
            ? `${reverseTarget.description} · $${reverseTarget.amount}`
            : undefined
        }
      />
    </div>
  );
}
