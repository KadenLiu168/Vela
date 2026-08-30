import type { ReactNode } from "react";

export function TableHeader({ columns }: { columns: readonly string[] }) {
  return (
    <thead>
      <tr>
        {columns.map((column) => (
          <th key={column} scope="col">
            {column}
          </th>
        ))}
      </tr>
    </thead>
  );
}

export function TableCells({ cells }: { cells: ReactNode[] }) {
  return cells.map((cell, index) => <td key={index}>{cell}</td>);
}
