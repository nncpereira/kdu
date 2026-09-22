import { useQuery } from "@tanstack/react-query";
import { getMySavings, getMyTransactions } from "@/api/memberPortal";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Table } from "@/components/Table";
import { TableSkeleton } from "@/components/Skeleton";
import { formatMoney } from "@/lib/format";

export function PortalSavingsPage() {
  const savingsQuery = useQuery({
    queryKey: ["portal", "savings"],
    queryFn: getMySavings,
  });
  const txnsQuery = useQuery({
    queryKey: ["portal", "transactions"],
    queryFn: getMyTransactions,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-800">My Savings</h1>
        <p className="text-sm text-gray-500">
          Your capital and voluntary deposits
        </p>
      </div>

      {/* Balance cards */}
      {savingsQuery.data && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card title="Kapital Sosial">
            <p className="text-2xl font-bold text-gray-800">
              ${formatMoney(savingsQuery.data.kapital_sosial_balance)}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Your permanent share in the cooperative
            </p>
          </Card>
          <Card title="Voluntary Deposits">
            <p className="text-2xl font-bold text-brand-700">
              ${formatMoney(savingsQuery.data.voluntary.balance_available)}
            </p>
            {parseFloat(savingsQuery.data.voluntary.balance_held_pipeline) >
              0 && (
              <p className="text-xs text-yellow-700 mt-1">
                $
                {formatMoney(
                  savingsQuery.data.voluntary.balance_held_pipeline
                )}{" "}
                held in a pending request
              </p>
            )}
          </Card>
          <Card title="Total Savings">
            <p className="text-2xl font-bold text-green-700">
              $
              {formatMoney(
                (
                  parseFloat(savingsQuery.data.kapital_sosial_balance) +
                  parseFloat(
                    savingsQuery.data.voluntary.balance_available
                  )
                ).toFixed(2)
              )}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Capital + Voluntary
            </p>
          </Card>
        </div>
      )}

      {/* Info box */}
      <div className="bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded-lg p-4">
        <p className="font-medium mb-1">Understanding your balances</p>
        <p className="mb-1">
          <strong>Kapital Sosial</strong> is your mandatory share. It is
          refunded only when you exit the cooperative.
        </p>
        <p>
          <strong>Voluntary Deposits</strong> are withdrawable at any time at
          the cooperative office. Obligatory monthly savings build your
          capital over time.
        </p>
      </div>

      {/* Transaction history */}
      <Card title="Transaction History">
        {txnsQuery.isError ? (
          <p className="text-sm text-red-600 py-6 text-center">
            Failed to load transactions.
          </p>
        ) : (
          <Table
            headers={["Date", "Type", "Amount", "Obligatory", "Voluntary", "Status"]}
            empty={!txnsQuery.isLoading && (txnsQuery.data?.length ?? 0) === 0}
          >
            {txnsQuery.isLoading ? (
              <TableSkeleton rows={5} cols={6} />
            ) : (
              (txnsQuery.data ?? []).map((t) => (
                <tr key={t.id} className="border-b border-gray-100">
                  <td className="py-2 px-2 text-xs text-gray-500">
                    {new Date(t.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-2 px-2">
                    <Badge value={t.transaction_type} />
                  </td>
                  <td className="py-2 px-2 font-medium">
                    ${formatMoney(t.requested_amount)}
                  </td>
                  <td className="py-2 px-2 text-gray-600">
                    {t.transaction_type === "DEPOSIT"
                      ? `$${formatMoney(t.obligatory_portion)}`
                      : "—"}
                  </td>
                  <td className="py-2 px-2 text-gray-600">
                    {t.transaction_type === "DEPOSIT"
                      ? `$${formatMoney(t.voluntary_portion)}`
                      : "—"}
                  </td>
                  <td className="py-2 px-2">
                    <Badge value={t.status} />
                  </td>
                </tr>
              ))
            )}
          </Table>
        )}
      </Card>
    </div>
  );
}