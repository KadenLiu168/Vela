# Vela Web

Minimal Vite, React, and TypeScript frontend skeleton for Vela.

## Setup

Install dependencies from the app directory:

```bash
cd apps/web
npm install
```

## Development

Start the development server from the repository root:

```bash
npm --prefix apps/web run dev
```

Equivalent app-local command:

```bash
cd apps/web
npm run dev
```

## Validation

Run frontend tests:

```bash
npm --prefix apps/web run test
```

Run lint checks:

```bash
npm --prefix apps/web run lint
```

Run type checking:

```bash
npm --prefix apps/web run typecheck
```

Build the frontend:

```bash
npm --prefix apps/web run build
```

## Structure

```text
src/
├── api/          API client modules
├── components/   Shared React components
├── pages/        Page-level React components
└── test/         Test setup and utilities
```
