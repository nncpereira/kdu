import { useState } from "react";
import { TableSkeleton } from "@/components/Skeleton";
import { useQuery } from "@tanstack/react-query";
import {
  getTrialBalance,
  getIncomeStatement,
  getBalanceSheet,
  getSurplusDistribution,
} from "@/api/reports";
import { listFiscalYears } from "@/api/shu";
import { listReversals } from "@/api/reversals";
import { Card } from "@/components/Card";
import { Table } from "@/components/Table";
import { DatePicker } from "@/components/DatePicker";
import { Badge } from "@/components/Badge";
import { formatMoney, formatDate } from "@/lib/format";
import clsx from "clsx";
import { DownloadPdfButton } from "@/components/DownloadPdfButton";

type Tab = "trial-balance" | "income-statement" | "balance-sheet" | "surplus" | "reversals";

const TABS: { id: Tab; label: string }[] = [
  { id: "trial-balance", label: "Trial Balance" },
  { id: "income-statement", label: "Income Statement" },
  { id: "balance-sheet", label: "Balance Sheet" },
  { id: "surplus", label: "Surplus Distribution" },
  { id: "reversals", label: "Reversals" },
];

export function ReportsPage() {
  const [tab, setTab] = useState<Tab>("trial-balance");

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Reports</h1>
        <p className="text-sm text-gray-500">
          Financial statements derived from the immutable ledger
        </p>
      </div>

      {/* Tab bar */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-1 -mb-px">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={clsx(
                "px-4 py-2 text-sm font-medium border-b-2 transition",
                tab === t.id
                  ? "border-brand-600 text-brand-700"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>

      {tab === "trial-balance" && <TrialBalanceTab />}
      {tab === "income-statement" && <IncomeStatementTab />}
      {tab === "balance-sheet" && <BalanceSheetTab />}
      {tab === "surplus" && <SurplusDistributionTab />}
      {tab === "reversals" && <ReversalsTab />}
    </div>
  );
}

