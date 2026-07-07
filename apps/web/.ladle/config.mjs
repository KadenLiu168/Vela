// apps/web/.ladle/config.mjs
//
// Ladle is a Vite-native component catalog for the @vela/web state
// components. Stories live in apps/web/src/components/*.stories.tsx
// and are discovered automatically.

/** @type {import('@ladle/react').Config} */
export default {
  // No provider wrappers required for the current state components.
  // Add a `provider` entry here when a future story needs
  // React Router, Redux, or a custom Theme context.
  stories: "src/components/*.stories.{ts,tsx}",
};
