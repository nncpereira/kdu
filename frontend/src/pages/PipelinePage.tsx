import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  listPendingCheck,
  listPendingCertify,
  checkActor,
  PipelineActor,
} from "@/api/pipeline";
import { useAuth } from "@/auth/useAuth";
import { Badge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Table } from "@/components/Table";
import { TableSkeleton } from "@/components/Skeleton";
import { CertifyConfirmModal } from "./pipeline/CertifyConfirmModal";
import { RejectConfirmModal } from "./pipeline/RejectConfirmModal";

export function PipelinePage() {
  const { profile } = useAuth();
  const qc = useQueryClient();
  const role = profile?.role;

  const [certifyTarget, setCertifyTarget] = useState<PipelineActor | null>(null);
  const [rejectTarget, setRejectTarget] = useState<PipelineActor | null>(null);

  const checkQuery = useQuery({
    queryKey: ["pipeline", "check"],
    queryFn: listPendingCheck,
    enabled: role === "CHECKER" || role === "SUPERADMIN",
  });

  const certifyQuery = useQuery({
    queryKey: ["pipeline", "certify"],
    queryFn: listPendingCertify,
    enabled: role === "CERTIFIER" || role === "SUPERADMIN",
  });

  // Check stays one-click — it's reversible (certification still required).
  const checkMutation = useMutation({
    mutationFn: (id: string) => checkActor(id),
    onSuccess: () => {
      toast.success("Transaction approved. Awaiting certification.");
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Approval failed.");
    },
  });

  const rows = [...(checkQuery.data ?? []), ...(certifyQuery.data ?? [])];
  const isLoading = checkQuery.isLoading || certifyQuery.isLoading;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Pipeline</h1>
        <p className="text-sm text-gray-500">
          Transactions awaiting your approval
        </p>
      </div>

      <Card>
        {isLoading ? (
          <Table
            headers={["Type", "Details", "Maker", "Status", "Actions"]}
            empty={false}
          >
            <TableSkeleton rows={5} cols={5} />
          </Table>
        ) : (
          <Table
            headers={["Type", "Details", "Maker", "Status", "Actions"]}
            empty={rows.length === 0}
          >
            {rows.map((r) => (
              <tr
                key={r.id}
                className="border-b border-gray-100 hover:bg-gray-50"
              >
                <td className="py-3 px-2 text-xs font-mono text-gray-600">
                  {r.transaction_type}
                </td>
                <td className="py-3 px-2 text-sm text-gray-800">
                  {r.target_summary?.label ?? (
                    <span className="text-gray-400 italic">
                      No summary available
                    </span>
                  )}
                  {r.target_summary?.member_number && (
                    <div className="text-xs text-gray-500 mt-0.5 font-mono">
                      {r.target_summary.member_number}
                    </div>
                  )}
                  {r.target_summary?.has_receipt &&
                    r.target_summary?.receipt_url && (
                      <a
                        href={r.target_summary.receipt_url as string}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-block mt-1 text-xs text-brand-600 hover:underline"
                      >
                        📎 View receipt
                      </a>
                    )}
                </td>
                <td className="py-3 px-2 text-sm text-gray-600">
                  {r.maker_username}
                </td>
                <td className="py-3 px-2">
                  <Badge value={r.status} />
                </td>
                <td className="py-3 px-2 space-x-2 whitespace-nowrap">
                  {r.status === "PENDING_CHECK" &&
                    (role === "CHECKER" || role === "SUPERADMIN") && (
                      <>
                        <Button
                          onClick={() => checkMutation.mutate(r.id)}
                          loading={checkMutation.isPending}
                        >
                          Approve
                        </Button>
                        <Button
                          variant="danger"
                          onClick={() => setRejectTarget(r)}
                        >
                          Reject
                        </Button>
                      </>
                    )}
                  {r.status === "PENDING_CERTIFY" &&
                    (role === "CERTIFIER" || role === "SUPERADMIN") && (
                      <>
                        <Button onClick={() => setCertifyTarget(r)}>
                          Certify
                        </Button>
                        <Button
                          variant="danger"
                          onClick={() => setRejectTarget(r)}
                        >
                          Reject
                        </Button>
                      </>
                    )}
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      <CertifyConfirmModal
        actor={certifyTarget}
        open={!!certifyTarget}
        onClose={() => setCertifyTarget(null)}
      />
      <RejectConfirmModal
        actor={rejectTarget}
        open={!!rejectTarget}
        onClose={() => setRejectTarget(null)}
      />
    </div>
  );
}