// ====================================================================
// Trial Balance
// ====================================================================
function TrialBalanceTab() {
  const [asOf, setAsOf] = useState(() => new Date().toISOString().slice(0, 10));

  const { data, isLoading, isError } = useQuery({
    queryKey: ["reports", "trial-balance", asOf],
    queryFn: () => getTrialBalance(asOf),
    enabled: !!asOf,
  });

  const totalDebit = data?.reduce(
    (s, r) => s + parseFloat(r.debit),
    0
  ) ?? 0;
  const totalCredit = data?.reduce(
    (s, r) => s + parseFloat(r.credit),
    0
  ) ?? 0;
  const balanced = Math.abs(totalDebit - totalCredit) < 0.01;

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-wrap items-end gap-4">
          <DatePicker label="As of" value={asOf} onChange={setAsOf} />
          <DownloadPdfButton
            url={`/reports/trial-balance/pdf/?as_of=${asOf}`}
            filename={`trial-balance-${asOf}.pdf`}
            disabled={!asOf}
          />
          <div className="ml-auto flex gap-4 text-sm">
            <div>
              <span className="text-gray-500">Total Debits: </span>
              <span className="font-semibold">
                ${formatMoney(totalDebit.toFixed(2))}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Total Credits: </span>
              <span className="font-semibold">
                ${formatMoney(totalCredit.toFixed(2))}
              </span>
            </div>
            <div
              className={clsx(
                "px-2 py-1 rounded text-xs font-medium",
                balanced
                  ? "bg-green-100 text-green-800"
                  : "bg-red-100 text-red-800"
              )}
            >
              {balanced ? "Balanced" : "UNBALANCED"}
            </div>
          </div>
        </div>
      </Card>

      <Card title="Trial Balance">
        {isLoading && (
          <TableSkeleton rows={8} cols={6} />
        )}
        {isError && (
          <p className="text-sm text-red-600 py-8 text-center">
            Failed to load.
          </p>
        )}
        {data && (
          <Table
            headers={[
              "Code",
              "Account",
              "Type",
              "Debit",
              "Credit",
              "Net",
            ]}
            empty={data.length === 0}
          >
            {data.map((r) => (
              <tr key={r.account_code} className="border-b border-gray-100">
                <td className="py-2 px-2 font-mono text-xs">
                  {r.account_code}
                </td>
                <td className="py-2 px-2">{r.account_name}</td>
                <td className="py-2 px-2 text-xs text-gray-500">
                  {r.account_type}
                </td>
                <td className="py-2 px-2 text-right">
                  ${formatMoney(r.debit)}
                </td>
                <td className="py-2 px-2 text-right">
                  ${formatMoney(r.credit)}
                </td>
                <td className="py-2 px-2 text-right font-medium">
                  ${formatMoney(r.net)}
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </div>
  );
}

// ====================================================================
// Income Statement
// ====================================================================
function IncomeStatementTab() {
  const today = new Date().toISOString().slice(0, 10);
  const yearAgo = new Date(new Date().getFullYear() - 1, 6, 1)
    .toISOString()
    .slice(0, 10);

  const [start, setStart] = useState(yearAgo);
  const [end, setEnd] = useState(today);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["reports", "income-statement", start, end],
    queryFn: () => getIncomeStatement(start, end),
    enabled: !!start && !!end,
  });

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-wrap items-end gap-4">
        <DatePicker label="From" value={start} onChange={setStart} />
        <DatePicker label="To" value={end} onChange={setEnd} />
        <DownloadPdfButton
          url={`/reports/income-statement/pdf/?start=${start}&end=${end}`}
          filename={`income-statement-${start}-${end}.pdf`}
          disabled={!start || !end}
        />
      </div>
      </Card>

      {isLoading && (
        <Card>
          <TableSkeleton rows={8} cols={6} />
        </Card>
      )}
      {isError && (
        <Card>
          <p className="text-sm text-red-600 py-8 text-center">
            Failed to load.
          </p>
        </Card>
      )}

      {data && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card title="Total Revenue">
              <p className="text-2xl font-bold text-green-700">
                ${formatMoney(data.total_revenue)}
              </p>
            </Card>
            <Card title="Total Expenses">
              <p className="text-2xl font-bold text-red-700">
                ${formatMoney(data.total_expenses)}
              </p>
            </Card>
            <Card title="Net Surplus">
              <p className="text-2xl font-bold text-gray-800">
                ${formatMoney(data.net_surplus)}
              </p>
            </Card>
          </div>

          <Card title="Revenue">
            <Table
              headers={["Code", "Account", "Credit"]}
              empty={data.revenue.length === 0}
            >
              {data.revenue.map((r) => (
                <tr key={r.account_code} className="border-b border-gray-100">
                  <td className="py-2 px-2 font-mono text-xs">
                    {r.account_code}
                  </td>
                  <td className="py-2 px-2">{r.account_name}</td>
                  <td className="py-2 px-2 text-right">
                    ${formatMoney(r.credit)}
                  </td>
                </tr>
              ))}
            </Table>
          </Card>

          <Card title="Expenses">
            <Table
              headers={["Code", "Account", "Debit"]}
              empty={data.expenses.length === 0}
            >
              {data.expenses.map((r) => (
                <tr key={r.account_code} className="border-b border-gray-100">
                  <td className="py-2 px-2 font-mono text-xs">
                    {r.account_code}
                  </td>
                  <td className="py-2 px-2">{r.account_name}</td>
                  <td className="py-2 px-2 text-right">
                    ${formatMoney(r.debit)}
                  </td>
                </tr>
              ))}
            </Table>
          </Card>
        </>
      )}
    </div>
  );
}

