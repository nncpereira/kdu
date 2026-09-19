import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMember } from "@/api/members";
import { useAuth } from "@/auth/useAuth";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { formatMoney, formatDate } from "@/lib/format";
import { PayInitialCapitalModal } from "./members/PayInitialCapitalModal";
import { RequestExitModal } from "./members/RequestExitModal";
import { DepositModal } from "./savings/DepositModal";
import { WithdrawModal } from "./savings/WithdrawModal";
import { getVoluntaryBalance } from "@/api/savings";
import { OriginateLoanModal } from "./loans/OriginateLoanModal";

export function MemberDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { profile } = useAuth();
  const [payOpen, setPayOpen] = useState(false);
  const [exitOpen, setExitOpen] = useState(false);
  const [depositOpen, setDepositOpen] = useState(false);
  const [withdrawOpen, setWithdrawOpen] = useState(false);
  const [loanOpen, setLoanOpen] = useState(false);

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

  if (isLoading) {
    return <div className="p-6 text-sm text-gray-500">Loading…</div>;
  }
  if (isError || !member) {
    return <div className="p-6 text-sm text-red-600">Member not found.</div>;
  }

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
      <div className="flex items-center justify-between">
        <div>
          <Link
            to="/members"
            className="text-sm text-brand-600 hover:underline"
          >
            ← Back to Members
          </Link>
          <h1 className="text-2xl font-bold text-gray-800 mt-2">
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