# UNMAPPED Protocol — Project Log

Append-only running record of every major contribution. Format follows v0.2
Section 12.4: each entry starts with a level-2 header `## YYYY-MM-DD — vX.Y.Z[-tag]`
and uses the seven canonical fields below. Never edit a past entry; correct via
a follow-up entry.

> ⚠️ **Inference note (Claude 2):** I do not have direct access to the
> `UNMAPPED_Protocol_v0.2_Complete.docx` file in this session. The Section 12.4
> field set below is reconstructed from the prompt brief. When the canonical
> spec is shared, please reconcile and amend in a follow-up entry rather than
> rewriting history.

---

## 2026-04-26 — v0.3.0-sse-alpha.1

- **Module:** M1 — Skills Signal Engine (Frontend / Human + Constraint Layer)
- **Author:** Claude 2 (frontend) — coordinating with Claude 1 (backend) via
  this log and `docs/api-contract.md`.
- **Branch:** `module/m1-sse-ui` from `main`.
- **Change type:** Feature (additive; first feature release on top of the
  empty `Initial commit`).
- **Primitives affected:**
  - **Human Layer** — `ProfileCard`, `SignalBar`, `NetworkEntryMap`,
    `QrSimulation` render the v0.2 Section 4.2 layout.
  - **Constraint Layer** — `SmsPreview`, `UssdSimulator` provide the
    low-bandwidth fallback experience.
  - **Localization Layer** — `LocaleSwitcher` toggles Ghana ↔ Armenia
    `country_profile`s; samples and USSD shortcodes per locale.
  - **Interface contract** — `docs/api-contract.md` + `frontend/src/lib/types.ts`
    define `POST /parse` for Claude 1.
- **Backward compatibility:** N/A — first feature release. `docs/api-contract.md`
  becomes the baseline for future SemVer decisions.
- **Test plan:**
  - `npm run lint` (strict TypeScript, no unused locals/params).
  - `npm run build` to confirm the production bundle compiles.
  - Manual: load SPA → paste Ghana sample → verify ProfileCard renders all
    primitives (header, skills, both signals, map, QR), SMS card shows
    correct segment count, USSD simulator dials *789# and renders the menu.
  - Manual: switch to Armenia → sample button populates Armenian text →
    re-parse → verify USSD shortcode flips to *404# and Armenian menu lines.
  - Manual offline: stop the backend / unset `VITE_API_URL` → verify the
    "Offline fallback" badge appears and the card still renders.
- **Rollback path:** `git checkout main && git branch -D module/m1-sse-ui` —
  no migrations, no data, no third-party state to revert. Tag
  `v0.3.0-sse-alpha.1` is not yet pushed; the branch remains the only artifact
  until the PR is merged.
- **Next step (handoff to Claude 1):** Implement FastAPI `POST /parse`
  matching `docs/api-contract.md`. Use the two fixtures in
  `frontend/src/lib/mock.ts` as your golden tests so the SPA renders
  identically in live and fallback modes. CORS allow-list:
  `http://localhost:5173` for dev.
