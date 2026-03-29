---
description: "Use when editing Python scripts in this project. Covers Credly API patterns, CSV handling, parallel fetching, and error handling conventions."
applyTo: "**/*.py"
---
# Python Code Guidelines

## API Requests
- Always use `requests` library with explicit timeouts (5-10s)
- Credly API base: `https://www.credly.com`
- GitHub org ID: `63074953-290b-4dce-86ce-ea04b4187219`
- Handle HTTP errors with try/except — never let API failures crash the pipeline
- Return safe defaults on failure (0, empty list, empty string)

## Badge Logic
- Expired badges (`expires_at_date < today`) are always excluded
- Excluded badges (`EXCLUDED_BADGES` set) are certifications no longer available — excluded even if issued by GitHub org
- Deduplicate badges by name per user (use `set`)
- Microsoft-issued GitHub certs are defined in `ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS`
- Two badge sources: GitHub org badges + Microsoft external badges
- Keep `EXCLUDED_BADGES` and `ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS` synchronized between `fetch_country.py` and `fetch_large_country.py`

## CSV Format
- Header: `first_name,middle_name,last_name,badge_count,profile_url`
- File naming: `datasource/github-certs-{country-with-hyphens}.csv`
- Use `csv.DictReader`/`csv.DictWriter` for all CSV operations
- UTF-8 encoding always

## Parallelism
- Use `concurrent.futures.ThreadPoolExecutor` for parallel work
- Large countries (India, USA, Brazil, UK) use `fetch_large_country.py`
- Regular countries use `fetch_country.py`

## Ranking Generation
- Position-based: 10 positions, tied users share the same rank
- Max 20 users displayed per position; overflow shown as count
- TOP 5 company ranking aggregated from ranked users' company data
- TOP 5 country ranking for multi-country rankings only
- Company names with `|` are sanitized to `/` for markdown compatibility

## Logging
- Use emoji prefixes: 📂 (file ops), ✅ (success), ⚠️ (warning), ❌ (error)
- Print to stdout, no logging framework
