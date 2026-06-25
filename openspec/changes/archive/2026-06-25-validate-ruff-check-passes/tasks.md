## 1. Ruff Lint Validation

- [x] 1.1 Run `uv run ruff check .` from the repository root and capture the result.
- [x] 1.2 If Ruff lint fails, apply the smallest scoped fix needed for COP-76.

## 2. Final Verification

- [x] 2.1 Run the existing pytest, lint, type check, and OpenSpec validation commands that apply to this repository.
- [x] 2.2 Confirm the final change only covers COP-76 and does not include unrelated formatting-only changes.
