import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listFiscalYears } from "@/api/shu";
import { useAuth } from "@/auth/useAuth";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { Table } from "@/components/Table";
import { formatMoney, formatDate } from "@/lib/format";
import { CreateFiscalYearModal } from "./shu/CreateFiscalYearModal";

export function ShuPage() {
  const { profile } = useAuth();
  const [createOpen, setCreateOpen] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["shu", "fiscal-years"],
    queryFn: listFiscalYears,
  });

  const canCreate = profile?.role === "SUPERADMIN";

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">
            Sisa Hasil Usaha (SHU)
          </h1>
          <p className="text-sm text-gray-500">
            Annual surplus distribution
          </p>
        </div>
        {canCreate && (
          <Button onClick={() => setCreateOpen(true)}>
            + Create Fiscal Year
          </Button>
        )}
      </div>

      <Card>
        {isLoading && (
          <p className="text-sm text-gray-500 py-8 text-center">Loading…</p>
        )}
        {isError && (
          <p className="text-sm text-red-600 py-8 text-center">
            Failed to load fiscal years.
          </p>
        )}

        {data && (
          <Table
            headers={[
              "Period",
              "Status",
              "Net Surplus",
              "Social Capital",
              "Legal Reserve",
              "Actions",
            ]}
            empty={data.length === 0}
          >
            {data.map((fy) => (
              <tr
                key={fy.id}
                className="border-b border-gray-100 hover:bg-gray-50"
              >
                <td className="py-3 px-2 font-medium">
                  {formatDate(fy.year_start)} – {formatDate(fy.year_end)}
                </td>
                <td className="py-3 px-2">
                  <Badge value={fy.status} />
                </td>
                <td className="py-3 px-2">
                  ${formatMoney(fy.net_surplus)}
                </td>
                <td className="py-3 px-2">
                  ${formatMoney(fy.kapital_sosial)}
                </td>
                <td className="py-3 px-2">
                  ${formatMoney(fy.accumulated_reserva_legal)}
                </td>
                <td className="py-3 px-2">
                  <Link
                    to={`/shu/${fy.id}`}
                    className="text-brand-600 hover:underline text-xs"
                  >
                    Open
                  </Link>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      <CreateFiscalYearModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
      />
    </div>
  );
}