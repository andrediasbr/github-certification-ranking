#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Certifications Rankings Generator
Generates TOP 10 rankings for Brazil, Americas, Europe, Asia, Oceania, and World
"""

import csv
import glob
import json
import os
import requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from certifications import (
    ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS,
    normalize_badge_name,
    request_with_retries,
    is_excluded_badge,
    get_badge_expiry_date,
    is_badge_expired,
    configure_utf8_output,
)

# --- Certification tooltip support ---
GITHUB_ORG_ID = '63074953-290b-4dce-86ce-ea04b4187219'

# Cache of profile_url -> set of valid cert names (or None when the fetch failed).
_USER_CERTS_CACHE = {}
# Union of every valid certification held by any ranked member across all rankings.
GLOBAL_CERT_UNIVERSE = set()

# Continent mapping
CONTINENT_MAP = {
    # AMERICAS
    'antigua and barbuda': 'Americas', 'argentina': 'Americas', 'bahamas': 'Americas',
    'barbados': 'Americas', 'belize': 'Americas', 'bolivia': 'Americas',
    'brazil': 'Americas', 'canada': 'Americas', 'chile': 'Americas',
    'colombia': 'Americas', 'costa rica': 'Americas', 'cuba': 'Americas',
    'dominica': 'Americas', 'dominican republic': 'Americas', 'ecuador': 'Americas',
    'el salvador': 'Americas', 'grenada': 'Americas', 'guatemala': 'Americas',
    'haiti': 'Americas', 'honduras': 'Americas', 'jamaica': 'Americas',
    'mexico': 'Americas', 'nicaragua': 'Americas', 'panama': 'Americas',
    'paraguay': 'Americas', 'peru': 'Americas', 'saint kitts and nevis': 'Americas',
    'saint lucia': 'Americas', 'saint vincent and the grenadines': 'Americas',
    'suriname': 'Americas', 'trinidad and tobago': 'Americas', 'united states': 'Americas',
    'uruguay': 'Americas', 'venezuela': 'Americas', 'guyana': 'Americas',
    
    # EUROPE
    'albania': 'Europe', 'andorra': 'Europe', 'armenia': 'Europe',
    'austria': 'Europe', 'azerbaijan': 'Europe', 'belarus': 'Europe',
    'belgium': 'Europe', 'bosnia and herzegovina': 'Europe', 'bulgaria': 'Europe',
    'croatia': 'Europe', 'cyprus': 'Europe', 'czech republic': 'Europe',
    'denmark': 'Europe', 'estonia': 'Europe', 'finland': 'Europe',
    'france': 'Europe', 'georgia': 'Europe', 'germany': 'Europe',
    'greece': 'Europe', 'hungary': 'Europe', 'iceland': 'Europe',
    'ireland': 'Europe', 'italy': 'Europe', 'kosovo': 'Europe',
    'latvia': 'Europe', 'liechtenstein': 'Europe', 'lithuania': 'Europe',
    'luxembourg': 'Europe', 'malta': 'Europe', 'moldova': 'Europe',
    'monaco': 'Europe', 'montenegro': 'Europe', 'netherlands': 'Europe',
    'north macedonia': 'Europe', 'norway': 'Europe', 'poland': 'Europe',
    'portugal': 'Europe', 'romania': 'Europe', 'russia': 'Europe',
    'san marino': 'Europe', 'serbia': 'Europe', 'slovakia': 'Europe',
    'slovenia': 'Europe', 'spain': 'Europe', 'sweden': 'Europe',
    'switzerland': 'Europe', 'ukraine': 'Europe', 'united kingdom': 'Europe',
    'vatican city': 'Europe',
    
    # ASIA
    'afghanistan': 'Asia', 'bahrain': 'Asia', 'bangladesh': 'Asia',
    'bhutan': 'Asia', 'brunei': 'Asia', 'cambodia': 'Asia',
    'china': 'Asia', 'east timor': 'Asia', 'indonesia': 'Asia',
    'iran': 'Asia', 'iraq': 'Asia', 'israel': 'Asia',
    'japan': 'Asia', 'jordan': 'Asia', 'kazakhstan': 'Asia',
    'kuwait': 'Asia', 'kyrgyzstan': 'Asia', 'laos': 'Asia',
    'lebanon': 'Asia', 'malaysia': 'Asia', 'maldives': 'Asia',
    'mongolia': 'Asia', 'myanmar': 'Asia', 'nepal': 'Asia',
    'north korea': 'Asia', 'oman': 'Asia', 'pakistan': 'Asia',
    'palestine': 'Asia', 'philippines': 'Asia', 'qatar': 'Asia',
    'saudi arabia': 'Asia', 'singapore': 'Asia', 'south korea': 'Asia',
    'sri lanka': 'Asia', 'syria': 'Asia', 'taiwan': 'Asia',
    'tajikistan': 'Asia', 'thailand': 'Asia', 'turkey': 'Asia',
    'turkmenistan': 'Asia', 'united arab emirates': 'Asia', 'uzbekistan': 'Asia',
    'vietnam': 'Asia', 'yemen': 'Asia', 'timor leste': 'Asia', 'india': 'Asia',
    
    # AFRICA
    'algeria': 'Africa', 'angola': 'Africa', 'benin': 'Africa',
    'botswana': 'Africa', 'burkina faso': 'Africa', 'burundi': 'Africa',
    'cameroon': 'Africa', 'cape verde': 'Africa', 'central african republic': 'Africa',
    'chad': 'Africa', 'comoros': 'Africa', 'democratic republic of the congo': 'Africa',
    'djibouti': 'Africa', 'egypt': 'Africa', 'equatorial guinea': 'Africa',
    'eritrea': 'Africa', 'eswatini': 'Africa', 'ethiopia': 'Africa',
    'gabon': 'Africa', 'gambia': 'Africa', 'ghana': 'Africa',
    'guinea': 'Africa', 'guinea-bissau': 'Africa',
    'ivory coast': 'Africa', 'kenya': 'Africa', 'lesotho': 'Africa', 'liberia': 'Africa',
    'libya': 'Africa', 'madagascar': 'Africa', 'malawi': 'Africa',
    'mali': 'Africa', 'mauritania': 'Africa', 'mauritius': 'Africa',
    'morocco': 'Africa', 'mozambique': 'Africa', 'namibia': 'Africa',
    'niger': 'Africa', 'nigeria': 'Africa', 'republic of the congo': 'Africa',
    'rwanda': 'Africa', 'sao tome and principe': 'Africa', 'senegal': 'Africa',
    'seychelles': 'Africa', 'sierra leone': 'Africa', 'somalia': 'Africa',
    'south africa': 'Africa', 'south sudan': 'Africa', 'sudan': 'Africa',
    'tanzania': 'Africa', 'togo': 'Africa', 'tunisia': 'Africa',
    'uganda': 'Africa', 'zambia': 'Africa', 'zimbabwe': 'Africa',
    
    # OCEANIA
    'australia': 'Oceania', 'fiji': 'Oceania', 'kiribati': 'Oceania',
    'marshall islands': 'Oceania', 'micronesia': 'Oceania', 'nauru': 'Oceania',
    'new zealand': 'Oceania', 'palau': 'Oceania', 'papua new guinea': 'Oceania',
    'samoa': 'Oceania', 'solomon islands': 'Oceania', 'tonga': 'Oceania',
    'tuvalu': 'Oceania', 'vanuatu': 'Oceania',
}

def get_continent(country_name):
    """Get continent from country name"""
    country_lower = country_name.lower().replace('-', ' ')
    return CONTINENT_MAP.get(country_lower, 'Unknown')

def load_metadata():
    """Load CSV metadata"""
    metadata_file = 'csv_metadata.json'
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            return json.load(f)
    return {}

def read_all_csv_files(base_path):
    """Read all CSV files and return users list"""
    users = []
    csv_files = glob.glob(os.path.join(base_path, 'datasource', 'github-certs-*.csv'))
    metadata = load_metadata()
    
    print(f"📂 Processing {len(csv_files)} CSV files...")
    
    for csv_file in csv_files:
        country = os.path.basename(csv_file).replace('github-certs-', '').replace('.csv', '')
        country_display = country.replace('-', ' ').title()
        continent = get_continent(country)
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        badge_count = int(row.get('badge_count', 0))
                        if badge_count > 0:
                            first_name = row.get('first_name', '').strip('"').strip()
                            middle_name = row.get('middle_name', '').strip('"').strip()
                            last_name = row.get('last_name', '').strip('"').strip()
                            profile_url = row.get('profile_url', '').strip('"').strip()
                            company = (row.get('company') or '').strip('"').strip()
                            
                            # Build full name
                            name_parts = [first_name]
                            if middle_name:
                                name_parts.append(middle_name)
                            if last_name:
                                name_parts.append(last_name)
                            full_name = ' '.join(name_parts)
                            
                            users.append({
                                'name': full_name,
                                'badges': badge_count,
                                'country': country_display,
                                'continent': continent,
                                'profile_url': profile_url,
                                'company': company
                            })
                    except (ValueError, KeyError):
                        continue
        except Exception as e:
            print(f"⚠️  Error processing {csv_file}: {e}")
            continue
    
    print(f"✅ Loaded {len(users)} users from all files")
    return users

def get_outdated_csvs():
    """Get list of CSVs that weren't updated in the last run"""
    metadata = load_metadata()
    current_time = datetime.now()
    outdated = []
    
    for country, info in metadata.items():
        last_updated = datetime.fromisoformat(info['last_updated'])
        hours_old = (current_time - last_updated).total_seconds() / 3600
        
        # Consider outdated if more than 25 hours old (1 day + buffer)
        if hours_old > 25:
            outdated.append({
                'country': country,
                'last_updated': last_updated.strftime('%Y-%m-%d %H:%M UTC'),
                'hours_old': int(hours_old)
            })
    
    return sorted(outdated, key=lambda x: x['hours_old'], reverse=True)

