/** Shared Dashboard card heading: an optional status pill on the right and an
 *  optional eyebrow label. Extracted so the Dashboard decision-layer sections
 *  and the reference panels render one identical heading primitive. */

export type StatusPillVariant = "success" | "partial" | "error" | "neutral" | "loading";

export type StatusPill = {
  label: string;
  variant: StatusPillVariant;
};

export function StatusPillBadge({ label, variant }: StatusPill) {
  return (
    <span className={`status-pill status-pill-${variant}`} aria-label={`Status: ${label}`}>
      {label}
    </span>
  );
}

export function PanelHeading({
  eyebrow,
  title,
  statusPill
}: {
  eyebrow?: string;
  title: string;
  statusPill?: StatusPill;
}) {
  return (
    <div className="panel-heading">
      <h3>{title}</h3>
      {eyebrow || statusPill ? (
        <div className="panel-heading-end">
          {statusPill ? <StatusPillBadge {...statusPill} /> : null}
          {eyebrow ? <span>{eyebrow}</span> : null}
        </div>
      ) : null}
    </div>
  );
}
