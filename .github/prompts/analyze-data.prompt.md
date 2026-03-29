---
description: "Analyze ranking data from CSV files in the datasource folder"
agent: "agent"
argument-hint: "What to analyze (e.g., 'top countries by total certs', 'Brazil vs India')"
---
Analyze the certification data in the `datasource/` directory. CSV files follow this format:
- Header: `first_name,middle_name,last_name,badge_count,profile_url`
- One file per country: `github-certs-{country}.csv`

Use Python or shell commands to read the CSV files and produce the requested analysis. Country-to-continent mapping is in `CONTINENT_MAP` in `generate_rankings.py`.
