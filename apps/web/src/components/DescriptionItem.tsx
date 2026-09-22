import type { ReactNode } from "react";

type DescriptionItemProps = {
  label: string;
  value: ReactNode;
  /** Marks a quantitative/code-like value so it renders in Mono with
   * tabular numerals. Language values (names, descriptions, statuses) stay
   * Sans by default; family is chosen by content semantics, never inferred. */
  mono?: boolean;
};

export function DescriptionItem({ label, value, mono = false }: DescriptionItemProps) {
  return (
    <>
      <dt>{label}</dt>
      <dd className={mono ? "mono-compact" : undefined}>{value}</dd>
    </>
  );
}