// ====================================================================
// Balance Sheet
// ====================================================================
function BalanceSheetTab() {
  const [asOf, setAsOf] = useState(() => new Date().toISOString().slice(0, 10));

  const { data, isLoading, isError } = useQuery({
    queryKey: ["reports", "balance-sheet", asOf],
    queryFn: () => getBalanceSheet(asOf),
    enabled: !!asOf,
  });

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-wrap items-end gap-4">
          <DatePicker label="As of" value={asOf} onChange={setAsOf} />
          <DownloadPdfButton
            url={`/reports/balance-sheet/pdf/?as_of=${asOf}`}
            filename={`balance-sheet-${asOf}.pdf`}
            disabled={!asOf}
          />
          {data && (
            <div
              className={clsx(
                "ml-auto px-2 py-1 rounded text-xs font-medium",
                data.balanced
                  ? "bg-green-100 text-green-800"
                  : "bg-red-100 text-red-800"
              )}
            >
              {data.balanced
                ? "Assets = Liabilities + Equity"
                : "UNBALANCED"}
            </div>
          )}
        </div>
      </Card>

      {isLoading && (
        <Card>
          <TableSkeleton rows={8} cols={6} />
        </Card>
      )}
      {isError && (
        <Card>
          <p className="text-sm text-red-600 py-8 text-center">
            Failed to load.
          </p>
        </Card>
      )}

      {data && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card title="Total Assets">
              <p className="text-2xl font-bold text-gray-800">
                ${formatMoney(data.total_assets)}
              </p>
            </Card>
            <Card title="Total Liabilities">
              <p className="text-2xl font-bold text-gray-800">
                ${formatMoney(data.total_liabilities)}
              </p>
            </Card>
            <Card title="Total Equity">
              <p className="text-2xl font-bold text-gray-800">
                ${formatMoney(data.total_equity)}
              </p>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card title="Assets">
              <Table
                headers={["Account", "Amount"]}
                empty={data.assets.length === 0}
              >
                {data.assets.map((r) => (
                  <tr key={r.account_code} className="border-b border-gray-100">
                    <td className="py-2 px-2">
                      <span className="font-mono text-xs text-gray-500 mr-2">
                        {r.account_code}
                      </span>
                      {r.account_name}
                    </td>
                    <td className="py-2 px-2 text-right">
                      ${formatMoney(r.net)}
                    </td>
                  </tr>
                ))}
              </Table>
            </Card>

            <Card title="Liabilities">
              <Table
                headers={["Account", "Amount"]}
                empty={data.liabilities.length === 0}
              >
                {data.liabilities.map((r) => (
                  <tr key={r.account_code} className="border-b border-gray-100">
                    <td className="py-2 px-2">
                      <span className="font-mono text-xs text-gray-500 mr-2">
                        {r.account_code}
                      </span>
                      {r.account_name}
                    </td>
                    <td className="py-2 px-2 text-right">
                      ${formatMoney(
                        (parseFloat(r.credit) - parseFloat(r.debit)).toFixed(2)
                      )}
                    </td>
                  </tr>
                ))}
              </Table>
            </Card>
          </div>

          <Card title="Equity">
            <Table
              headers={["Account", "Amount"]}
              empty={data.equity.length === 0}
            >
              {data.equity.map((r) => (
                <tr key={r.account_code} className="border-b border-gray-100">
                  <td className="py-2 px-2">
                    <span className="font-mono text-xs text-gray-500 mr-2">
                      {r.account_code}
                    </span>
                    {r.account_name}
                  </td>
                  <td className="py-2 px-2 text-right">
                    ${formatMoney(
                      (parseFloat(r.credit) - parseFloat(r.debit)).toFixed(2)
                    )}
                  </td>
                </tr>
              ))}
            </Table>
          </Card>
        </>
      )}
    </div>
  );
}

