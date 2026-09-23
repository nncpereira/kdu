import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  getMember,
  getMemberCapitalHistory,
  MemberCapitalHistory,
} from "@/api/members";
import { useAuth } from "@/auth/useAuth";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Table } from "@/components/Table";
import { formatMoney, formatDate } from "@/lib/format";
import { PayInitialCapitalModal } from "./members/PayInitialCapitalModal";
import { RequestExitModal } from "./members/RequestExitModal";
import { DepositModal } from "./savings/DepositModal";
import { WithdrawModal } from "./savings/WithdrawModal";
import { getVoluntaryBalance, listTransactions, SavingsTransaction } from "@/api/savings";
import { OriginateLoanModal } from "./loans/OriginateLoanModal";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { MemberLoginModal } from "./members/MemberLoginModal";

export function MemberDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { profile } = useAuth();
  const [payOpen, setPayOpen] = useState(false);
  const [exitOpen, setExitOpen] = useState(false);
  const [depositOpen, setDepositOpen] = useState(false);
  const [withdrawOpen, setWithdrawOpen] = useState(false);
  const [loanOpen, setLoanOpen] = useState(false);
  const [loginModalMode, setLoginModalMode] = useState<"create" | "reset" | null>(null);

  const { data: member, isLoading, isError } = useQuery({
    queryKey: ["member", id],
    queryFn: () => getMember(id!),
    enabled: !!id,
  });
  const voluntaryQuery = useQuery({
    queryKey: ["savings", "voluntary", id],
    queryFn: () => getVoluntaryBalance(id!),
    enabled: !!id,
  });
  const historyQuery = useQuery({
    queryKey: ["members", "capital-history", id],
    queryFn: () => getMemberCapitalHistory(id!),
    enabled: !!id,
  });
  const savingsTxnQuery = useQuery({
    queryKey: ["savings", "transactions", id],
    queryFn: () => listTransactions({ member: id }),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="p-6">
        <Breadcrumbs
          items={[
            { label: "Members", to: "/members" },
            { label: "Loading…" },
          ]}
        />
        <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
      </div>
    );
  }
  if (isError || !member) {
    return (
      <div className="p-6">
        <Breadcrumbs
          items={[
            { label: "Members", to: "/members" },
            { label: "Not found" },
          ]}
        />
        <p className="text-sm text-red-600">Member not found.</p>
      </div>
    );
  }

  const isSuperadmin = profile?.role === "SUPERADMIN";
  const canMake = profile?.role === "MAKER" || profile?.role === "SUPERADMIN";
  const canPay = canMake && member.status === "Pending";
  const canExit = canMake && member.status === "Active";

  const voluntaryBalance = voluntaryQuery.data?.balance_available ?? "0.00";
  const voluntaryHeld = voluntaryQuery.data?.balance_held_pipeline ?? "0.00";
  const totalSavings = (
    parseFloat(member.kapital_sosial_balance) +
    parseFloat(voluntaryBalance)
  ).toFixed(2);
  const hasHold = parseFloat(voluntaryHeld) > 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <Breadcrumbs
          items={[
            { label: "Members", to: "/members" },
            { label: member.full_name },
          ]}
        />
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              {member.full_name}
            </h1>
            <p className="text-sm text-gray-500 font-mono">
              {member.membership_number}
            </p>
          </div>
          <div className="text-right">
            <Badge value={member.status} />
          </div>
        </div>
      </div>

      {/* Action bar */}
      <div className="flex gap-2">
        {canMake && member.status === "Active" && (
          <>
            <Button onClick={() => setDepositOpen(true)}>Deposit</Button>
            <Button variant="secondary" onClick={() => setWithdrawOpen(true)}>
              Withdraw
            </Button>
          </>
        )}
        {canPay && (
          <Button onClick={() => setPayOpen(true)}>
            Pay Initial Capital
          </Button>
        )}
        {canExit && (
          <Button variant="danger" onClick={() => setExitOpen(true)}>
            Request Exit
          </Button>
        )}
        {canMake && member.status === "Active" && (
          <Button variant="secondary" onClick={() => setLoanOpen(true)}>
            Originate Loan
          </Button>
        )}
        {/* NEW: login management */}
        {isSuperadmin && !member.has_login && (
          <Button
            variant="secondary"
            onClick={() => setLoginModalMode("create")}
          >
            Create Login
          </Button>
        )}
        {isSuperadmin && member.has_login && (
          <Button
            variant="secondary"
            onClick={() => setLoginModalMode("reset")}
          >
            Reset Login Password
          </Button>
        )}
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card title="Capital (Obligatory)">
          <p className="text-2xl font-bold text-gray-800">
            ${formatMoney(member.kapital_sosial_balance)}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Kapital Sosial — locked while active
          </p>
        </Card>

        <Card title="Voluntary Deposits">
          <p className="text-2xl font-bold text-blue-700">
            ${formatMoney(voluntaryBalance)}
          </p>
          {hasHold ? (
            <p className="text-xs text-yellow-700 mt-1">
              ${formatMoney(voluntaryHeld)} held in pending
            </p>
          ) : (
            <p className="text-xs text-gray-500 mt-1">
              Available for withdrawal
            </p>
          )}
        </Card>

        <Card title="Total Savings">
          <p className="text-2xl font-bold text-green-700">
            ${formatMoney(totalSavings)}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Capital + Voluntary
          </p>
        </Card>

        <Card title="Status">
          <p className="text-2xl font-bold text-gray-800">{member.status}</p>
          <p className="text-xs text-gray-500 mt-1">
            Joined {formatDate(member.date_joined)}
          </p>
        </Card>
      </div>

      {/* Transaction history */}
      <Card title="Transaction History">
        {(historyQuery.isLoading || savingsTxnQuery.isLoading) && (
          <p className="text-sm text-gray-500">Loading…</p>
        )}
        {(historyQuery.isError || savingsTxnQuery.isError) && (
          <p className="text-sm text-red-600">Failed to load transaction history.</p>
        )}
        {historyQuery.data && savingsTxnQuery.data && (
          <TransactionHistoryTable
            history={historyQuery.data}
            savingsTransactions={
              Array.isArray(savingsTxnQuery.data)
                ? savingsTxnQuery.data
                : savingsTxnQuery.data.results
            }
          />
        )}
      </Card>

      {/* Personal info */}
      <Card title="Personal Information">
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3 text-sm">
          <Row label="Salutation" value={member.salutation} />
          <Row label="First Name" value={member.first_name} />
          <Row label="Middle Name" value={member.middle_name || "—"} />
          <Row label="Last Name" value={member.last_name} />
          <Row label="National ID" value={member.national_id || "—"} />
          <Row label="Phone" value={member.phone_number} />
          <Row label="Email" value={member.email || "—"} />
          <Row label="Date of Birth" value={formatDate(member.date_of_birth)} />
          <Row label="Profession" value={member.profession || "—"} />
        </dl>
      </Card>

      {/* Address */}
      <Card title="Address">
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3 text-sm">
          <Row label="Aldeia" value={member.aldeia || "—"} />
          <Row label="Suco" value={member.suco || "—"} />
          <Row label="Posto" value={member.posto || "—"} />
          <Row label="Municipio" value={member.municipio || "—"} />
        </dl>
      </Card>

      {/* Audit */}
      <Card title="Audit">
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3 text-sm">
          <Row
            label="Member Portal Login"
            value={
              member.has_login
                ? `Active · ${member.login_username}`
                : "Not created"
            }
          />
          <Row label="Created" value={formatDate(member.created_at)} />
          <Row label="Member Since" value={formatDate(member.date_joined)} />
          <Row
            label="Last Activity"
            value={member.last_transaction_at ? formatDate(member.last_transaction_at) : "No activity yet"}
          />
          <Row
            label="Voluntary Account Opened"
            value={
              voluntaryQuery.data?.updated_at
                ? formatDate(voluntaryQuery.data.updated_at)
                : "Not yet opened"
            }
          />
        </dl>
      </Card>

      <PayInitialCapitalModal
        member={member}
        open={payOpen}
        onClose={() => setPayOpen(false)}
      />
      <RequestExitModal
        member={member}
        open={exitOpen}
        onClose={() => setExitOpen(false)}
      />
      <DepositModal
        open={depositOpen}
        onClose={() => setDepositOpen(false)}
        presetMemberId={member.id}
      />
      <WithdrawModal
        open={withdrawOpen}
        onClose={() => setWithdrawOpen(false)}
        presetMemberId={member.id}
      />
      <OriginateLoanModal
        open={loanOpen}
        onClose={() => setLoanOpen(false)}
        presetMemberId={member.id}
      />
      <MemberLoginModal
        member={member}
        mode={loginModalMode ?? "create"}
        open={loginModalMode !== null}
        onClose={() => setLoginModalMode(null)}
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

