import { useQuery } from "@tanstack/react-query";
import { getMyShuStatement } from "@/api/memberPortal";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Table } from "@/components/Table";
import { formatMoney, formatDate } from "@/lib/format";

export function PortalStatementPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["portal", "shu"],
    queryFn: getMyShuStatement,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
        <Card>
          <div className="h-24 animate-pulse bg-gray-100 rounded" />
        </Card>
      </div>
    );
  }

  if (isError) {
    return (
      <p className="text-sm text-red-600">
        Failed to load your SHU statement.
      </p>
    );
  }

  const payouts = data ?? [];
  const totalReceived = payouts.reduce(
    (s, p) => s + parseFloat(p.net_payout),
    0
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-800">SHU Statement</h1>
        <p className="text-sm text-gray-500">
          Your share of the cooperative's annual surplus
        </p>
      </div>

      {payouts.length === 0 ? (
        <Card>
          <div className="py-8 text-center">
            <p className="text-sm text-gray-500">
              No SHU distribution has been made to you yet.
            </p>
            <p className="text-xs text-gray-400 mt-2">
              SHU is calculated once per year after the AGM.
            </p>
          </div>
        </Card>
      ) : (
        <>
          {/* Total card */}
          <Card title="Total Received (all years)">
            <p className="text-3xl font-bold text-green-700">
              ${formatMoney(totalReceived.toFixed(2))}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Across {payouts.length} fiscal year
              {payouts.length === 1 ? "" : "s"}
            </p>
          </Card>

          {/* Per-year table */}
          <Card title="Distribution History">
            <Table
              headers={[
                "Fiscal Year",
                "Jasa Simpanan",
                "Jasa Bunga",
                "Total Payout",
                "Status",
              ]}
              empty={false}
            >
              {payouts.map((p) => (
                <tr key={p.id} className="border-b border-gray-100">
                  <td className="py-3 px-2 text-xs">
                    {formatDate(p.fiscal_year_start)} –{" "}
                    {formatDate(p.fiscal_year_end)}
                  </td>
                  <td className="py-3 px-2 text-sm">
                    ${formatMoney(p.jasa_simpanan_gross)}
                  </td>
                  <td className="py-3 px-2 text-sm">
                    ${formatMoney(p.jasa_bunga_gross)}
                  </td>
                  <td className="py-3 px-2 font-semibold">
                    ${formatMoney(p.net_payout)}
                  </td>
                  <td className="py-3 px-2">
                    <Badge value={p.status} />
                  </td>
                </tr>
              ))}
            </Table>
          </Card>

          {/* Explanation */}
          <div className="bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded-lg p-4">
            <p className="font-medium mb-1">How SHU works</p>
            <p className="mb-1">
              <strong>Jasa Simpanan</strong> rewards you for the length of time
              and amount you kept in the cooperative. Money saved earlier in
              the year earns a higher weight.
            </p>
            <p>
              <strong>Jasa Bunga</strong> refunds a portion of the loan
              interest you paid during the year.
            </p>
          </div>
        </>
      )}
    </div>
  );
}