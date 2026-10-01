import { Fragment, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import clsx from "clsx";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getFiscalYear, calculateShu, getCalculation, getCalculationForFiscalYear, listPayouts,
  backfillSnapshots, runAggregation, cancelCalculation, getPayoutDetail, ShuPayout,
  refreshFiscalYear,
} from "@/api/shu";
import { useAuth } from "@/auth/useAuth";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Table } from "@/components/Table";
import { formatMoney, formatDate } from "@/lib/format";
import { toast } from "sonner";
import { Breadcrumbs } from "@/components/Breadcrumbs";

export function ShuDetailPage() {
  const { fyId } = useParams<{ fyId: string }>();
  const { profile } = useAuth();
  const qc = useQueryClient();
  const [pendingCalcId, setPendingCalcId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [calcError, setCalcError] = useState<string | null>(null);
  const [expandedMemberId, setExpandedMemberId] = useState<string | null>(null);

  useEffect(() => {
    setCalcError(null);
    setFeedback(null);
    setPendingCalcId(null);
  }, [fyId]);

  const fyCalcQuery = useQuery({
    queryKey: ["shu", "fy-calc", fyId],
    queryFn: () => getCalculationForFiscalYear(fyId!),
    enabled: !!fyId,
    retry: false,
  });

  const calcId = fyCalcQuery.data?.id ?? pendingCalcId;

  const fyQuery = useQuery({
    queryKey: ["shu", "fy", fyId],
    queryFn: () => getFiscalYear(fyId!),
    enabled: !!fyId,
  });

  const calcQuery = useQuery({
    queryKey: ["shu", "calc", calcId],
    queryFn: () => getCalculation(calcId!),
    enabled: !!calcId,
  });

  const payoutsQuery = useQuery({
    queryKey: ["shu", "payouts", calcId],
    queryFn: () => listPayouts(calcId!),
    enabled: !!calcId,
  });

  const calcMutation = useMutation({
    mutationFn: () => calculateShu(fyId!),
    onSuccess: (calc) => {
      toast.success("SHU calculation created.");
      setPendingCalcId(calc.id);
      setCalcError(null);
      setFeedback("SHU calculation created. Awaiting Checker approval.");
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      qc.setQueryData(["shu", "fy-calc", fyId], calc);
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail ?? "Calculation failed.";
      toast.error(detail);
      setCalcError(detail);
    },
  });

  const backfillMutation = useMutation({
    mutationFn: () => backfillSnapshots(fyId!),
    onSuccess: (r) => {
      toast.success(`Backfilled ${r.rows_created} monthly snapshots.`);
      setFeedback(`Backfilled ${r.rows_created} monthly snapshots.`);
    },
  });

  const aggregateMutation = useMutation({
    mutationFn: () => runAggregation(fyId!),
    onSuccess: (r) => {
      toast.success(`Aggregated ${r.rows_created} member weighting rows.`);
      setFeedback(`Aggregated ${r.rows_created} member weighting rows.`);
    },
  });

  const refreshMutation = useMutation({
    mutationFn: () => refreshFiscalYear(fyId!),
    onSuccess: (updated) => {
      toast.success("Fiscal year totals recalculated from the ledger.");
      setFeedback("Fiscal year totals recalculated from the ledger.");
      qc.setQueryData(["shu", "fy", fyId], updated);
    },
    onError: (err: any) => {
      toast.error(
        err?.response?.data?.detail ?? "Could not recalculate totals."
      );
    },
  });

  const cancelMutation = useMutation({
    mutationFn: () => cancelCalculation(calcId!),
    onSuccess: (calc) => {
      toast.success("SHU calculation cancelled.");
      setFeedback("SHU calculation cancelled.");
      setCalcError(null);
      qc.setQueryData(["shu", "calc", calc.id], calc);
      qc.setQueryData(["shu", "fy-calc", fyId], calc);
      qc.invalidateQueries({ queryKey: ["pipeline"] });
    },
    onError: (err: any) => {
      setCalcError(err?.response?.data?.detail ?? "Could not cancel calculation.");
    },
  });

  if (fyQuery.isLoading) {
  return (
    <div className="p-6">
      <Breadcrumbs
        items={[
          { label: "SHU", to: "/shu" },
          { label: "Loading…" },
        ]}
      />
      <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
    </div>
  );
}
  if (fyQuery.isError || !fyQuery.data) {
    return (
      <div className="p-6">
        <Breadcrumbs
          items={[
            { label: "SHU", to: "/shu" },
            { label: "Not found" },
          ]}
        />
        <p className="text-sm text-red-600">Fiscal year not found.</p>
      </div>
    );
  }

  const fy = fyQuery.data;
  const isSuperadmin = profile?.role === "SUPERADMIN";
  const isMaker = profile?.role === "MAKER" || isSuperadmin;
  const reserveRatio = fy.kapital_sosial !== "0.00"
    ? (parseFloat(fy.accumulated_reserva_legal) / parseFloat(fy.kapital_sosial)) * 100
    : 0;
  const reserveMeetsThreshold = reserveRatio >= 100;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <Breadcrumbs
          items={[
            { label: "SHU", to: "/shu" },
            { label: `Fiscal Year ${formatDate(fy.year_start)} – ${formatDate(fy.year_end)}` },
          ]}
        />
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              Fiscal Year {formatDate(fy.year_start)} – {formatDate(fy.year_end)}
            </h1>
            <p className="text-sm text-gray-500 font-mono">{fy.id}</p>
          </div>
          <Badge value={fy.status} />
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card title="Net Surplus">
          <p className="text-2xl font-bold text-gray-800">
            ${formatMoney(fy.net_surplus)}
          </p>
        </Card>
        <Card title="Social Capital">
          <p className="text-2xl font-bold text-gray-800">
            ${formatMoney(fy.kapital_sosial)}
          </p>
        </Card>
        <Card title="Legal Reserve">
          <p className="text-2xl font-bold text-gray-800">
            ${formatMoney(fy.accumulated_reserva_legal)}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {reserveRatio.toFixed(1)}% of capital
          </p>
        </Card>
        <Card title="Legal Reserve Rule">
          {reserveMeetsThreshold ? (
            <>
              <p className="text-lg font-bold text-green-700">AGM may lower</p>
              <p className="text-xs text-gray-500 mt-1">
                Reserve ≥ 100% of capital
              </p>
            </>
          ) : (
            <>
              <p className="text-lg font-bold text-yellow-700">≥ 25% required</p>
              <p className="text-xs text-gray-500 mt-1">
                DL 76/2022 Art. 69
              </p>
            </>
          )}
        </Card>
      </div>

      {/* Actions */}
      {isSuperadmin && (
        <Card title="Data Preparation (Superadmin)">
          <div className="flex flex-wrap gap-2">
            {fy.status === "OPEN" && !calcId && (
              <Button
                variant="secondary"
                onClick={() => refreshMutation.mutate()}
                loading={refreshMutation.isPending}
              >
                Recalculate Totals
              </Button>
            )}
            <Button
              variant="secondary"
              onClick={() => backfillMutation.mutate()}
              loading={backfillMutation.isPending}
            >
              Backfill Monthly Snapshots
            </Button>
            <Button
              variant="secondary"
              onClick={() => aggregateMutation.mutate()}
              loading={aggregateMutation.isPending}
            >
              Aggregate Annual Weighting
            </Button>
          </div>
          <p className="text-xs text-gray-500 mt-3">
            {fy.status === "OPEN" && !calcId && (
              <>
                Net Surplus/Social Capital/Legal Reserve above are captured
                once and don't auto-update — Recalculate Totals re-reads them
                from the ledger (e.g. after posting a late expense). {" "}
              </>
            )}
            Run backfill/aggregate before calculating SHU. Backfill captures
            month-end balances for every month in the FY; aggregation
            produces the per-member weighting units and interest totals.
          </p>
        </Card>
      )}

      {isMaker && fy.status === "OPEN" && (
        <div className="flex gap-2">
          <Button
            onClick={() => calcMutation.mutate()}
            loading={calcMutation.isPending}
          >
            Calculate SHU
          </Button>
        </div>
      )}

      {calcError && (
        <Card>
          <div className="flex items-start gap-3">
            <div className="text-red-600 text-2xl leading-none">⚠</div>
            <div className="flex-1">
              <p className="font-semibold text-red-800">
                {calcErrorTitle(calcError)}
              </p>
              <p className="text-sm text-red-700 mt-1">{calcError}</p>
              {calcError.includes("Reserva Legal") && (
                <p className="text-sm text-gray-600 mt-2">
                  The current AGM-approved split sets Reserva Legal below 25%, but
                  DL 76/2022 Art. 69 requires ≥ 25% until the accumulated reserve
                  reaches 100% of social capital.
                </p>
              )}
              {calcError.includes("already exists") && (
                <p className="text-sm text-gray-600 mt-2">
                  A previous calculation for this fiscal year is still pending
                  approval. Complete it through the Pipeline, or ask the Superadmin
                  to clear it.
                </p>
              )}
              {profile?.role === "SUPERADMIN" &&
                calcError.includes("Reserva Legal") && (
                  <div className="mt-3">
                    <Link
                      to="/governance"
                      className="text-brand-600 hover:underline text-sm font-medium"
                    >
                      → Go to Governance to propose a legal split
                    </Link>
                  </div>
                )}
            </div>
          </div>
        </Card>
      )}

      {feedback && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 text-sm rounded px-3 py-2">
          {feedback}
        </div>
      )}

      {/* Calculation detail */}
      {calcQuery.data && (
        <>
          <Card title="SHU Allocation">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <Alloc
                label="Reserva Legal"
                pct={calcQuery.data.reserva_legal_pct}
                amount={calcQuery.data.reserva_legal_amt}
              />
              <Alloc
                label="Admin & Operational Fund"
                pct={calcQuery.data.admin_fund_pct}
                amount={calcQuery.data.admin_fund_amt}
              />
              <Alloc
                label="Jasa Simpanan"
                pct={calcQuery.data.jasa_simpanan_pct}
                amount={calcQuery.data.jasa_simpanan_amt}
              />
              <Alloc
                label="Jasa Bunga"
                pct={calcQuery.data.jasa_bunga_pct}
                amount={calcQuery.data.jasa_bunga_amt}
              />
            </div>
            <div className="mt-4 pt-4 border-t border-gray-200 flex justify-between text-sm">
              <span className="text-gray-500">Status</span>
              <Badge value={calcQuery.data.status} />
            </div>
            {(calcQuery.data.status === "PENDING_CHECK" ||
              calcQuery.data.status === "PENDING_CERTIFY") &&
              (profile?.role === "MAKER" || profile?.role === "SUPERADMIN") && (
                <div className="mt-4">
                  <Button
                    variant="danger"
                    onClick={() => cancelMutation.mutate()}
                    loading={cancelMutation.isPending}
                  >
                    Cancel Stale Calculation
                  </Button>
                </div>
              )}
          </Card>

          <Card title="Member Payouts">
            {payoutsQuery.isLoading && (
              <p className="text-sm text-gray-500 py-4">Loading…</p>
            )}
            {payoutsQuery.data && (
              <Table
                headers={[
                  "Member",
                  "Jasa Simpanan",
                  "Jasa Bunga",
                  "Annual Fee",
                  "Net Payout",
                ]}
                empty={payoutsQuery.data.length === 0}
              >
                {payoutsQuery.data.map((p) => {
                  const isIneligible = p.status === "NOT_ELIGIBLE";
                  const isExpanded = !isIneligible && expandedMemberId === p.member;
                  return (
                    <Fragment key={p.member}>
                      <tr
                        onClick={
                          isIneligible
                            ? undefined
                            : () =>
                                setExpandedMemberId(isExpanded ? null : p.member)
                        }
                        className={clsx(
                          "border-b border-gray-100",
                          isIneligible
                            ? "text-gray-400"
                            : "hover:bg-gray-50 cursor-pointer"
                        )}
                      >
                        <td className="py-2 px-2">
                          {!isIneligible && (
                            <span className="text-gray-400 mr-1">
                              {isExpanded ? "▾" : "▸"}
                            </span>
                          )}
                          <span className="font-mono text-xs">
                            {p.member_number}
                          </span>{" "}
                          {p.full_name}
                          {isIneligible && (
                            <span
                              className="ml-2 text-xs italic"
                              title="No eligible months in this fiscal year (e.g. joined too late to qualify)."
                            >
                              — not eligible this FY
                            </span>
                          )}
                        </td>
                        <td className="py-2 px-2">
                          ${formatMoney(p.jasa_simpanan_gross)}
                        </td>
                        <td className="py-2 px-2">
                          ${formatMoney(p.jasa_bunga_gross)}
                        </td>
                        <td className="py-2 px-2 text-orange-700">
                          {parseFloat(p.annual_fee_deducted) > 0
                            ? `-$${formatMoney(p.annual_fee_deducted)}`
                            : "—"}
                        </td>
                        <td className="py-2 px-2 font-medium">
                          ${formatMoney(p.net_payout)}
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan={5} className="bg-gray-50 p-0">
                            <PayoutDetailPanel calcId={calcId!} payout={p} />
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </Table>
            )}
          </Card>
        </>
      )}
    </div>
  );
}

function calcErrorTitle(error: string): string {
  if (error.includes("Reserva Legal")) return "Legal reserve requirement not met";
  if (error.includes("already exists")) return "An active calculation already exists";
  if (error.includes("No active SHU split")) return "SHU split not configured";
  if (error.includes("not OPEN")) return "Fiscal year is closed";
  return "SHU calculation failed";
}

function PayoutDetailPanel({
  calcId,
  payout,
}: {
  calcId: string;
  payout: ShuPayout;
}) {
  const detailQuery = useQuery({
    queryKey: ["shu", "payout-detail", calcId, payout.member],
    queryFn: () => getPayoutDetail(calcId, payout.member),
  });

  if (detailQuery.isLoading) {
    return <p className="text-sm text-gray-500 px-4 py-3">Loading breakdown…</p>;
  }
  if (detailQuery.isError || !detailQuery.data) {
    return (
      <p className="text-sm text-red-600 px-4 py-3">
        Failed to load breakdown.
      </p>
    );
  }
  const d = detailQuery.data;

  return (
    <div className="px-4 py-4 space-y-4 text-sm">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MiniStat label="Months Active" value={String(d.months_active)} />
        <MiniStat
          label="Weighted Savings Units"
          value={formatMoney(d.weighted_savings_units)}
        />
        <MiniStat
          label="Loan Interest Paid"
          value={`$${formatMoney(d.loan_interest_paid)}`}
        />
        <MiniStat
          label="Sum Weighted Balance"
          value={formatMoney(d.sum_weighted_balance)}
        />
      </div>

      <div className="bg-white border border-gray-200 rounded p-3 space-y-1 text-xs text-gray-600">
        <p>
          <span className="font-medium text-gray-800">Jasa Simpanan:</span>{" "}
          {formatMoney(d.weighted_savings_units)} / {formatMoney(d.total_weighted_savings_units)}{" "}
          units × ${formatMoney(d.jasa_simpanan_pool)} pool ={" "}
          <span className="font-medium text-gray-800">
            ${formatMoney(d.jasa_simpanan_gross)}
          </span>
        </p>
        <p>
          <span className="font-medium text-gray-800">Jasa Bunga:</span>{" "}
          ${formatMoney(d.loan_interest_paid)} / ${formatMoney(d.total_loan_interest_paid)}{" "}
          interest × ${formatMoney(d.jasa_bunga_pool)} pool ={" "}
          <span className="font-medium text-gray-800">
            ${formatMoney(d.jasa_bunga_gross)}
          </span>
        </p>
        {parseFloat(d.annual_fee_deducted) > 0 && (
          <p>
            <span className="font-medium text-gray-800">Annual Fee:</span>{" "}
            <span className="text-orange-700">
              -${formatMoney(d.annual_fee_deducted)}
            </span>{" "}
            (deducted from Jasa Simpanan + Jasa Bunga)
          </p>
        )}
        <p className="pt-1 border-t border-gray-100">
          <span className="font-medium text-gray-800">Net Payout:</span>{" "}
          <span className="font-medium text-gray-800">
            ${formatMoney(d.net_payout)}
          </span>
        </p>
      </div>

      <div>
        <p className="text-xs font-medium text-gray-500 mb-2">
          Monthly savings balances (weight runs 12 → 1, July → June). A
          balance can exist for a month marked "not eligible" below — it's
          just historical record, and doesn't count toward the sum.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-200">
                <th className="py-1 pr-3">Month</th>
                <th className="py-1 pr-3">Balance</th>
                <th className="py-1 pr-3">Weight</th>
                <th className="py-1 pr-3">Weighted</th>
              </tr>
            </thead>
            <tbody>
              {d.monthly_balances.map((mb) => (
                <tr
                  key={mb.month_date}
                  className={clsx(
                    "border-b border-gray-100",
                    !mb.eligible && "text-gray-400"
                  )}
                >
                  <td className="py-1 pr-3">{formatDate(mb.month_date)}</td>
                  <td className="py-1 pr-3">${formatMoney(mb.total_balance)}</td>
                  <td className="py-1 pr-3">
                    {mb.eligible ? `×${mb.weight}` : "—"}
                  </td>
                  <td className="py-1 pr-3">
                    {mb.eligible ? (
                      formatMoney(mb.weighted_balance)
                    ) : (
                      <span
                        className="italic"
                        title="Member joined after the 15th of this month, so it doesn't count toward the weighting (DL 76/2022 eligibility rule)."
                      >
                        not eligible
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded p-2">
      <p className="text-[10px] text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="text-sm font-semibold text-gray-800">{value}</p>
    </div>
  );
}

function Alloc({
  label,
  pct,
  amount,
}: {
  label: string;
  pct: string;
  amount: string;
}) {
  return (
    <div className="bg-gray-50 rounded p-3">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-xs text-gray-400">{pct}%</p>
      <p className="text-lg font-bold text-gray-800 mt-1">
        ${formatMoney(amount)}
      </p>
    </div>
  );
}
