import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMyDashboard } from "@/api/memberPortal";
import { Card } from "@/components/Card";
import { formatMoney, formatDate } from "@/lib/format";

export function PortalDashboardPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["portal", "dashboard"],
    queryFn: getMyDashboard,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[0, 1, 2].map((i) => (
            <Card key={i}>
              <div className="h-16 animate-pulse bg-gray-100 rounded" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="p-4 text-sm text-red-600">
        Failed to load your dashboard. Please refresh the page.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-800">
          Welcome, {data.member.full_name}
        </h1>
        <p className="text-sm text-gray-500">
          Member since {formatDate(data.member.date_joined)} ·{" "}
          <span className="font-mono">{data.member.membership_number}</span>
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SummaryCard
          to="/portal/savings"
          title="Total Savings"
          value={`$${formatMoney(data.total_savings)}`}
          subtitle={`Capital $${formatMoney(data.capital)} · Voluntary $${formatMoney(data.voluntary)}`}
        />
        <SummaryCard
          to="/portal/loans"
          title="Loans Outstanding"
          value={`$${formatMoney(data.loans.outstanding_total)}`}
          subtitle={
            data.loans.active_count === 0
              ? "No active loans"
              : `${data.loans.active_count} active loan${data.loans.active_count === 1 ? "" : "s"}`
          }
        />
        <SummaryCard
          to="/portal/statement"
          title="SHU Statement"
          value="View"
          subtitle="Annual surplus distribution"
        />
      </div>

      {/* Recent activity */}
      <Card
        title="Recent Activity"
        action={
          <Link
            to="/portal/savings"
            className="text-xs text-brand-600 hover:underline"
          >
            View all →
          </Link>
        }
      >
        {data.recent_activity.length === 0 ? (
          <p className="text-sm text-gray-500 py-6 text-center">
            No transactions yet. Deposits made at the office will appear here.
          </p>
        ) : (
          <ul className="divide-y divide-gray-100">
            {data.recent_activity.map((a) => (
              <li
                key={a.id}
                className="py-3 flex items-center justify-between"
              >
                <div>
                  <p className="text-sm font-medium text-gray-800">
                    {a.type === "DEPOSIT" ? "Deposit" : "Withdrawal"}
                  </p>
                  <p className="text-xs text-gray-500">
                    {new Date(a.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">
                    ${formatMoney(a.amount)}
                  </p>
                  <p className="text-xs text-gray-500">{a.status}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <div className="bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded-lg p-4">
        <p className="font-medium mb-1">Need help?</p>
        <p>
          For deposits, withdrawals, and loan applications, please visit the
          cooperative office during business hours. Your account is protected
          by the cooperative's ledger — every transaction is recorded and
          auditable.
        </p>
      </div>
    </div>
  );
}

function SummaryCard({
  to,
  title,
  value,
  subtitle,
}: {
  to: string;
  title: string;
  value: string;
  subtitle: string;
}) {
  return (
    <Link
      to={to}
      className="block bg-white rounded-lg shadow border border-gray-200 hover:shadow-md hover:border-brand-300 transition"
    >
      <div className="px-5 py-3 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
      </div>
      <div className="p-5">
        <p className="text-2xl font-bold text-gray-800">{value}</p>
        <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
      </div>
    </Link>
  );
}