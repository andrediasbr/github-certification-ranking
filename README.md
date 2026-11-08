# 🏆 GitHub Certifications Rankings

[![Generate GitHub Certifications Rankings](https://github.com/andrediasbr/github-certification-ranking/actions/workflows/generate-rankings.yml/badge.svg)](https://github.com/andrediasbr/github-certification-ranking/actions/workflows/generate-rankings.yml)

> Automated rankings of GitHub Certifications leaders across different regions worldwide.
> Rankings by **professionals**, **companies**, and **countries** — updated twice a week (Wednesdays and Sundays).

<img src="images/github-octocat.jpg" alt="GitHub Octocat" width="120"/>

---

## 📊 Rankings Index

Each ranking page includes:
- 🏆 **Top 10 Positions** — Professionals ranked by number of certifications (tied users share the same position)
  - 🏅 hover tooltip listing the certifications each professional holds
  - 🎯 hover tooltip listing the certifications they are still missing (compared to every certification held by any ranked professional)
- 🏢 **Top 5 Companies** — Companies with the most certifications among their certified professionals
- 🌐 **Top 5 Countries** — Countries leading in certifications (multi-country rankings only)

### 🌎 Regional Rankings

| Region | Ranking | Description |
|--------|---------|-------------|
| 🇧🇷 | [**TOP 10 Brazil**](TOP10_BRAZIL.md) | Top certified professionals in Brazil |
| 🗽 | [**TOP 10 Americas**](TOP10_AMERICAS.md) | Leaders across North, Central & South America |
| 🇪🇺 | [**TOP 10 Europe**](TOP10_EUROPE.md) | Top performers in European countries |
| 🏯 | [**TOP 10 Asia**](TOP10_ASIA.md) | Asian region certification leaders |
| 🦁 | [**TOP 10 Africa**](TOP10_AFRICA.md) | Top performers across African countries |
| 🌊 | [**TOP 10 Oceania**](TOP10_OCEANIA.md) | Australia, New Zealand & Pacific islands |

### 🌍 Global Ranking

| Scope | Ranking | Description |
|-------|---------|-------------|
| 🌍 | [**TOP 10 Global**](TOP10_WORLD.md) | Global top 10 across all countries |


## 🔄 How It Works

The rankings are automatically updated via GitHub Actions every **Wednesday and Sunday at 00:00 UTC** (and on demand):

1. **Data Collection**: Fetches certification data from Credly API for all countries worldwide
   - Collects GitHub certifications from official GitHub organization badges
   - Includes Microsoft-issued GitHub certifications (migrated from GitHub in 2024) and proficiency badges
   - Validates the badges of **every** certified user in each country (not just the top candidates)
   - Uses parallel processing for fast data retrieval
   - Optimized handling for large countries (India, United States, Brazil, United Kingdom, Canada, Spain)
   
2. **Fair Ranking Criteria**: Ensures an equitable competition
   - **Position-based ranking**: The ranking shows 10 positions, not 10 users — professionals with the same number of certifications share the same position
   - **Expired certifications are excluded**: Only active, valid certifications count (`GitHub Foundations` no longer expires, so its expiration date is ignored)
   - **Excluded badges**: Badges that can no longer be earned (e.g., `GitHub Sales Professional`) and non-certification awards (community, recognition and MVP badges) are excluded to keep the competition fair
   - **Duplicate prevention**: Same badge name counts only once per user, including badges renamed by Microsoft
   
3. **Multi-dimensional Rankings**: Each regional ranking includes
   - 🏆 **Top 10 Professionals** — Individual ranking by certification count
   - 🏢 **Top 5 Companies** — Companies ranked by total certifications of all their certified professionals in the region
   - 🌐 **Top 5 Countries** — Countries leading in certifications (excluded for single-country rankings)
   
4. **Company Information**: Enriches rankings with professional context
   - Company data fetched from public Credly user profiles
   - Displayed alongside name and certification count in rankings
   
5. **Data Storage**: All certification data in the `datasource/` directory
   - Individual CSV files per country (e.g., `github-certs-brazil.csv`)
   - `csv_metadata.json` tracks the last update of each country; rankings show a **Data Freshness Warning** for countries that could not be refreshed

6. **Data Integrity**: A country's CSV is only replaced by a complete fetch
   - Failed requests are retried with backoff
   - If any page fails, fewer unique users than Credly reports are collected, or more than 1% of badge lookups fail, the run is marked incomplete and the previous CSV is kept

### ℹ️ GitHub Certifications Sources

This project tracks GitHub certifications from two sources:

1. **GitHub Organization Badges** - Certifications issued directly by GitHub on Credly
   - **Core Certifications**: Foundations, Actions, Advanced Security, Administration, Copilot
   - **Partner Credentials**: Migrations, AzureDevOps Migrations, Advanced Security Partner Delivery
   - **Any other active badge** issued by the GitHub organization, except non-certification awards listed in `certifications.py`
   
2. **Microsoft-Issued Badges** - GitHub certifications transitioned to Microsoft Learn
   - GitHub Foundations, Actions, Advanced Security, Administration, Copilot (Microsoft Certified)
   - GitHub Certified: Agentic AI Developer
   - Microsoft Certified: DevOps Engineer Expert
   - Microsoft Certified: Agentic DevOps Engineer Expert (AZ-401)
   - Microsoft Applied Skills related to GitHub
   - Microsoft Pro Badge: GitHub Copilot - Proficient

> **Note**: As of 2024, GitHub migrated some certification issuance to Microsoft Learn. Certifications that can no longer be earned (e.g., `GitHub Sales Professional`) are excluded from rankings to ensure fair competition.

### 🎯 Ranking Fairness

- **Position-based**: 10 positions shown — tied professionals share the same rank
- **Active only**: Expired certifications are automatically excluded
- **Excluded badges**: Certifications no longer available for earning are not counted
- **Regular Updates**: Rankings refresh twice a week to reflect newly issued and expired certifications

### ⚠️ Known Limitations

- **Stale expiration dates for renewed Microsoft certifications**: Badge counts rely on the expiration dates reported by the Credly API. Credly may not refresh synced Microsoft credentials after a renewal, so a recently renewed certification can be counted as expired. If your count looks wrong, check your badge data at `https://www.credly.com/api/v1/users/<your-username>/external_badges/open_badges/public?page=1&page_size=100` and look for badges whose `expires_at_date` is in the past but are still **Active** on Microsoft Learn. The fix has to happen on Credly: add the credential again with a new share link from Microsoft Learn (then hide the old badge), or [contact Credly support](https://support.credly.com/hc/en-us/requests/new). See [#30](../../issues/30) for details.

## 🚀 Manual Execution

You can manually trigger the rankings generation:

1. Go to the [Actions tab](../../actions)
2. Select "Generate GitHub Certifications Rankings"
3. Click "Run workflow"

Pull requests that change Python code run the **Validate PR** workflow, which fetches a single country and generates the rankings without committing anything (the output is uploaded as an artifact). It can also be triggered manually with a chosen country.

## 💻 Local Execution

### Install Dependencies

```bash
pip install requests
```

### Fetch Data for a Specific Country

```bash
# Fetch data for a single country
python3 fetch_country.py "Brazil"
python3 fetch_country.py "United States"
```

### Fetch Data for All Countries

```bash
# Fetch all countries in parallel
python3 fetch_data.py
```

### Fetch Large Countries (Optimized)

```bash
# For countries with thousands of certified users
python3 fetch_large_country.py "India"
python3 fetch_large_country.py "United States"
```

### Generate Rankings

```bash
# Generate all regional and global rankings
python3 generate_rankings.py
```

## 📁 Repository Structure

```
.
├── .github/
│   ├── copilot-instructions.md        # Copilot project guidelines
│   ├── instructions/                  # Copilot coding instructions
│   ├── prompts/                       # Reusable Copilot prompts
│   └── workflows/
│       ├── generate-rankings.yml      # Scheduled rankings workflow
│       ├── validate-pr.yml            # PR validation (no commit)
│       └── actions.lock               # Pinned action versions
├── datasource/                        # Directory with all country CSVs
│   ├── github-certs-brazil.csv
│   ├── github-certs-united-states.csv
│   ├── github-certs-india.csv
│   └── ... (198 country files)
├── images/
│   └── github-octocat.jpg             # Project image
├── certifications.py                  # Shared badge rules and HTTP helpers
├── fetch_country.py                   # Single country data fetcher
├── fetch_data.py                      # Parallel fetcher for all countries
├── fetch_large_country.py             # Optimized fetcher for large countries
├── generate_rankings.py               # Main ranking generator
├── csv_metadata.json                  # Metadata for tracking updates
├── TOP10_*.md                         # Generated ranking files
└── README.md                          # This file
```

## 🛠️ Technical Details

### Data Source
Data is sourced from the [Credly API](https://www.credly.com/api/v1/directory) for GitHub certifications.

### Performance Optimizations
- **Parallel Processing**: Fetches multiple countries simultaneously using ThreadPoolExecutor, and each user's badges and company in parallel
- **Single Pass per User**: Badges and company are fetched in the same pass for every user
- **Connection Reuse**: A shared HTTP session reuses TLS connections across requests
- **Resilient Requests**: Rate limits and transient server errors (429/5xx) are retried with backoff
- **Specialized Handlers**: Large countries use parallel page fetching; when Credly caps the directory listing (10,000 users), users are collected per badge instead

### Certification Validation
- **Expiration Checking**: Each badge's `expires_at_date` is validated against current date (except non-expiring badges such as `GitHub Foundations`)
- **Dual Source Tracking**: Combines GitHub org badges + Microsoft-issued badges (filtered by `ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS`)
- **Excluded Badges**: Certifications no longer available and non-certification awards are excluded via `EXCLUDED_BADGES` and `EXCLUDED_BADGE_PREFIXES`
- **Duplicate Prevention**: Only unique badge names are counted, with renamed badges normalized via `BADGE_NAME_ALIASES`
- **Single Source of Truth**: All badge rules live in `certifications.py`

### Regional Coverage
- **Americas**: 35 countries including Brazil, USA, Canada, Argentina, Mexico, etc.
- **Europe**: 49 countries including UK, Germany, France, Spain, Italy, etc.
- **Asia**: 46 countries including India, China, Japan, South Korea, Singapore, etc.
- **Oceania**: 14 countries including Australia, New Zealand, Fiji, etc.
- **Africa**: 54 countries including South Africa, Nigeria, Egypt, Kenya, etc.

**Total: 198 countries tracked globally**

## 📝 License

This project is open source and available under the MIT License.

---

*Last updated: Automated via GitHub Actions*
