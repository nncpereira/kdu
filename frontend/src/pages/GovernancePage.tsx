import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listActiveConfig, listChanges } from "@/api/governance";
import { useAuth } from "@/auth/useAuth";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Table } from "@/components/Table";
import { formatDate, formatMoney } from "@/lib/format";
import { ProposeSplitModal } from "./governance/ProposeSplitModal";
import { ProposeAnnualFeeModal } from "./governance/ProposeAnnualFeeModal";

export function GovernancePage() {
  const { profile } = useAuth();
  const [proposeOpen, setProposeOpen] = useState(false);
  const [proposeFeeOpen, setProposeFeeOpen] = useState(false);

  const configQuery = useQuery({
    queryKey: ["governance", "config"],
    queryFn: listActiveConfig,
  });

  const changesQuery = useQuery({
    queryKey: ["governance", "changes"],
    queryFn: listChanges,
  });

  const canPropose =
    profile?.role === "MAKER" || profile?.role === "SUPERADMIN";

  const split = configQuery.data?.find(
    (c) => c.parameter_key === "shu_split"
  );
  const splitValue = split?.parameter_value as Record<string, unknown> | undefined;

  const annualFee = configQuery.data?.find(
    (c) => c.parameter_key === "shu_annual_fee"
  );

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Governance</h1>
          <p className="text-sm text-gray-500">
            System configuration, AGM-approved parameters
          </p>
        </div>
        {canPropose && (
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setProposeFeeOpen(true)}>
              + Propose Annual Fee
            </Button>
            <Button onClick={() => setProposeOpen(true)}>
              + Propose SHU Split
            </Button>
          </div>
        )}
      </div>

      {/* Active SHU Split */}
      {split && (
        <Card title="Active SHU Split">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {(
              [
                ["Reserva Legal", "reserva_legal_pct"],
                ["Admin & Operational Fund", "admin_fund_pct"],
                ["Jasa Simpanan", "jasa_simpanan_pct"],
                ["Jasa Bunga", "jasa_bunga_pct"],
              ] as const
            ).map(([label, key]) => (
              <div key={key} className="bg-gray-50 rounded p-3">
                <p className="text-xs text-gray-500">{label}</p>
                <p className="text-xl font-bold text-gray-800">
                  {String(splitValue?.[key])}%
                </p>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Effective from {formatDate(split.effective_from)} · DL 76/2022
            Art. 69 requires Reserva Legal ≥ 25% until the reserve reaches
            100% of social capital.
          </p>
        </Card>
      )}

      {/* Active Annual Fee */}
      {annualFee && (
        <Card title="Active Annual Fee">
          <div className="bg-gray-50 rounded p-3 inline-block">
            <p className="text-xs text-gray-500">Deducted per member from SHU payout</p>
            <p className="text-xl font-bold text-gray-800">
              ${formatMoney(String(annualFee.parameter_value))}
            </p>
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Effective from {formatDate(annualFee.effective_from)} · floored at
            $0 per member, never collected as a negative payout.
          </p>
        </Card>
      )}

      {/* Change history */}
      <Card title="Change History">
        {changesQuery.data && (
          <Table
            headers={[
              "Parameter",
              "Proposed",
              "Effective",
              "Status",
              "",
              "Created",
            ]}
            empty={changesQuery.data.length === 0}
          >
            {changesQuery.data.map((c) => (
              <tr
                key={c.id}
                className="border-b border-gray-100 hover:bg-gray-50"
              >
                <td className="py-2 px-2 font-mono text-xs">
                  {c.parameter_key}
                </td>
                <td className="py-2 px-2 text-xs">
                  {JSON.stringify(c.proposed_value)}
                </td>
                <td className="py-2 px-2 text-xs">
                  {formatDate(c.effective_from)}
                </td>
                <td className="py-2 px-2">
                  <Badge value={c.status} />
                </td>
                <td className="py-2 px-2">
                  {c.warnings.length > 0 && (
                    <span
                      title={c.warnings.join("\n")}
                      className="inline-block px-2 py-1 text-xs font-medium rounded bg-yellow-100 text-yellow-800 cursor-help"
                    >
                      ⚠ {c.warnings.length}
                    </span>
                  )}
                </td>
                <td className="py-2 px-2 text-xs text-gray-500">
                  {formatDate(c.created_at)}
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      <ProposeSplitModal
        open={proposeOpen}
        onClose={() => setProposeOpen(false)}
      />
      <ProposeAnnualFeeModal
        open={proposeFeeOpen}
        onClose={() => setProposeFeeOpen(false)}
      />
    </div>
  );
}