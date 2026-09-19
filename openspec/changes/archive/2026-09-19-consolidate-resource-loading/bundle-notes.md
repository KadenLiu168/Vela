# Bundle notes: consolidate-resource-loading

This change declares no spec-level behavior change, so it does not revise any
budget band. These notes record the measurement because the change's second
motivation was the lazy band's headroom.

Build identity is unchanged from the reviewed identity (Node v25.8.2, npm
11.11.1, Vite 7.3.6, lockfile `770031e7e424b525f90d9da3ea5b7fea06e2e9e67d61b819e9cf50102cd77a34`);
no dependency, toolchain, or lockfile change is part of this change.

## Measured after the change

| Band | Before | After | Delta | Band | Headroom |
|---|---:|---:|---:|---:|---:|
| Eager application (raw) | 54,402 | 54,448 | +46 | 55,000 | 552 |
| Initial JavaScript (raw) | 283,589 | 283,635 | +46 | 284,000 | 365 |
| Lazy route JavaScript (raw) | 69,446 | 68,322 | **−1,124** | 70,000 | 1,678 |
| Total JavaScript (raw) | 353,035 | 351,957 | **−1,078** | 354,000 | 2,043 |

The lazy band is the point: six pages now share one 807-raw-byte module
(`useResource-*.js`, counted once in the lazy aggregate) instead of carrying
six handwritten copies of the same lifecycle.

## The eager +46 bytes are not attributed

No module in the eager graph was edited by this change. The eager graph is the
`index-*.js` chunk plus the React runtime chunk; `useResource`, `listQuery`,
`listReturn`, and `Pagination` all landed in the lazy aggregate or their own
lazy chunks. Checked by searching the built `index-*.js` for strings unique to
the modules this change touched (for example `No rows at this offset.`, which
belongs to the Pagination chunk) — none of them appear there.

The delta is therefore a chunk-boundary bookkeeping effect whose cause I did
not isolate further. It is recorded rather than explained, and it stays well
inside the eager band (552 raw bytes of headroom remain).
