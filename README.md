# 🏆 GitHub Certifications Rankings

[![Generate GitHub Certifications Rankings](https://github.com/andrediasbr/github-certification-ranking/actions/workflows/generate-rankings.yml/badge.svg)](https://github.com/andrediasbr/github-certification-ranking/actions/workflows/generate-rankings.yml)

> Automated daily rankings of GitHub Certifications leaders across different regions worldwide.
> Rankings by **professionals**, **companies**, and **countries** — updated daily.

<img src="images/github-octocat.jpg" alt="GitHub Octocat" width="120"/>

---

## 📊 Rankings Index

Each ranking page includes:
- 🏆 **Top 10 Positions** — Professionals ranked by number of certifications (tied users share the same position)
- 🏢 **Top 5 Companies** — Companies with the most certified professionals
- 🌐 **Top 5 Countries** — Countries leading in certifications (regional rankings only)

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

The rankings are automatically updated daily via GitHub Actions:

1. **Data Collection**: Fetches certification data from Credly API for all countries worldwide
   - Collects GitHub certifications from official GitHub organization badges
   - Includes Microsoft-issued GitHub certifications (migrated from GitHub in 2024)
   - Uses parallel processing for fast data retrieval
   - Optimized handling for large countries (India, USA, Brazil, UK)
   
2. **Fair Ranking Criteria**: Ensures an equitable competition
   - **Position-based ranking**: The ranking shows 10 positions, not 10 users — professionals with the same number of certifications share the same position
   - **Expired certifications are excluded**: Only active, valid certifications count
   - **Excluded certifications**: Badges that can no longer be earned (e.g., `GitHub Sales Professional`) are excluded to keep the competition fair
   - **Duplicate prevention**: Same badge name counts only once per user
   - Top 50 candidates per country are validated for accurate results
   
3. **Multi-dimensional Rankings**: Each regional ranking includes
   - 🏆 **Top 10 Professionals** — Individual ranking by certification count
   - 🏢 **Top 5 Companies** — Companies with the most certified professionals in the region
   - 🌐 **Top 5 Countries** — Countries leading in certifications (excluded for single-country rankings)
   
4. **Company Information**: Enriches rankings with professional context
   - Company data fetched from public Credly user profiles
   - Displayed alongside name and certification count in rankings
   
5. **Data Storage**: All certification data in the `datasource/` directory
   - Individual CSV files per country (e.g., `github-certs-brazil.csv`)
   - Metadata tracking for update timestamps and optimization

### ℹ️ GitHub Certifications Sources

This project tracks GitHub certifications from two sources:

1. **GitHub Organization Badges** - Certifications issued directly by GitHub on Credly
   - **Core Certifications**: Foundations, Actions, Advanced Security, Administration, Copilot
   - **Partner Credentials**: Migrations, AzureDevOps Migrations, Advanced Security Partner Delivery
   - **Any other active badge** issued by the GitHub organization
   
2. **Microsoft-Issued Badges** - GitHub certifications transitioned to Microsoft Learn
   - GitHub Foundations, Actions, Advanced Security, Administration, Copilot (Microsoft Certified)
   - Microsoft Certified: DevOps Engineer Expert
   - Microsoft Applied Skills related to GitHub

> **Note**: As of 2024, GitHub migrated some certification issuance to Microsoft Learn. Certifications that can no longer be earned (e.g., `GitHub Sales Professional`) are excluded from rankings to ensure fair competition.

### 🎯 Ranking Fairness

- **Position-based**: 10 positions shown — tied professionals share the same rank
- **Active only**: Expired certifications are automatically excluded
- **Excluded badges**: Certifications no longer available for earning are not counted
- **Daily Updates**: Rankings refresh daily to reflect newly issued and expired certifications

## 🚀 Manual Execution

You can manually trigger the rankings generation:

1. Go to the [Actions tab](../../actions)
2. Select "Generate GitHub Certifications Rankings"
3. Click "Run workflow"

## 💻 Local Execution

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
│   └── workflows/
│       └── generate-rankings.yml      # GitHub Actions workflow
├── datasource/                        # Directory with all country CSVs
│   ├── github-certs-brazil.csv
│   ├── github-certs-united-states.csv
│   ├── github-certs-india.csv
│   └── ... (190+ country files)
├── images/
│   └── github-octocat.jpg             # Project image
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
- **Intelligent Candidate Selection**: Fetches detailed badge data only for top 50 candidates per country
  - Reduces API requests by ~95% for large countries
- **Parallel Processing**: Fetches multiple countries simultaneously using ThreadPoolExecutor
- **Metadata Tracking**: Skips recently updated countries to reduce unnecessary API calls
- **Specialized Handlers**: Large countries use optimized parallel page fetching
- **Smart Caching**: CSV files stored with timestamps for efficient updates

### Certification Validation
- **Expiration Checking**: Each badge's `expires_at_date` is validated against current date
- **Dual Source Tracking**: Combines GitHub org badges + Microsoft external badges
- **Excluded Badges**: Certifications no longer available (e.g., `GitHub Sales Professional`) are excluded via `EXCLUDED_BADGES`
- **Duplicate Prevention**: Only unique badge names are counted (no duplicates)
- **Top Performer Focus**: Detailed validation applied to top 50 candidates per country

### Regional Coverage
- **Americas**: 30+ countries including Brazil, USA, Canada, Argentina, Mexico, etc.
- **Europe**: 45+ countries including UK, Germany, France, Spain, Italy, etc.
- **Asia**: 45+ countries including India, China, Japan, South Korea, Singapore, etc.
- **Oceania**: 15+ countries including Australia, New Zealand, Fiji, etc.
- **Africa**: 50+ countries including South Africa, Nigeria, Egypt, Kenya, etc.

**Total: 190+ countries tracked globally**

## 📝 License

This project is open source and available under the MIT License.

---

*Last updated: Automated via GitHub Actions*
