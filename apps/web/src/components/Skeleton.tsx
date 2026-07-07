import type { CSSProperties, HTMLAttributes } from "react";

type SkeletonVariant = "text" | "circle";
type SkeletonShape = "inline" | "block";

export type SkeletonProps = {
  as?: SkeletonShape;
  variant?: SkeletonVariant;
  width?: string | number;
  height?: string | number;
  diameter?: string | number;
  className?: string;
} & Omit<HTMLAttributes<HTMLElement>, "className">;

function toCssSize(value: string | number | undefined, fallback: string): string {
  if (value === undefined) return fallback;
  return typeof value === "number" ? `${value}px` : value;
}

export function Skeleton({
  as = "inline",
  variant = "text",
  width,
  height,
  diameter,
  className,
  style,
  ...rest
}: SkeletonProps) {
  const isCircle = variant === "circle";
  const sizeStyle: CSSProperties = isCircle
    ? {
        width: toCssSize(diameter, "3em"),
        height: toCssSize(diameter, "3em"),
        borderRadius: "9999px"
      }
    : {
        width: toCssSize(width, "100%"),
        height: toCssSize(height, "0.75em")
      };

  const classes = ["skeleton", "skeleton-pulse", isCircle && "skeleton-circle", className]
    .filter(Boolean)
    .join(" ");

  const mergedStyle: CSSProperties = { ...sizeStyle, ...style };

  if (as === "block") {
    return (
      <div
        aria-hidden="true"
        className={classes}
        role="presentation"
        style={mergedStyle}
        {...rest}
      />
    );
  }

  return (
    <span
      aria-hidden="true"
      className={classes}
      role="presentation"
      style={mergedStyle}
      {...rest}
    />
  );
}
