import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DashboardSummary, getDashboard } from "@/api/reports";
import { Card } from "@/components/Card";
import { formatMoney } from "@/lib/format";

const MONTH_LABELS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

const LOAN_STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  DISBURSED: "Disbursed",
  FULLY_REPAID: "Fully Repaid",
  WRITTEN_OFF: "Written Off",
};

const LOAN_STATUS_COLORS: Record<string, string> = {
  DRAFT: "#9ca3af",
  DISBURSED: "#6366f1",
  FULLY_REPAID: "#10b981",
  WRITTEN_OFF: "#ef4444",
};

function compactMoney(value: number): string {
  if (value >= 1000) return `${(value / 1000).toFixed(1).replace(/\.0$/, "")}k`;
  return String(value);
}

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
          color="blue"
        />

        <DashboardCard
          to="/savings"
          title="Total Savings"
          value={`$${formatMoney(data.savings.total_savings)}`}
          subtitle="Principal + Mandatory + Voluntary"
          color="emerald"
        />

        <DashboardCard
          to="/loans"
          title="Loans Outstanding"
          value={`$${formatMoney(data.loans.outstanding_total)}`}
          subtitle={`${data.loans.disbursed} active loans`}
          color="violet"
        />

        <DashboardCard
          to="/pipeline"
          title="Pipeline"
          value={String(
            data.pipeline.pending_check + data.pipeline.pending_certify
          )}
          subtitle={`${data.pipeline.pending_check} to check · ${data.pipeline.pending_certify} to certify`}
          color="amber"
          highlight={
            data.pipeline.pending_check + data.pipeline.pending_certify > 0
          }
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <CashFlowChart data={data.cash_flow_trend} />
        <LoanPipelineChart data={data.loan_pipeline} />
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
const CARD_ACCENTS = {
  blue: { bar: "bg-blue-500", value: "text-blue-700" },
  emerald: { bar: "bg-emerald-500", value: "text-emerald-700" },
  violet: { bar: "bg-violet-500", value: "text-violet-700" },
  amber: { bar: "bg-amber-500", value: "text-amber-700" },
};

function DashboardCard({
  to,
  title,
  value,
  subtitle,
  highlight,
  color,
}: {
  to: string;
  title: string;
  value: string;
  subtitle?: string;
  highlight?: boolean;
  color: keyof typeof CARD_ACCENTS;
}) {
  const accent = CARD_ACCENTS[color];
  return (
    <Link
      to={to}
      className="block bg-white rounded-lg shadow border border-gray-200 hover:shadow-md hover:border-brand-300 transition overflow-hidden"
    >
      <div className={`h-1 ${accent.bar}`} />
      <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        {highlight && (
          <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
        )}
      </div>
      <div className="p-5">
        <p className={`text-2xl font-bold ${accent.value}`}>{value}</p>
        {subtitle && (
          <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
        )}
      </div>
    </Link>
  );
}

// ====================================================================
// Cash flow trend (deposits vs withdrawals, last 6 months)
// ====================================================================
function CashFlowChart({ data }: { data: DashboardSummary["cash_flow_trend"] }) {
  const chartData = data.map((d) => {
    const [, monthNum] = d.month.split("-");
    return {
      label: MONTH_LABELS[Number(monthNum) - 1],
      Deposits: Number(d.deposits),
      Withdrawals: Number(d.withdrawals),
    };
  });

  return (
    <Card title="Cash Flow Trend">
      <p className="text-xs text-gray-500 -mt-2 mb-3">
        Monthly deposits and withdrawals for the last six months
      </p>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 12, fill: "#6b7280" }}
              axisLine={{ stroke: "#e5e7eb" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "#6b7280" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={compactMoney}
            />
            <Tooltip
              formatter={(value: number) => `$${formatMoney(String(value))}`}
              contentStyle={{ fontSize: 12, borderRadius: 8 }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="Deposits" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Withdrawals" fill="#f97316" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

// ====================================================================
// Loan pipeline (loans grouped by current status)
// ====================================================================
function LoanPipelineChart({ data }: { data: DashboardSummary["loan_pipeline"] }) {
  const total = data.reduce((sum, d) => sum + d.count, 0);
  const chartData = data
    .filter((d) => d.count > 0)
    .map((d) => ({ name: LOAN_STATUS_LABELS[d.status], status: d.status, value: d.count }));

  return (
    <Card
      title="Loan Pipeline"
      action={
        <Link to="/loans" className="text-xs text-brand-600 hover:underline">
          View loans →
        </Link>
      }
    >
      <p className="text-xs text-gray-500 -mt-2 mb-3">
        Loans by current status
      </p>
      {total === 0 ? (
        <p className="text-sm text-gray-500 py-16 text-center">
          No loans originated yet.
        </p>
      ) : (
        <div className="h-64 relative">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={2}
              >
                {chartData.map((entry) => (
                  <Cell key={entry.status} fill={LOAN_STATUS_COLORS[entry.status]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number, name: string) => [`${value} loans`, name]}
                contentStyle={{ fontSize: 12, borderRadius: 8 }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none -mt-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-800">{total}</p>
              <p className="text-xs text-gray-500">total loans</p>
            </div>
          </div>
        </div>
      )}
    </Card>
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