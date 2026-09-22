import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import clsx from "clsx";

import {
  listAuditEntries,
  listLedgerActivity,
  auditExportUrl,
  AuditFilters,
} from "@/api/audit";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Badge } from "@/components/Badge";
import { Table } from "@/components/Table";
import { TableSkeleton } from "@/components/Skeleton";
import { DatePicker } from "@/components/DatePicker";
import { downloadBlob } from "@/lib/download";
import { formatMoney, formatDate } from "@/lib/format";

type Tab = "system" | "ledger";

export function AuditPage() {
  const [tab, setTab] = useState<Tab>("system");

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Audit Log</h1>
        <p className="text-sm text-gray-500">
          Complete activity trail — logins, user management, configuration,
          and every certified ledger entry
        </p>
      </div>

      <div className="border-b border-gray-200">
        <nav className="flex gap-1 -mb-px">
          <TabButton active={tab === "system"} onClick={() => setTab("system")}>
            System Audit
          </TabButton>
          <TabButton active={tab === "ledger"} onClick={() => setTab("ledger")}>
            Ledger Activity
          </TabButton>
        </nav>
      </div>

      {tab === "system" && <SystemAuditTab />}
      {tab === "ledger" && <LedgerActivityTab />}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "px-4 py-2 text-sm font-medium border-b-2 transition",
        active
          ? "border-brand-600 text-brand-700"
          : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
      )}
    >
      {children}
    </button>
  );
}

// ====================================================================
// System Audit
// ====================================================================
const ACTION_LABELS: Record<string, string> = {
  LOGIN_SUCCESS: "Login",
  LOGIN_FAILURE: "Login Failed",
  LOGOUT: "Logout",
  USER_CREATED: "User Created",
  USER_DISABLED: "User Disabled",
  USER_ENABLED: "User Enabled",
  USER_PASSWORD_RESET: "Password Reset",
  USER_UPDATED: "User Updated",
  MEMBER_LOGIN_CREATED: "Member Login",
  MEMBER_LOGIN_RESET: "Member PW Reset",
  CONFIG_PROPOSED: "Config Proposed",
  CONFIG_CERTIFIED: "Config Certified",
  CONFIG_REJECTED: "Config Rejected",
  MEMBER_EXIT_REQUESTED: "Exit Requested",
  MEMBER_EXIT_COMPLETED: "Exit Completed",
  REVERSAL_REQUESTED: "Reversal Requested",
  REVERSAL_COMPLETED: "Reversal Completed",
  OTHER: "Other",
};

const ACTION_GROUPS: { label: string; actions: string[] }[] = [
  { label: "All actions", actions: [] },
  {
    label: "Authentication",
    actions: ["LOGIN_SUCCESS", "LOGIN_FAILURE", "LOGOUT"],
  },
  {
    label: "User Management",
    actions: [
      "USER_CREATED",
      "USER_DISABLED",
      "USER_ENABLED",
      "USER_PASSWORD_RESET",
      "USER_UPDATED",
    ],
  },
  {
    label: "Member Logins",
    actions: ["MEMBER_LOGIN_CREATED", "MEMBER_LOGIN_RESET"],
  },
  {
    label: "Governance",
    actions: ["CONFIG_PROPOSED", "CONFIG_CERTIFIED", "CONFIG_REJECTED"],
  },
  {
    label: "Reversals",
    actions: ["REVERSAL_REQUESTED", "REVERSAL_COMPLETED"],
  },
];

function SystemAuditTab() {
  const today = new Date().toISOString().slice(0, 10);
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 3600 * 1000)
    .toISOString()
    .slice(0, 10);

  const [start, setStart] = useState(thirtyDaysAgo);
  const [end, setEnd] = useState(today);
  const [actionGroup, setActionGroup] = useState(0);
  const [exporting, setExporting] = useState(false);

  const filters: AuditFilters = {
    start,
    end,
    limit: 300,
  };

  const { data, isLoading, isError } = useQuery({
    queryKey: ["audit", "log", start, end, actionGroup],
    queryFn: () => listAuditEntries(filters),
  });

  // Client-side filter by action group (server doesn't support multiple actions).
  const rows =
    data?.results.filter((row) => {
      if (actionGroup === 0) return true;
      return ACTION_GROUPS[actionGroup].actions.includes(row.action);
    }) ?? [];

  async function handleExport() {
    setExporting(true);
    try {
      const stamp = new Date().toISOString().slice(0, 10);
      await downloadBlob(
        auditExportUrl({ start, end }),
        `audit-log-${stamp}.csv`,
        "text/csv"
      );
      toast.success("Audit log exported.");
    } catch (e) {
      toast.error("Failed to export.");
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-wrap items-end gap-4">
          <DatePicker label="From" value={start} onChange={setStart} />
          <DatePicker label="To" value={end} onChange={setEnd} />

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Action Group
            </label>
            <select
              value={actionGroup}
              onChange={(e) => setActionGroup(Number(e.target.value))}
              className="border border-gray-300 rounded px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              {ACTION_GROUPS.map((g, i) => (
                <option key={g.label} value={i}>
                  {g.label}
                </option>
              ))}
            </select>
          </div>

          <div className="ml-auto">
            <Button
              variant="secondary"
              onClick={handleExport}
              loading={exporting}
            >
              Export CSV
            </Button>
          </div>
        </div>
      </Card>

      <Card>
        {isError ? (
          <p className="text-sm text-red-600 py-8 text-center">
            Failed to load audit log.
          </p>
        ) : (
          <Table
            headers={[
              "Timestamp",
              "Actor",
              "Action",
              "Target",
              "Description",
              "IP",
            ]}
            empty={!isLoading && rows.length === 0}
          >
            {isLoading ? (
              <TableSkeleton rows={8} cols={6} />
            ) : (
              rows.map((row) => (
                <tr
                  key={row.id}
                  className="border-b border-gray-100 hover:bg-gray-50"
                >
                  <td className="py-2 px-2 text-xs text-gray-500 whitespace-nowrap">
                    {new Date(row.created_at).toLocaleString()}
                  </td>
                  <td className="py-2 px-2">
                    <span className="text-sm font-medium">
                      {row.actor_username ?? "—"}
                    </span>
                    {row.actor_role && (
                      <span className="block text-[10px] text-gray-400 uppercase tracking-wider">
                        {row.actor_role}
                      </span>
                    )}
                  </td>
                  <td className="py-2 px-2">
                    <ActionBadge action={row.action} />
                  </td>
                  <td className="py-2 px-2 text-xs font-mono text-gray-600">
                    {row.target_repr || "—"}
                  </td>
                  <td className="py-2 px-2 text-sm text-gray-700 max-w-md">
                    {row.description}
                  </td>
                  <td className="py-2 px-2 text-xs font-mono text-gray-400">
                    {row.ip_address ?? "—"}
                  </td>
                </tr>
              ))
            )}
          </Table>
        )}

        {data && data.count > data.limit && (
          <p className="text-xs text-gray-500 mt-4 text-center">
            Showing the most recent {data.limit} of {data.count} entries.
            Use the date filter or export to see more.
          </p>
        )}
      </Card>
    </div>
  );
}