def fetch_user_certs(profile_url):
    """Return the set of valid (non-expired, deduplicated) GitHub certification
    names for a user, combining GitHub org badges and allowed Microsoft external
    badges. Cached by profile_url. Returns None on fetch failure so callers can
    omit tooltips instead of showing misleading data."""
    if not profile_url:
        return set()
    if profile_url in _USER_CERTS_CACHE:
        return _USER_CERTS_CACHE[profile_url]

    username = profile_url.split('/')[2] if '/users/' in profile_url else ''
    if not username:
        _USER_CERTS_CACHE[profile_url] = set()
        return set()

    names = set()
    try:
        # GitHub org badges (paginated)
        page = 1
        while True:
            resp = request_with_retries(
                f"https://www.credly.com/users/{username}/badges.json?page={page}&per_page=48",
                timeout=30,
            )
            badges = resp.json().get('data', [])
            if not badges:
                break
            for badge in badges:
                entities = badge.get('issuer', {}).get('entities', [])
                if any(e.get('entity', {}).get('id') == GITHUB_ORG_ID for e in entities):
                    if not is_badge_expired(get_badge_expiry_date(badge)):
                        name = badge.get('badge_template', {}).get('name', '')
                        if name and not is_excluded_badge(name):
                            names.add(name)
            page += 1
            if page > 10:
                break

        # Microsoft-issued external badges (allowlist only, paginated)
        page = 1
        while True:
            resp = request_with_retries(
                f"https://www.credly.com/api/v1/users/{username}/external_badges/open_badges/public?page={page}&page_size=100",
                timeout=30,
            )
            ext_badges = resp.json().get('data', [])
            if not ext_badges:
                break
            for badge in ext_badges:
                eb = badge.get('external_badge', {})
                name = eb.get('badge_name', '').strip()
                if eb.get('issuer_name') == 'Microsoft' and name in ALLOWED_MICROSOFT_GITHUB_CERTIFICATIONS:
                    if not is_badge_expired(get_badge_expiry_date(badge)):
                        names.add(normalize_badge_name(name))
            page += 1
            if page > 10:
                break
    except Exception as e:
        print(f"    ⚠️  Failed to fetch certs for {username}: {e}")
        _USER_CERTS_CACHE[profile_url] = None
        return None

    _USER_CERTS_CACHE[profile_url] = names
    return names


