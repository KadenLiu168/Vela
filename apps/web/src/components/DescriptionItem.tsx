import type { ReactNode } from "react";

type DescriptionItemProps = {
  label: string;
  value: ReactNode;
};

export function DescriptionItem({ label, value }: DescriptionItemProps) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  );
}
