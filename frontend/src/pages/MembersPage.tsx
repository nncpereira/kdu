import { useState } from "react";
import { TableSkeleton } from "@/components/Skeleton";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listMembers, Member, MemberStatus } from "@/api/members";
import { useAuth } from "@/auth/useAuth";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Table } from "@/components/Table";
import { Pagination } from "@/components/Pagination";
import { formatMoney, formatDate } from "@/lib/format";
import { CreateMemberModal } from "./members/CreateMemberModal";

const STATUSES: (MemberStatus | "")[] = [
  "",
  "Pending",
  "Active",
  "Dormant",
  "Suspended",
  "Closed",
];

export function MembersPage() {
  const { profile } = useAuth();
  const [status, setStatus] = useState<string>("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);

  const pageSize = 20;

  const { data, isLoading, isError } = useQuery({
    queryKey: ["members", { status, search, page }],
    queryFn: () =>
      listMembers({
        status: status || undefined,
        search: search || undefined,
        page,
        page_size: pageSize,
      }),
  });

  const canCreate = profile?.role === "MAKER" || profile?.role === "SUPERADMIN";

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Members</h1>
          <p className="text-sm text-gray-500">
            Member register and capital status
          </p>
        </div>
        {canCreate && (
          <Button onClick={() => setCreateOpen(true)}>+ Onboard Member</Button>
        )}
      </div>

      <Card>
        <div className="flex flex-wrap gap-3 mb-4">
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Search by name, member number, phone..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="border border-gray-300 rounded px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {STATUSES.map((s) => (
              <option key={s || "all"} value={s}>
                {s || "All statuses"}
              </option>
            ))}
          </select>
        </div>

        {isLoading && (
          <TableSkeleton rows={5} cols={7} />
        )}
        {isError && (
          <p className="text-sm text-red-600 py-8 text-center">
            Failed to load members.
          </p>
        )}

        {data && (
          <>
            <Table
              headers={[
                "Member #",
                "Name",
                "Status",
                "Capital",
                "Phone",
                "Joined",
                "Actions",
              ]}
              empty={data.results.length === 0}
            >
              {data.results.map((m) => (
                <tr
                  key={m.id}
                  className="border-b border-gray-100 hover:bg-gray-50"
                >
                  <td className="py-2 px-2 font-mono text-xs">
                    {m.membership_number}
                  </td>
                  <td className="py-2 px-2">
                    <Link
                      to={`/members/${m.id}`}
                      className="text-brand-600 hover:underline"
                    >
                      {m.full_name}
                    </Link>
                  </td>
                  <td className="py-2 px-2">
                    <Badge value={m.status} />
                  </td>
                  <td className="py-2 px-2">
                    ${formatMoney(m.kapital_sosial_balance)}
                  </td>
                  <td className="py-2 px-2 text-gray-600">{m.phone_number}</td>
                  <td className="py-2 px-2 text-gray-500">
                    {formatDate(m.date_joined)}
                  </td>
                  <td className="py-2 px-2">
                    <Link
                      to={`/members/${m.id}`}
                      className="text-brand-600 hover:underline text-xs"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </Table>

            <Pagination
              count={data.count}
              page={page}
              pageSize={pageSize}
              onChange={setPage}
            />
          </>
        )}
      </Card>

      <CreateMemberModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
      />
    </div>
  );
}