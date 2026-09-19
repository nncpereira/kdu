import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getDashboard } from "@/api/reports";
import { Card } from "@/components/Card";
import { formatMoney } from "@/lib/format";

export function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  });

  if (isLoading || !data) {
    return (
      <div className="p-6 space-y-6">
        <SkeletonHeader />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => (
            <Card key={i}>
              <div className="h-16 animate-pulse bg-gray-100 rounded" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
        <p className="text-sm text-gray-500">Today's cooperative snapshot</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <DashboardCard
          to="/members"
          title="Members"
          value={String(data.members.active)}
          subtitle={`${data.members.pending} pending onboarding`}
        />

        <DashboardCard
          to="/savings"
          title="Voluntary Savings"
          value={`$${formatMoney(data.savings.voluntary_total)}`}
          subtitle="Across all members"
        />

        <DashboardCard
          to="/loans"
          title="Loans Outstanding"
          value={`$${formatMoney(data.loans.outstanding_total)}`}
          subtitle={`${data.loans.disbursed} active loans`}
        />

        <DashboardCard
          to="/pipeline"
          title="Pipeline"
          value={String(
            data.pipeline.pending_check + data.pipeline.pending_certify
          )}
          subtitle={`${data.pipeline.pending_check} to check · ${data.pipeline.pending_certify} to certify`}
          highlight={
            data.pipeline.pending_check + data.pipeline.pending_certify > 0
          }
        />
      </div>

      <Card
        title="Recent Activity"
        action={
          <Link
            to="/savings"
            className="text-xs text-brand-600 hover:underline"
          >
            View all →
          </Link>
        }
      >
        {data.recent_activity.length === 0 ? (
          <p className="text-sm text-gray-500 py-6 text-center">
            No recent activity.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead className="text-left text-gray-500">
              <tr>
                <th className="pb-2">Type</th>
                <th className="pb-2">Member</th>
                <th className="pb-2 text-right">Amount</th>
                <th className="pb-2 text-right">Date</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_activity.map((a, i) => (
                <tr key={i} className="border-t border-gray-100">
                  <td className="py-2">
                    <span className="inline-block px-2 py-0.5 text-xs font-medium rounded bg-gray-100 text-gray-700">
                      {a.type}
                    </span>
                  </td>
                  <td className="py-2 font-mono text-xs">
                    {a.member_number}
                  </td>
                  <td className="py-2 text-right font-medium">
                    ${formatMoney(a.amount)}
                  </td>
                  <td className="py-2 text-right text-gray-500 text-xs">
                    {new Date(a.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}

// ====================================================================
// Clickable dashboard card
// ====================================================================
function DashboardCard({
  to,
  title,
  value,
  subtitle,
  highlight,
}: {
  to: string;
  title: string;
  value: string;
  subtitle?: string;
  highlight?: boolean;
}) {
  return (
    <Link
      to={to}
      className="block bg-white rounded-lg shadow border border-gray-200 hover:shadow-md hover:border-brand-300 transition"
    >
      <div className="px-5 py-3 border-b border-gray-200 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        {highlight && (
          <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
        )}
      </div>
      <div className="p-5">
        <p className="text-2xl font-bold text-gray-800">{value}</p>
        {subtitle && (
          <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
        )}
      </div>
    </Link>
  );
}

function SkeletonHeader() {
  return (
    <div>
      <div className="h-6 w-32 bg-gray-200 rounded animate-pulse" />
      <div className="h-4 w-48 bg-gray-200 rounded mt-2 animate-pulse" />
    </div>
  );
}