# Changelog

All notable changes to UNMAPPED Protocol are tracked here.
The project follows [Semantic Versioning](https://semver.org) per the protocol's
Section 12.1, and the versions in this file map 1:1 to git tags on `main`.

## [0.3.0-sse-alpha.1] — 2026-04-26

### Added

- **`/frontend`** — single-page React + Vite + TypeScript + Tailwind app
  for the Skills Signal Engine demo (Module M1).
  - One-prompt input panel that accepts chaotic personal stories in any
    language (Ghana and Armenia samples included).
  - `ProfileCard` rendering the Human Layer per v0.2 Section 4.2: pseudonym,
    languages, parser-detected skills with evidence, wage and growth signal
    bars with rationale, and a network-entry channel + offline SVG map.
  - QR simulation (`qrcode.react`) for the share-link / verifiable claim
    handoff envisioned for v0.4.
  - Constraint-Layer demos: `SmsPreview` (160-char fallback, segment
    counter) and `UssdSimulator` (interactive feature-phone shell rendering
    the parser-supplied menu).
  - Locale switcher that reloads the SPA against a different
    `country_profile` (`GH` ↔ `AM`).
  - Offline-first behaviour: 8-second `/parse` timeout, transparent
    fallback to a bundled mock parser, `localStorage` cache of the last
    input / locale / result.
- **`docs/api-contract.md`** — frozen `/parse` contract for backend (Claude 1).
- **`PROJECT_LOG.md`** — initialized with the M1-SSE-UI entry.

### Changed

- Repository structure: introduced `frontend/`, `docs/`, top-level
  `CHANGELOG.md` and `PROJECT_LOG.md`.

### Backward compatibility

- This is the first feature release after the empty `Initial commit`. No
  consumers exist yet; the API contract in `docs/api-contract.md` becomes
  the baseline for any future change.
