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

export function TableCells({ cells, classNames }: { cells: ReactNode[]; classNames?: readonly (string | undefined)[] }) {
  return cells.map((cell, index) => (
    <td key={index} className={classNames?.[index]}>
      {cell}
    </td>
  ));
}