// ====================================================================
// Surplus Distribution
// ====================================================================
function SurplusDistributionTab() {
  const { data: fiscalYears, isLoading: fysLoading } = useQuery({
    queryKey: ["shu", "fiscal-years"],
    queryFn: listFiscalYears,
  });

  const [fyId, setFyId] = useState<string>("");

  // Auto-select the first (most recent) fiscal year
  if (!fyId && fiscalYears && fiscalYears.length > 0) {
    setFyId(fiscalYears[0].id);
  }

  const { data, isLoading, isError } = useQuery({
    queryKey: ["reports", "surplus", fyId],
    queryFn: () => getSurplusDistribution(fyId),
    enabled: !!fyId,
  });

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Fiscal Year
            </label>
            <select
              value={fyId}
              onChange={(e) => setFyId(e.target.value)}
              className="border border-gray-300 rounded px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              {fysLoading && <option>Loading…</option>}
              {fiscalYears?.map((fy) => (
                <option key={fy.id} value={fy.id}>
                  {formatDate(fy.year_start)} – {formatDate(fy.year_end)}{" "}
                  ({fy.status})
                </option>
              ))}
            </select>
          </div>
          {fyId && (
            <DownloadPdfButton
              url={`/reports/surplus-distribution/${fyId}/pdf/`}
              filename={`shu-${fyId}.pdf`}
            />
          )}
        </div>
      </Card>

      {isLoading && (
        <Card>
          <TableSkeleton rows={8} cols={6} />
        </Card>
      )}

      {!isLoading && !isError && !data && (
        <Card>
          <p className="text-sm text-gray-500 py-8 text-center">
            No SHU calculation exists for this fiscal year yet.
          </p>
        </Card>
      )}

      {data && (
        <>
          <Card>
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-gray-500">
                Status of the calculation:
              </p>
              <Badge value={data.status} />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <AllocBox
                label="Reserva Legal"
                amount={data.reserva_legal_amt}
                color="text-green-700"
              />
              <AllocBox
                label="Admin & Operational Fund"
                amount={data.admin_fund_amt}
                color="text-blue-700"
              />
              <AllocBox
                label="Jasa Simpanan"
                amount={data.jasa_simpanan_amt}
                color="text-purple-700"
              />
              <AllocBox
                label="Jasa Bunga"
                amount={data.jasa_bunga_amt}
                color="text-orange-700"
              />
            </div>
          </Card>

          <Card title="Distribution Summary">
            <p className="text-sm text-gray-600 leading-relaxed">
              The gross surplus has been allocated according to the
              AGM-approved split. The Reserva Legal and Admin Fund have been
              credited to their statutory equity accounts, and the Jasa
              Simpanan and Jasa Bunga pools have been distributed to members
              according to the age-weighted savings and interest-paid ratios.
            </p>
            <p className="text-sm text-gray-600 mt-3 leading-relaxed">
              Full details, including per-member payouts, are available on the
              SHU page for the corresponding fiscal year.
            </p>
          </Card>
        </>
      )}
    </div>
  );
}

function ReversalsTab() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["reversals"],
    queryFn: listReversals,
  });

  return (
    <Card title="Reversal History">
      {isLoading && (
        <TableSkeleton rows={8} cols={6} />
      )}
      {isError && (
        <p className="text-sm text-red-600 py-8 text-center">
          Failed to load reversal history.
        </p>
      )}
      {!isLoading && !isError && data && (
        <Table
          headers={[
            "Requested",
            "Original Entry",
            "Reason",
            "Requested by",
            "Status",
          ]}
          empty={data.length === 0}
        >
          {data.map((r) => (
            <tr key={r.id} className="border-b border-gray-100">
              <td className="py-2 px-2 text-xs text-gray-500">
                {new Date(r.created_at).toLocaleDateString()}
              </td>
              <td className="py-2 px-2 text-sm">
                {r.original_description}
                <span className="block text-xs text-gray-400">
                  {new Date(r.original_entry_date).toLocaleDateString()}
                </span>
              </td>
              <td className="py-2 px-2 text-sm text-gray-700 max-w-md truncate">
                {r.reason}
              </td>
              <td className="py-2 px-2 text-xs text-gray-600">
                {r.maker_username ?? "—"}
              </td>
              <td className="py-2 px-2">
                <Badge value={r.status} />
              </td>
            </tr>
          ))}
        </Table>
      )}
    </Card>
  );
}

function AllocBox({
  label,
  amount,
  color,
}: {
  label: string;
  amount: string;
  color: string;
}) {
  return (
    <div className="bg-gray-50 rounded p-3">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={clsx("text-xl font-bold mt-1", color)}>
        ${formatMoney(amount)}
      </p>
    </div>
  );
}
