# Project Guidelines

## Overview

This project generates automated rankings (updated twice a week) of GitHub Certifications leaders across different regions worldwide. It fetches certification data from the Credly API and produces ranking markdown files with **Top 10 positions** for professionals, **Top 5 companies**, and **Top 5 countries**.

## Architecture

- **`certifications.py`** — Single source of truth for badge rules (`EXCLUDED_BADGES`, `EXCLUDED_BADGE_PREFIXES`, `ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS`, `NON_EXPIRING_BADGES`, `BADGE_NAME_ALIASES`) and shared HTTP helpers (`request_with_retries`, `fetch_user_company`)
- **`fetch_country.py`** — Fetches certifications for a single country from Credly API (GitHub org + Microsoft-issued badges)
- **`fetch_large_country.py`** — Specialized parallel fetcher for large countries (India, United States, Brazil, United Kingdom, Canada, Spain — see `large_countries` in `fetch_data.py`)
- **`fetch_data.py`** — Orchestrator that runs fetch scripts in parallel for all countries
- **`generate_rankings.py`** — Reads CSV files, aggregates data, and generates TOP10_*.md ranking files (including 🏅 obtained / 🎯 missing certification tooltips)
- **`csv_metadata.json`** — Tracks update timestamps and status per country
- **`datasource/`** — One CSV per country with certification data (`github-certs-<country>.csv`)

## Code Style

- Python 3.11+, scripts use `#!/usr/bin/env python3` and UTF-8 encoding
- Use `requests` for HTTP calls to Credly API, preferably via `request_with_retries` (retries 429/5xx with backoff)
- Use `concurrent.futures.ThreadPoolExecutor` for parallelism
- Use emoji prefixes in print statements for logging (📂, ✅, ⚠️, ❌)
- Timeouts on all external API requests (30s for Credly API calls, 10s for profile/company lookups)
- Handle API failures gracefully — never crash the pipeline; a country whose fetch is incomplete keeps its previous CSV

## Conventions

- Country names use lowercase with hyphens in filenames (`github-certs-united-states.csv`)
- Country names use Title Case in code/display (`United States`)
- `CONTINENT_MAP` in `generate_rankings.py` is the single source of truth for country-to-continent mapping
- Expired certifications are always excluded from counts (except `NON_EXPIRING_BADGES`, e.g. `GitHub Foundations`)
- Excluded badges (`EXCLUDED_BADGES` set and `EXCLUDED_BADGE_PREFIXES`) are certifications no longer available for earning (e.g., `GitHub Sales Professional`) and non-certification awards
- Badge deduplication by name — same badge name counts once per user; renamed badges are normalized via `BADGE_NAME_ALIASES`
- CSV format: `first_name,middle_name,last_name,badge_count,profile_url,company`
- Company names with `|` are sanitized to `/` to avoid breaking markdown tables

## Ranking Rules

- **Position-based**: Rankings show 10 positions, not 10 users — tied professionals share the same position
- **Max 20 users per position**: If a position has more than 20 tied users, only the first 20 are shown with a count of remaining
- **Company ranking (TOP 5)**: Aggregated from all users in the region (company from the CSV), sorted by total badges
- **Country ranking (TOP 5)**: Shows top countries by total badges (only for multi-country rankings)

## Data Sources

Two sources of GitHub certifications tracked:
1. **GitHub Organization on Credly** — org ID `63074953-290b-4dce-86ce-ea04b4187219`
2. **Microsoft-issued badges** — external badges and native Credly badges from the Microsoft org, filtered by the `ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS` set

Badges in `EXCLUDED_BADGES` (or matching `EXCLUDED_BADGE_PREFIXES`) are ignored even if issued by the GitHub org.

## Build and Test

```bash
# Install dependencies
pip install requests

# Fetch data for a single country
python3 fetch_country.py "Brazil"

# Fetch data for a large country (parallel)
python3 fetch_large_country.py "India"

# Fetch all countries
python3 fetch_data.py

# Generate rankings from existing CSVs
python3 generate_rankings.py
```

## CI/CD

- GitHub Actions workflow at `.github/workflows/generate-rankings.yml`
- Runs at 00:00 UTC on Wednesdays and Sundays via cron, or manually via `workflow_dispatch`
- Auto-commits updated CSVs, markdown files, and metadata
- `.github/workflows/validate-pr.yml` runs on PRs that change Python code: fetches one country and generates rankings without committing
- Action versions are pinned in `.github/workflows/actions.lock` (managed by `gh actions-lock`)
