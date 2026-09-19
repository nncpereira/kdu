import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { resetStaffPassword, StaffUser } from "@/api/users";
import { toast } from "sonner";

interface Props {
  user: StaffUser | null;
  open: boolean;
  onClose: () => void;
}

export function ResetPasswordModal({ user, open, onClose }: Props) {
  const [result, setResult] = useState<{ temporary_password: string } | null>(
    null
  );

  const mutation = useMutation({
    mutationFn: () => resetStaffPassword(user!.id),
    onSuccess: (data) => {
      toast.success("Temporary password generated.");
      setResult({ temporary_password: data.temporary_password });
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Failed to reset password.");
    },
  });

  if (!user) return null;

  function handleClose() {
    setResult(null);
    onClose();
  }

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title="Reset Password"
      size="sm"
    >
      {!result ? (
        <div className="space-y-4">
          <p className="text-sm text-gray-700">
            Issue a new temporary password for{" "}
            <strong>{user.username}</strong>?
          </p>
          <p className="text-xs text-gray-500">
            Their current session will continue until it expires. They will be
            forced to change the password on their next login.
          </p>

          {mutation.isError && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded px-3 py-2">
              Failed to reset password.
            </div>
          )}

          <div className="flex justify-end gap-2 pt-4 border-t border-gray-200">
            <Button variant="secondary" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              onClick={() => mutation.mutate()}
              loading={mutation.isPending}
            >
              Reset Password
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-gray-700">
            New temporary password for <strong>{user.username}</strong>:
          </p>
          <div className="bg-gray-100 border border-gray-300 rounded p-3 font-mono text-lg text-center break-all">
            {result.temporary_password}
          </div>
          <p className="text-xs text-red-600">
            Copy this now. It will not be shown again.
          </p>
          <div className="flex justify-end pt-4 border-t border-gray-200">
            <Button onClick={handleClose}>Done</Button>
          </div>
        </div>
      )}
    </Modal>
  );
}
