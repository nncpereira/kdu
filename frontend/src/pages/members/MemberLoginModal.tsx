import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import {
  createMemberLogin,
  resetMemberLoginPassword,
  type Member,
  type LoginCredentials,
} from "@/api/members";

interface Props {
  member: Member | null;
  mode: "create" | "reset";
  open: boolean;
  onClose: () => void;
}

export function MemberLoginModal({ member, mode, open, onClose }: Props) {
  const qc = useQueryClient();
  const [creds, setCreds] = useState<LoginCredentials | null>(null);
  const [copied, setCopied] = useState(false);

  const mutation = useMutation({
    mutationFn: () =>
      mode === "create"
        ? createMemberLogin(member!.id)
        : resetMemberLoginPassword(member!.id),
    onSuccess: (data) => {
      setCreds(data);
      qc.invalidateQueries({ queryKey: ["members"] });
      qc.invalidateQueries({ queryKey: ["member", member!.id] });
      toast.success(
        mode === "create" ? "Member login created." : "Password reset."
      );
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail ?? "Action failed.");
    },
  });

  if (!member) return null;

  function handleClose() {
    setCreds(null);
    setCopied(false);
    onClose();
  }

  async function copyToClipboard(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Could not copy to clipboard.");
    }
  }

  return (
    <Modal
      open={open}
      onClose={handleClose}
      title={mode === "create" ? "Create Member Login" : "Reset Member Password"}
      size="md"
    >
      {!creds ? (
        // ---- Confirmation step -----------------------------------------
        <div className="space-y-4">
          <div className="bg-gray-50 rounded p-3 text-sm">
            <p className="font-medium">{member.full_name}</p>
            <p className="text-xs text-gray-500 font-mono">
              {member.membership_number}
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Status: <span className="font-medium">{member.status}</span>
            </p>
          </div>

          {mode === "create" ? (
            <div className="bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded p-3">
              <p className="font-medium mb-1">What this does</p>
              <p>
                Creates a member portal login with a username derived from
                the member's name and a random temporary password. The
                member is required to change the password on first
                sign-in.
              </p>
            </div>
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-xs rounded p-3">
              <p className="font-medium mb-1">Password reset</p>
              <p>
                A new temporary password will be generated. The member's current
                password will stop working immediately. Their existing login{" "}
                <span className="font-mono">{member.login_username}</span> stays
                the same.
              </p>
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
              {mode === "create" ? "Create Login" : "Reset Password"}
            </Button>
          </div>
        </div>
      ) : (
        // ---- Success step -----------------------------------------------
        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 text-green-800 text-sm rounded p-3">
            {creds.detail}
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Username
            </label>
            <div className="flex gap-2">
              <div className="flex-1 bg-gray-100 border border-gray-300 rounded px-3 py-2 font-mono text-sm">
                {creds.login_username}
              </div>
              <Button
                variant="secondary"
                onClick={() => copyToClipboard(creds.login_username)}
              >
                Copy
              </Button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Temporary Password
            </label>
            <div className="flex gap-2">
              <div className="flex-1 bg-gray-100 border border-gray-300 rounded px-3 py-2 font-mono text-sm break-all">
                {creds.temporary_password}
              </div>
              <Button
                variant="secondary"
                onClick={() => copyToClipboard(creds.temporary_password)}
              >
                {copied ? "Copied ✓" : "Copy"}
              </Button>
            </div>
          </div>

          <div className="bg-red-50 border border-red-200 text-red-800 text-xs rounded p-3">
            <p className="font-medium mb-1">Write this down now</p>
            <p>
              The password will not be shown again. Share it with the member in
              person or through a secure channel. They will be prompted to
              change it on first login.
            </p>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-gray-200">
            <Button
              variant="secondary"
              onClick={() =>
                copyToClipboard(
                  `Username: ${creds.login_username}\nTemporary password: ${creds.temporary_password}`
                )
              }
            >
              Copy Both
            </Button>
            <Button onClick={handleClose}>Done</Button>
          </div>
        </div>
      )}
    </Modal>
  );
}