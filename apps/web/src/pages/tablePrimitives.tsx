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

/** Keyboard-accessible horizontal scroll region for wide data tables.
 *  The region carries an accessible name, a programmatic tab stop and a
 *  visible focus outline, so table columns stay reachable by keyboard. */
export function ScrollableTableWrap({
  children,
  className,
  label
}: {
  children: ReactNode;
  className?: string;
  label: string;
}) {
  return (
    <div
      aria-label={label}
      className={className ? `holdings-table-wrap ${className}` : "holdings-table-wrap"}
      role="region"
      tabIndex={0}
    >
      {children}
    </div>
  );
}
