import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getFiscalYear, calculateShu, getCalculation, getCalculationForFiscalYear, listPayouts,
  backfillSnapshots, runAggregation, cancelCalculation,
} from "@/api/shu";
import { useAuth } from "@/auth/useAuth";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Table } from "@/components/Table";
import { formatMoney, formatDate } from "@/lib/format";
import { toast } from "sonner";

export function ShuDetailPage() {
  const { fyId } = useParams<{ fyId: string }>();
  const { profile } = useAuth();
  const qc = useQueryClient();
  const [pendingCalcId, setPendingCalcId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [calcError, setCalcError] = useState<string | null>(null);

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
    return <div className="p-6 text-sm text-gray-500">Loading…</div>;
  }
  if (fyQuery.isError || !fyQuery.data) {
    return <div className="p-6 text-sm text-red-600">Fiscal year not found.</div>;
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
      <div className="flex items-center justify-between">
        <div>
          <Link to="/shu" className="text-sm text-brand-600 hover:underline">
            ← Back to SHU
          </Link>
          <h1 className="text-2xl font-bold text-gray-800 mt-2">
            Fiscal Year {formatDate(fy.year_start)} – {formatDate(fy.year_end)}
          </h1>
          <p className="text-sm text-gray-500 font-mono">{fy.id}</p>
        </div>
        <Badge value={fy.status} />
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
            Run these before calculating SHU. Backfill captures month-end
            balances for every month in the FY; aggregation produces the
            per-member weighting units and interest totals.
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
                  "Total Payout",
                ]}
                empty={payoutsQuery.data.length === 0}
              >
                {payoutsQuery.data.map((p) => (
                  <tr
                    key={p.id}
                    className="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td className="py-2 px-2">
                      <span className="font-mono text-xs">
                        {p.member_number}
                      </span>{" "}
                      {p.full_name}
                    </td>
                    <td className="py-2 px-2">
                      ${formatMoney(p.jasa_simpanan_gross)}
                    </td>
                    <td className="py-2 px-2">
                      ${formatMoney(p.jasa_bunga_gross)}
                    </td>
                    <td className="py-2 px-2 font-medium">
                      ${formatMoney(p.net_payout)}
                    </td>
                  </tr>
                ))}
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