def _cert_tooltip(header, items):
    """Build an HTML title-attribute string with one certification per line.

    &#10; renders as a line break inside the tooltip on GitHub; quotes are
    escaped so they don't terminate the attribute.
    """
    body = '&#10;'.join(i.replace('"', '&quot;') for i in items)
    return f"{header}&#10;{body}" if body else header


def build_cert_emojis(profile_url_rel, profile_full_url):
    """Return the ' 🏅 🎯' emoji suffix (with cert tooltips) for a ranked member.

    🏅 lists all obtained certifications; 🎯 lists the ones missing versus the
    global universe. Returns '' when cert data is unavailable so the name stays
    clean. 🎯 is omitted when the member already holds every known certification.
    """
    certs = fetch_user_certs(profile_url_rel)
    if not certs:
        return ''

    obtained = sorted(certs)
    missing = sorted(GLOBAL_CERT_UNIVERSE - certs)

    ob_tip = _cert_tooltip(f"🏅 Obtained ({len(obtained)}):", obtained)
    suffix = f' [🏅]({profile_full_url} "{ob_tip}")'
    if missing:
        mi_tip = _cert_tooltip(f"🎯 Missing ({len(missing)}):", missing)
        suffix += f' [🎯]({profile_full_url} "{mi_tip}")'
    return suffix


