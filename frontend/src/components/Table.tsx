import { ReactNode } from "react";

export function Table({
  headers,
  children,
  empty,
}: {
  headers: string[];
  children: ReactNode;
  empty?: boolean;
}) {
  if (empty) {
    return (
      <div className="py-12 text-center text-sm text-gray-500">
        No records to display.
      </div>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-left text-gray-500 border-b border-gray-200">
          <tr>
            {headers.map((h) => (
              <th key={h} className="py-2 px-2 font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}