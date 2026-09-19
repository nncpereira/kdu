import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listPendingCheck, listPendingCertify,
  checkActor, certifyActor, rejectActor,
} from "@/api/pipeline";
import { useAuth } from "@/auth/useAuth";
import { Badge } from "@/components/Badge";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Table } from "@/components/Table";
import { toast } from "sonner";
import { TableSkeleton } from "@/components/Skeleton";

export function PipelinePage() {
  const { profile } = useAuth();
  const qc = useQueryClient();
  const role = profile?.role;

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

  const mutation = useMutation({
    mutationFn: async (args: { action: string; id: string }) => {
      if (args.action === "check") return checkActor(args.id);
      if (args.action === "certify") return certifyActor(args.id);
      return rejectActor(args.id, "rejected by " + role);
    },
    onSuccess: (_data, variables) => {
      const verb = variables.action === "check" ? "approved" : variables.action === "certify" ? "certified" : "rejected";
      toast.success(`Transaction ${verb}.`);
      // Broad invalidation — React Query matches by prefix, so "member"
      // catches ["member", id], "savings" catches ["savings", "voluntary", id], etc.
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["members"] });
      qc.invalidateQueries({ queryKey: ["member"] });
      qc.invalidateQueries({ queryKey: ["savings"] });
      qc.invalidateQueries({ queryKey: ["loans"] });
      qc.invalidateQueries({ queryKey: ["loan"] });
      qc.invalidateQueries({ queryKey: ["repayments"] });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Action failed.");
    },
  });

  const rows = [...(checkQuery.data ?? []), ...(certifyQuery.data ?? [])];
  const isLoading = checkQuery.isLoading || certifyQuery.isLoading;
  const isError = checkQuery.isError || certifyQuery.isError;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Pipeline</h1>
        <p className="text-sm text-gray-500">
          Transactions awaiting your approval
        </p>
      </div>

      <Card>
        {isError && (
          <p className="text-sm text-red-600 py-8 text-center">
            Failed to load pipeline items.
          </p>
        )}

        {!isError && (
          <Table
            headers={["Type", "Details", "Maker", "Status", "Actions"]}
            empty={!isLoading && rows.length === 0}
          >
            {isLoading ? <TableSkeleton rows={5} cols={5} /> : rows.map((r) => (
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
                  {r.target_summary?.has_receipt && r.target_summary?.receipt_url && (
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
                          onClick={() =>
                            mutation.mutate({ action: "check", id: r.id })
                          }
                        >
                          Approve
                        </Button>
                        <Button
                          variant="danger"
                          onClick={() =>
                            mutation.mutate({ action: "reject", id: r.id })
                          }
                        >
                          Reject
                        </Button>
                      </>
                    )}
                  {r.status === "PENDING_CERTIFY" &&
                    (role === "CERTIFIER" || role === "SUPERADMIN") && (
                      <>
                        <Button
                          onClick={() =>
                            mutation.mutate({ action: "certify", id: r.id })
                          }
                        >
                          Certify
                        </Button>
                        <Button
                          variant="danger"
                          onClick={() =>
                            mutation.mutate({ action: "reject", id: r.id })
                          }
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
    </div>
  );
}
