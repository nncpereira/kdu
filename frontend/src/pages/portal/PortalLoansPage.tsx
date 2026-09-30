import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  getMyLoanRepayments,
  getMyLoans,
  PortalLoan,
} from "@/api/memberPortal";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { formatMoney, formatDate } from "@/lib/format";

export function PortalLoansPage() {
  const [expandedLoanId, setExpandedLoanId] = useState<string | null>(null);
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

            {loan.status !== "DRAFT" && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <button
                  onClick={() =>
                    setExpandedLoanId(
                      expandedLoanId === loan.id ? null : loan.id
                    )
                  }
                  className="text-xs font-medium text-brand-600 hover:underline"
                >
                  {expandedLoanId === loan.id
                    ? "Hide repayment history"
                    : "View repayment history"}
                </button>
                {expandedLoanId === loan.id && (
                  <RepaymentHistory loan={loan} />
                )}
              </div>
            )}
          </Card>
        ))
      )}
    </div>
  );
}

// ====================================================================
// Repayment history (fetched lazily when a loan card is expanded)
// ====================================================================
function RepaymentHistory({ loan }: { loan: PortalLoan }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["portal", "loan-repayments", loan.id],
    queryFn: () => getMyLoanRepayments(loan.id),
  });

  if (isLoading) {
    return (
      <div className="mt-3 h-16 animate-pulse bg-gray-100 rounded" />
    );
  }

  if (isError) {
    return (
      <p className="mt-3 text-xs text-red-600">
        Failed to load repayment history.
      </p>
    );
  }

  const repayments = data ?? [];

  if (repayments.length === 0) {
    return (
      <p className="mt-3 text-xs text-gray-500">
        No repayments recorded yet.
      </p>
    );
  }

  return (
    <table className="w-full text-xs mt-3">
      <thead className="text-left text-gray-500">
        <tr>
          <th className="pb-1">Date</th>
          <th className="pb-1 text-right">Principal</th>
          <th className="pb-1 text-right">Interest</th>
          <th className="pb-1 text-right">Total</th>
        </tr>
      </thead>
      <tbody>
        {repayments.map((r) => (
          <tr key={r.id} className="border-t border-gray-100">
            <td className="py-1.5 text-gray-600">
              {formatDate(r.payment_date)}
            </td>
            <td className="py-1.5 text-right">
              ${formatMoney(r.principal_paid)}
            </td>
            <td className="py-1.5 text-right">
              ${formatMoney(r.interest_paid)}
            </td>
            <td className="py-1.5 text-right font-semibold">
              $
              {formatMoney(
                (
                  parseFloat(r.principal_paid) + parseFloat(r.interest_paid)
                ).toFixed(2)
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}