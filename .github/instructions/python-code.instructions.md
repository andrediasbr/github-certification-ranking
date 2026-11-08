---
description: "Use when editing Python scripts in this project. Covers Credly API patterns, CSV handling, parallel fetching, and error handling conventions."
applyTo: "**/*.py"
---
# Python Code Guidelines

## API Requests
- Use `request_with_retries` from `certifications.py` (retries 429/5xx with backoff) with explicit timeouts (30s for Credly API, 10s for company lookups)
- Credly API base: `https://www.credly.com`
- GitHub org ID: `63074953-290b-4dce-86ce-ea04b4187219`
- Handle HTTP errors with try/except — never let API failures crash the pipeline
- Record failures instead of silently returning defaults: failed pages, a unique-user count below Credly's reported `total_count`, or >1% failed badge lookups mark the run incomplete, and `save_to_csv` then keeps the previous CSV

## Badge Logic
- Expired badges (`expires_at_date < today`) are always excluded, except `NON_EXPIRING_BADGES` (e.g. `GitHub Foundations`) — use `is_badge_expired`
- Excluded badges (`EXCLUDED_BADGES` set and `EXCLUDED_BADGE_PREFIXES`) are certifications no longer available or non-certification awards — excluded even if issued by GitHub org (use `is_excluded_badge`)
- Deduplicate badges by name per user (use `set`), normalizing renamed badges with `normalize_badge_name` / `BADGE_NAME_ALIASES`
- Microsoft-issued GitHub certs are defined in `ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS`
- Two badge sources: GitHub org badges + Microsoft-issued badges (both external badges and native Credly badges from the Microsoft org, filtered by the allowlist via `is_allowed_organization_badge`)
- All badge rules live only in `certifications.py`; import them, never duplicate them in other scripts

## CSV Format
- Header: `first_name,middle_name,last_name,badge_count,profile_url,company`
- File naming: `datasource/github-certs-{country-with-hyphens}.csv`
- Use `csv.DictReader`/`csv.DictWriter` for all CSV operations
- UTF-8 encoding always

## Parallelism
- Use `concurrent.futures.ThreadPoolExecutor` for parallel work
- Large countries (`large_countries` in `fetch_data.py`: India, United States, Brazil, United Kingdom, Canada, Spain) use `fetch_large_country.py`
- Regular countries use `fetch_country.py`

## Ranking Generation
- Position-based: 10 positions, tied users share the same rank
- Max 20 users displayed per position; overflow shown as count
- TOP 5 company ranking aggregated from all users in the region (company from the CSV), sorted by total badges
- TOP 5 country ranking for multi-country rankings only
- Company names with `|` are sanitized to `/` for markdown compatibility

## Logging
- Use emoji prefixes: 📂 (file ops), ✅ (success), ⚠️ (warning), ❌ (error)
- Print to stdout, no logging framework
