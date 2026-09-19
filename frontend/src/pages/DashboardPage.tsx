import { useQuery } from "@tanstack/react-query";
import { getDashboard } from "@/api/reports";
import { Card } from "@/components/Card";
import { formatMoney } from "@/lib/format";

export function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  });

  if (isLoading || !data) return <div className="p-6">Loading…</div>;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
        <p className="text-sm text-gray-500">Today’s cooperative snapshot</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card title="Members">
          <p className="text-2xl font-bold">{data.members.active}</p>
          <p className="text-xs text-gray-500">
            Active · {data.members.pending} pending
          </p>
        </Card>

        <Card title="Voluntary Savings">
          <p className="text-2xl font-bold">
            ${formatMoney(data.savings.voluntary_total)}
          </p>
        </Card>

        <Card title="Loans Outstanding">
          <p className="text-2xl font-bold">
            ${formatMoney(data.loans.outstanding_total)}
          </p>
          <p className="text-xs text-gray-500">
            {data.loans.disbursed} active
          </p>
        </Card>

        <Card title="Pipeline">
          <p className="text-2xl font-bold">
            {data.pipeline.pending_check + data.pipeline.pending_certify}
          </p>
          <p className="text-xs text-gray-500">
            {data.pipeline.pending_check} check ·{" "}
            {data.pipeline.pending_certify} certify
          </p>
        </Card>
      </div>

      <Card title="Recent Activity">
        <table className="w-full text-sm">
          <thead className="text-left text-gray-500">
            <tr>
              <th className="pb-2">Type</th>
              <th className="pb-2">Member</th>
              <th className="pb-2">Amount</th>
              <th className="pb-2">Date</th>
            </tr>
          </thead>
          <tbody>
            {data.recent_activity.map((a, i) => (
              <tr key={i} className="border-t border-gray-100">
                <td className="py-2">{a.type}</td>
                <td className="py-2">{a.member_number}</td>
                <td className="py-2">${formatMoney(a.amount)}</td>
                <td className="py-2 text-gray-500">
                  {new Date(a.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}