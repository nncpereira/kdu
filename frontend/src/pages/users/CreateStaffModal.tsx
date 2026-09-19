import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Button } from "@/components/Button";
import { Input, Select } from "@/components/Input";
import { createStaff, Role } from "@/api/users";

interface Props {
  open: boolean;
  onClose: () => void;
}

const ROLES: { value: Role; label: string; description: string }[] = [
  {
    value: "MAKER",
    label: "Maker",
    description: "Initiates transactions (deposits, withdrawals, loans, expenses)",
  },
  {
    value: "CHECKER",
    label: "Checker",
    description: "First-level review of Maker submissions",
  },
  {
    value: "CERTIFIER",
    label: "Certifier",
    description: "Final approval — triggers ledger posting",
  },
  {
    value: "BOARD",
    label: "Board",
    description: "Read-only access to all reports",
  },
  {
    value: "AUDITOR",
    label: "Auditor",
    description: "Read-only access, PII masked",
  },
  {
    value: "SUPERADMIN",
    label: "Superadmin",
    description: "Full system access including configuration",
  },
];

export function CreateStaffModal({ open, onClose }: Props) {
  const qc = useQueryClient();
  const [username, setUsername] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("MAKER");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setUsername("");
      setFirstName("");
      setLastName("");
      setEmail("");
      setPassword("");
      setRole("MAKER");
      setError(null);
    }
  }, [open]);

  const mutation = useMutation({
    mutationFn: () =>
      createStaff({
        username,
        password,
        role,
        email,
        first_name: firstName,
        last_name: lastName,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users", "staff"] });
      onClose();
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail;
      const fieldErr = err?.response?.data?.fields;
      if (typeof detail === "string") setError(detail);
      else if (fieldErr?.username) setError(fieldErr.username[0]);
      else if (fieldErr?.password) setError(fieldErr.password[0]);
      else if (fieldErr?.role) setError(fieldErr.role[0]);
      else setError("Failed to create staff user.");
    },
  });

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    await mutation.mutateAsync();
  }

  const selectedRole = ROLES.find((r) => r.value === role);

  return (
    <Modal open={open} onClose={onClose} title="Create Staff User" size="md">
      <form onSubmit={onSubmit} className="space-y-4">
        <Input
          label="Username *"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="off"
          required
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="First Name"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
          />
          <Input
            label="Last Name"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
          />
        </div>

        <Input
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <Input
          label="Initial Password *"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          minLength={8}
          autoComplete="new-password"
          required
        />
        <p className="text-xs text-gray-500 -mt-2">
          Minimum 8 characters. The user will be forced to change it on first login.
        </p>

        <Select
          label="Role *"
          value={role}
          onChange={(e) => setRole(e.target.value as Role)}
        >
          {ROLES.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </Select>

        {selectedRole && (
          <div className="bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded p-3">
            <p className="font-medium">{selectedRole.label}</p>
            <p className="mt-0.5">{selectedRole.description}</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded px-3 py-2">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-4 border-t border-gray-200">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending}>
            Create User
          </Button>
        </div>
      </form>
    </Modal>
  );
}