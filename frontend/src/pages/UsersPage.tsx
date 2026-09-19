import { useState } from "react";
import { TableSkeleton } from "@/components/Skeleton";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listStaff, disableStaff, enableStaff, StaffUser, Role,
} from "@/api/users";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Table } from "@/components/Table";
import { formatDate } from "@/lib/format";
import { CreateStaffModal } from "./users/CreateStaffModal";
import { ResetPasswordModal } from "./users/ResetPasswordModal";
import clsx from "clsx";

const ROLE_LABEL: Record<Role, string> = {
  MAKER: "Maker",
  CHECKER: "Checker",
  CERTIFIER: "Certifier",
  SUPERADMIN: "Superadmin",
  MEMBER: "Member",
  BOARD: "Board",
  AUDITOR: "Auditor",
};

export function UsersPage() {
  const qc = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [resetUser, setResetUser] = useState<StaffUser | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["users", "staff"],
    queryFn: listStaff,
  });

  const toggleMutation = useMutation({
    mutationFn: async ({ id, active }: { id: string; active: boolean }) =>
      active ? enableStaff(id) : disableStaff(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users", "staff"] });
    },
  });

  const rows: StaffUser[] = data ?? [];
  const activeCount = rows.filter((r) => r.is_active).length;
  const disabledCount = rows.length - activeCount;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Users</h1>
          <p className="text-sm text-gray-500">
            Staff accounts and role assignments
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>+ Create User</Button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card title="Total Staff">
          <p className="text-2xl font-bold text-gray-800">{rows.length}</p>
        </Card>
        <Card title="Active">
          <p className="text-2xl font-bold text-green-700">{activeCount}</p>
        </Card>
        <Card title="Disabled">
          <p className="text-2xl font-bold text-gray-500">{disabledCount}</p>
        </Card>
      </div>

      <Card>
        {isLoading && (
          <TableSkeleton rows={5} cols={7} />
        )}
        {isError && (
          <p className="text-sm text-red-600 py-8 text-center">
            Failed to load users.
          </p>
        )}

        {!isLoading && !isError && (
          <Table
            headers={[
              "Username",
              "Name",
              "Role",
              "Email",
              "Status",
              "Last Login",
              "Actions",
            ]}
            empty={rows.length === 0}
          >
            {rows.map((u) => (
              <tr
                key={u.id}
                className={clsx(
                  "border-b border-gray-100 hover:bg-gray-50",
                  !u.is_active && "opacity-60"
                )}
              >
                <td className="py-2 px-2 font-mono text-sm">{u.username}</td>
                <td className="py-2 px-2">
                  {u.first_name || u.last_name
                    ? `${u.first_name} ${u.last_name}`.trim()
                    : "—"}
                </td>
                <td className="py-2 px-2">
                  <span className="inline-block px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-800">
                    {ROLE_LABEL[u.role]}
                  </span>
                </td>
                <td className="py-2 px-2 text-gray-600 text-sm">
                  {u.email || "—"}
                </td>
                <td className="py-2 px-2">
                  {u.is_active ? (
                    <Badge value="Active" />
                  ) : (
                    <Badge value="Disabled" />
                  )}
                </td>
                <td className="py-2 px-2 text-xs text-gray-500">
                  {u.last_login ? formatDate(u.last_login) : "Never"}
                </td>
                <td className="py-2 px-2 space-x-2 whitespace-nowrap">
                  <button
                    onClick={() => setResetUser(u)}
                    className="text-brand-600 hover:underline text-xs"
                  >
                    Reset Password
                  </button>
                  <button
                    onClick={() =>
                      toggleMutation.mutate({
                        id: u.id,
                        active: !u.is_active,
                      })
                    }
                    className={clsx(
                      "hover:underline text-xs",
                      u.is_active
                        ? "text-red-600"
                        : "text-green-600"
                    )}
                  >
                    {u.is_active ? "Disable" : "Enable"}
                  </button>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      <CreateStaffModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
      />
      <ResetPasswordModal
        user={resetUser}
        open={!!resetUser}
        onClose={() => setResetUser(null)}
      />
    </div>
  );
}