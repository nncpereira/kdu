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
import { formatMoney } from "@/lib/format";
import { DepositModal } from "./savings/DepositModal";
import { WithdrawModal } from "./savings/WithdrawModal";

export function SavingsPage() {
  const { profile } = useAuth();
  const [typeFilter, setTypeFilter] = useState<SavingsTxnType | "">("");
  const [memberFilter, setMemberFilter] = useState("");
  const [depositOpen, setDepositOpen] = useState(false);
  const [withdrawOpen, setWithdrawOpen] = useState(false);

  const canMake =
    profile?.role === "MAKER" || profile?.role === "SUPERADMIN";
  const canView = true; // All staff can view savings transactions

  const { data, isLoading, isError } = useQuery({
    queryKey: ["savings", "transactions", { typeFilter, memberFilter }],
    queryFn: () =>
      listTransactions({
        type: typeFilter || undefined,
        member: memberFilter || undefined,
      }),
    // enabled: canView || canMake,
  });

  // The endpoint may return a plain list or a paginated object
  const rows: SavingsTransaction[] = Array.isArray(data)
    ? data
    : data?.results ?? [];

  const totalDeposits = rows
    .filter((r) => r.transaction_type === "DEPOSIT")
    .reduce((sum, r) => sum + parseFloat(r.requested_amount), 0);
  const totalWithdrawals = rows
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
            Across displayed transactions
          </p>
        </Card>
        <Card title="Total Withdrawals">
          <p className="text-2xl font-bold text-orange-700">
            ${formatMoney(totalWithdrawals)}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Across displayed transactions
          </p>
        </Card>
        <Card title="Transactions">
          <p className="text-2xl font-bold text-gray-800">{rows.length}</p>
          <p className="text-xs text-gray-500 mt-1">Recent entries</p>
        </Card>
      </div>

      <Card>
        <div className="flex flex-wrap gap-3 mb-4">
          <select
            value={typeFilter}
            onChange={(e) =>
              setTypeFilter(e.target.value as SavingsTxnType | "")
            }
            className="border border-gray-300 rounded px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">All types</option>
            <option value="DEPOSIT">Deposits</option>
            <option value="WITHDRAWAL">Withdrawals</option>
          </select>
        </div>

        {isLoading && (
          <p className="text-sm text-gray-500 py-8 text-center">Loading…</p>
        )}
        {isError && (
          <p className="text-sm text-red-600 py-8 text-center">
            Failed to load transactions.
          </p>
        )}

        {!isLoading && !isError && (
          <Table
            headers={[
              "Date",
              "Type",
              "Member",
              "Amount",
              "Obligatory",
              "Voluntary",
              "Status",
            ]}
            empty={rows.length === 0}
          >
            {rows.map((r) => (
              <tr
                key={r.id}
                className="border-b border-gray-100 hover:bg-gray-50"
              >
                <td className="py-2 px-2 text-gray-500 text-xs">
                  {new Date(r.created_at).toLocaleString()}
                </td>
                <td className="py-2 px-2">
                  <Badge value={r.transaction_type} />
                </td>
                <td className="py-2 px-2">
                  <span className="font-medium">{r.member_number}</span>
                </td>
                <td className="py-2 px-2 font-medium">
                  ${formatMoney(r.requested_amount)}
                </td>
                <td className="py-2 px-2 text-gray-600">
                  {r.transaction_type === "DEPOSIT"
                    ? `$${formatMoney(r.obligatory_portion)}`
                    : "—"}
                </td>
                <td className="py-2 px-2 text-gray-600">
                  {r.transaction_type === "DEPOSIT"
                    ? `$${formatMoney(r.voluntary_portion)}`
                    : "—"}
                </td>
                <td className="py-2 px-2">
                  <Badge value={r.status} />
                </td>
              </tr>
            ))}
          </Table>
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