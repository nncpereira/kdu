import { useQuery } from "@tanstack/react-query";
import { Modal } from "@/components/Modal";
import { Badge } from "@/components/Badge";
import { getJournalEntry } from "@/api/audit";
import { formatMoney, formatDate } from "@/lib/format";

interface Props {
  entryId: string | null;
  onClose: () => void;
}

export function JournalEntryDetailModal({ entryId, onClose }: Props) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["audit", "ledger", "detail", entryId],
    queryFn: () => getJournalEntry(entryId!),
    enabled: !!entryId,
  });

  const totalDebits =
    data?.lines
      .filter((l) => l.entry_type === "DEBIT")
      .reduce((sum, l) => sum + Number(l.amount), 0) ?? 0;
  const totalCredits =
    data?.lines
      .filter((l) => l.entry_type === "CREDIT")
      .reduce((sum, l) => sum + Number(l.amount), 0) ?? 0;

  return (
    <Modal
      open={!!entryId}
      onClose={onClose}
      title="Journal Entry"
      size="md"
    >
      {isLoading && (
        <p className="text-sm text-gray-500 py-4 text-center">Loading…</p>
      )}
      {isError && (
        <p className="text-sm text-red-600 py-4 text-center">
          Failed to load journal entry.
        </p>
      )}
      {data && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <Field label="Entry Date" value={formatDate(data.entry_date)} />
            <Field label="Status">
              <Badge value={data.status} />
              {data.is_reversal && (
                <span className="ml-2 px-1.5 py-0.5 text-[10px] font-medium bg-orange-100 text-orange-800 rounded align-middle">
                  REVERSAL
                </span>
              )}
            </Field>
            <Field
              label="Maker"
              value={data.maker_username ?? "—"}
            />
            <Field
              label="Certifier"
              value={data.certifier_username ?? "—"}
            />
          </div>

          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
              Description
            </p>
            <p className="text-sm text-gray-800">{data.description}</p>
          </div>

          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
              Lines
            </p>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-500 border-b border-gray-200">
                  <th className="py-1.5 pr-2 font-medium">Account</th>
                  <th className="py-1.5 pr-2 font-medium">Member</th>
                  <th className="py-1.5 pr-2 font-medium text-right">
                    Debit
                  </th>
                  <th className="py-1.5 pl-2 font-medium text-right">
                    Credit
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.lines.map((line) => (
                  <tr
                    key={line.id}
                    className="border-b border-gray-100 last:border-0"
                  >
                    <td className="py-1.5 pr-2">
                      <span className="font-mono text-xs text-gray-400 mr-1">
                        {line.account_code}
                      </span>
                      {line.account_name}
                    </td>
                    <td className="py-1.5 pr-2 text-xs text-gray-600">
                      {line.member_number
                        ? `${line.member_name} (${line.member_number})`
                        : "—"}
                    </td>
                    <td className="py-1.5 pr-2 text-right font-medium">
                      {line.entry_type === "DEBIT"
                        ? `$${formatMoney(line.amount)}`
                        : ""}
                    </td>
                    <td className="py-1.5 pl-2 text-right font-medium">
                      {line.entry_type === "CREDIT"
                        ? `$${formatMoney(line.amount)}`
                        : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t-2 border-gray-300 font-semibold">
                  <td className="py-1.5 pr-2" colSpan={2}>
                    Total
                  </td>
                  <td className="py-1.5 pr-2 text-right">
                    ${formatMoney(totalDebits.toFixed(2))}
                  </td>
                  <td className="py-1.5 pl-2 text-right">
                    ${formatMoney(totalCredits.toFixed(2))}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}
    </Modal>
  );
}

function Field({
  label,
  value,
  children,
}: {
  label: string;
  value?: string;
  children?: React.ReactNode;
}) {
  return (
    <div>
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
        {label}
      </p>
      <p className="text-sm text-gray-800 mt-0.5">{children ?? value}</p>
    </div>
  );
}
