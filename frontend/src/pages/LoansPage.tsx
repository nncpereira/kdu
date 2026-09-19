import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listLoans, Loan, LoanStatus } from "@/api/loans";
import { useAuth } from "@/auth/useAuth";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Table } from "@/components/Table";
import { Pagination } from "@/components/Pagination";
import { formatMoney, formatDate } from "@/lib/format";
import { OriginateLoanModal } from "./loans/OriginateLoanModal";

const STATUSES: (LoanStatus | "")[] = [
  "",
  "DRAFT",
  "DISBURSED",
  "FULLY_REPAID",
  "WRITTEN_OFF",
];

export function LoansPage() {
  const { profile } = useAuth();
  const [status, setStatus] = useState<LoanStatus | "">("");
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);

  const pageSize = 20;

  const { data, isLoading, isError } = useQuery({
    queryKey: ["loans", { status, page }],
    queryFn: () =>
      listLoans({
        status: status || undefined,
        page,
        page_size: pageSize,
      }),
  });

  const canOriginate =
    profile?.role === "MAKER" || profile?.role === "SUPERADMIN";

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Loans</h1>
          <p className="text-sm text-gray-500">
            Active and historical loans
          </p>
        </div>
        {canOriginate && (
          <Button onClick={() => setCreateOpen(true)}>+ Originate Loan</Button>
        )}
      </div>

      <Card>
        <div className="flex flex-wrap gap-3 mb-4">
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value as LoanStatus | "");
              setPage(1);
            }}
            className="border border-gray-300 rounded px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {STATUSES.map((s) => (
              <option key={s || "all"} value={s}>
                {s ? s.replace("_", " ") : "All statuses"}
              </option>
            ))}
          </select>
        </div>

        {isLoading && (
          <p className="text-sm text-gray-500 py-8 text-center">Loading…</p>
        )}
        {isError && (
          <p className="text-sm text-red-600 py-8 text-center">
            Failed to load loans.
          </p>
        )}

        {data && (
          <>
            <Table
              headers={[
                "Member",
                "Principal",
                "Outstanding",
                "Rate",
                "Term",
                "Status",
                "Disbursed",
                "Actions",
              ]}
              empty={data.results.length === 0}
            >
              {data.results.map((loan) => (
                <tr
                  key={loan.id}
                  className="border-b border-gray-100 hover:bg-gray-50"
                >
                  <td className="py-2 px-2 font-mono text-xs">
                    {loan.member_number}
                  </td>
                  <td className="py-2 px-2">
                    ${formatMoney(loan.principal_original)}
                  </td>
                  <td className="py-2 px-2 font-medium">
                    ${formatMoney(loan.principal_outstanding)}
                  </td>
                  <td className="py-2 px-2 text-gray-600">
                    {formatMoney(
                      (parseFloat(loan.monthly_rate) * 100).toFixed(2)
                    )}
                    %
                  </td>
                  <td className="py-2 px-2 text-gray-600">
                    {loan.term_months} mo
                  </td>
                  <td className="py-2 px-2">
                    <Badge value={loan.status} />
                  </td>
                  <td className="py-2 px-2 text-gray-500 text-xs">
                    {formatDate(loan.disbursed_date)}
                  </td>
                  <td className="py-2 px-2">
                    <Link
                      to={`/loans/${loan.id}`}
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

      <OriginateLoanModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
      />
    </div>
  );
}