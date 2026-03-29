---
description: "Add a new country to the ranking system"
agent: "agent"
argument-hint: "Country name (e.g., 'Monaco')"
---
Add the country provided to the ranking system:

1. Add the country to `CONTINENT_MAP` in `generate_rankings.py` under the correct continent
2. Verify the country name follows the convention: lowercase with spaces in the map key, Title Case in display
3. The CSV file will be auto-generated as `datasource/github-certs-{country-with-hyphens}.csv` on the next pipeline run
4. If the country has a large user base (>800 users), consider adding it to the `large_countries` list in `fetch_data.py`
