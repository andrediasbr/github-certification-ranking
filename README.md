# 🏆 GitHub Certifications Rankings

[![Generate GitHub Certifications Rankings](https://github.com/andrediasbr/github-certification-ranking/actions/workflows/generate-rankings.yml/badge.svg)](https://github.com/andrediasbr/github-certification-ranking/actions/workflows/generate-rankings.yml)

> Automated daily rankings of GitHub Certifications leaders across different regions worldwide.

<img src="images/github-octocat.jpg" alt="GitHub Octocat" width="120"/>

---

## 📊 Rankings Index

### 🌎 Regional Rankings

| Region | Ranking | Description |
|--------|---------|-------------|
| 🇧🇷 | [**TOP 10 Brazil**](TOP10_BRAZIL.md) | Top certified professionals in Brazil |
| 🌎 | [**TOP 10 Americas**](TOP10_AMERICAS.md) | Leaders across North, Central & South America |
| 🇪🇺 | [**TOP 10 Europe**](TOP10_EUROPE.md) | Top performers in European countries |
| 🌏 | [**TOP 10 Asia**](TOP10_ASIA.md) | Asian region certification leaders |
| 🌊 | [**TOP 10 Oceania**](TOP10_OCEANIA.md) | Australia, New Zealand & Pacific islands |

### 🌍 Global Ranking

| Scope | Ranking | Description |
|-------|---------|-------------|
| 🌍 | [**TOP 10 Global**](TOP10_WORLD.md) | Global top 10 across all countries |


## 🔄 How It Works

The rankings are automatically updated daily via GitHub Actions:

1. **Data Collection**: Fetches certification data from Credly API for all countries globally
   - Uses parallel processing with `fetch_data.py` for fast data retrieval
   - Specialized `fetch_large_country.py` for countries with large datasets (e.g., India, United States)
   - Smart metadata tracking to skip recently updated countries and optimize API usage
2. **Data Storage**: All certification data stored in the `datasource/` directory
   - Individual CSV files per country (e.g., `github-certs-brazil.csv`)
   - Metadata tracking in `csv_metadata.json` for update timestamps
3. **Processing**: Consolidates data from 190+ country CSV files
4. **Ranking Generation**: Creates TOP 10 rankings for each region using `generate_rankings.py`
   - Regional rankings: Brazil, Americas, Europe, Asia, Oceania
   - Global ranking with top performers worldwide
5. **Auto-Commit**: Updates markdown files automatically with latest rankings

## 🚀 Manual Execution

You can manually trigger the rankings generation:

1. Go to the [Actions tab](../../actions)
2. Select "Generate GitHub Certifications Rankings"
3. Click "Run workflow"

## 💻 Local Execution

### Fetch Data for a Specific Country

```bash
# Fetch data for a single country
./cert-github.sh "Brazil"
./cert-github.sh "United States"
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
├── cert-github.sh                     # Single country data fetcher
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
- **Parallel Processing**: Fetches multiple countries simultaneously using ThreadPoolExecutor
- **Metadata Tracking**: Skips recently updated countries to reduce API calls
- **Specialized Handlers**: Large countries use optimized parallel page fetching (up to 20 concurrent requests)
- **Intelligent Caching**: CSV files stored with timestamps in metadata

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