function TransactionHistoryTable({
  history,
  savingsTransactions,
}: {
  history: MemberCapitalHistory;
  savingsTransactions: SavingsTransaction[];
}) {
  const rows = [
    ...history.onboardings.map((o) => ({
      id: o.id,
      date: o.created_at,
      event: "Initial Capital",
      amount: o.initial_capital_amount,
      status: o.status,
    })),
    ...history.exit_requests.map((e) => ({
      id: e.id,
      date: e.created_at,
      event: "Capital Refund (Exit)",
      amount: e.refund_amount,
      status: e.status,
    })),
    ...savingsTransactions.map((t) => ({
      id: t.id,
      date: t.created_at,
      event: t.transaction_type === "DEPOSIT" ? "Deposit" : "Withdrawal",
      amount: t.requested_amount,
      status: t.status,
    })),
    ...history.loan_repayment_sweeps.map((s) => ({
      id: s.id,
      date: s.created_at,
      event: "Loan Repayment → Savings",
      amount: (
        parseFloat(s.obligatory_portion) + parseFloat(s.voluntary_portion)
      ).toFixed(2),
      status: s.status,
    })),
  ].sort((a, b) => (a.date < b.date ? 1 : -1));

  return (
    <Table
      headers={["Date", "Event", "Amount", "Status"]}
      empty={rows.length === 0}
    >
      {rows.map((row) => (
        <tr key={row.id} className="border-b border-gray-50">
          <td className="py-2 px-2 text-gray-600">{formatDate(row.date)}</td>
          <td className="py-2 px-2">{row.event}</td>
          <td className="py-2 px-2 font-medium">${formatMoney(row.amount)}</td>
          <td className="py-2 px-2">
            <Badge value={row.status} />
          </td>
        </tr>
      ))}
    </Table>
  );
}
