import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { certifyActor, PipelineActor } from "@/api/pipeline";
import { formatMoney } from "@/lib/format";

interface Props {
  actor: PipelineActor | null;
  open: boolean;
  onClose: () => void;
}

export function CertifyConfirmModal({ actor, open, onClose }: Props) {
  const qc = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => certifyActor(actor!.id),
    onSuccess: () => {
      toast.success("Transaction certified. The ledger has been updated.");
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["members"] });
      qc.invalidateQueries({ queryKey: ["member"] });
      qc.invalidateQueries({ queryKey: ["savings"] });
      qc.invalidateQueries({ queryKey: ["loans"] });
      qc.invalidateQueries({ queryKey: ["loan"] });
      qc.invalidateQueries({ queryKey: ["expenses"] });
      qc.invalidateQueries({ queryKey: ["reversals"] });
      qc.invalidateQueries({ queryKey: ["audit"] });
      qc.invalidateQueries({ queryKey: ["notifications"] });
      onClose();
    },
    onError: (err: any) => {
      toast.error(
        err?.response?.data?.detail ?? "Failed to certify transaction."
      );
    },
  });

  if (!actor) return null;

  const summary = actor.target_summary;
  const isShu = actor.transaction_type === "SHU_CALCULATE";
  const isReversal = actor.transaction_type === "JOURNAL_REVERSAL";
  const isMemberExit = actor.transaction_type === "MEMBER_EXIT";

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Confirm Certification"
      size="md"
    >
      <div className="space-y-4">
        {/* Warning banner */}
        <div className="bg-red-50 border-l-4 border-red-500 px-4 py-3 rounded">
          <p className="text-sm font-semibold text-red-800">
            This action is permanent
          </p>
          <p className="text-xs text-red-700 mt-1">
            {isShu
              ? "Certifying will post the reserve allocations, distribute member payouts to the ledger, and close the fiscal year. It cannot be undone."
              : isReversal
              ? "Certifying will post the offsetting entry to the ledger. Balances will be restored, and the original transaction will be marked REVERSED. This cannot be undone."
              : isMemberExit
              ? "Certifying will refund the member's capital, close their account, and deactivate their portal login. This cannot be undone."
              : "Certifying will post the balanced journal entry to the immutable ledger and update all affected balances. This cannot be undone."}
          </p>
        </div>

        {/* Transaction details */}
        <div className="bg-gray-50 border border-gray-200 rounded p-4 space-y-2 text-sm">
          <DetailRow label="Type" value={actor.transaction_type.replace("_", " ")} />
          <DetailRow
            label="Description"
            value={summary?.label ?? "(no description)"}
          />
          {summary?.member_number && (
            <DetailRow label="Member" value={summary.member_number} />
          )}
          {summary?.amount && (
            <DetailRow
              label="Amount"
              value={`$${formatMoney(summary.amount)}`}
              valueClass="font-semibold"
            />
          )}
          <DetailRow label="Maker" value={actor.maker_username} />
        </div>

        <p className="text-xs text-gray-500">
          Once certified, this entry becomes immutable. If a mistake is made,
          a reversal must be requested and approved separately.
        </p>

        <div className="flex justify-end gap-2 pt-4 border-t border-gray-200">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={() => mutation.mutate()}
            loading={mutation.isPending}
          >
            Yes, Certify
          </Button>
        </div>
      </div>
    </Modal>
  );
}

function DetailRow({
  label,
  value,
  valueClass = "",
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-gray-500 shrink-0">{label}</span>
      <span className={`text-gray-800 text-right truncate ${valueClass}`}>
        {value}
      </span>
    </div>
  );
}