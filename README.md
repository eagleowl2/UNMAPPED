# UNMAPPED Protocol

> Make the chaotic, multilingual reality of LMIC livelihoods legible to the
> formal economy — without forcing anyone to flatten themselves first.

Hackathon submission for the World Bank brief. v0.2 spec (Human Layer +
Constraint Layer + Localization Layer) is being incrementally implemented in
modular SemVer-tagged releases per Section 12.

## Repo layout

```
.
├── frontend/             ← Skills Signal Engine SPA (Module M1, this PR)
├── docs/
│   └── api-contract.md   ← /parse contract — frontend ⇄ backend agreement
├── CHANGELOG.md
├── PROJECT_LOG.md        ← append-only log per Section 12.4
└── LICENSE
```

The FastAPI backend lives in a sibling module owned by Claude 1; see
[`docs/api-contract.md`](docs/api-contract.md) for the interface.

## Run the demo

```bash
cd frontend
npm install
npm run dev
```

The SPA falls back to a bundled mock parser when `VITE_API_URL` is unset, so
you can run the full pitch with no backend at all.

## Versioning & branching

- **Versioning:** SemVer (Section 12.1). Pre-release tags (`-sse-alpha.N`)
  for each module milestone.
- **Branches:** Each module ships from `module/<id>-<slug>` per Section 12.2.
- **Logging:** Every major contribution appends a `PROJECT_LOG.md` entry per
  Section 12.4.

Current release: **v0.3.0-sse-alpha.1** (Module M1 — SSE UI).
