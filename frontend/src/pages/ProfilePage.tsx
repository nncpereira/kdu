import { FormEvent, useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { Badge } from "@/components/Badge";
import { useAuth } from "@/auth/useAuth";
import { changePassword, updateMyProfile } from "@/api/users";
import { formatDate } from "@/lib/format";

export function ProfilePage() {
  const { profile, refreshProfile, logout } = useAuth();
  const navigate = useNavigate();

  if (!profile) {
    return (
      <div className="p-6 text-sm text-gray-500">Loading profile…</div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">My Profile</h1>
        <p className="text-sm text-gray-500">
          Manage your account information and password
        </p>
      </div>

      {/* Identity summary */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-lg font-semibold text-gray-800">
              {profile.first_name || profile.last_name
                ? `${profile.first_name} ${profile.last_name}`.trim()
                : profile.username}
            </p>
            <p className="text-sm text-gray-500 font-mono">
              @{profile.username}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Account created {formatDate(profile.created_at)}
            </p>
          </div>
          <div className="text-right">
            <Badge value={profile.role} />
            {profile.must_change_password && (
              <p className="text-xs text-red-600 mt-2 font-medium">
                Password change required
              </p>
            )}
          </div>
        </div>
      </Card>

      {/* Personal details form */}
      <PersonalDetailsForm
        initial={{
          first_name: profile.first_name,
          last_name: profile.last_name,
          email: profile.email,
        }}
        onSaved={refreshProfile}
      />

      {/* Password form */}
      <PasswordForm
        mustChange={profile.must_change_password}
        onSaved={async () => {
          await refreshProfile();
          // If the password was a forced reset, send them to the dashboard.
          if (profile.must_change_password) {
            navigate("/dashboard");
          }
        }}
        onLogout={logout}
      />
    </div>
  );
}

// ====================================================================
// Personal Details
// ====================================================================
function PersonalDetailsForm({
  initial,
  onSaved,
}: {
  initial: { first_name: string; last_name: string; email: string };
  onSaved: () => Promise<void>;
}) {
  const [firstName, setFirstName] = useState(initial.first_name);
  const [lastName, setLastName] = useState(initial.last_name);
  const [email, setEmail] = useState(initial.email);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset success message after 3s
  useEffect(() => {
    if (success) {
      const t = setTimeout(() => setSuccess(false), 3000);
      return () => clearTimeout(t);
    }
  }, [success]);

  const mutation = useMutation({
    mutationFn: () =>
      updateMyProfile({
        first_name: firstName,
        last_name: lastName,
        email,
      }),
    onSuccess: async () => {
      setSuccess(true);
      setError(null);
      await onSaved();
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail;
      const fieldErr = err?.response?.data?.fields;
      if (typeof detail === "string") setError(detail);
      else if (fieldErr?.email) setError(fieldErr.email[0]);
      else setError("Failed to update profile.");
    },
  });

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    await mutation.mutateAsync();
  }

  return (
    <Card title="Personal Details">
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

        <p className="text-xs text-gray-500">
          Your username and role cannot be changed here. Contact a Superadmin
          if they need to be updated.
        </p>

        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 text-sm rounded px-3 py-2">
            Profile updated.
          </div>
        )}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded px-3 py-2">
            {error}
          </div>
        )}

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
function PasswordForm({
  mustChange,
  onSaved,
  onLogout,
}: {
  mustChange: boolean;
  onSaved: () => Promise<void>;
  onLogout: () => void;
}) {
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (success) {
      const t = setTimeout(() => setSuccess(false), 3000);
      return () => clearTimeout(t);
    }
  }, [success]);

  const mutation = useMutation({
    mutationFn: () => changePassword(oldPassword, newPassword),
    onSuccess: async () => {
      setSuccess(true);
      setError(null);
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
      await onSaved();
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail;
      const fieldErr = err?.response?.data?.fields;
      if (typeof detail === "string") setError(detail);
      else if (fieldErr?.old_password) setError(fieldErr.old_password[0]);
      else if (fieldErr?.new_password) setError(fieldErr.new_password[0]);
      else setError("Failed to change password.");
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
      {mustChange && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm rounded px-3 py-3 mb-4">
          <p className="font-medium">Password change required</p>
          <p className="text-xs mt-1">
            An administrator reset your password. Please set a new one now
            before continuing.
          </p>
        </div>
      )}

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

        <p className="text-xs text-gray-500">
          Minimum 8 characters. Choose something you don't use elsewhere.
        </p>

        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 text-sm rounded px-3 py-2">
            Password updated.{" "}
            <button
              type="button"
              onClick={onLogout}
              className="underline font-medium"
            >
              Log out and sign in again
            </button>{" "}
            if you want a fresh session.
          </div>
        )}
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