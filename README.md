# UNMAPPED Protocol — Skills Signal Engine

> Make the chaotic, multilingual reality of LMIC livelihoods legible to the formal economy — without forcing anyone to flatten themselves first.

UNMAPPED is a **full-stack skills recognition system** for Low and Middle-Income Countries. It transforms free-form, multilingual narratives about livelihoods into portable **Skills Signal Profiles** (SSP) that bridge informal economies and formal institutions.

**Current Release:** `v0.4.0` — Module 2 (Dynamic Job-Match Signal) + Module 1 (Skills Signal Engine UI) ✓ 178 tests passing

---

## 📋 Table of Contents

- [What is UNMAPPED?](#what-is-unmapped)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
  - [Backend (Python / FastAPI)](#backend-python--fastapi)
  - [Frontend (React / TypeScript)](#frontend-react--typescript)
- [Supported Countries & Languages](#supported-countries--languages)
- [API Contract](#api-contract)
- [Development](#development)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Key Features](#key-features)

---

# UNMAPPED

**Open Protocol Layer for Real Skills → Real Economic Opportunity**  
*World Bank Youth Summit × Hack-Nation Global AI Hackathon 2026*

**Closing the distance between a young person’s real skills and real economic opportunity in the age of AI.**

---

## Overview

UNMAPPED is an **open, localizable infrastructure layer** — a thin protocol, not a product or closed API — that sits between any client-side **Candidate CRM** (NGOs, governments, training providers) and **Employer CRM** (firms, job boards, ministries).

It solves three structural failures identified by the World Bank:
- **Broken signals** — informal and real skills are invisible to formal systems
- **AI disruption without readiness** — youth have no honest view of automation risk and future resilience
- **No matching infrastructure** — opportunity flows through opaque networks that systematically exclude the most vulnerable

Every behaviour that varies by country (taxonomy, language, automation calibration, econometric sources, opportunity types, device constraints) is a **pure config input**. A single `country_profile.json` swap reconfigures the entire protocol for any LMIC context (e.g. Ghana urban informal ↔ Armenia IT/mining/tourism).

## High-Level Architecture

graph TD
    A[Candidate CRM<br/>(NGO / Govt / School)] 
    B[UNMAPPED Protocol Layer<br/>v0.2 — Stateless Transform]
    C[Employer CRM<br/>(Firms / Job Boards / MDA)]

    A -->|Evidence<br/>(raw_input, task logs, attestations)| B
    C -->|Vacancies, growth data, networks| B

    B -->|Verifiable Skill Signal + Human Layer| C
    B -->|Econometric Opportunity Signals + BONA Flags| A

    subgraph "Protocol Core"
        M1[Module 1 — Skills Signal Engine]
        M2[Module 2 — AI Readiness & Displacement Lens]
        M3[Module 3 — Opportunity Matching & Dashboard]
        BONA[BONA — Bidirectional Opaque Network Auditor]
    end

Key Features

Zero-credential primary path — works for Amara with no formal documents
True localizability — Ghana ↔ Armenia with one config file swap
Constraint-aware design — 4 bandwidth tiers + SMS/USSD fallbacks
Multilingual-first parser — strong support for Twi, Ga, Ewe, Hausa, Armenian, Russian
Human Layer — beautiful, readable profile card owned by the youth
Explainable & auditable — SHAP decomposition + provenance on every signal

Quick Start
Bash# Clone and run full stack
git clone https://github.com/eagleowl2/UNMAPPED.git
cd UNMAPPED
docker compose up --build

Frontend: http://localhost:5173 (single chaotic input field)
Backend: http://localhost:8000
Swagger: http://localhost:8000/docs

Tech Stack

Backend: FastAPI + Python 3.11, spaCy, multilingual-e5-small, NetworkX, Pydantic v2
Frontend: React 18 + Vite + TypeScript + Tailwind
Infrastructure: Docker Compose, production-ready Dockerfiles
Data: ILOSTAT, WDI, WBES, Wittgenstein, Frey-Osborne, STEP, etc. (bundled or live)

License
Apache 2.0 — Open Protocol. Anyone (government, NGO, employer) can plug in and run their own instance.
