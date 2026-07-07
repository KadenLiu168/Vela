import { Skeleton } from "./Skeleton";

export const TextDefault = () => (
  <p>
    <Skeleton /> Loading summary line.
  </p>
);

export const TextCustomWidth = () => (
  <p>
    <Skeleton width="20em" /> Custom width.
  </p>
);

export const BlockShape = () => (
  <div style={{ display: "grid", gap: "0.5em", maxWidth: 300 }}>
    <Skeleton as="block" height="2.5em" />
    <Skeleton as="block" height="2.5em" />
    <Skeleton as="block" height="2.5em" />
  </div>
);

export const CircleAvatar = () => (
  <div style={{ display: "flex", gap: "1em" }}>
    <Skeleton variant="circle" diameter="2em" />
    <Skeleton variant="circle" diameter="3em" />
    <Skeleton variant="circle" diameter="4em" />
  </div>
);

export const ReducedMotion = () => (
  <p style={{ fontFamily: "sans-serif" }}>
    <Skeleton /> With prefers-reduced-motion, the pulse freezes at opacity 0.55.
  </p>
);