def _compute_positions(filtered_users):
    """Group filtered users into ranking positions (ties share a position, top 10).

    Returns (positions, all_ranked_users) where positions is a list of
    (position_number, [users]) and all_ranked_users is the capped flat list.
    Shared by the render step and the universe pre-pass so both stay in sync.
    """
    sorted_users = sorted(filtered_users, key=lambda x: (-x['badges'], x['name'].lower()))

    positions = []  # list of (position_number, [users])
    current_pos = 0
    prev_badges = None
    for user in sorted_users:
        if user['badges'] != prev_badges:
            current_pos += 1
            prev_badges = user['badges']
            if current_pos > 10:
                break
            positions.append((current_pos, [user]))
        else:
            if current_pos <= 10:
                positions[-1][1].append(user)

    max_users_per_position = 20
    all_ranked_users = []
    for _pos, pos_users in positions:
        all_ranked_users.extend(pos_users[:max_users_per_position])
    return positions, all_ranked_users


def generate_markdown_top10(users, title, filename, filter_func=None):
    """Generate TOP 10 markdown file with position-based ranking (tied users on same row)"""
    
    # Filter users if filter function provided
    if filter_func:
        filtered_users = [u for u in users if filter_func(u)]
    else:
        filtered_users = users
    
    # Compute positions and capped ranked users (shared with the universe pre-pass)
    positions, all_ranked_users = _compute_positions(filtered_users)
    
    # Cap display: if a position has too many tied users, show first N and a count
    MAX_USERS_PER_POSITION = 20
    
    # Get outdated CSVs
    outdated = get_outdated_csvs()
    
    # Generate markdown content
    content = f"""# {title}

> Last updated: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}

## 🏆 Top 10 GitHub Certifications Leaders

| Rank | Name | Badges | Company | Country |
|------|------|--------|---------|---------|
"""
    
    for pos, pos_users in positions:
        medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(pos, '')
        rank_display = f"{medal} #{pos}" if medal else f"#{pos}"
        
        # Cap display for positions with many tied users
        display_users = pos_users[:MAX_USERS_PER_POSITION]
        overflow = len(pos_users) - MAX_USERS_PER_POSITION
        
        # Build cell content for each column, joining tied users with <br>
        names = []
        companies = []
        countries = []
        for user in display_users:
            if user.get('profile_url'):
                profile_url = f"https://www.credly.com{user['profile_url']}"
                emojis = build_cert_emojis(user['profile_url'], profile_url)
                names.append(f"[{user['name']}]({profile_url}){emojis}")
            else:
                names.append(user['name'])
            companies.append(user.get('company', ''))
            countries.append(user['country'])
        
        if overflow > 0:
            names.append(f"*... and {overflow} more*")
            companies.append('')
            countries.append('')
        
        name_cell = '<br>'.join(names)
        badge_cell = str(pos_users[0]['badges'])
        company_cell = '<br>'.join(companies)
        country_cell = '<br>'.join(countries)
        
        content += f"| {rank_display} | {name_cell} | {badge_cell} | {company_cell} | {country_cell} |\n"
    
    # --- Company Rankings (TOP 5) --- based on ALL users in the region, mirroring
    # the country ranking, so totals reflect every certified member rather than
    # only the top-10 ranked users (company is read from the CSV).
    company_stats = defaultdict(lambda: {'badges': 0, 'users': 0})
    for user in filtered_users:
        company = user.get('company', '')
        if company:
            company_stats[company]['badges'] += user['badges']
            company_stats[company]['users'] += 1
    
    if company_stats:
        sorted_companies = sorted(company_stats.items(), key=lambda x: (-x[1]['badges'], -x[1]['users'], x[0].lower()))
        
        # Build TOP 5 positions (with ties)
        company_positions = []
        prev_badges = None
        current_pos = 0
        for company_name, stats in sorted_companies:
            if stats['badges'] != prev_badges:
                current_pos += 1
                prev_badges = stats['badges']
                if current_pos > 5:
                    break
                company_positions.append((current_pos, [(company_name, stats)]))
            else:
                if current_pos <= 5:
                    company_positions[-1][1].append((company_name, stats))
        
        if company_positions:
            content += f"""
---

## 🏢 Top 5 Companies

| Rank | Company | Total Badges | Certified Users |
|------|---------|--------------|-----------------|
"""
            for pos, companies in company_positions:
                medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(pos, '')
                rank_display = f"{medal} #{pos}" if medal else f"#{pos}"
                
                company_names = '<br>'.join(c[0] for c in companies)
                badges_cell = str(companies[0][1]['badges'])
                users_cell = '<br>'.join(str(c[1]['users']) for c in companies)
                
                content += f"| {rank_display} | {company_names} | {badges_cell} | {users_cell} |\n"
    
    # --- Country Rankings (TOP 5) --- only for multi-country rankings
    unique_countries = set(u['country'] for u in filtered_users)
    if len(unique_countries) > 1:
        country_stats = defaultdict(lambda: {'badges': 0, 'users': 0})
        for user in filtered_users:
            country_stats[user['country']]['badges'] += user['badges']
            country_stats[user['country']]['users'] += 1
        
        sorted_countries = sorted(country_stats.items(), key=lambda x: (-x[1]['badges'], -x[1]['users'], x[0].lower()))
        
        # Build TOP 5 positions (with ties)
        country_positions = []
        prev_badges = None
        current_pos = 0
        for country_name, stats in sorted_countries:
            if stats['badges'] != prev_badges:
                current_pos += 1
                prev_badges = stats['badges']
                if current_pos > 5:
                    break
                country_positions.append((current_pos, [(country_name, stats)]))
            else:
                if current_pos <= 5:
                    country_positions[-1][1].append((country_name, stats))
        
        if country_positions:
            content += f"""
---

## 🌐 Top 5 Countries

| Rank | Country | Total Badges | Certified Users |
|------|---------|--------------|-----------------|
"""
            for pos, countries_list in country_positions:
                medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(pos, '')
                rank_display = f"{medal} #{pos}" if medal else f"#{pos}"
                
                country_names = '<br>'.join(c[0] for c in countries_list)
                badges_cell = str(countries_list[0][1]['badges'])
                users_cell = '<br>'.join(str(c[1]['users']) for c in countries_list)
                
                content += f"| {rank_display} | {country_names} | {badges_cell} | {users_cell} |\n"
    
    # Add statistics
    if filtered_users:
        total_users = len(filtered_users)
        total_badges = sum(u['badges'] for u in filtered_users)
        avg_badges = total_badges / total_users if total_users > 0 else 0
        
        content += f"""
---

## 📊 Statistics

- **Total Certified Users**: {total_users:,}
- **Total Badges Earned**: {total_badges:,}
- **Average Badges per User**: {avg_badges:.2f}
- **Highest Badge Count**: {all_ranked_users[0]['badges'] if all_ranked_users else 0}

---
"""
    
    # Add outdated data warning if applicable
    if outdated:
        content += """
## ⚠️ Data Freshness Warning

The following countries have data that was not updated in the last run:

| Country | Last Updated | Hours Old |
|---------|--------------|-----------|
"""
        for item in outdated[:10]:  # Show max 10
            content += f"| {item['country']} | {item['last_updated']} | {item['hours_old']}h |\n"
        
        if len(outdated) > 10:
            content += f"\n*... and {len(outdated) - 10} more countries*\n"
        
        content += "\n---\n"
    
    content += "\n*Data sourced from GitHub Certifications via Credly API*\n"
    
    # Write to file
    output_path = os.path.join(os.path.dirname(__file__), filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Generated: {filename}")

def main():
    """Main execution function"""
    configure_utf8_output()
    print("=" * 80)
    print("GitHub Certifications Rankings Generator")
    print("=" * 80)
    print()
    
    # Get base path
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Read all CSV files
    users = read_all_csv_files(base_path)
    
    if not users:
        print("❌ No users found in CSV files!")
        return
    
    # Ranking specs: (title, filename, filter_func)
    ranking_specs = [
        ("🇧🇷 TOP 10 GitHub Certifications - Brazil", "TOP10_BRAZIL.md",
         lambda u: u['country'].lower() == 'brazil'),
        ("🗽 TOP 10 GitHub Certifications - Americas", "TOP10_AMERICAS.md",
         lambda u: u['continent'] == 'Americas'),
        ("🇪🇺 TOP 10 GitHub Certifications - Europe", "TOP10_EUROPE.md",
         lambda u: u['continent'] == 'Europe'),
        ("� TOP 10 GitHub Certifications - Asia", "TOP10_ASIA.md",
         lambda u: u['continent'] == 'Asia'),
        ("🦁 TOP 10 GitHub Certifications - Africa", "TOP10_AFRICA.md",
         lambda u: u['continent'] == 'Africa'),
        ("🌊 TOP 10 GitHub Certifications - Oceania", "TOP10_OCEANIA.md",
         lambda u: u['continent'] == 'Oceania'),
        ("🌍 TOP 10 GitHub Certifications - Global", "TOP10_WORLD.md", None),
    ]
    
    # Pre-pass: collect every ranked member across ALL rankings, then fetch their
    # certifications to build the global universe used for the "missing" tooltip.
    ranked_profiles = {}
    for _title, _filename, filter_func in ranking_specs:
        subset = [u for u in users if filter_func(u)] if filter_func else users
        _positions, ranked = _compute_positions(subset)
        for u in ranked:
            if u.get('profile_url'):
                ranked_profiles[u['profile_url']] = u
    
    print()
    print(f"🔎 Building certification universe from {len(ranked_profiles)} ranked members...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_user_certs, p): p for p in ranked_profiles}
        for future in as_completed(futures):
            certs = future.result()
            if certs:
                GLOBAL_CERT_UNIVERSE.update(certs)
    print(f"🌐 Universe: {len(GLOBAL_CERT_UNIVERSE)} distinct certifications")

    print()
    print("📝 Generating markdown files...")
    print()
    
    for title, filename, filter_func in ranking_specs:
        generate_markdown_top10(users, title, filename, filter_func)
    
    print()
    print("=" * 80)
    print("✨ All rankings generated successfully!")
    print("=" * 80)

if __name__ == "__main__":
    main()
