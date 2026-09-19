import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { requestMemberExit } from "@/api/members";
import type { Member } from "@/api/members";

interface Props {
  member: Member | null;
  open: boolean;
  onClose: () => void;
}

export function RequestExitModal({ member, open, onClose }: Props) {
  const qc = useQueryClient();
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (r: string) => requestMemberExit(member!.id, r),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["members"] });
      qc.invalidateQueries({ queryKey: ["member", member!.id] });
      qc.invalidateQueries({ queryKey: ["pipeline"] });
      onClose();
    },
    onError: (err: any) => {
      setError(err?.response?.data?.detail ?? "Exit request failed.");
    },
  });

  if (!member) return null;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    await mutation.mutateAsync(reason);
  }

  return (
    <Modal open={open} onClose={onClose} title="Request Member Exit" size="sm">
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm rounded p-3">
          <p className="font-medium">This will refund the member's capital.</p>
          <p className="mt-1">
            Blocked if the member has any outstanding loans or unsettled obligations
            (DL 16/2004 Art. 24).
          </p>
        </div>

        <div className="text-sm bg-gray-50 rounded p-3">
          <p>
            <span className="text-gray-500">Member:</span>{" "}
            <span className="font-medium">{member.full_name}</span>
          </p>
          <p>
            <span className="text-gray-500">Capital to refund:</span>{" "}
            <span className="font-medium">
              ${parseFloat(member.kapital_sosial_balance).toFixed(2)}
            </span>
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Reason (optional)
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded px-3 py-2">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-4 border-t border-gray-200">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="danger" loading={mutation.isPending}>
            Submit Exit Request
          </Button>
        </div>
      </form>
    </Modal>
  );
}