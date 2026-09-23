import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  listTransactions,
  SavingsTransaction,
  SavingsTxnType,
} from "@/api/savings";
import { useAuth } from "@/auth/useAuth";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Table } from "@/components/Table";
import { Pagination } from "@/components/Pagination";
import { formatMoney } from "@/lib/format";
import { DepositModal } from "./savings/DepositModal";
import { WithdrawModal } from "./savings/WithdrawModal";
import { ReverseModal } from "@/components/ReverseModal";
import { TableSkeleton } from "@/components/Skeleton";

export function SavingsPage() {
  const { profile } = useAuth();
  const [typeFilter, setTypeFilter] = useState<SavingsTxnType | "">("");
  const [memberFilter, setMemberFilter] = useState("");
  const [page, setPage] = useState(1);
  const [depositOpen, setDepositOpen] = useState(false);
  const [withdrawOpen, setWithdrawOpen] = useState(false);
  const [reverseTarget, setReverseTarget] = useState<SavingsTransaction | null>(null);

  const pageSize = 20;

  const canMake =
    profile?.role === "MAKER" || profile?.role === "SUPERADMIN";
  const { data, isLoading, isError } = useQuery({
    queryKey: ["savings", "transactions", { typeFilter, memberFilter, page }],
    queryFn: () =>
      listTransactions({
        type: typeFilter || undefined,
        member: memberFilter || undefined,
        page,
        page_size: pageSize,
      }),
  });

  const rows: SavingsTransaction[] = data?.results ?? [];

  // Only COMPLETED transactions actually moved cash -- a rejected or
  // still-pending one shouldn't count toward the totals.
  const completedRows = rows.filter((r) => r.status === "COMPLETED");
  const totalDeposits = completedRows
    .filter((r) => r.transaction_type === "DEPOSIT")
    .reduce((sum, r) => sum + parseFloat(r.requested_amount), 0);
  const totalWithdrawals = completedRows
    .filter((r) => r.transaction_type === "WITHDRAWAL")
    .reduce((sum, r) => sum + parseFloat(r.requested_amount), 0);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Savings</h1>
          <p className="text-sm text-gray-500">
            Deposits and withdrawals
          </p>
        </div>
        {canMake && (
          <div className="flex gap-2">
            <Button onClick={() => setDepositOpen(true)}>
              + Record Deposit
            </Button>
            <Button
              variant="secondary"
              onClick={() => setWithdrawOpen(true)}
            >
              Record Withdrawal
            </Button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card title="Total Deposits">
          <p className="text-2xl font-bold text-green-700">
            ${formatMoney(totalDeposits)}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Completed, this page
          </p>
        </Card>
        <Card title="Total Withdrawals">
          <p className="text-2xl font-bold text-orange-700">
            ${formatMoney(totalWithdrawals)}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Completed, this page
          </p>
        </Card>
        <Card title="Transactions">
          <p className="text-2xl font-bold text-gray-800">
            {data?.count ?? 0}
          </p>
          <p className="text-xs text-gray-500 mt-1">Total entries</p>
        </Card>
      </div>

      <Card>
        <div className="flex flex-wrap gap-3 mb-4">
          <input
            value={memberFilter}
            onChange={(e) => {
              setMemberFilter(e.target.value);
              setPage(1);
            }}
            placeholder="Filter by member number..."
            className="border border-gray-300 rounded px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value as SavingsTxnType | "");
              setPage(1);
            }}
            className="border border-gray-300 rounded px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">All types</option>
            <option value="DEPOSIT">Deposits</option>
            <option value="WITHDRAWAL">Withdrawals</option>
            <option value="LOAN_REPAYMENT_SWEEP">
              Loan Repayment (Savings)
            </option>
          </select>
        </div>

        {isError ? (
          <p className="text-sm text-red-600 py-8 text-center">
            Failed to load transactions.
          </p>
        ) : (
          <>
            <Table
              headers={[
                "Date", "Type", "Member", "Amount", "Obligatory",
                "Voluntary", "Status", "Actions",
              ]}
              empty={!isLoading && rows.length === 0}
            >
              {isLoading ? <TableSkeleton rows={6} cols={8} /> : rows.map((r) => {
                const showSplit = r.transaction_type !== "WITHDRAWAL";
                return (
                  <tr key={r.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-2 px-2 text-gray-500 text-xs">
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                    <td className="py-2 px-2"><Badge value={r.transaction_type} /></td>
                    <td className="py-2 px-2"><span className="font-medium">{r.member_number}</span></td>
                    <td className="py-2 px-2 font-medium">${formatMoney(r.requested_amount)}</td>
                    <td className="py-2 px-2 text-gray-600">
                      {showSplit ? `$${formatMoney(r.obligatory_portion)}` : "—"}
                    </td>
                    <td className="py-2 px-2 text-gray-600">
                      {showSplit ? `$${formatMoney(r.voluntary_portion)}` : "—"}
                    </td>
                    <td className="py-2 px-2"><Badge value={r.status} /></td>
                    <td className="py-2 px-2">
                      {r.transaction_type !== "LOAN_REPAYMENT_SWEEP" &&
                        r.status === "COMPLETED" &&
                        r.journal_entry && (
                          <button onClick={() => setReverseTarget(r)} className="text-red-600 hover:underline text-xs">
                            Reverse
                          </button>
                        )}
                    </td>
                  </tr>
                );
              })}
            </Table>
            {data && (
              <Pagination
                count={data.count}
                page={page}
                pageSize={pageSize}
                onChange={setPage}
              />
            )}
            <ReverseModal
              open={!!reverseTarget}
              onClose={() => setReverseTarget(null)}
              journalEntryId={reverseTarget?.journal_entry ?? null}
              sourceType="SAVINGS_TRANSACTION"
              sourceId={reverseTarget?.id}
              description={
                reverseTarget
                  ? `${reverseTarget.transaction_type} $${reverseTarget.requested_amount} · ${reverseTarget.member_number}`
                  : undefined
              }
            />
          </>
        )}
      </Card>

      <DepositModal open={depositOpen} onClose={() => setDepositOpen(false)} />
      <WithdrawModal
        open={withdrawOpen}
        onClose={() => setWithdrawOpen(false)}
      />
    </div>
  );
}
