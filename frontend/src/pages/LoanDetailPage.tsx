import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getLoan, listRepayments, LoanRepayment } from "@/api/loans";
import { useAuth } from "@/auth/useAuth";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Table } from "@/components/Table";
import { formatMoney, formatDate } from "@/lib/format";
import { ManualRepaymentModal } from "./loans/ManualRepaymentModal";
import { ScheduledRepaymentModal } from "./loans/ScheduledRepaymentModal";
import { ReverseModal } from "@/components/ReverseModal";

export function LoanDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { profile } = useAuth();
  const [manualOpen, setManualOpen] = useState(false);
  const [scheduledOpen, setScheduledOpen] = useState(false);
  const [reverseTarget, setReverseTarget] = useState<LoanRepayment | null>(null);

  const loanQuery = useQuery({
    queryKey: ["loan", id],
    queryFn: () => getLoan(id!),
    enabled: !!id,
  });

  const repaymentsQuery = useQuery({
    queryKey: ["repayments", id],
    queryFn: () => listRepayments(id!),
    enabled: !!id,
  });

  if (loanQuery.isLoading) {
    return <div className="p-6 text-sm text-gray-500">Loading…</div>;
  }
  if (loanQuery.isError || !loanQuery.data) {
    return <div className="p-6 text-sm text-red-600">Loan not found.</div>;
  }

  const loan = loanQuery.data;
  const repayments = repaymentsQuery.data ?? [];

  const canMake =
    profile?.role === "MAKER" || profile?.role === "SUPERADMIN";
  const canRepay = canMake && loan.status === "DISBURSED";

  const interestDueThisMonth =
    parseFloat(loan.principal_outstanding) *
    parseFloat(loan.monthly_rate);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link to="/loans" className="text-sm text-brand-600 hover:underline">
            ← Back to Loans
          </Link>
          <h1 className="text-2xl font-bold text-gray-800 mt-2">
            Loan · {loan.member_number}
          </h1>
          <p className="text-sm text-gray-500 font-mono">{loan.id}</p>
        </div>
        <Badge value={loan.status} />
      </div>

      {/* Actions */}
      {canRepay && (
        <div className="flex gap-2">
          <Button onClick={() => setScheduledOpen(true)}>
            Record Scheduled Installment
          </Button>
          <Button variant="secondary" onClick={() => setManualOpen(true)}>
            Record Manual Repayment
          </Button>
        </div>
      )}

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card title="Original Principal">
          <p className="text-2xl font-bold text-gray-800">
            ${formatMoney(loan.principal_original)}
          </p>
        </Card>
        <Card title="Outstanding">
          <p className="text-2xl font-bold text-orange-700">
            ${formatMoney(loan.principal_outstanding)}
          </p>
        </Card>
        <Card title="Monthly Rate">
          <p className="text-2xl font-bold text-gray-800">
            {formatMoney((parseFloat(loan.monthly_rate) * 100).toFixed(2))}%
          </p>
          <p className="text-xs text-gray-500 mt-1">
            ≈ ${formatMoney(interestDueThisMonth.toFixed(2))}/mo interest
          </p>
        </Card>
        <Card title="Term">
          <p className="text-2xl font-bold text-gray-800">
            {loan.term_months} mo
          </p>
        </Card>
      </div>

      {/* Details */}
      <Card title="Loan Details">
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3 text-sm">
          <Row label="Member" value={loan.member_number} />
          <Row label="Purpose" value={loan.purpose || "—"} />
          <Row label="Disbursed" value={formatDate(loan.disbursed_date)} />
          <Row label="Created" value={formatDate(loan.created_at)} />
        </dl>
      </Card>

      {/* Repayment history */}
      <Card title="Repayment History">
        {repaymentsQuery.isLoading && (
          <p className="text-sm text-gray-500 py-4 text-center">Loading…</p>
        )}
        {!repaymentsQuery.isLoading && (
          <Table
            headers={[
              "Date",
              "Mode",
              "Principal",
              "Interest",
              "Total",
              "Status",
              "Actions",
            ]}
            empty={repayments.length === 0}
          >
            {repayments.map((r) => {
              const total =
                parseFloat(r.principal_paid) + parseFloat(r.interest_paid);
              return (
                <tr
                  key={r.id}
                  className="border-b border-gray-100 hover:bg-gray-50"
                >
                  <td className="py-2 px-2 text-xs text-gray-500">
                    {formatDate(r.payment_date)}
                  </td>
                  <td className="py-2 px-2">
                    <Badge value={r.mode} />
                  </td>
                  <td className="py-2 px-2">
                    ${formatMoney(r.principal_paid)}
                  </td>
                  <td className="py-2 px-2">
                    ${formatMoney(r.interest_paid)}
                  </td>
                  <td className="py-2 px-2 font-medium">
                    ${formatMoney(total.toFixed(2))}
                  </td>
                  <td className="py-2 px-2">
                    <Badge value={r.status} />
                  </td>
                  <td className="py-2 px-2">
                    {r.status === "COMPLETED" && r.journal_entry && (
                      <button
                        onClick={() => setReverseTarget(r)}
                        className="text-red-600 hover:underline text-xs"
                      >
                        Reverse
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </Table>
        )}
      </Card>

      <ManualRepaymentModal
        loan={loan}
        open={manualOpen}
        onClose={() => setManualOpen(false)}
      />
      <ScheduledRepaymentModal
        loan={loan}
        open={scheduledOpen}
        onClose={() => setScheduledOpen(false)}
      />
      <ReverseModal
        open={!!reverseTarget}
        onClose={() => setReverseTarget(null)}
        journalEntryId={reverseTarget?.journal_entry ?? null}
        sourceType="LOAN_REPAYMENT"
        sourceId={reverseTarget?.id}
        description={
          reverseTarget
            ? `${reverseTarget.mode} repayment · $${formatMoney(
                (parseFloat(reverseTarget.principal_paid) +
                  parseFloat(reverseTarget.interest_paid)).toFixed(2)
              )}`
            : undefined
        }
      />
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-gray-100 pb-2">
      <dt className="text-gray-500">{label}</dt>
      <dd className="text-gray-800 font-medium text-right">{value}</dd>
    </div>
  );
}
