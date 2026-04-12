# Automation System

> This folder contains design rationale and high-level architecture docs.
> For implementation details, see `src/automation/README.md`.

The `src/automation/` package is the runtime home for all browser automation: job discovery (scraping) and job application. It replaced the old split between `src/scraper/` and `src/apply/` in the 2026-04-06 Phase 1 migration.

---

## 🏗️ Architecture & Features

## ⚙️ Configuration

## 🚀 CLI / Usage

See `src/automation/main.py` for authoritative CLI definitions.

## 📝 Data Contract

- `src/automation/ariadne/models.py` — Ariadne portal schema
- `src/automation/ariadne/contracts/base.py` — executor, command contracts
