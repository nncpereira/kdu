import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  getMyProfile,
  updateMyMemberProfile,
} from "@/api/memberPortal";
import { changePassword } from "@/api/users";
import { useAuth } from "@/auth/useAuth";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { Badge } from "@/components/Badge";
import { formatDate } from "@/lib/format";

export function PortalProfilePage() {
  const { profile, refreshProfile } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-800">My Profile</h1>
        <p className="text-sm text-gray-500">
          Your account details and password
        </p>
      </div>

      {profile?.must_change_password && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm rounded-lg p-4">
          <p className="font-medium">Password change required</p>
          <p className="text-xs mt-1">
            Your password was reset by an administrator. Please set a new one
            now before continuing.
          </p>
        </div>
      )}

      <ContactDetailsForm />
      <PasswordForm onSaved={refreshProfile} />
      <ReadOnlyIdentity />
    </div>
  );
}

// ====================================================================
// Contact details
// ====================================================================
function ContactDetailsForm() {
  const qc = useQueryClient();
  const { data: member } = useQuery({
    queryKey: ["portal", "me"],
    queryFn: getMyProfile,
  });

  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [aldeia, setAldeia] = useState("");
  const [suco, setSuco] = useState("");
  const [posto, setPosto] = useState("");
  const [municipio, setMunicipio] = useState("");
  const [profession, setProfession] = useState("");

  // Populate once data arrives.
  useEffect(() => {
    if (member) {
      setPhone(member.phone_number ?? "");
      setEmail(member.email ?? "");
      setAldeia(member.aldeia ?? "");
      setSuco(member.suco ?? "");
      setPosto(member.posto ?? "");
      setMunicipio(member.municipio ?? "");
      setProfession(member.profession ?? "");
    }
  }, [member]);

  const mutation = useMutation({
    mutationFn: () =>
      updateMyMemberProfile({
        phone_number: phone,
        email,
        aldeia,
        suco,
        posto,
        municipio,
        profession,
      }),
    onSuccess: () => {
      toast.success("Contact details updated.");
      qc.invalidateQueries({ queryKey: ["portal"] });
    },
    onError: (err: any) => {
      toast.error(
        err?.response?.data?.detail ?? "Failed to update details."
      );
    },
  });

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    await mutation.mutateAsync();
  }

  if (!member) {
    return (
      <Card title="Contact Details">
        <div className="h-24 animate-pulse bg-gray-100 rounded" />
      </Card>
    );
  }

  return (
    <Card title="Contact Details">
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Input
            label="Aldeia"
            value={aldeia}
            onChange={(e) => setAldeia(e.target.value)}
          />
          <Input
            label="Suco"
            value={suco}
            onChange={(e) => setSuco(e.target.value)}
          />
          <Input
            label="Posto"
            value={posto}
            onChange={(e) => setPosto(e.target.value)}
          />
          <Input
            label="Municipio"
            value={municipio}
            onChange={(e) => setMunicipio(e.target.value)}
          />
        </div>

        <Input
          label="Profession"
          value={profession}
          onChange={(e) => setProfession(e.target.value)}
        />

        <div className="flex justify-end pt-4 border-t border-gray-200">
          <Button type="submit" loading={mutation.isPending}>
            Save Changes
          </Button>
        </div>
      </form>
    </Card>
  );
}

// ====================================================================
// Password
// ====================================================================
function PasswordForm({ onSaved }: { onSaved: () => Promise<void> }) {
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => changePassword(oldPassword, newPassword),
    onSuccess: async () => {
      toast.success("Password updated.");
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setError(null);
      await onSaved();
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.detail ??
        err?.response?.data?.fields?.old_password?.[0] ??
        "Failed to change password.";
      setError(msg);
      toast.error(msg);
    },
  });

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match.");
      return;
    }
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    await mutation.mutateAsync();
  }

  return (
    <Card title="Change Password">
      <form onSubmit={onSubmit} className="space-y-4">
        <Input
          label="Current Password"
          type="password"
          value={oldPassword}
          onChange={(e) => setOldPassword(e.target.value)}
          autoComplete="current-password"
          required
        />
        <Input
          label="New Password"
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          autoComplete="new-password"
          minLength={8}
          required
        />
        <Input
          label="Confirm New Password"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          autoComplete="new-password"
          minLength={8}
          required
        />

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded px-3 py-2">
            {error}
          </div>
        )}

        <div className="flex justify-end pt-4 border-t border-gray-200">
          <Button type="submit" loading={mutation.isPending}>
            Change Password
          </Button>
        </div>
      </form>
    </Card>
  );
}

// ====================================================================
// Read-only identity block
// ====================================================================
function ReadOnlyIdentity() {
  const { data: member } = useQuery({
    queryKey: ["portal", "me"],
    queryFn: getMyProfile,
  });

  if (!member) return null;

  return (
    <Card title="Membership Details">
      <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3 text-sm">
        <Row label="Member Number" value={member.membership_number} />
        <Row label="Status" value={member.status} />
        <Row label="Full Name" value={member.full_name} />
        <Row label="Date of Birth" value={formatDate(member.date_of_birth)} />
        <Row label="National ID" value={member.national_id || "—"} />
        <Row label="Joined" value={formatDate(member.date_joined)} />
        <Row label="Kapital Sosial" value={`$${member.kapital_sosial_balance}`} />
      </dl>
      <p className="text-xs text-gray-500 mt-4 pt-4 border-t border-gray-100">
        Your name, date of birth, national ID, and member number can only be
        changed at the cooperative office with staff assistance.
      </p>
    </Card>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-gray-100 pb-2">
      <dt className="text-gray-500">{label}</dt>
      <dd className="text-gray-800 font-medium text-right">{value}</dd>
    </div>
  );
}