function ActionBadge({ action }: { action: string }) {
  const label = ACTION_LABELS[action] ?? action;
  const colorClass = action.endsWith("_FAILURE")
    ? "bg-red-100 text-red-800"
    : action.endsWith("_SUCCESS") || action.endsWith("_CERTIFIED")
    ? "bg-green-100 text-green-800"
    : action.startsWith("LOGIN")
    ? "bg-blue-100 text-blue-800"
    : action.startsWith("USER") || action.startsWith("MEMBER_LOGIN")
    ? "bg-purple-100 text-purple-800"
    : action.startsWith("CONFIG")
    ? "bg-amber-100 text-amber-800"
    : action.startsWith("REVERSAL")
    ? "bg-orange-100 text-orange-800"
    : "bg-gray-100 text-gray-800";

  return (
    <span
      className={clsx(
        "inline-block px-2 py-1 text-xs font-medium rounded whitespace-nowrap",
        colorClass
      )}
    >
      {label}
    </span>
  );
}

// ====================================================================
// Ledger Activity
// ====================================================================
function LedgerActivityTab() {
  const today = new Date().toISOString().slice(0, 10);
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 3600 * 1000)
    .toISOString()
    .slice(0, 10);

  const [start, setStart] = useState(thirtyDaysAgo);
  const [end, setEnd] = useState(today);
  const [reversalsOnly, setReversalsOnly] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["audit", "ledger", start, end, reversalsOnly],
    queryFn: () =>
      listLedgerActivity({
        start,
        end,
        limit: 300,
        reversals_only: reversalsOnly ? "1" : undefined,
      }),
  });

  const rows = data?.results ?? [];

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-wrap items-end gap-4">
          <DatePicker label="From" value={start} onChange={setStart} />
          <DatePicker label="To" value={end} onChange={setEnd} />

          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={reversalsOnly}
              onChange={(e) => setReversalsOnly(e.target.checked)}
              className="rounded border-gray-300"
            />
            Reversals only
          </label>
        </div>
      </Card>

      <Card>
        {isError ? (
          <p className="text-sm text-red-600 py-8 text-center">
            Failed to load ledger activity.
          </p>
        ) : (
          <Table
            headers={[
              "Entry Date",
              "Description",
              "Maker",
              "Certifier",
              "Amount",
              "Status",
            ]}
            empty={!isLoading && rows.length === 0}
          >
            {isLoading ? (
              <TableSkeleton rows={8} cols={6} />
            ) : (
              rows.map((row) => (
                <tr
                  key={row.id}
                  className="border-b border-gray-100 hover:bg-gray-50"
                >
                  <td className="py-2 px-2 text-xs text-gray-500 whitespace-nowrap">
                    {formatDate(row.entry_date)}
                  </td>
                  <td className="py-2 px-2 text-sm">
                    <div className="flex items-center gap-2">
                      <span>{row.description}</span>
                      {row.is_reversal && (
                        <span className="px-1.5 py-0.5 text-[10px] font-medium bg-orange-100 text-orange-800 rounded">
                          REVERSAL
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-gray-400">
                      {row.line_count} line{row.line_count === 1 ? "" : "s"}
                    </span>
                  </td>
                  <td className="py-2 px-2 text-xs text-gray-600">
                    {row.maker_username ?? "—"}
                  </td>
                  <td className="py-2 px-2 text-xs text-gray-600">
                    {row.certifier_username ?? "—"}
                  </td>
                  <td className="py-2 px-2 font-medium">
                    ${formatMoney(row.total_amount)}
                  </td>
                  <td className="py-2 px-2">
                    <Badge value={row.status} />
                  </td>
                </tr>
              ))
            )}
          </Table>
        )}

        {data && data.count > data.limit && (
          <p className="text-xs text-gray-500 mt-4 text-center">
            Showing the most recent {data.limit} of {data.count} entries.
          </p>
        )}
      </Card>
    </div>
  );
}