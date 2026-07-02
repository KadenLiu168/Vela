import type { ReactNode } from "react";

type FeedbackMessageProps = {
  children: ReactNode;
  className?: string;
  variant: "error" | "info" | "loading" | "success";
};

export function FeedbackMessage({ children, className, variant }: FeedbackMessageProps) {
  const role = variant === "error" ? "alert" : "status";
  const classes = ["feedback-message", `feedback-message-${variant}`, className]
    .filter(Boolean)
    .join(" ");

  return (
    <div aria-live="polite" className={classes} role={role}>
      {children}
    </div>
  );
}
