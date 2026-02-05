# 🏆 GitHub Certifications Rankings

[![Generate GitHub Certifications Rankings](https://github.com/andrediasbr/github-certification-ranking/actions/workflows/generate-rankings.yml/badge.svg)](https://github.com/andrediasbr/github-certification-ranking/actions/workflows/generate-rankings.yml)

> Automated daily rankings of GitHub Certifications leaders across different regions worldwide.

<img src="images/github-octocat.jpg" alt="GitHub Octocat" width="120"/>

---

## 📊 Rankings Index

### 🌎 Regional Rankings

| Region | Ranking | Description |
|--------|---------|-------------|
| :br: | [**TOP 10 Brazil**](TOP10_BRAZIL.md) | Top certified professionals in Brazil |
| 🗽 | [**TOP 10 Americas**](TOP10_AMERICAS.md) | Leaders across North, Central & South America |
| :eu: | [**TOP 10 Europe**](TOP10_EUROPE.md) | Top performers in European countries |
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
   
2. **Smart Filtering**: Ensures ranking accuracy
   - **Expired certifications are automatically excluded** from counts
   - Only valid (non-expired) certifications count toward rankings
   - Top 30 candidates per country are validated for accurate results
   - 96% reduction in API requests with intelligent candidate selection
   
3. **Company Information**: Enriches rankings with professional context
   - Company data fetched from public Credly user profiles
   - Displayed alongside name and certification count in rankings
   - Updated during ranking generation for top performers only
   
4. **Data Storage**: All certification data in the `datasource/` directory
   - Individual CSV files per country (e.g., `github-certs-brazil.csv`)
   - Metadata tracking for update timestamps and optimization
   
5. **Ranking Generation**: Creates TOP 10 rankings for each region
   - Regional rankings: Brazil, Americas, Europe, Asia, Africa, Oceania
   - Global ranking with top performers worldwide
   - Automatic markdown file updates with latest data

### ℹ️ GitHub Certifications Sources

This project tracks **ALL GitHub certifications** from two sources:

1. **GitHub Organization Badges** - All certifications issued directly by GitHub on Credly
   - **Core Certifications**: Foundations, Actions, Advanced Security, Administration, Copilot
   - **Partner Credentials**: Migrations, AzureDevOps Migrations, Advanced Security Partner Delivery
   - **Sales Badges**: FY26 Sales Professional, Revenue Motions, Platform, Copilot, etc.
   - **Professional Badges**: Tech Sales Professional, Sales Professional
   - **Any other badge** issued by the GitHub organization
   
2. **Microsoft-Issued Badges** - GitHub certifications transitioned to Microsoft Learn
   - GitHub Foundations (Microsoft Certified)
   - Other GitHub certifications now issued via learn.microsoft.com

> **Note**: All badges from the GitHub organization on Credly are counted, not just the core certifications. As of 2024, GitHub migrated some certification issuance to Microsoft Learn.

### 🎓 Microsoft Learn Integration

This project now supports tracking GitHub certifications from **Microsoft Learn** transcripts, including:

**Certifications (with exam numbers):**
- **GH-100**: GitHub Administration
- **GH-200**: GitHub Actions  
- **GH-300**: GitHub Copilot
- **GH-400**: GitHub Advanced Security Partner
- **GH-500**: GitHub Advanced Security

**Applied Skills Assessments:**
- [Accelerate app development by using GitHub Copilot](https://learn.microsoft.com/en-us/credentials/applied-skills/accelerate-app-development-by-using-github-copilot/)

#### How to Link Your MS Learn Profile

To have your Microsoft Learn GitHub certifications counted in the rankings:

1. **Go to your MS Learn profile**: https://learn.microsoft.com/en-us/users/me/transcript
2. **Click "Share link"** to create a share URL for your transcript
3. **Copy the share link** (it looks like: `https://learn.microsoft.com/en-us/users/YOUR-NAME/transcript/share/SHARE_ID`)
4. **Submit a PR** to update your entry in the appropriate country CSV file in the `datasource/` directory:
   - Add your share URL to the `mslearn_url` column
   - Example row: `Jesse,Houwing,6,/users/jessehouwing/badges,https://learn.microsoft.com/en-us/users/jessehouwing-1848/transcript/share/d5gza1z690gp607`

> **Privacy Note**: The transcript share link only exposes your completed certifications and training, not personal account details.

#### MVP Badge

Users with a linked MS Learn profile who have the **Microsoft MVP** affiliation will automatically receive an MVP badge <img src="images/mvp.svg" alt="Microsoft MVP" width="16" height="16"/> next to their name in the rankings. MVP status is detected automatically from the MS Learn profile API.

### 🎯 Ranking Accuracy

- **Expiration Filtering**: Only active, non-expired certifications are counted
- **Automatic Validation**: Certification expiration dates are checked against current date
- **Example**: A user with 15 total badges but 3 expired will show 12 valid certifications
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
├── fetch_mslearn_badges.py            # MS Learn transcript scraper
├── generate_rankings.py               # Main ranking generator
├── csv_metadata.json                  # Metadata for tracking updates
├── TOP10_*.md                         # Generated ranking files
└── README.md                          # This file
```

## 🛠️ Technical Details

### Data Source
Data is sourced from the [Credly API](https://www.credly.com/api/v1/directory) for GitHub certifications.

### Performance Optimizations
- **Intelligent Candidate Selection**: Fetches detailed badge data only for top 30 candidates per country
  - Reduces API requests by 96% (from ~1,600 to ~60 requests for large countries)
  - ~27x faster execution while maintaining accuracy
- **Parallel Processing**: Fetches multiple countries simultaneously using ThreadPoolExecutor
- **Metadata Tracking**: Skips recently updated countries to reduce unnecessary API calls
- **Specialized Handlers**: Large countries use optimized parallel page fetching
- **Smart Caching**: CSV files stored with timestamps for efficient updates

### Certification Validation
- **Expiration Checking**: Each badge's `expires_at_date` is validated against current date
- **Dual Source Tracking**: Combines GitHub org badges + Microsoft external badges
- **Top Performer Focus**: Detailed validation applied to ranking candidates only

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
