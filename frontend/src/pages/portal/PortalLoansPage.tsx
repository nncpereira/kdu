import { useQuery } from "@tanstack/react-query";
import { getMyLoans } from "@/api/memberPortal";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { formatMoney, formatDate } from "@/lib/format";

export function PortalLoansPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["portal", "loans"],
    queryFn: getMyLoans,
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
      <p className="text-sm text-red-600">Failed to load your loans.</p>
    );
  }

  const loans = data ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-800">My Loans</h1>
        <p className="text-sm text-gray-500">
          Active and historical loans from the cooperative
        </p>
      </div>

      {loans.length === 0 ? (
        <Card>
          <div className="py-8 text-center">
            <p className="text-sm text-gray-500">
              You have no loans with the cooperative.
            </p>
            <p className="text-xs text-gray-400 mt-2">
              Visit the office to apply for a loan.
            </p>
          </div>
        </Card>
      ) : (
        loans.map((loan) => (
          <Card key={loan.id}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-lg font-semibold text-gray-800">
                  ${formatMoney(loan.principal_original)}
                </p>
                <p className="text-xs text-gray-500">
                  {loan.purpose || "General purpose"}
                </p>
              </div>
              <Badge value={loan.status} />
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-xs text-gray-500">Outstanding</p>
                <p className="font-semibold text-orange-700">
                  ${formatMoney(loan.principal_outstanding)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Monthly rate</p>
                <p className="font-semibold">
                  {formatMoney(
                    (parseFloat(loan.monthly_rate) * 100).toFixed(2)
                  )}
                  %
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Term</p>
                <p className="font-semibold">{loan.term_months} months</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Disbursed</p>
                <p className="font-semibold">
                  {loan.disbursed_date
                    ? formatDate(loan.disbursed_date)
                    : "—"}
                </p>
              </div>
            </div>

            {loan.status === "DISBURSED" && (
              <div className="mt-4 pt-4 border-t border-gray-100 text-xs text-gray-500">
                Approximate interest this month: $
                {formatMoney(
                  (
                    parseFloat(loan.principal_outstanding) *
                    parseFloat(loan.monthly_rate)
                  ).toFixed(2)
                )}
              </div>
            )}
          </Card>
        ))
      )}
    </div>
  );
}